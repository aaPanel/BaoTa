#!/usr/bin/python
# coding: utf-8
# Date 2022/3/29
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: lkq <lkq@bt.cn>
# Java 漏洞扫描
# -------------------------------------------------------------------
import json,time,os
import public
from projectModel.base import projectBase
import zipfile
import hashlib

'''
规则库支持两种类型的规则  class 和hash256
第一种就是class 通过class文件来判断是否存在漏洞
第二种就是hash256 通过hash256来判断是否存在漏洞 对比的是jar包的hash256值

增加漏洞的规则操作如下
1.在vlu目录下创建json文件
2.文件内容如下:
   {
              "Name": "Fastjson", #漏洞的名称 如果有ＣＶＥ编号的话就是CVE编号
              "product":"fastjson-",　＃这个模块的关键词
              "types":"class",　　#这个是这个模块的类型 class 或者是hash256 
              "class":["com/alibaba/fastjson/util/TypeUtils.class"],　　# 这个是这个模块的class文件 建议是比较好识别的，每个版本的class文件都不一样
              "vlu_list": [  
              {
                "CVE": "FastJson-1.2.47,FastJson-1.2.68,FastJson-1.2.80", #这个是这个模块的漏洞编号
                "com/alibaba/fastjson/util/TypeUtils.class": "9311585152b2064de8162bc7e933f17f51428115fa08843f0d7b523497072992",  #这个是这个模块的class文件的hash值
                "MavenVersion": "1.2.10" #这个是这个模块的版本号
                "hash256": "b843e17b7b4f748257b1f9e765326dc040c44bc669a4643371b365dd13ef4e6a"  # 这个是这个模块的hash256值
              }
  }

3.增加到cve-database.json中 将这个CVE的信息添加到这个文件中 如上述的FastJson-1.2.47的信息 
  {
    "CVE": "FastJson-1.2.47",  #这个是这个模块的漏洞编号
    "CVSS": 9.8,  #这个是这个模块的漏洞的危险等级
    "DESC": "FASTJSON 1.2.47 及以下版本存在 RCE 漏洞，利用条件较低，危害较大" #这个是这个模块的漏洞的描述
  }
'''
class main(projectBase):
    __config_file = '/www/server/panel/config/java_cve_scanning.json'
    __path='/www/server/panel/class/projectModel/vlu'
    __vlu_name=[]   #存储配置文件中的product name 这个当作遍历jar的时候的关键字
    __vlu_name_class={}   # 存储配置文件中的product name 和对应的class文件
    __vlu_list={}        #存储所有的组件的匹配信息
    __cve_list={}        #存储所有的cve信息


    def _get_config(self):
        if not os.path.exists(self.__path):
            os.makedirs(self.__path)
        #遍历path 一层目录
        for file in os.listdir(self.__path):
            #判断是否为json
            if file.endswith('.json'):
                #判断是否为cve-database.json
                if file == 'cve-database.json':
                    with open(os.path.join(self.__path,file),'r') as f:
                        self.__cve_list=json.load(f)
                else:
                    with open(os.path.join(self.__path,file),'r') as f:
                        try:
                            vlu_list=json.load(f)
                        except:
                            continue
                        if 'product' not in vlu_list:
                            continue
                        if 'class' not in vlu_list:
                            continue
                        if 'vlu_list' not in vlu_list:
                            continue
                        self.__vlu_name.append(vlu_list['product'])
                        self.__vlu_name_class[vlu_list['product']]=vlu_list['class']
                        self.__vlu_list[vlu_list['product']]=vlu_list['vlu_list']

    def __check_auth(self):
        try:
            from pluginAuth import Plugin
            plugin_obj = Plugin(False)
            plugin_list = plugin_obj.get_plugin_list()
            if int(plugin_list['ltd']) > time.time():
                return True
            return False
        except:
            return False

    def is_spring_boot_jar(self,jar):
        """
        判断JAR包是否为Spring Boot项目

        Args:
            jar: 已打开的ZipFile对象

        Returns:
            bool: 是否为Spring Boot项目
        """
        file_list = jar.namelist()

        # 检查Spring Boot特有的标志
        spring_boot_indicators = [
            # 检查Spring Boot启动类
            "org/springframework/boot/loader/",
            # 检查Spring Boot特有目录结构
            "BOOT-INF/classes/",
            "BOOT-INF/lib/"
        ]

        # 检查MANIFEST.MF文件内容是否包含Spring Boot特有的属性
        has_spring_boot_manifest = False
        if "META-INF/MANIFEST.MF" in file_list:
            manifest_content = jar.read("META-INF/MANIFEST.MF").decode('utf-8', errors='ignore')
            spring_boot_manifest_indicators = [
                "Spring-Boot-Version:",
                "Spring-Boot-Classes:",
                "Spring-Boot-Lib:",
                "Main-Class: org.springframework.boot.loader."
            ]

            for indicator in spring_boot_manifest_indicators:
                if indicator in manifest_content:
                    has_spring_boot_manifest = True
                    break

        # 检查其他Spring Boot特有文件
        for indicator in spring_boot_indicators:
            for file_name in file_list:
                if file_name.startswith(indicator):
                    return True

        return has_spring_boot_manifest

    def get_spring_boot_libs(self,jar):
        """
        获取Spring Boot项目中的所有库文件

        Args:
            jar: 已打开的ZipFile对象

        Returns:
            list: 库文件列表
        """
        lib_files = []
        for file_name in jar.namelist():
            if file_name.startswith("BOOT-INF/lib/") and file_name.endswith(".jar"):
                lib_files.append(file_name)
        return lib_files

    def calculate_sha256(self,data):
        """
        计算数据的SHA-256哈希值

        Args:
            data: 二进制数据

        Returns:
            str: SHA-256哈希值的十六进制表示
        """
        sha256_hash = hashlib.sha256()
        sha256_hash.update(data)
        return sha256_hash.hexdigest()


    def get_jar_class_hash256(self,main_jar, shiro_jars, target_classes):
        """
        main_jar : 主JAR文件路径

        从主JAR中读取嵌套JAR的字节数据，直接在内存中操作，无需解压。
        Args:
            main_jar: 已打开的主JAR文件
            shiro_jars: Shiro相关JAR文件列表
            target_classes : 目标Class文件列表

        Returns:
            dict: 包含目标Class文件SHA-256哈希值的字典
        """
        # 定义要查找的Class文件
        class_hashes = {}
        # 分析每个Shiro JAR（直接在内存中操作）
        for lib_file, jar_name in shiro_jars:
            # 从主JAR中读取嵌套JAR的字节数据
            nested_jar_data = main_jar.read(lib_file)
            from io import BytesIO
            nested_jar_bytes = BytesIO(nested_jar_data)
            # 直接从内存中打开嵌套JAR
            try:
                with zipfile.ZipFile(nested_jar_bytes) as shiro_jar:
                    for target_class in target_classes:
                        normalized_class = target_class
                        if not normalized_class.endswith(".class"):
                            normalized_class += ".class"
                        try:
                            class_data = shiro_jar.read(normalized_class)
                            sha256 = self.calculate_sha256(class_data)
                            class_hashes[normalized_class] = sha256
                            class_hashes["lib_path"] = lib_file
                        except KeyError:
                            continue
            except zipfile.BadZipFile:
                continue
            except Exception as e:
                continue
        return class_hashes

    def get_jar_hash256(self,main_jar_path):
        """
        Args:
            main_jar_path: 主JAR文件的路径
        """
        list_hash={}
        if not os.path.exists(main_jar_path):
            return list_hash
        try:
            # 打开主JAR文件
            with zipfile.ZipFile(main_jar_path, 'r') as main_jar:
                # 检查是否为Spring Boot项目
                is_spring_boot = self.is_spring_boot_jar(main_jar)
                if not is_spring_boot:
                    return list_hash
                lib_files = self.get_spring_boot_libs(main_jar)
                for lib_name in lib_files:
                    for vlu_name in self.__vlu_name:
                        if vlu_name in lib_name:
                            shiro_jars = []
                            target_classes = []
                            for class_name in self.__vlu_name_class[vlu_name]:
                                target_classes.append(class_name)
                            jar_name = os.path.basename(lib_name)
                            shiro_jars.append((lib_name, jar_name))
                            class_hashes = self.get_jar_class_hash256(main_jar, shiro_jars, target_classes)
                            list_hash[vlu_name]=class_hashes

        except zipfile.BadZipFile:
            return list_hash
        except Exception as e:
            return list_hash
        return list_hash


    def get_jar_vulnerabilities(self,get):
        """
        获取JAR漏洞信息
        Args:
            get: 请求参数
        """
        self._get_config()
        # __vlu_name = []  # 存储配置文件中的product name 这个当作遍历jar的时候的关键字
        # __vlu_name_class = {}  # 存储配置文件中的product name 和对应的class文件
        # __vlu_list = {}  # 存储所有的组件的匹配信息
        # __cve_list = {}  # 存储所有的cve信息
        get_vlu_hash=self.get_jar_hash256(get.path)
        # if len(get_vlu_hash)==0:
        #     return public.returnMsg(False, '未发现相关漏洞')
        tmp_vlu_list={}

        if len(get_vlu_hash) > 0:
            for i in get_vlu_hash:
                if i in self.__vlu_list:
                    for j in self.__vlu_list[i]:
                        #获取get_vlu_hash[i] 的keys 判断j 中是否存在
                        for k in get_vlu_hash[i]:
                            if k in j:
                                # 判断hash值是否相等
                                    if get_vlu_hash[i][k]==j[k]:
                                        #通过遍历CVE 来确定这个项目中存在的漏洞
                                        cve_list=j["CVE"].split(',')
                                        for cv in cve_list:
                                            if cv not in tmp_vlu_list:
                                                tmp_vlu_list[cv]={}
                                                tmp_vlu_list[cv]["CVE"]=cv
                                                tmp_vlu_list[cv]["class"]=k
                                                tmp_vlu_list[cv]["hash256"]=j[k]
                                                tmp_vlu_list[cv]["lib"]=get_vlu_hash[i]["lib_path"]
                                                tmp_vlu_list[cv]["jar"]=get.path
                                                tmp_vlu_list[cv]["cvss"]=0.0
                                                tmp_vlu_list[cv]["desc"]=""
                                                tmp_vlu_list[cv]["product"]=False
        # if len(tmp_vlu_list)==0:
        #     return public.returnMsg(False, '未发现相关漏洞')
        if len(tmp_vlu_list) > 0:
            for i in tmp_vlu_list:
                for j in self.__cve_list:
                    if i ==j["CVE"]:
                        tmp_vlu_list[i]["cvss"]=j["CVSS"]
                        tmp_vlu_list[i]["desc"]=j["DESC"]
        return  tmp_vlu_list

    def scan_sites_vlu_list(self,get):
        infos=public.M("sites").where("project_type=?","Java").select()
        result={"count":0,"time":time.time(),"list":[],"pay":self.__check_auth()}

        for i in infos:
            if not os.path.exists(i["path"]):
                continue
            get.path=i["path"]
            #判断是否为jar
            if not i["path"].endswith('.jar'):
                continue
            vlu_list=self.get_jar_vulnerabilities(get)
            
            if len(vlu_list)>0:
                site_item = {"title": i["name"], "list": []}
                for vlu_key in vlu_list:
                    site_item["list"].append(vlu_list[vlu_key])
                result["count"]+=len(vlu_list)
                result["list"].append(site_item)

        return public.returnMsg(True, result)


    def sync_update_rule(self,get):
        "更新规则库"
        url="https://download.bt.cn/btwaf_rule/vlu/"
        import requests
        result={}
        try:
            data_list=requests.get(url+"/java_list.json").json()
            for i in data_list:
                data=requests.get(url+i).json()
                result[i]=data
        except:
            return public.returnMsg(False, '获取规则库失败')

        #判断result 是否为空
        if len(result)==0:
            return public.returnMsg(False, '获取规则库失败')
        for i in result:
            with open(os.path.join(self.__path,i),'w') as f:
                f.write(json.dumps(result[i]))

        return public.returnMsg(True, '更新规则库成功')