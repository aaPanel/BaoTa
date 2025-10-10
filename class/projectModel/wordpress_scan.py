# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2024-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: lkq <safe@bt.cn>
# +-------------------------------------------------------------------
# |   Wordpress 安全扫描
# +--------------------------------------------------------------------
import re
import os
#进入到
from projectModel import totle_db
class wordpress_scan:

    #默认插件的头部信息
    plugin_default_headers = {
        "Name": "Plugin Name",
        "PluginURI": "Plugin URI",
        "Version": "Version",
        "Description": "Description",
        "Author": "Author",
        "AuthorURI": "Author URI",
        "TextDomain": "Text Domain",
        "DomainPath": "Domain Path",
        "Network": "Network",
        "RequiresWP": "Requires at least",
        "RequiresPHP": "Requires PHP",
        "UpdateURI": "Update URI",
        "RequiresPlugins": "Requires Plugins",
        "_sitewide": "Site Wide Only"
    }

    #默认主题的头部信息
    theme_default_headers = {
        "Name": "Theme Name",
        "Title": "Theme Name",
        "Version": "Version",
        "Author": "Author",
        "AuthorURI": "Author URI",
        "UpdateURI": "Update URI",
        "Template": "Theme Name",
        "Stylesheet": "Theme Name",
    }

    def M(self, table):
        '''
            @name 获取数据库对象
            @param table 表名
            @param db 数据库名
        '''
        with totle_db.Sql().dbfile("../wordpress") as sql:
            return sql.table(table)

    def get_plugin_data(self, plugin_file, default_headers, context=''):
        '''
            @参考：/wp-admin/includes/plugin.php get_plugin_data 代码
            @name 获取插件信息
            @param plugin_file 插件文件
            @return dict
            @auther lkq
            @time 2024-10-08
        '''
        # 读取文件内容
        if not os.path.exists(plugin_file): return {}
        # 定义8KB大小
        max_length = 8 * 1024  # 8 KB
        try:
            # 读取文件的前8KB
            with open(plugin_file, 'r', encoding='utf-8') as file:
                file_data = file.read(max_length)
        except Exception as e:
            return {}
        # 替换CR为LF
        file_data = file_data.replace('\r', '\n')
        # 处理额外的headers
        extra_headers = {}
        if context:
            extra_context_headers = []
            # 假设有一个函数可以获取额外的headers
            # extra_context_headers = get_extra_headers(context)
            extra_headers = dict.fromkeys(extra_context_headers, '')  # 假设额外的headers
        all_headers = {**extra_headers, **default_headers}

        # 检索所有headers
        for field, regex in all_headers.items():
            if field.startswith('_'):  # 跳过以_开头的内部字段
                continue
            match = re.search(f'{regex}:(.*)$', file_data, re.IGNORECASE | re.MULTILINE)
            if match:
                all_headers[field] = match.group(1).strip()
            else:
                all_headers[field] = ''
        if all_headers.get("Network") and not all_headers['Network'] and all_headers['_sitewide']:
            all_headers['Network'] = all_headers['_sitewide']
        if all_headers.get("Network"):
            all_headers['Network'] = 'true' == all_headers['Network'].lower()
        if all_headers.get("_sitewide"):
            del all_headers['_sitewide']

        if all_headers.get("TextDomain") and not all_headers['TextDomain']:
            plugin_slug = os.path.dirname(os.path.basename(plugin_file))
            if '.' != plugin_slug and '/' not in plugin_slug:
                all_headers['TextDomain'] = plugin_slug

        all_headers['Title'] = all_headers['Name']
        all_headers['AuthorName'] = all_headers['Author']

        # 返回插件的信息
        return all_headers

    def Md5(self,strings):
        """
            @name    生成MD5
            @author hwliang<hwl@bt.cn>
            @param strings 要被处理的字符串
            @return string(32)
        """
        if type(strings) != bytes:
            strings = strings.encode()
        import hashlib
        m = hashlib.md5()
        m.update(strings)
        return m.hexdigest()

    def FileMd5(self,filename):
        """
            @name 生成文件的MD5
            @author hwliang<hwl@bt.cn>
            @param filename 文件名
            @return string(32) or False
        """
        if not os.path.isfile(filename): return False
        import hashlib
        my_hash = hashlib.md5()
        f = open(filename, 'rb')
        while True:
            b = f.read(8096)
            if not b:
                break
            my_hash.update(b)
        f.close()
        return my_hash.hexdigest()
    def get_plugin(self, path,one=''):
        '''
            @name 获取WordPress插件信息
            @param path 插件路径
            @return dict
            @auther lkq
            @time 2024-10-08
        '''
        plugin_path = path + "/wp-content/plugins"
        if not os.path.exists(plugin_path): return {}
        tmp_list = []
        for file in os.listdir(plugin_path):
            if one:
                if file!=one:continue
            plugin_file = os.path.join(plugin_path, file)
            # if os.path.isfile(plugin_file) and plugin_file.endswith(".php"):
            #     tmp_list.append(file)
            if os.path.isdir(plugin_file):
                # 读取文件夹中的第一层文件
                for file2 in os.listdir(plugin_file):
                    plugin_file2 = os.path.join(plugin_file, file2)
                    if os.path.isfile(plugin_file2) and plugin_file2.endswith(".php"): tmp_list.append(
                        file + "/" + file2)
        if len(tmp_list) == 0: return {}
        result = {}

        for i in tmp_list:
            plugin_file = plugin_path + "/" + i
            # 判断文件是否可读
            if not os.access(plugin_file, os.R_OK): continue
            plugin_data = self.get_plugin_data(plugin_file, self.plugin_default_headers)
            if not plugin_data: continue
            if plugin_data["Name"] == "": continue
            #如果 name 中没/ 的话
            if "/" not in i:
                #则判断一下
                if 'wordpress.org/plugins/' in  plugin_data["PluginURI"]:
                    plugin_data["PluginURI"] = plugin_data["PluginURI"].replace('http://wordpress.org/plugins/', '').replace("http://wordpress.org/plugins/","")
                    #去掉最后的/
                    if plugin_data["PluginURI"][-1]=="/":
                        plugin_data["PluginURI"]=plugin_data["PluginURI"][:-1]
                    i=plugin_data["PluginURI"]
                else:
                    continue
            result[i] = plugin_data
        return result


    def compare_versions(self,version1, version2):
        '''
            @name 对比版本号
            @param version1 版本1
            @param version2 版本2
            @return int  0 相等 1 大于 -1 小于
        '''
        # 分割版本号为整数列表
        v1 = [int(num) for num in version1.split('.')]
        v2 = [int(num) for num in version2.split('.')]
        # 逐个比较版本号的每个部分
        for num1, num2 in zip(v1, v2):
            if num1 > num2:
                return 1  # version1 > version2
            elif num1 < num2:
                return -1  # version1 < version2
        # 如果所有部分都相同，比较长度（处理像'1.0'和'1.0.0'这样的情况）
        if len(v1) > len(v2):
            return 1 if any(num > 0 for num in v1[len(v2):]) else 0
        elif len(v1) < len(v2):
            return -1 if any(num > 0 for num in v2[len(v1):]) else 0
        # 如果完全相同
        return 0
    def let_identify(self,version,vlun_infos):
        '''
            @name 对比版本号判断是否存在漏洞
            @param version 当前版本
            @param vlun_infos 漏洞信息
            @return list
        '''
        for i in vlun_infos:
            i["vlun_status"] = False
            #如果是小于等于的话
            if i["let"]=="<=":
                if self.compare_versions(version,i["vlun_version"])<=0:
                    i["vlun_status"]=True
            #小于
            if i["let"]=="<":
                if self.compare_versions(version,i["vlun_version"])<0:
                    i["vlun_status"]=True
            if i['let']=='-':
                #从某个版本开始、到某个版本结束
                version_list=i["vlun_version"].split("-")
                if len(version_list)!=2:continue
                if self.compare_versions(version,version_list[0])>=0 and self.compare_versions(version,version_list[1])<=0:
                    i["vlun_status"]=True

        return vlun_infos

    def scan(self,path):
        '''
            @name 扫描WordPress
            @param path WordPress路径
            @return dict
            @auther lkq
            @time 2024-10-10
            @msg 通过扫描WordPress的版本、插件、主题来判断是否存在漏洞
        '''
        vlun_list = []
        #判断文件是否存在
        import os
        if not os.path.exists(path):
            return vlun_list
        result = {}
        result["plugins"] = self.get_plugin(path)
        #扫描插件是否存在漏洞
        for i in result["plugins"]:
            plguin=i.split("/")[0]
            Name=result["plugins"][i]["Name"]
            if result["plugins"][i]["Version"]=="":continue
            #检查插件是否存在漏洞
            if self.M("vulnerabilities").where("plugin=?",(plguin,)).count()>0:
                vlun_infos=self.M("vulnerabilities").where("plugin=?",(plguin)).select()
                vlun_infos=self.let_identify(result["plugins"][i]["Version"],vlun_infos)
                for j2 in vlun_infos:
                    if j2["vlun_status"]:
                        vlun = {"name": "", "vlun_info": "", "css": "", "type": "plugin", "load_version": "","cve": "","time":""}
                        vlun["load_version"]=result["plugins"][i]["Version"]
                        vlun["cve"]=j2["cve"]
                        vlun["slug"]=plguin
                        vlun["name"] = Name
                        vlun["vlun_info"]=j2["msg"]
                        vlun["css"]=j2["css"]
                        vlun["time"] = j2["time"]
                        vlun_list.append(vlun)

        return vlun_list