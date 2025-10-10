# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: lkq <lkq@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# Java模型
# ------------------------------
import os, sys, re, json, shutil, psutil, time
import datetime
import pwd
from projectModel.base import projectBase
from projectModel.watchModel import use_project_watch, add_project_watch, del_project_watch
import public, firewalls

try:
    from BTPanel import cache
except:
    pass
from xml.etree.ElementTree import ElementTree, Element


class mobj:
    port = ps = ''


class main(projectBase):
    _panel_path = public.get_panel_path()
    __bttomcat_path = '/usr/local/bttomcat'
    __jdk_path = '/usr/lib/jvm/'
    __btjdk_path = '/usr/local/btjdk/'
    _log_name = '项目管理'
    __tomcat7_server = '/usr/local/bttomcat/tomcat7/conf/server.xml'
    __tomcat8_server = '/usr/local/bttomcat/tomcat8/conf/server.xml'
    __tomcat9_server = '/usr/local/bttomcat/tomcat9/conf/server.xml'
    __tomcat7_path = '/usr/local/bttomcat/tomcat7'
    __tomcat8_path = '/usr/local/bttomcat/tomcat8'
    __tomcat9_path = '/usr/local/bttomcat/tomcat9'
    __tomcat7_path_bak = '/usr/local/bttomcat/tomcat_bak7'
    __tomcat8_path_bak = '/usr/local/bttomcat/tomcat_bak8'
    __tomcat9_path_bak = '/usr/local/bttomcat/tomcat_bak9'
    __site_path = '/www/server/bt_tomcat_web/'
    _springboot = '/var/tmp/springboot'
    _springboot_pid_path = '{}/vhost/pids'.format(_springboot)
    _springboot_logs_path = '/www/wwwlogs/java/springboot'
    _springboot_logs = '{}/vhost/logs'.format(_springboot)
    _springboot_run_scripts = '{}/vhost/scripts'.format(_springboot)
    __log_split_script_py = public.get_panel_path() + '/script/run_log_split.py'
    _pids = None
    __TREE = None
    __ENGINE = None
    __ROOT = None
    __CONF_FILE = ''
    __CONNECTROR = ''
    _vhost_path = '{}/vhost'.format(_panel_path)
    
    def __init__(self):
        if not os.path.exists(self.__site_path):
            os.makedirs(self.__site_path)
        if not os.path.exists(self.__bttomcat_path):
            os.makedirs(self.__bttomcat_path)
        if not os.path.exists(self.__btjdk_path):
            os.makedirs(self.__btjdk_path)
        if not os.path.exists(self._springboot):
            os.makedirs(self._springboot)
        if not os.path.exists(self._springboot_pid_path):
            os.makedirs(self._springboot_pid_path)
        if not os.path.exists(self._springboot_logs_path):
            os.makedirs(self._springboot_logs_path)
        if not os.path.exists(self._springboot_logs):
            os.makedirs(self._springboot_logs)
        if not os.path.exists(self._springboot_run_scripts):
            os.makedirs(self._springboot_run_scripts)
    
    def test(self, get):
        
        return type(get.domains)
    
    def get_os_version(self, get):
        """
        @name 获取操作系统版本的安装命令
        @author lkq<2021-08-25>
        @param get<dict_obj>
        @return string
        """
        # 获取Centos
        if os.path.exists('/usr/bin/yum') and os.path.exists('/etc/yum.conf'):
            return 'Centos'
        # 获取Ubuntu
        if os.path.exists('/usr/bin/apt-get') and os.path.exists('/usr/bin/dpkg'):
            return 'Ubuntu'
        return 'Unknown'
    
    def get_jdk_version(self, get):
        '''
        @name 获取JDK 版本
        @author lkq<2021-08-25>
        @param get<dict_obj>
        @return string
        '''
        ret = []
        ret2 = {}
        if not 'JDK11' in ret2:
            ret2['JDK11'] = {}
            ret2['JDK11']['status'] = False
        if not 'JDK8' in ret2:
            ret2['JDK8'] = {}
            ret2['JDK8']['status'] = False
        if not os.path.exists(self.__jdk_path): return ret2
        for root, dirs, files in os.walk(self.__jdk_path):
            for i2 in dirs:
                if not os.path.islink(self.__jdk_path + i2):
                    ret.append(self.__jdk_path + i2)
            break
        for i in ret:
            if os.path.exists(i):
                if 'java-1.8' in i or 'java-8' in i:
                    # 检查jdk是否可用
                    result = self.check_jdk(i)
                    java_ret = {}
                    if result:
                        java_ret['path'] = result
                        java_ret['status'] = True
                        java_ret['is_error'] = False
                    else:
                        java_ret['is_error'] = True
                    ret2['JDK8'] = java_ret
                if 'java-11' in i or 'openjdk-11' in i:
                    result = self.check_jdk(i)
                    java_ret = {}
                    if result:
                        java_ret['path'] = i
                        java_ret['is_error'] = False
                        java_ret['status'] = True
                    else:
                        java_ret['is_error'] = True
                    ret2['JDK11'] = java_ret
        return ret2
    
    def install_jdk(self, get):
        '''
        @name 安装JDK 版本
        @author lkq<2021-08-25>
        @param get<dict_obj>
        @param get.jdk_version<string>
        @return string
        '''
        tmp_file = '/tmp/panelShell.pl'
        jdk_version = get.jdk_version.strip()
        if jdk_version == '': return public.returnMsg(False, 'JDK版本不能为空!')
        jdk_list = ['8', '11']
        if not jdk_version in jdk_list: return public.returnMsg(False, 'JDK版本只能为8或11!')
        os_version = self.get_os_version(None)
        if os_version == 'Centos':
            if jdk_version == '8':
                public.ExecShell('yum install java-1.8.0-openjdk  java-1.8.0-openjdk-devel -y >>%s' % tmp_file)
            elif jdk_version == '11':
                public.ExecShell('yum install java-11-openjdk java-11-openjdk-devel -y >>%s' % tmp_file)
            else:
                return public.returnMsg(False, 'JDK版本只能为8或11!')
            # 检查jdk是否可用
            jdk_data = self.get_jdk_version(None)
            if jdk_data['JDK%s' % jdk_version]['status']:
                # public.WriteFile(tmp_file,'Successify','a+')
                return public.returnMsg(True, '安装成功!')
            else:
                public.WriteFile(tmp_file, 'Error:请查看yum源是否正常', 'a+')
                return public.returnMsg(False, '安装失败!')
        elif os_version == 'Ubuntu':
            if jdk_version == '8':
                public.ExecShell('apt-get install -y openjdk-8-jre openjdk-8-jdk >>%s' % tmp_file)
            elif jdk_version == '11':
                public.ExecShell('apt-get install -y openjdk-11-jre openjdk-11-jdk >>%s' % tmp_file)
            else:
                return public.returnMsg(False, 'JDK版本只能为8或11!')
            # 检查jdk是否可用
            jdk_data = self.get_jdk_version(None)
            if jdk_data['JDK%s' % jdk_version]['status']:
                # public.WriteFile(tmp_file,'Successify','a+')
                return public.returnMsg(True, '安装成功!')
            else:
                public.WriteFile(tmp_file, 'Error:请查看apt源是否正常', 'a+')
                return public.returnMsg(False, '安装失败!')
        else:
            public.WriteFile(tmp_file, 'Error:不支持此操作系统', 'a+')
            return public.returnMsg(False, '操作系统不支持!')
    
    def remove_jdk(self, get):
        '''
        @name 删除JDK
        @author lkq
        @param get
        @param get.jdk_version JDK版本
        @return
        '''
        jdk_version = get.jdk_version.strip()
        os_version = self.get_os_version(None)
        tmp_file = '/tmp/panelShell.pl'
        if os_version == 'Centos':
            if jdk_version == '8':
                public.ExecShell('yum remove java-1.8.0-openjdk  java-1.8.0-openjdk-devel -y >>%s' % tmp_file)
            elif jdk_version == '11':
                public.ExecShell('yum remove java-11-openjdk java-11-openjdk-devel -y >>%s' % tmp_file)
            else:
                return public.returnMsg(False, 'JDK版本只能为8或11!')
            # public.WriteFile(tmp_file,'Successify','a+')
            return public.returnMsg(True, '卸载成功')
        elif os_version == 'Ubuntu':
            if jdk_version == '8':
                public.ExecShell('apt-get remove -y openjdk-8-jre openjdk-8-jdk >>%s' % tmp_file)
            elif jdk_version == '11':
                public.ExecShell('apt-get remove -y openjdk-11-jre  openjdk-11-jdk>>%s' % tmp_file)
            else:
                return public.returnMsg(False, 'JDK版本只能为8或11!')
            # public.WriteFile(tmp_file,'Successify','a+')
            return public.returnMsg(True, '卸载成功')
    
    def check_jdk(self, jdk_path=None):
        '''
        @name  检查JDK版本是否可以用
        @author lkq<2021-08-25>
        @param get<dict_obj>
        @return string
        '''
        java_path = jdk_path + '/jre/bin/java'
        java_path2 = jdk_path + '/bin/java'
        if os.path.exists(java_path):
            ret = public.ExecShell(java_path + ' -version')
            if ret[0].find('Error occurred') != -1:
                return False
            return java_path
        elif os.path.exists(java_path2):
            ret = public.ExecShell(java_path2 + ' -version')
            if ret[0].find('Error occurred') != -1:
                return False
            return java_path2
        else:
            return False
    
    def replace_jdk_version(self, get):
        '''
        @name 修改JDK版本
        @author lkq<2021-08-27>
        @param get.tomcat_start  tomcat启动脚本路径
        @param get.jdk_path  JDK路径
        @return string
        '''
        jdk_path = get.jdk_path.strip()
        jdk_path2 = jdk_path.split('/')
        if jdk_path2[-1] == 'java':
            if jdk_path2[-3] == 'jre':
                jdk_path2 = '/'.join(jdk_path2[:-3])
            if jdk_path2[-2] == 'bin':
                jdk_path2 = '/'.join(jdk_path2[:-2])
        else:
            jdk_path2 = '/'.join(jdk_path2[:-1])
        # 检查jdk是否可用
        jdk_path = jdk_path2
        jdk_data = self.check_jdk(jdk_path)
        if not jdk_data: return public.returnMsg(False, '请输入正确的JDK路径,例如:/www/server/jdk1.8/bin/java')
        if jdk_data:
            if not os.path.exists(jdk_data): return public.returnMsg(False, 'JDK目录不存在!')
        if not jdk_data: return public.returnMsg(False, '当前输入的JDK不可用!')
        tomcat_start = get.tomcat_start.strip()
        if not os.path.exists(tomcat_start): return public.returnMsg(False, 'tomcat启动脚本不存在!')
        tomcat_start_file = public.ReadFile(tomcat_start)
        if isinstance(tomcat_start_file, str):
            # 正则匹配到jdk_path
            jdk_path_re = re.findall('^JAVA_HOME=(.*)$', tomcat_start_file, re.M)
            if jdk_path_re:
                tomcat_start_file = tomcat_start_file.replace(jdk_path_re[0], jdk_path)
                public.WriteFile(tomcat_start, tomcat_start_file)
                # 重启服务
                public.ExecShell('bash %s stop' % (tomcat_start))
                public.ExecShell('bash %s start' % (tomcat_start))
                return public.returnMsg(True, '修改成功!')
        return public.returnMsg(False, '修改失败!')
    
    def get_tomcat_version(self, get):
        '''
        @name 获取tomcat版本信息
        @author lkq<2021-08-27>
        @param get<dict_obj>
        @return string
        '''
        ret = ["7", "8", "9", "10"]
        default_path = "/usr/local/btjdk/jdk8/bin/java"
        ret2 = {
            'tomcat7': {'status': False, "jdk_path": default_path},
            'tomcat8': {'status': False, "jdk_path": default_path},
            'tomcat9': {'status': False, "jdk_path": default_path},
            'tomcat10': {'status': False, "jdk_path": default_path},
        }
        rep_deemon_sh = re.compile(r"^JAVA_HOME=(?P<path>.*)\n", re.M)
        for i in ret:
            tmp_path = self.__bttomcat_path + '/tomcat' + i + "/bin/daemon.sh"
            if os.path.exists(tmp_path):
                tmp_data = public.readFile(tmp_path)
                if isinstance(tmp_data, str):
                    re_res_jdk_path = rep_deemon_sh.search(tmp_data)
                    if re_res_jdk_path:
                        ret2["tomcat" + i]["jdk_path"] = re_res_jdk_path.group("path").strip()
                ret2["tomcat" + i]["status"] = True
                ret2["tomcat" + i]["path"] = self.__bttomcat_path + '/tomcat' + i
                ret2["tomcat" + i]["start_path"] = "/etc/init.d/bttomcat" + i
                ret2["tomcat" + i]["info"] = self.get_tomcat_info(version = i)
                if i == '7':
                    ret2["tomcat" + i]["tomcat_server"] = self.__tomcat7_server
                    ret2["tomcat" + i]["tomcat_start"] = self.__tomcat7_path + '/bin/daemon.sh'
                elif i == '8':
                    ret2["tomcat" + i]["tomcat_server"] = self.__tomcat8_server
                    ret2["tomcat" + i]["tomcat_start"] = self.__tomcat8_path + '/bin/daemon.sh'
                elif i == '9':
                    ret2["tomcat" + i]["tomcat_server"] = self.__tomcat9_server
                    ret2["tomcat" + i]["tomcat_start"] = self.__tomcat9_path + '/bin/daemon.sh'
                elif i == '10':
                    ret2["tomcat" + i]["tomcat_server"] = '/usr/local/bttomcat/tomcat10/conf/server.xml'
                    ret2["tomcat" + i]["tomcat_start"] = "/usr/local/bttomcat/tomcat10/bin/daemon.sh"
        return ret2
    
    def get_tomcat_info(self, version):
        '''
        @name 获取tomcat版本信息
        @author lkq<2021-08-27>
        @param version  tomcat版本 7 8 9
        @return string
        '''
        tmp = {}
        tmp_path = '/usr/local/bttomcat/tomcat%s/conf/server.xml' % version
        if os.path.exists(tmp_path):
            if not self.Initialization(version):
                tmp["port"] = False
            else:
                tmp["port"] = self.get_port()
            tmp['status'] = self.get_server(version)
            tmp['conf'] = public.readFile(tmp_path)
            tmp['jdk_path'] = self.get_jdk_path(version)
            # tmp['log'] = public.GetNumLines('/usr/local/bttomcat/tomcat%s/logs/catalina-daemon.out'%version, 3000)
            tmp['stype'] = 'built'
        else:
            tmp['status'] = False
            tmp["port"] = False
            tmp['conf'] = False
            tmp['jdk'] = False
            tmp['log'] = False
            tmp['stype'] = 'uninstall'
        return tmp
    
    def install_tomcat(self, get):
        '''
        @name 安装tomcat版本
        @author lkq<2021-08-27>
        @param get<dict_obj>
        @param get.version 安装|卸载的版本
        @param get.type    install ==安装  uninstall ==卸载
        @return string
        '''
        tmp_file = '/tmp/panelShell2.pl'
        if not os.path.exists(tmp_file):
            public.ExecShell("touch /tmp/panelShell2.pl")
        else:
            public.ExecShell("echo ""> /tmp/panelShell2.pl")
        version = str(get.version)
        os_ver = self.get_os_version(None)
        if 'type' not in get:
            return public.returnMsg(False, '参数错误!')
        type_list = ['install', 'uninstall']
        if not get.type in type_list:
            return public.returnMsg(False, '安装卸载只能是install或者uninstall!')
        if version == "7":
            if os_ver == 'Ubuntu':
                return public.returnMsg(False, '操作系统不支持!')
        download_url = self.test_download_url()
        if get.type != 'install' and os.path.exists("/tmp/1.sh"):
            public.ExecShell("bash /tmp/1.sh %s %s >>%s" % (get.type, version, tmp_file))
        else:
            if download_url is None:
                error = '<br>错误：连接宝塔官网异常，请按照以下方法排除问题后重试：<br>解决方法：<a target="_blank" class="btlink" href="https://www.bt.cn/bbs/thread-87257-1-1.html">https://www.bt.cn/bbs/thread-87257-1-1.html</a><br>'
                raise public.PanelError(error)
                # return public.returnMsg(False, '网络链接错误<br>请尝试检查网络配置或更换节点')
            public.ExecShell(
                "rm -rf /tmp/1.sh && /usr/local/curl/bin/curl -o /tmp/1.sh %s/install/src/webserver/shell/new_jdk.sh && bash  /tmp/1.sh %s %s >>%s" % (
                download_url, get.type, version, tmp_file)
            )
        
        # self.collect_msg("tomcat-{}".format(version), log_path=tmp_file)
        tomcat_status = self.get_tomcat_version(None)
        if get.type == 'install':
            if tomcat_status['tomcat' + version]['status']:
                return public.returnMsg(True, '安装成功!')
            else:
                return public.returnMsg(False, '安装失败!')
        else:
            if not tomcat_status['tomcat' + version]['status']:
                return public.returnMsg(True, '卸载成功!')
            else:
                return public.returnMsg(False, '卸载失败!')
    
    @staticmethod
    def test_download_url():
        _sh = """
. /www/server/panel/install/public.sh
curl -s -o /dev/null "${NODE_URL}"
if [ $? -ne 0 ]; then
  echo "网络链接错误"
  exit
fi
echo "${NODE_URL}"
"""
        res: str = public.ExecShell(_sh)[0]
        if res.find("网络链接错误") != -1:
            return None
        else:
            return res.split("\n")[-2].strip()
    
    @staticmethod
    def _get_jdk_version_by_jdk_path(jdk_path):
        pass
    
    def install_tomcat_new(self, get):
        '''
        @name 安装tomcat版本
        @author lkq<2021-08-27>
        @param get<dict_obj>
        @param get.version 安装|卸载的版本
        @param get.type    install ==安装  uninstall ==卸载
        @param get.jdk_path 使用其他的jdk版本
        @return string
        '''
        try:
            jdk_path = ""
            version = str(int(get.version))
            action = get.type.strip()
            if "jdk_path" in get:
                jdk_path = get.jdk_path.strip()
        except (AttributeError, TypeError, ValueError):
            return public.returnMsg(False, "参数错误")
        
        if action not in ('install', 'uninstall'):
            return public.returnMsg(False, '安装卸载只能是install或者uninstall!')
        os_ver = self.get_os_version(None)
        if version == "7":
            if os_ver == 'Ubuntu':
                return public.returnMsg(False, '操作系统不支持!')
        
        if jdk_path:
            if jdk_path.endswith("/bin/java"):
                jdk_path = jdk_path[:-9]
            _, error = public.ExecShell("{}/bin/java -version".format(jdk_path))  # 信息在标准错误
            # public.print_log(_)
            # public.print_log(error)
            if not (error.find("version") != -1 and error.find("Runtime") != -1):
                return public.returnMsg(False, "指定的jdk不可用")
        
        tmp_file = '/tmp/panelShell2.pl'
        public.writeFile(tmp_file, "")
        
        download_url = self.test_download_url()
        if download_url is None:
            error = (
                '<br>错误：连接宝塔官网异常，请按照以下方法排除问题后重试：<br>解决方法：'
                '<a target="_blank" class="btlink" href="https://www.bt.cn/bbs/thread-87257-1-1.html">'
                'https://www.bt.cn/bbs/thread-87257-1-1.html</a><br>'
            )
            raise public.PanelError(error)
        
        shell_str = (
                        'rm -rf /tmp/1.sh && '
                        'wget -O /tmp/1.sh %s/install/src/webserver/shell/new_jdk.sh && '
                        'bash /tmp/1.sh %s %s  %s >>%s'
                    ) % (download_url, action, version, jdk_path, tmp_file)
        # shell_str = (
        #     'bash /tmp/1.sh %s %s %s >>%s'
        # ) % (action, version, jdk_path, tmp_file)
        # public.print_log(shell_str)
        _, _ = public.ExecShell(shell_str)
        # self.collect_msg("tomcat-{}".format(version), log_path=tmp_file)
        tomcat_status = self.get_tomcat_version(None)
        if action == 'install':
            if tomcat_status['tomcat' + version]['status']:
                return public.returnMsg(True, '安装成功!')
            else:
                return public.returnMsg(False, '安装失败!')
        else:
            if not tomcat_status['tomcat' + version]['status']:
                return public.returnMsg(True, '卸载成功!')
            else:
                return public.returnMsg(False, '卸载失败!')
    
    @staticmethod
    def change_tomcat_jdk(get):
        try:
            version_str = get.version
            if version_str.startswith("tomcat") or version_str.startswith("Tomcat"):
                version_str = version_str.replace("tomcat", "").replace("Tomcat", "")
            version = str(int(version_str))
            jdk_path: str = get.jdk_path.strip()
        except (AttributeError, TypeError, ValueError):
            return public.returnMsg(False, "参数错误")
        
        if not os.path.exists(jdk_path):
            return public.returnMsg(False, "指定的jdk路径不存在")
        if jdk_path.endswith("/bin/java"):
            jdk_path = jdk_path[:-9]
        
        _, error = public.ExecShell("{}/bin/java -version".format(jdk_path))  # 信息在标准错误
        if not (error.find("version") != -1 and error.find("Runtime") != -1):
            return public.returnMsg(False, "指定的jdk不可用")
        
        tomcat_path = "/usr/local/bttomcat/tomcat{}".format(version)
        if not os.path.isdir(tomcat_path):
            return public.returnMsg(False, '没有安装Tomcat{}!'.format(version))
        
        deemon_sh_path = "{}/bin/daemon.sh".format(tomcat_path)
        if not os.path.isfile(deemon_sh_path):
            return public.returnMsg(False, 'Tomcat{}启动文件丢失!'.format(version))
        
        deemon_sh_data = public.readFile(deemon_sh_path)
        if not isinstance(deemon_sh_data, str):
            return public.returnMsg(False, 'Tomcat{}启动文件读取失败!'.format(version))
        
        # deemon_sh
        rep_deemon_sh = re.compile(r"^JAVA_HOME=(?P<path>.*)\n", re.M)
        re_res_deemon_sh = rep_deemon_sh.search(deemon_sh_data)
        if not re_res_deemon_sh:
            return public.returnMsg(False, 'Tomcat{}启动文件解析失败!'.format(version))
        
        jsvc_make_path = None
        for i in os.listdir(tomcat_path + "/bin"):
            tmp_dir = "{}/bin/{}".format(tomcat_path, i)
            if i.startswith("commons-daemon") and os.path.isdir(tmp_dir):
                make_path = tmp_dir + "/unix"
                if os.path.isdir(make_path):
                    jsvc_make_path = make_path
                    break
        
        if jsvc_make_path is None:
            return public.returnMsg(False, 'Jsvc{}文件丢失!'.format(version))
        
        # 重装jsvc
        if os.path.isfile(tomcat_path + "/bin/jsvc"):
            os.remove(tomcat_path + "/bin/jsvc")
        
        if os.path.isfile(jsvc_make_path + "/jsvc"):
            os.remove(jsvc_make_path + "/jsvc")
        
        shell_str = r'''
cd {}
make clean
./configure --with-java={}
make
\cp jsvc {}
'''.format(jsvc_make_path, jdk_path, tomcat_path + "/bin/jsvc")
        public.ExecShell(shell_str)
        
        new_deemon_sh_data = deemon_sh_data[:re_res_deemon_sh.start()] + (
            'JAVA_HOME={}\n'.format(jdk_path)
        ) + deemon_sh_data[re_res_deemon_sh.end():]
        public.writeFile(deemon_sh_path, new_deemon_sh_data)
        return public.returnMsg(True, '修改成功')
    
    def change_duli_tomcat_jdk(self, project_name, jdk_path):
        project_info = self.get_project_find(project_name)
        if not project_info:
            return public.returnMsg(False, "项目不存在")
        project_conf = project_info['project_config']
        if project_conf["java_type"] != "duli":
            return public.returnMsg(False, "项目类型错误")
        
        if not os.path.exists(jdk_path):
            return public.returnMsg(False, "指定的jdk路径不存在")
        if jdk_path.endswith("/bin/java"):
            jdk_path = jdk_path[:-9]
        
        _, error = public.ExecShell("{}/bin/java -version".format(jdk_path))  # 信息在标准错误
        if not (error.find("version") != -1 and error.find("Runtime") != -1):
            return public.returnMsg(False, "指定的jdk不可用")
        
        tomcat_path = "/www/server/bt_tomcat_web/{}".format(project_name)
        if not os.path.isdir(tomcat_path):
            return public.returnMsg(False, '没有安装Tomcat!')
        
        deemon_sh_path = "{}/bin/daemon.sh".format(tomcat_path)
        if not os.path.isfile(deemon_sh_path):
            return public.returnMsg(False, 'Tomcat启动文件丢失!')
        
        deemon_sh_data = public.readFile(deemon_sh_path)
        if not isinstance(deemon_sh_data, str):
            return public.returnMsg(False, 'Tomcat启动文件读取失败!')
        
        # deemon_sh
        rep_deemon_sh = re.compile(r"^JAVA_HOME=(?P<path>.*)\n", re.M)
        re_res_deemon_sh = rep_deemon_sh.search(deemon_sh_data)
        if not re_res_deemon_sh:
            return public.returnMsg(False, 'Tomcat启动文件解析失败!')
        
        jsvc_make_path = None
        for i in os.listdir(tomcat_path + "/bin"):
            tmp_dir = "{}/bin/{}".format(tomcat_path, i)
            if i.startswith("commons-daemon") and os.path.isdir(tmp_dir):
                make_path = tmp_dir + "/unix"
                if os.path.isdir(make_path):
                    jsvc_make_path = make_path
                    break
        
        if jsvc_make_path is None:
            return public.returnMsg(False, 'Jsvc文件丢失!')
        
        # 重装jsvc
        if os.path.isfile(tomcat_path + "/bin/jsvc"):
            os.remove(tomcat_path + "/bin/jsvc")
        
        if os.path.isfile(jsvc_make_path + "/jsvc"):
            os.remove(jsvc_make_path + "/jsvc")
        
        shell_str = r'''
cd {}
make clean
./configure --with-java={}
make
\cp jsvc {}
'''.format(jsvc_make_path, jdk_path, tomcat_path + "/bin/jsvc")
        public.ExecShell(shell_str)
        
        new_deemon_sh_data = deemon_sh_data[:re_res_deemon_sh.start()] + (
            'JAVA_HOME={}\n'.format(jdk_path)
        ) + deemon_sh_data[re_res_deemon_sh.end():]
        public.writeFile(deemon_sh_path, new_deemon_sh_data)
        
        project_conf["jdk_path"] = jdk_path
        public.M('sites').where("name=?", (project_name,)).update({"project_config": json.dumps(project_conf)})
        return public.returnMsg(True, '修改成功')
    
    def xml_init(self, path):
        '''
        @name 初始化XML文件
        @author lkq<2021-08-27>
        @param path<string>
        @return string
        '''
        try:
            self.__CONF_FILE = str(path)
            self.__TREE = ElementTree()
            self.__TREE.parse(self.__CONF_FILE)
            self.__ROOT = self.__TREE.getroot()
            self.__ENGINE = self.__TREE.findall('Service/Engine')[0]
            self.__CONNECTROR = self.__TREE.findall('Service/Connector')
            return True
        except Exception as e:
            return False
    
    def Initialization(self, version):
        '''
        @name 初始化XML文件
        @author lkq<2021-08-27>
        @param version<string>
        @return string
        '''
        if version == '7' or version == 'tomcat7' or version == 7:
            if self.xml_init(self.__tomcat7_server):
                return True
            else:
                return False
        elif version == '8' or version == 'tomcat8' or version == 8:
            if self.xml_init(self.__tomcat8_server):
                return True
            else:
                return False
        elif version == '9' or version == 'tomcat9' or version == 9:
            if self.xml_init(self.__tomcat9_server):
                return True
            else:
                return False
        elif version == '10' or version == 'tomcat10' or version == 10:
            if self.xml_init('/usr/local/bttomcat/tomcat10/conf/server.xml'):
                return True
            else:
                return False
        else:
            return False
    
    def get_server(self, version, domain=None):
        '''
        @name 取服务状态
        @author lkq<2021-08-27>
        @param version<string>
        @return string
        '''
        if domain:
            pid_path = self.__site_path + '/' + domain + '/logs/catalina-daemon.pid'
        else:
            pid_path = self.__bttomcat_path + '/tomcat%s/logs/catalina-daemon.pid' % version
        if os.path.exists(pid_path):
            reuslt = public.ReadFile(pid_path)
            if isinstance(reuslt, str):
                if not reuslt.strip(): return False
                pid = int(reuslt.split()[0].strip())
            else:
                return False
            try:
                ret = psutil.Process(pid)
                return True
            except:
                return False
        else:
            return False
    
    def get_port(self):
        '''
        @name 取端口号
        @author lkq<2021-08-27>
        @param version<string>
        @return string

        '''
        for i in self.__CONNECTROR:
            if 'protocol' in i.attrib and 'port' in i.attrib:
                if i.attrib['protocol'] == 'HTTP/1.1':
                    return int(i.attrib['port'])
        else:
            return int(8080)
    
    def set_tomcat_duli_path(self, get, get_project_find=''):
        '''
        @name 更改独立项目路径
        @author lkq<2021-09-17>
        @param get.project_path<int>
        @param get.project_name 项目名称
        '''
        project_name = get.project_name.strip()
        project_info = get_project_find
        if not project_info: return public.returnMsg(False, '更改项目路径失败!')
        if project_info['project_config']['java_type'] == 'duli':
            # 独立项目
            project_path = get.project_path.strip()
            if not os.path.exists(project_path): os.makedirs(project_path)
            if not self.Initialization2(version = '7', site = project_name): return public.returnMsg(
                False, "Tomcat配置文件错误请检查配置文件"
                )
            ret = self.Set_Domain_path(project_name, project_path)
            if ret:
                # 更改数据库
                # project_info['path']=project_path
                project_info['project_config']['project_cwd'] = project_path
                pdata = {
                    'path': project_path,
                    'project_config': json.dumps(project_info['project_config'])
                }
                public.M('sites').where('name=?', (project_name,)).update(pdata)
                return public.returnMsg(True, '更改项目路径成功!')
            else:
                return public.returnMsg(False, '更改项目路径失败!')
        if project_info['project_config']['java_type'] == 'neizhi':
            project_path = get.project_path.strip()
            if not os.path.exists(project_path): os.makedirs(project_path)
            if not self.Initialization(
                version = project_info['project_config']['tomcat_version']
                ): return public.returnMsg(False, "Tomcat配置文件错误请检查配置文件")
            ret = self.Set_Domain_path(project_name, project_path)
            if ret:
                project_info['project_config']['project_cwd'] = project_path
                pdata = {
                    'path': project_path,
                    'project_config': json.dumps(project_info['project_config'])
                }
                public.M('sites').where('name=?', (project_name,)).update(pdata)
                return public.returnMsg(True, '更改项目路径成功!')
            else:
                return public.returnMsg(False, '更改项目路径失败')
    
    def set_tomcat_duli_port(self, get, get_project_find=''):
        '''
        @name 更改独立项目端口
        @author lkq<2021-08-27>
        @param get.port<int>
        @param get.project_name 项目名称
        '''
        project_name = get.project_name.strip()
        project_info = get_project_find
        if not project_info: return public.returnMsg(False, '项目不存在!')
        if project_info['project_config']['java_type'] == 'duli':
            # 独立项目
            port = str(get.port)
            if self.check_port_is_used(port): return public.returnMsg(False, '端口已经被占用!')
            if not self.Initialization2(version = '7', site = project_name): return public.returnMsg(
                False, "配置文件错误请检查配置文件"
                )
            ret = self.TomcatSetPort(port = port)
            if ret:
                get.domain = project_name
                get.type = 'reload'
                self.pendent_tomcat_start(get)
                fs = firewalls.firewalls()
                get = mobj()
                get.port = port
                get.ps = 'tomcat外部端口'
                fs.AddAcceptPort(get)
                # 更改数据库
                project_info['project_config']['port'] = int(port)
                pdata = {'project_config': json.dumps(project_info['project_config'])}
                public.M('sites').where('name=?', (project_name,)).update(pdata)
                # self.set_config(get)
                return public.returnMsg(True, '更改成功!')
            else:
                return public.returnMsg(False, '更改失败')
        if project_info['project_config']['java_type'] == 'neizhi':
            port = str(get.port)
            if self.check_port_is_used(port): return public.returnMsg(False, '端口已经被占用!')
            if not self.Initialization(
                version = project_info['project_config']['tomcat_version']
                ): return public.returnMsg(False, "配置文件错误请检查配置文件")
            ret = self.TomcatSetPort(port = port)
            if ret:
                get.version = project_info['project_config']['tomcat_version']
                get.type = 'reload'
                self.start_tomcat(get)
                fs = firewalls.firewalls()
                get = mobj()
                get.port = port
                get.ps = 'tomcat外部端口'
                fs.AddAcceptPort(get)
                # 更改数据库
                project_info['project_config']['port'] = int(port)
                pdata = {'project_config': json.dumps(project_info['project_config'])}
                public.M('sites').where('name=?', (project_name,)).update(pdata)
                return public.returnMsg(True, '更改成功!')
            else:
                return public.returnMsg(False, '更改失败')
    
    def get_jdk_path(self, version, is_independent=False):
        '''
        @name 获取JDK版本路径
        @author lkq<2021-08-27>
        @param version<string>
        @param is_independent<bool> 是否是独立版本
        @return string
        '''
        if is_independent:
            path = self.__site_path + '/%s/bin/daemon.sh' % version
        else:
            path = self.__bttomcat_path + '/tomcat%s/bin/daemon.sh' % version
        if os.path.exists(path):
            ret = public.ReadFile(path)
            if isinstance(ret, str):
                rec = "\nJAVA_HOME=.+"
                if re.search(rec, ret):
                    jdk = re.search(rec, ret)
                    if not jdk: return ''
                    if jdk:
                        jdk = jdk.group(0).split('=')[1].strip()
                    return jdk
                else:
                    return ''
            else:
                return ''
        else:
            return ''
    
    def format(self, em, level=0):
        '''
        @name 格式化配置文件
        @author lkq<2021-08-27>
        @param em<string>
        @param level<int>
        '''
        i = "\n" + level * "  "
        if len(em):
            if not em.text or not em.text.strip():
                em.text = i + "  "
            for e in em:
                self.format(e, level + 1)
                if not e.tail or not e.tail.strip():
                    e.tail = i
        if level and (not em.tail or not em.tail.strip()):
            em.tail = i
    
    # 保存配置
    def save_tomcat(self):
        '''
        @name 保存tomcat配置文件
        @author lkq<2021-08-27>
        '''
        self.format(self.__ROOT)
        self.__TREE.write(self.__CONF_FILE, 'utf-8')
    
    def get_vhost(self, domain):
        '''
        @name 获取指定虚拟主机
        @author lkq<2021-08-27>
        @param domain<string>
        @return string
        '''
        try:
            Hosts = self.__ENGINE.getchildren()
        except:
            Hosts = list(self.__ENGINE)
        for host in Hosts:
            if host.tag != 'Host': continue
            if host.attrib['name'] == domain:
                return host
        return None
    
    def add_vhost(self, path, domain):
        '''
        @name tomcat 填写虚拟主机
        @author lkq<2021-08-27>
        @param path<string>
        @param domain<string>
        @return bool
        '''
        if not os.path.exists(path): os.makedirs(path)
        if self.get_vhost(domain): return False
        attr = {
            "autoDeploy": "true", "name": domain, "unpackWARs": "true",
            "xmlNamespaceAware": "false", "xmlValidation": "false"
        }
        Host = Element("Host", attr)
        attr = {"docBase": path, "path": "", "reloadable": "true", "crossContext": "true", }
        Context = Element("Context", attr)
        Host.append(Context)
        self.__ENGINE.append(Host)
        self.save_tomcat()
        return True
    
    # Tomcat服务管理
    def start_tomcat(self, get):
        version = str(get.version)
        s_type = get.type
        if version.startswith('tomcat') or version.startswith('Tomcat'):
            version = version.replace('tomcat', '').replace('Tomcat', '')
        # 判断服务是否正常
        execStr = '/etc/init.d/bttomcat%s stop && /etc/init.d/bttomcat%s start' % (version, version)
        start = '/usr/local/bttomcat/tomcat%s/bin/daemon.sh start' % version
        stop = '/usr/local/bttomcat/tomcat%s/bin/daemon.sh stop' % version
        if s_type == 'start':
            ret = self.get_server(version)
            if not ret:
                pid_path = '/www/server/%s/logs/catalina-daemon.pid' % version
                if os.path.exists(pid_path):
                    os.remove(pid_path)
                public.ExecShell(start)
            self.start_by_user("/etc/init.d/bttomcat{}".format(version))
            return public.returnMsg(True, '启动成功')
        elif s_type == 'stop':
            public.ExecShell(stop)
            if self.get_server(version):
                public.ExecShell(stop)
            self.stop_by_user("/etc/init.d/bttomcat{}".format(version))
            return public.returnMsg(True, '关闭成功')
        elif s_type == 'reload' or s_type == 'restart':
            # public.ExecShell(execStr)
            public.ExecShell(stop)
            public.ExecShell(start)
            return public.returnMsg(True, '重载成功')
        else:
            return public.returnMsg(False, '类型错误')
    
    def pendent_tomcat_start(self, get):
        '''
            独立项目的tomcat启动
            @author lkq 2021-08-27
            @param get.domain  项目域名
            @param get.type  启动类型 start stop  reload
        '''
        version = get.domain
        s_type = get.type
        # 判断服务是否正常
        execStr = '%s/%s/bin/daemon.sh stop && %s/%s/bin/daemon.sh start' % (
        self.__site_path, version, self.__site_path, version)
        start = '%s/%s/bin/daemon.sh start' % (self.__site_path, version)
        stop = '%s/%s/bin/daemon.sh stop' % (self.__site_path, version)
        if s_type == 'start':
            ret = self.get_server(version, version)
            if not ret:
                pid_path = '%s/%s/logs/catalina-daemon.pid' % (self.__site_path, version)
                if os.path.exists(pid_path):
                    os.remove(pid_path)
                public.ExecShell(start)
            self.start_by_user(self.__site_path + "/" + version)
            return public.returnMsg(True, '启动成功')
        elif s_type == 'stop':
            public.ExecShell(stop)
            if self.get_server(version, version):
                public.ExecShell(stop)
            self.stop_by_user(self.__site_path + "/" + version)
            return public.returnMsg(True, '关闭成功')
        elif s_type == 'reload' or s_type == 'restart':
            # public.ExecShell(execStr)
            public.ExecShell(stop)
            public.ExecShell(start)
            return public.returnMsg(True, '重载成功')
        else:
            return public.returnMsg(False, '类型错误')
    
    def pendent_tomcat_info(self, get=None, domain=None):
        '''
        @name 独立项目的项目信息
        @author lkq 2021-08-27
        '''
        if get: domain = get.domain.strip()
        tmp = {}
        tmp_path = self.__site_path + '' + domain + '/conf/server.xml'
        if os.path.exists(tmp_path):
            if not self.Initialization2('7', domain):
                tmp["port"] = False
            else:
                tmp["port"] = self.get_port()
            tmp['status'] = self.get_server(domain, domain)
            tmp['conf'] = public.readFile(tmp_path)
            tmp['jdk_path'] = self.get_jdk_path(domain, True)
            # tmp['log'] = public.GetNumLines('%s/%s/logs/catalina-daemon.out'%(self.__site_path,domain), 3000)
            tmp["tomcat_server"] = tmp_path
            tmp['tomcat_start'] = self.__site_path + '' + domain + '/bin/daemon.sh'
            tmp['stype'] = 'built'
        else:
            tmp['status'] = False
            tmp["port"] = False
            tmp['conf'] = False
            tmp['jdk'] = False
            tmp['log'] = False
            tmp['jdk_path'] = False
            tmp['stype'] = 'uninstall'
        return tmp
    
    def exists_nginx_ssl(self, project_name):
        '''
            @name 判断项目是否配置Nginx SSL配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return tuple
        '''
        config_file = "{}/nginx/java_{}.conf".format(public.get_vhost_path(), project_name)
        if not os.path.exists(config_file):
            return False, False
        
        config_body = public.readFile(config_file)
        if not config_body:
            return False, False
        
        is_ssl, is_force_ssl = False, False
        if config_body.find('ssl_certificate') != -1:
            is_ssl = True
        if config_body.find('HTTP_TO_HTTPS_START') != -1:
            is_force_ssl = True
        return is_ssl, is_force_ssl
    
    def set_nginx_config(self, project_find):
        '''
            @name 设置Nginx配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']
        ports = []
        domains = []
        for d in project_find['project_config']['domains']:
            domain_tmp = d.split(':')
            if len(domain_tmp) == 1: domain_tmp.append(80)
            if not int(domain_tmp[1]) in ports:
                ports.append(int(domain_tmp[1]))
            if not domain_tmp[0] in domains:
                domains.append(domain_tmp[0])
        listen_ipv6 = public.listen_ipv6()
        is_ssl, is_force_ssl = self.exists_nginx_ssl(project_name)
        listen_ports_list = []
        for p in ports:
            listen_ports_list.append("    listen {};".format(p))
            if listen_ipv6:
                listen_ports_list.append("    listen [::]:{};".format(p))
        
        ssl_config = ''
        if is_ssl:
            http3_header = ""
            if self.is_nginx_http3():
                http3_header = '''\n    add_header Alt-Svc 'quic=":443"; h3=":443"; h3-29=":443"; h3-27=":443";h3-25=":443"; h3-T050=":443"; h3-Q050=":443";h3-Q049=":443";h3-Q048=":443"; h3-Q046=":443"; h3-Q043=":443"';'''
            
            nginx_ver = public.nginx_version()
            if nginx_ver:
                port_str = ["443"]
                if listen_ipv6:
                    port_str.append("[::]:443")
                use_http2_on = False
                for p in port_str:
                    listen_str = "    listen {} ssl".format(p)
                    if nginx_ver < [1, 9, 5]:
                        listen_str += ";"
                    elif [1, 9, 5] <= nginx_ver < [1, 25, 1]:
                        listen_str += " http2;"
                    else:  # >= [1, 25, 1]
                        listen_str += ";"
                        use_http2_on = True
                    listen_ports_list.append(listen_str)
                    
                    if self.is_nginx_http3():
                        listen_ports_list.append("    listen {} quic;".format(p))
                if use_http2_on:
                    listen_ports_list.append("    http2 on;")
            
            else:
                listen_ports_list.append("    listen 443 ssl;")
            
            ssl_config = '''ssl_certificate    {vhost_path}/cert/{priject_name}/fullchain.pem;
    ssl_certificate_key    {vhost_path}/cert/{priject_name}/privkey.pem;
    ssl_protocols TLSv1.1 TLSv1.2 TLSv1.3;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000";{http3_header}
    error_page 497  https://$host$request_uri;'''.format(
                vhost_path = self._vhost_path, priject_name = project_name,
                http3_header = http3_header
                )
            
            if is_force_ssl:
                ssl_config += '''
    #HTTP_TO_HTTPS_START
    if ($server_port !~ 443){
        rewrite ^(/.*)$ https://$host$1 permanent;
    }
    #HTTP_TO_HTTPS_END'''
        
        config_file = "{}/nginx/java_{}.conf".format(self._vhost_path, project_name)
        template_file = "{}/template/nginx/java_http.conf".format(self._vhost_path)
        
        listen_ports = "\n".join(listen_ports_list).strip()
        config_body = public.readFile(template_file)
        if project_find['project_config']['java_type'] == 'neizhi' or project_find['project_config'][
            'java_type'] == 'duli':
            host = '{}'.format(project_find['project_config']['project_name'])
        else:
            host = '$Host'
        # api_url='/' if not 'api_url' in project_find['project_config'] else project_find['project_config']['api_url']
        # site_path=project_find['path'] if not 'static_path' in project_find['project_config'] else project_find['project_config']['static_path']
        # host_url = host if not 'host_url' in project_find['project_config'] else project_find['project_config']['host_url']
        if 'host_url' in project_find['project_config']:
            if project_find['project_config']['host_url']:
                url2 = project_find['project_config']['host_url']
            else:
                url2 = 'http://127.0.0.1:{}'.format(project_find['project_config']['port'])
        else:
            url2 = 'http://127.0.0.1:{}'.format(project_find['project_config']['port'])
        
        if project_find["project_config"]["java_type"] == "springboot":
            _site_path = project_find["project_config"]["static_path"] if (
                        "static_path" in project_find["project_config"] and project_find["project_config"][
                    "static_path"]) else \
                project_find["project_config"]["jar_path"]
        else:
            _site_path = project_find['path']
        
        mut_config = {
            "api_url": '/' if not 'api_url' in project_find['project_config'] else project_find['project_config'][
                'api_url'],
            "site_path": _site_path,
            "domains": ' '.join(domains),
            "url": url2,
            "listen_ports": listen_ports,
            "ssl_config": ssl_config,
        }
        config_body = config_body.format(
            api_url = mut_config["api_url"],
            site_path = mut_config["site_path"],
            domains = ' '.join(domains),
            project_name = project_name,
            panel_path = self._panel_path,
            log_path = public.get_logs_path(),
            url = url2,
            host = host,
            listen_ports = listen_ports,
            ssl_config = ssl_config
        )
        
        # # 恢复旧的SSL配置
        # ssl_config = self.get_nginx_ssl_config(project_name)
        # if ssl_config:
        #     config_body.replace('#error_page 404/404.html;',ssl_config)
        
        rewrite_file = "{panel_path}/vhost/rewrite/java_{project_name}.conf".format(
            panel_path = self._panel_path, project_name = project_name
            )
        if not os.path.exists(rewrite_file):
            public.writeFile(rewrite_file, '# 请将伪静态规则或自定义NGINX配置填写到此处\n')
        if not os.path.exists("/www/server/panel/vhost/nginx/well-known"):
            os.makedirs("/www/server/panel/vhost/nginx/well-known", 0o600)
        apply_check = "{}/vhost/nginx/well-known/{}.conf".format(self._panel_path, project_name)
        from mod.base.web_conf import ng_ext
        config_body = ng_ext.set_extension_by_config(project_name, config_body)
        if not os.path.exists(apply_check):
            public.writeFile(apply_check, '')
        if not os.path.exists(config_file):
            public.writeFile(config_file, config_body)
        else:
            if not self._replace_nginx_conf(config_file, mut_config):
                public.writeFile(config_file, config_body)
        
        return True
    
    @staticmethod
    def _replace_nginx_conf(config_file, mut_config: dict) -> bool:
        """尝试替换"""
        data: str = public.readFile(config_file)
        tab_spc = "    "
        rep_list = [
            (
                 r"([ \f\r\t\v]*listen[^;\n]*;\n(\s*http2\s+on\s*;[^\n]*\n)?)+",
                mut_config["listen_ports"] + "\n"
            ),
            (
                r"[ \f\r\t\v]*root [ \f\r\t\v]*/[^;\n]*;",
                "    root {};".format(mut_config["site_path"])
            ),
            (
                r"[ \f\r\t\v]*server_name [ \f\r\t\v]*[^\n;]*;",
                "   server_name {};".format(mut_config["domains"])
            ),
            (
                r"[ \f\r\t\v]*location [^{\n]* { *\n *proxy_pass[^\n;]*;\n *proxy_set_header *Host",
                "{}location {} {{\n{}proxy_pass {};\n{}proxy_set_header Host".format(
                    tab_spc, mut_config["api_url"], tab_spc * 2, mut_config["url"], tab_spc * 2, )
            ),
            (
                "[ \f\r\t\v]*#SSL-START(.*\n){2,15}[ \f\r\t\v]*#SSL-END",
                "{}#SSL-START SSL相关配置\n{}#error_page 404/404.html;\n{}{}\n{}#SSL-END".format(
                    tab_spc, tab_spc, tab_spc, mut_config["ssl_config"], tab_spc
                )
            )
        ]
        for rep, info in rep_list:
            if re.search(rep, data):
                data = re.sub(rep, info, data, 1)
            else:
                return False
        
        public.writeFile(config_file, data)
        return True
    
    def exists_apache_ssl(self, project_name):
        '''
            @name 判断项目是否配置Apache SSL配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        '''
        config_file = "{}/apache/java_{}.conf".format(public.get_vhost_path(), project_name)
        if not os.path.exists(config_file):
            return False, False
        
        config_body = public.readFile(config_file)
        if not config_body:
            return False, False
        
        is_ssl, is_force_ssl = False, False
        if config_body.find('SSLCertificateFile') != -1:
            is_ssl = True
        if config_body.find('HTTP_TO_HTTPS_START') != -1:
            is_force_ssl = True
        return is_ssl, is_force_ssl
    
    def set_apache_config(self, project_find):
        '''
            @name 设置Apache配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']
        
        # 处理域名和端口
        ports = []
        domains = []
        for d in project_find['project_config']['domains']:
            domain_tmp = d.split(':')
            if len(domain_tmp) == 1: domain_tmp.append(80)
            if not int(domain_tmp[1]) in ports:
                ports.append(int(domain_tmp[1]))
            if not domain_tmp[0] in domains:
                domains.append(domain_tmp[0])
        
        config_file = "{}/apache/java_{}.conf".format(self._vhost_path, project_name)
        template_file = "{}/template/apache/java_http.conf".format(self._vhost_path)
        config_body = public.readFile(template_file)
        apache_config_body = ''
        
        # 旧的配置文件是否配置SSL
        is_ssl, is_force_ssl = self.exists_apache_ssl(project_name)
        if is_ssl:
            if not 443 in ports: ports.append(443)
        
        from panelSite import panelSite
        s = panelSite()
        
        if project_find["project_config"]["java_type"] == "springboot":
            _site_path = project_find["project_config"]["jar_path"]
        else:
            _site_path = project_find['path']
        
        # 根据端口列表生成配置
        for p in ports:
            # 生成SSL配置
            ssl_config = ''
            if p == 443 and is_ssl:
                ssl_key_file = "{vhost_path}/cert/{project_name}/privkey.pem".format(
                    project_name = project_name, vhost_path = public.get_vhost_path()
                    )
                if not os.path.exists(ssl_key_file): continue  # 不存在证书文件则跳过
                ssl_config = '''#SSL
    SSLEngine On
    SSLCertificateFile {vhost_path}/cert/{project_name}/fullchain.pem
    SSLCertificateKeyFile {vhost_path}/cert/{project_name}/privkey.pem
    SSLCipherSuite EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5
    SSLProtocol All -SSLv2 -SSLv3 -TLSv1
    SSLHonorCipherOrder On'''.format(project_name = project_name, vhost_path = public.get_vhost_path())
            else:
                if is_force_ssl:
                    ssl_config = '''#HTTP_TO_HTTPS_START
    <IfModule mod_rewrite.c>
        RewriteEngine on
        RewriteCond %{SERVER_PORT} !^443$
        RewriteRule (.*) https://%{SERVER_NAME}$1 [L,R=301]
    </IfModule>
    #HTTP_TO_HTTPS_END'''
            
            # 生成vhost主体配置
            apache_config_body += config_body.format(
                site_path = _site_path,
                server_name = '{}.{}'.format(p, project_name),
                domains = ' '.join(domains),
                log_path = public.get_logs_path(),
                server_admin = 'admin@{}'.format(project_name),
                url = 'http://127.0.0.1:{}'.format(project_find['project_config']['port']),
                port = p,
                ssl_config = ssl_config,
                project_name = project_name
            )
            apache_config_body += "\n"
            
            # 添加端口到主配置文件
            if not p in [80]:
                s.apacheAddPort(p)
        
        # 写.htaccess
        if project_find["project_config"]["java_type"] == "springboot":
            _path = project_find["project_config"]["static_path"] if (
                        "static_path" in project_find["project_config"] and project_find["project_config"][
                    "static_path"]) else \
                project_find["project_config"]["jar_path"]
            rewrite_file = "{}/.htaccess".format(_path)
        else:
            rewrite_file = "{}/.htaccess".format(project_find['path'])
        if not os.path.exists(rewrite_file): public.writeFile(
            rewrite_file, '# 请将伪静态规则或自定义Apache配置填写到此处\n'
            )
        from mod.base.web_conf import ap_ext
        apache_config_body = ap_ext.set_extension_by_config(project_name, apache_config_body)
        # 写配置文件
        public.writeFile(config_file, apache_config_body)
        return True
    
    def get_nginx_ssl_config(self, project_name):
        '''
            @name 获取项目Nginx SSL配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return string
        '''
        result = ''
        config_file = "{}/nginx/java_{}".format(self._vhost_path, project_name)
        if not os.path.exists(config_file):
            return result
        
        config_body = public.readFile(config_file)
        if not config_body:
            return result
        if config_body.find('ssl_certificate') == -1:
            return result
        
        ssl_body = re.search("#SSL-START(.|\n)+#SSL-END", config_body)
        if not ssl_body: return result
        result = ssl_body.group()
        return result
    
    def set_config(self, project_name):
        '''
            @name 设置项目配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        '''
        project_find = self.get_project_find(project_name)
        if not project_find: return False
        if not project_find['project_config']: return False
        if not project_find['project_config']['bind_extranet']: return False
        if not project_find['project_config']['domains']: return False
        self.set_nginx_config(project_find)
        self.set_apache_config(project_find)
        public.serviceReload()
        return True
    
    def clear_nginx_config(self, project_find):
        '''
            @name 清除nginx配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']
        config_file = "{}/nginx/java_{}.conf".format(self._vhost_path, project_name)
        if os.path.exists(config_file):
            os.remove(config_file)
        rewrite_file = "{panel_path}/vhost/rewrite/java_{project_name}.conf".format(
            panel_path = self._panel_path, project_name = project_name
            )
        if os.path.exists(rewrite_file):
            os.remove(rewrite_file)
        return True
    
    def clear_apache_config(self, project_find):
        '''
            @name 清除apache配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']
        config_file = "{}/apache/java_{}.conf".format(self._vhost_path, project_name)
        if os.path.exists(config_file):
            os.remove(config_file)
        return True
    
    def clear_config(self, project_name):
        '''
            @name 清除项目配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        '''
        project_find = self.get_project_find(project_name)
        if not project_find: return False
        self.clear_nginx_config(project_find)
        self.clear_apache_config(project_find)
        public.serviceReload()
        return True
    
    def del_vhost(self, domain, context_path: str = ""):
        '''
        @name  删除虚拟主机
        @author lkq
        @param domain: string
        @return bool
        '''
        if domain == 'localhost': return False
        host = self.get_vhost(domain)
        if not host: return False
        target_context, other_context_count = None, 0
        for i in host:
            if i.tag == "Context":
                if i.attrib["path"] == context_path:
                    target_context = i
                else:
                    other_context_count += 1
        if target_context is None and not other_context_count:
            return False
        if target_context is not None:
            host.remove(target_context)
        if not other_context_count:
            self.__ENGINE.remove(host)
        self.save_tomcat()
        return True
    
    def tomcat_vhost_delete(self, version, domains, get):
        '''
        @name 删除内置tomcat虚拟主机
        @author lkq
        @param version: string
        @param domain: string
        @return bool
        '''
        if not self.Initialization(version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        context_path = get.get("project_name", "")
        domain = domains[0].split(":")[0]
        if self.del_vhost(domain, context_path):
            get.version = version
            get.type = 'reload'
            self.start_tomcat(get)
            return public.returnMsg(True, '删除成功')
        return public.returnMsg(False, '不存在')
    
    def set_hosts(self, domain):
        '''
        @name 建立本地HOST
        '''
        pass
        ret = public.ReadFile('/etc/hosts')
        # if isinstance(ret, str):
        #     import re
        #     rec = '%s' % domain
        #     if not re.search(rec, ret):
        #         public.ExecShell('echo "127.0.0.1 ' + domain + '" >> /etc/hosts')

    @staticmethod
    def set_spring_user():
        '''
        @name 建立本地HOST
        '''
        try:
            pwd.getpwnam('springboot')
        except KeyError:
            public.ExecShell('useradd springboot')
    
    def del_hosts(self, domain):
        '''
        @name 删除本地hosts
        '''
        pass
        # ret = public.ReadFile('/etc/hosts')
        # if isinstance(ret, str):
        #     import re
        #     rec = '127.0.0.1 %s' % domain
        #     if re.search(rec, ret):
        #         ret=ret.replace(rec,'')
        #         public.writeFile('/etc/hosts',ret)
    
    def Initialization2(self, version, site):
        '''
        @name 初始独立项目
        @author lkq 2021-08-28
        @param site: string<项目名称>
        @param version: string<版本号>
        '''
        # ! 项目初始化有关tomcat部分移至Tomcat版本管理
        if self.xml_init(self.__site_path + site + '/conf/server.xml'):
            return True
        # if version == '7' or version == 'tomcat7' or version == 7:
        #     if self.xml_init(self.__site_path + site + '/conf/server.xml'):
        #         return True
        #     else:
        #         return False
        # elif version == '8' or version == 'tomcat8' or version == 8:
        #     if self.xml_init(self.__site_path + site + '/conf/server.xml'):
        #         return True
        #     else:
        #         return False
        # elif version == '9' or version == 'tomcat9' or version == 9:
        #     if self.xml_init(self.__site_path + site + '/conf/server.xml'):
        #         return True
        #     else:
        #         return False
        # else:
        #     return False
    
    def replce_tomcat_port(self, get):
        '''
        @name 更改tomcat端口
        @param get.port: int
        @param get.version: string
        '''
        port = str(get.port)
        version = str(get.version)
        if version.startswith('tomcat') or version.startswith('Tomcat'):
            version = version.replace('tomcat', '').replace('Tomcat', '')
        if self.IsOpen(port): return public.returnMsg(False, '端口已经被占用!')
        if not self.Initialization(version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.TomcatSetPort(port = port)
        if ret:
            # 重载tomcat
            get.type = 'reload'
            self.start_tomcat(get)
            return public.returnMsg(True, '端口更改成功')
        return public.returnMsg(False, '端口更改失败')
    
    def replace_duli_port(self, get):
        '''
        @name 更改duli端口
        @param get.port: int
        @param get.version: string
        @param get.domain   string
        @return bool
        '''
        return self.set_site_port(get.port, "", get.domain.strip())
    
    def TomcatSetPort(self, port):
        '''
        @name 更改tomcat端口
        @author lkq
        @param port: string<端口号>
        '''
        for i in self.__CONNECTROR:
            if 'protocol' in i.attrib and 'port' in i.attrib:
                if i.attrib['protocol'] == 'HTTP/1.1':
                    i.attrib['port'] = port
        self.save_tomcat()
        if self.get_port() == int(port):
            return True
        else:
            return False
    
    # 获取指定虚拟主机
    def Set_Domain_path(self, domain, docBase):
        try:
            Hosts = self.__ENGINE.getchildren()
        except:
            Hosts = list(self.__ENGINE)
        flag = False
        for host in Hosts:
            if host.tag != 'Host': continue
            if host.attrib['name'] == domain:
                try:
                    ch = host.getchildren()
                except:
                    ch = list(host)
                for i in ch:
                    print(i.attrib)
                    if 'docBase' in i.attrib:
                        i.attrib['docBase'] = docBase
                        flag = True
        if flag:
            self.save_tomcat()
            return True
        return False
    
    def TomcatSetPath(self, port):
        '''
        @name 更改tomcat 项目路径
        @author lkq
        @param port: string<端口号>
        '''
        for i in self.__CONNECTROR:
            if 'protocol' in i.attrib and 'port' in i.attrib:
                if i.attrib['protocol'] == 'HTTP/1.1':
                    i.attrib['port'] = port
        self.save_tomcat()
        if self.get_port() == int(port):
            return True
        else:
            return False
    
    def set_site_port(self, port, version, domain):
        '''
        @name 更改独立项目端口
        @param port: int<端口>
        @param version: string<版本>
        @param domain: string<域名>
        @author lkq 2021-08-28
        '''
        if self.IsOpen(port): return public.returnMsg(False, '端口已经被占用!')
        if not self.Initialization2(version, domain): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.TomcatSetPort(port = port)
        if ret:
            fs = firewalls.firewalls()
            get = mobj()
            get.port = port
            get.ps = 'tomcat外部端口'
            fs.AddAcceptPort(get)
            return public.returnMsg(True, '更改成功!')
        else:
            return public.returnMsg(False, '更改失败')
    
    def _get_jdk_status(self):
        default_version = {
            "x64": [
                "jdk1.7.0_80",
                "jdk1.8.0_371",
                "jdk-9.0.4",
                "jdk-10.0.2",
                "jdk-11.0.19",
                "jdk-12.0.2",
                "jdk-13.0.2",
                "jdk-14.0.2",
                "jdk-15.0.2",
                "jdk-16.0.2",
                "jdk-17.0.8",
                "jdk-18.0.2.1",
                "jdk-19.0.2",
                "jdk-20.0.2"
            ],
            "arm": [
                "jdk1.8.0_371",
                "jdk-11.0.19",
                "jdk-15.0.2",
                "jdk-16.0.2",
                "jdk-17.0.8",
                "jdk-18.0.2.1",
                "jdk-19.0.2",
                "jdk-20.0.2"
            ],
            "loongarch64": [
                "jdk-8.1.18", "jdk-11.0.22", "jdk-17.0.10", "jdk-21.0.2"
            ]
        }
        tmp_file = '/www/server/panel/data/jdk.json'
        tmp_pl = '/www/server/panel/data/jdk.json.pl'
        download_url = '{}/src/jdk/jdk.json'.format(public.get_url())
        setup_path = public.GetConfigValue('setup_path') + '/java'
        file_data = public.readFile(tmp_pl)
        if not file_data and os.path.exists(tmp_pl):
            os.remove(tmp_pl)
        if not os.path.exists(setup_path):
            public.ExecShell('mkdir -p ' + setup_path)
            public.ExecShell('chown 755 ' + setup_path)
        if not os.path.exists(tmp_pl) or time.time() - int(file_data) > 3600:
            public.run_thread(public.downloadFile, (download_url, tmp_file))
            public.writeFile(tmp_pl, str(int(time.time())))
            versions = default_version
        else:
            try:
                import json
                versions = json.loads(public.readFile(tmp_file))
            except:
                versions = default_version
        # 获取本机系统架构
        import platform
        arce = platform.machine()
        if arce == 'x86_64':
            arce = 'x64'
        elif arce == 'aarch64' or 'arm' in arce:
            arce = 'arm'
        try:
            versions = versions.get(arce, [])
            data = {
                "name": "jdk",
                "check": "/usr/local/java/VERSION/bin/java",
                "msg": "Java 语言是一种通用的、面向对象的编程语言",
                "shell": "java.sh",
                "task": "1",
                "type": "语言解释器",
                "versions": [
                    {"status": True if os.path.exists('/www/server/java/' + i) else False, "version": i}
                    for i in versions]
            }
            return data
        except:
            import json
            versions_data = public.readFile(tmp_file)
            if not versions_data:
                versions = default_version
                versions = versions.get(arce, [])
            else:
                versions = json.loads(versions_data).get(arce, [])
            data = {
                "name": 'jdk',
                "check": "/usr/local/java/VERSION/bin/java",
                "msg": "Java 语言是一种通用的、面向对象的编程语言",
                "shell": "java.sh",
                "task": "1",
                "type": "语言解释器",
                "versions": [{'status': False, "name": i} for i in versions]
            }
            return data
    
    # def get_local_jdk_version(self, get=None):
    #     '''
    #     @name 获取本地jdk版本
    #     @parcm get<>
    #     @return list
    #     operation 0 1 2 3 0表示安装 1表示删除 2表示不可操作,3正在安装
    #     '''
    #     ret = []
    #     # 获取本地文件中的JDK版本
    #     if os.path.exists(self._panel_path + '/data/get_local_jdk.json'):
    #         ret2 = public.ReadFile(self._panel_path + '/data/get_local_jdk.json')
    #         if isinstance(ret2, str):
    #             ret2 = json.loads(ret2)
    #             for i in range(len(ret2)):
    #                 ret.append({'name': '自定义JDK', 'path': ret2[len(ret)], 'operation': 1})
    #     jdks = self._get_jdk_status()['versions']
    #     jdks = sorted(jdks, key=lambda x: x['status'], reverse=True)
    #     for jdk in jdks:
    #         if jdk['status']:
    #             ret.append({'name': jdk['version'], 'path': '/www/server/java/' + jdk['version'] + '/bin/java',
    #                         'operation': 1})
    #         else:
    #             ret.append({'name': jdk['version'], 'path': '', 'operation': 0})
    #     for i in ret:
    #         if os.path.exists('/www/server/java/' + i['name'] + '.pl'):
    #             i['operation'] = 3
    #     if os.path.exists('/usr/bin/java'):
    #         ret.append({'name': 'JDK', 'path': '/usr/bin/java', 'operation': 2})
    #     if os.path.exists('/usr/java/jdk1.8.0_121/bin/java'):
    #         ret.append({'name': 'jdk8', 'path': '/usr/java/jdk1.8.0_121/bin/java', 'operation': 2})
    #     if os.path.exists('/usr/local/btjdk/jdk8/bin/java'):
    #         ret.append({'name': 'openjdk8', 'path': '/usr/local/btjdk/jdk8/bin/java', 'operation': 2})
    #     if os.path.exists('/usr/java/jdk1.7.0_80/bin/java'):
    #         ret.append({'name': 'jdk7', 'path': '/usr/java/jdk1.7.0_80/bin/java', 'operation': 2})
    #     return ret
    
    def get_local_jdk_version(self, get=None):
        import os
        import json
        # 获取本地文件中的JDK版本
        ret = []
        if os.path.exists(self._panel_path + '/data/get_local_jdk.json'):
            ret2 = public.ReadFile(self._panel_path + '/data/get_local_jdk.json')
            if isinstance(ret2, str):
                ret2 = json.loads(ret2)
                for i in range(len(ret2)):
                    ret.append({'name': '自定义JDK', 'path': ret2[i], 'operation': 1, 'is_current': False})
        
        # 读取/etc/profile文件来获取当前JAVA_HOME环境变量
        bashrc_path = os.path.expanduser('/etc/profile')
        
        current_java_home = ''
        # 检查文件是否存在
        if os.path.exists(bashrc_path):
            profile_data = public.readFile(bashrc_path)
            if profile_data:
                for line in profile_data.strip("\n"):
                    if 'export JAVA_HOME=' in line:
                        current_java_home = line.split('=')[1].strip().replace('"', '').replace("'", "")
        
        # 获取已安装的JDK版本
        jdks = self._get_jdk_status()['versions']
        jdks = sorted(jdks, key = lambda x: x['status'], reverse = True)
        for jdk in jdks:
            jdk_path = '/www/server/java/' + jdk['version'] + '/bin/java'
            is_current = os.path.dirname(os.path.dirname(jdk_path)) == current_java_home
            if jdk['status']:
                ret.append({'name': jdk['version'], 'path': jdk_path, 'operation': 1, 'is_current': is_current})
            else:
                ret.append({'name': jdk['version'], 'path': '', 'operation': 0, 'is_current': False})
        
        # 检查其他JDK路径
        jdk_paths = [
            ('JDK', '/usr/bin/java'),
            ('jdk8', '/usr/java/jdk1.8.0_121/bin/java'),
            ('openjdk8', '/usr/local/btjdk/jdk8/bin/java'),
            ('jdk7', '/usr/java/jdk1.7.0_80/bin/java')
        ]
        for name, path in jdk_paths:
            if os.path.exists(path):
                is_current = os.path.dirname(os.path.dirname(path)) == current_java_home
                ret.append({'name': name, 'path': path, 'operation': 2, 'is_current': is_current})
        
        # 检查是否有正在安装的JDK
        for i in ret:
            import psutil
            try:
                if os.path.exists('/www/server/java/' + i['name'] + '.pl'):
                    pid = int(public.readFile('/www/server/java/' + i['name'] + '.pl'))
                    psutil.Process(pid)
                    i['operation'] = 3
            except UnicodeEncodeError:
                continue
            except:
                public.ExecShell('rm -rf /www/server/java/' + i['name'] + '.pl')
        return ret
    
    def get_system_info(self, get):
        '''
        @name 获取基础信息
        '''
        reuslt = {}
        reuslt['jdk_info'] = self.get_local_jdk_version(get)
        reuslt['tomcat_info'] = self.get_tomcat_version(get)
        return public.returnMsg(True, reuslt)
    
    def install_jdk_new(self, get):
        try:
            if not hasattr(get, 'version'):
                return public.returnMsg(False, '版本号不能为空')
            if not os.path.exists('/www/server/panel/install/jdk.sh'):
                public.ExecShell('wget -O /www/server/panel/install/jdk.sh ' + public.get_url() + '/install/0/jdk.sh')
            jdk_version = self.get_local_jdk_version()
            jdk_version = [i["name"] for i in jdk_version if i["operation"] == 0]
            if os.path.exists('/www/server/java/' + get['version']):
                return public.returnMsg(False, '版本已经存在')
            if get['version'] not in jdk_version:
                return public.returnMsg(False, '版本号不存在')
            public.writeFile('/www/server/java/{}.pl'.format(get['version']), str(os.getpid()))
            res = public.ExecShell('bash /www/server/panel/install/jdk.sh install ' + get['version'])
            public.ExecShell('rm -rf /www/server/java/{}.*'.format(get['version']))
            # self.collect_msg("jdk-{}".format(get['version']), log=res[1] + res[0])
            if res[0].find('安装java成功') == -1:
                return public.returnMsg(False, '安装java失败')
            return public.returnMsg(True, '安装java成功')
        except:
            public.ExecShell('rm -rf /www/server/java/{}.*'.format(get['version']))
            return public.returnMsg(False, '安装java失败')
    
    # def collect_msg(self, title, log=None, log_path=None):
    #     from panel_msg import collect_message
    #     logs_dir = public.get_panel_path() + "/logs/installed"
    #     if not os.path.exists(logs_dir):
    #         os.makedirs(logs_dir, 0o600)
    #     file_path = logs_dir + "/{}_{}.log".format(title, int(time.time()))
    #
    #     if log:
    #         public.writeFile(file_path, log)
    #     elif log_path and os.path.isfile(log_path):
    #         shutil.copyfile(log_path, file_path)
    #     else:
    #         public.writeFile(file_path, "{}安装结束".format(title))
    #
    #     data = {
    #         "soft_name": title,
    #         "install_status": "安装" + title + "完成",
    #         "file_name": file_path,
    #         "self_type": "soft_install",
    #         "status": 2,
    #         "task_id": -1
    #     }
    #     title = data["install_status"]
    #     res = collect_message(title, ["软件安装", "软件安装"], ["Java项目", "JAVA环境管理"], data, 'info')
    #     if isinstance(res, str):
    #         public.WriteLog("消息盒子", "安装信息收集失败")
    #         return None
    #
    #     return res
    
    # 添加本地JDK
    def add_local_jdk(self, get):
        '''
        @name 添加本地JDK
        @parcm get.jdk<>
        @return list
        '''
        jdk = get.jdk.strip()
        loacl_jdk = self.get_local_jdk_version()
        local_jdk = [i['path'] for i in loacl_jdk if i['operation'] in [1, 2]]
        if jdk in local_jdk: return public.returnMsg(False, 'jdk路径已经存在')
        jdk_path = jdk.split('/')
        if jdk_path[-1] != 'java': return public.returnMsg(False, '请填写完整的路径,例如:/www/server/jdk1.8/bin/java')
        if not os.path.exists(jdk): return public.returnMsg(False, 'JDK路径不存在')
        if not os.path.exists(self._panel_path + '/data/get_local_jdk.json'):
            # 验证JDK是否可用
            # if not self.check_jdk(jdk):return public.returnMsg(False,'JDK不可用')
            ret = public.ExecShell(jdk + ' -version')
            if ret[0].find('Error occurred') != -1:
                return public.returnMsg(False, 'JDK不可用')
            public.writeFile(self._panel_path + '/data/get_local_jdk.json', json.dumps([jdk]))
            return public.returnMsg(True, '保存成功')
        else:
            ret = public.ExecShell(jdk + ' -version')
            if ret[0].find('Error occurred') != -1:
                return public.returnMsg(False, 'JDK不可用')
            data = public.readFile(self._panel_path + '/data/get_local_jdk.json')
            if isinstance(data, str):
                data = json.loads(data)
                if jdk in data: return public.returnMsg(False, '已经存在')
                data.append(jdk)
                public.writeFile(self._panel_path + '/data/get_local_jdk.json', json.dumps(data))
                return public.returnMsg(True, '保存成功')
            else:
                public.writeFile(self._panel_path + '/data/get_local_jdk.json', json.dumps([jdk]))
                return public.returnMsg(True, '保存成功')
    
    # 删除本地JDK
    def del_local_jdk(self, get):
        jdk = get.jdk.strip()
        if '/www/server/java/' in jdk:
            jdk_version = jdk.split('/')[-3]
            public.ExecShell('rm -rf ' + '/www/server/java/' + jdk_version)
            data = public.readFile(self._panel_path + '/data/get_local_jdk.json')
            if isinstance(data, str):
                data = json.loads(data)
                if jdk in data:
                    data.remove(jdk)
                    public.writeFile(self._panel_path + '/data/get_local_jdk.json', json.dumps(data))
            return public.returnMsg(True, '删除成功')
        
        if not os.path.exists(self._panel_path + '/data/get_local_jdk.json'):
            return public.returnMsg(False, '删除失败')
        data = public.readFile(self._panel_path + '/data/get_local_jdk.json')
        if isinstance(data, str):
            data = json.loads(data)
            if jdk in data:
                data.remove(jdk)
                public.writeFile(self._panel_path + '/data/get_local_jdk.json', json.dumps(data))
                return public.returnMsg(True, '删除成功')
            else:
                return public.returnMsg(False, '删除失败')
        else:
            return public.returnMsg(False, '删除失败')
    
    def get_process_cpu_time(self, cpu_times):
        cpu_time = 0.00
        for s in cpu_times: cpu_time += s
        return cpu_time
    
    def get_cpu_precent(self, p):
        '''
            @name 获取进程cpu使用率
            @author hwliang<2021-08-09>
            @param p: Process<进程对像>
            @return dict
        '''
        skey = "cpu_pre_{}".format(p.pid)
        old_cpu_times = cache.get(skey)
        
        process_cpu_time = self.get_process_cpu_time(p.cpu_times())
        if not old_cpu_times:
            cache.set(skey, [process_cpu_time, time.time()], 3600)
            # time.sleep(0.1)
            old_cpu_times = cache.get(skey)
            process_cpu_time = self.get_process_cpu_time(p.cpu_times())
        
        old_process_cpu_time = old_cpu_times[0]
        old_time = old_cpu_times[1]
        new_time = time.time()
        cache.set(skey, [process_cpu_time, new_time], 3600)
        percent = round(
            100.00 * (process_cpu_time - old_process_cpu_time) / (new_time - old_time) / psutil.cpu_count(), 2
            )
        return percent
    
    def get_project_run_state(self, get=None, project_name=None):
        '''
            @name 获取项目运行状态
            @author hwliang<2021-08-12>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @param project_name<string> 项目名称
            @return bool
        '''
        if get: project_name = get.project_name.strip()
        project_info = self.get_project_find(project_name)
        if not project_info: return False
        if not 'project_config' in project_info: return False
        if not 'pids' in project_info['project_config']: return self.check_project_run_status_by_ps(project_info)
        pid_file = project_info['project_config']['pids']
        if not os.path.exists(pid_file): return self.check_project_run_status_by_ps(project_info)
        try:
            pid = int(public.readFile(pid_file))
        except:
            return self.check_project_run_status_by_ps(project_info)
        pids = self.get_project_pids(pid = pid)
        if not pids: return self.check_project_run_status_by_ps(project_info)
        return True
    
    @staticmethod
    def check_project_run_status_by_ps(project_conf: dict) -> bool:
        cmd_str = project_conf["project_config"]['project_cmd']
        if not isinstance(cmd_str, str):
            return False
        cmd_str = re.sub(r' {2,}', ' ', cmd_str)  # 将可能存在的多个空格更换为单空格
        tmp: str = public.ExecShell('ps aux| grep "%s" |grep -v grep' % cmd_str)[0]
        if not tmp.strip():
            return False
        try:
            tmp = re.sub(r' {2,}', ' ', tmp)
            pids = [int(i.split(' ')[1]) for i in tmp.split("\n") if bool(i)]
        except (IndexError, ValueError, TypeError):
            return False
        running_pid = []
        for pid in pids:
            if pid in psutil.pids():
                running_pid.append(pid)
        if not running_pid:
            return False
        if len(running_pid) == 1:
            public.writeFile(project_conf["project_config"]['pids'], str(running_pid[0]))
            return True
        for pid in running_pid:
            p = psutil.Process(pid)
            if p.ppid() not in running_pid:
                public.writeFile(project_conf["project_config"]['pids'], str(pid))
                return True
        return False
    
    def get_duli_run_state(self, get=None, project_name=None, bt_tomcat_web='/www/server/bt_tomcat_web', neizhi=False):
        '''
            @name 获取项目运行状态
            @author hwliang<2021-08-12>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @param project_name<string> 项目名称
            @return bool
        '''
        if get: project_name = get.project_name.strip()
        if neizhi:
            pid_file = "{}/logs/catalina-daemon.pid".format(bt_tomcat_web, project_name)
        else:
            pid_file = "{}/{}/logs/catalina-daemon.pid".format(bt_tomcat_web, project_name)
        if not os.path.exists(pid_file):
            return False
        try:
            pid_data = public.readFile(pid_file)
            if isinstance(pid_data, str) and bool(pid_data.strip()):
                tmp_pid_data = pid_data.split()
                if len(tmp_pid_data) < 1:
                    return False
                pid = int(tmp_pid_data[0])
                pids = self.get_project_pids(pid = pid)
                if not pids: return False
                return True
            else:
                return False
        except:
            return False
    
    def format_connections(self, connects):
        '''
            @name 获取进程网络连接信息
            @author hwliang<2021-08-09>
            @param connects<pconn>
            @return list
        '''
        result = []
        for i in connects:
            raddr = i.raddr
            if not i.raddr:
                raddr = ('', 0)
            laddr = i.laddr
            if not i.laddr:
                laddr = ('', 0)
            result.append(
                {
                    "fd": i.fd,
                    "family": i.family,
                    "local_addr": laddr[0],
                    "local_port": laddr[1],
                    "client_addr": raddr[0],
                    "client_rport": raddr[1],
                    "status": i.status
                }
            )
        return result
    
    def get_project_load_info(self, get=None, project_name=None):
        '''
            @name 获取项目负载信息
            @author hwliang<2021-08-12>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        if get: project_name = get.project_name.strip()
        load_info = {}
        # id_file = "{}/{}.pid".format(self._springboot_pid_path,project_name)
        project_info = self.get_project_find(project_name)
        if not project_info: return load_info
        if not 'project_config' in project_info: return load_info
        if not 'pids' in project_info['project_config']: return load_info
        pid_file = project_info['project_config']['pids']
        if not os.path.exists(pid_file): return load_info
        try:
            pid = int(public.readFile(pid_file))
        except:
            return load_info
        pids = self.get_project_pids(pid = pid)
        if not pids: return load_info
        for i in pids:
            process_info = self.get_process_info_by_pid(i)
            if process_info: load_info[i] = process_info
        return load_info
    
    def get_duli_load_info(self, get=None, project_name=None, bt_tomcat_web='/www/server/bt_tomcat_web/', neizhi=False):
        '''
            @name 获取项目负载信息
            @author hwliang<2021-08-12>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        if get: project_name = get.project_name.strip()
        load_info = {}
        if neizhi:
            pid_file = "{}/logs/catalina-daemon.pid".format(bt_tomcat_web, project_name)
        else:
            pid_file = "{}/{}/logs/catalina-daemon.pid".format(bt_tomcat_web, project_name)
        if not os.path.exists(pid_file): return load_info
        try:
            pid_data = public.readFile(pid_file)
        except:
            return load_info
        
        if isinstance(pid_data, str):
            pid = pid_data.split()[0]
            pid = int(pid)
        else:
            return load_info
        pids = self.get_project_pids(pid = pid)
        if not pids: return load_info
        for i in pids:
            process_info = self.get_process_info_by_pid(i)
            if process_info: load_info[i] = process_info
        return load_info
    
    def get_connects(self, pid):
        '''
            @name 获取进程连接信息
            @author hwliang<2021-08-09>
            @param pid<int>
            @return dict
        '''
        connects = 0
        try:
            if pid == 1: return connects
            tp = '/proc/' + str(pid) + '/fd/'
            if not os.path.exists(tp): return connects
            for d in os.listdir(tp):
                fname = tp + d
                if os.path.islink(fname):
                    l = os.readlink(fname)
                    if l.find('socket:') != -1: connects += 1
        except:
            pass
        return connects
    
    def object_to_dict(self, obj):
        '''
            @name 将对象转换为字典
            @author hwliang<2021-08-09>
            @param obj<object>
            @return dict
        '''
        result = {}
        for name in dir(obj):
            value = getattr(obj, name)
            if not name.startswith('__') and not callable(value) and not name.startswith('_'): result[name] = value
        return result
    
    def list_to_dict(self, data):
        '''
            @name 将列表转换为字典
            @author hwliang<2021-08-09>
            @param data<list>
            @return dict
        '''
        result = []
        for s in data:
            result.append(self.object_to_dict(s))
        return result
    
    def get_process_info_by_pid(self, pid):
        '''
            @name 获取进程信息
            @author hwliang<2021-08-12>
            @param pid: int<进程id>
            @return dict
        '''
        process_info = {}
        try:
            if not os.path.exists('/proc/{}'.format(pid)): return process_info
            p = psutil.Process(pid)
            status_ps = {'sleeping': '睡眠', 'running': '活动'}
            with p.oneshot():
                p_mem = p.memory_full_info()
                if p_mem.uss + p_mem.rss + p_mem.pss + p_mem.data == 0: return process_info
                p_state = p.status()
                if p_state in status_ps: p_state = status_ps[p_state]
                # process_info['exe'] = p.exe()
                process_info['name'] = p.name()
                process_info['pid'] = pid
                process_info['ppid'] = p.ppid()
                process_info['create_time'] = int(p.create_time())
                process_info['status'] = p_state
                process_info['user'] = p.username()
                process_info['memory_used'] = p_mem.uss
                process_info['cpu_percent'] = self.get_cpu_precent(p)
                try:
                    process_info['io_write_bytes'], process_info['io_read_bytes'] = p.io_counters()
                except:
                    process_info['io_write_bytes'], process_info['io_read_bytes'] = 0, 0
                process_info['connections'] = self.format_connections(p.connections())
                process_info['connects'] = self.get_connects(pid)
                process_info['open_files'] = self.list_to_dict(p.open_files())
                process_info['threads'] = p.num_threads()
                process_info['exe'] = ' '.join(p.cmdline())
            return process_info
        except:
            return process_info
    
    def get_io_speed(self, p):
        '''
            @name 获取磁盘IO速度
            @author hwliang<2021-08-12>
            @param p: Process<进程对像>
            @return list
        '''
        skey = "io_speed_{}".format(p.pid)
        old_pio = cache.get(skey)
        if not hasattr(p, 'io_counters'): return 0, 0
        pio = p.io_counters()
        if not old_pio:
            cache.set(skey, [pio, time.time()], 3600)
            # time.sleep(0.1)
            old_pio = cache.get(skey)
            pio = p.io_counters()
        old_write_bytes = old_pio[0].write_bytes
        old_read_bytes = old_pio[0].read_bytes
        old_time = old_pio[1]
        new_time = time.time()
        write_bytes = pio.write_bytes
        read_bytes = pio.read_bytes
        cache.set(skey, [pio, new_time], 3600)
        write_speed = int((write_bytes - old_write_bytes) / (new_time - old_time))
        read_speed = int((read_bytes - old_read_bytes) / (new_time - old_time))
        return write_speed, read_speed
    
    def get_project_find(self, project_name):
        '''
            @name 获取指定项目配置
            @author hwliang<2021-08-09>
            @param project_name<string> 项目名称
            @return dict
        '''
        project_info = public.M('sites').where('project_type=? AND name=?', ('Java', project_name)).find()
        if isinstance(project_info, str):
            raise public.PanelError('数据库查询错误：' + project_info)
        if not project_info: return False
        project_info['project_config'] = json.loads(project_info['project_config'])
        return project_info
    
    def project_remove_domain(self, get):
        '''
            @name 为指定项目删除域名
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                domain: string<域名>
            }
            @return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return public.returnMsg(False, '指定项目不存在')
        last_domain = get.domain
        domain_arr = get.domain.split(':')
        if len(domain_arr) == 1:
            domain_arr.append(80)
        if domain_arr[0] == get.project_name: return public.returnMsg(False, '不能删除当前项目域名')
        project_id = public.M('sites').where('name=?', (get.project_name,)).getField('id')
        if len(public.M('domain').where('pid=?', (project_find['id'],)).select()) == 1:
            return public.returnMsg(False, '项目至少需要一个域名')
        domain_id = public.M('domain').where('name=? AND pid=?', (domain_arr[0], project_id)).getField('id')
        if not domain_id:
            return public.returnMsg(False, '指定域名不存在')
        public.M('domain').where('id=?', (domain_id,)).delete()
        if get.domain in project_find['project_config']['domains']:
            project_find['project_config']['domains'].remove(get.domain)
        if get.domain + ":80" in project_find['project_config']['domains']:
            project_find['project_config']['domains'].remove(get.domain + ":80")
        public.M('sites').where('id=?', (project_id,)).save(
            'project_config', json.dumps(project_find['project_config'])
            )
        public.WriteLog(self._log_name, '从项目：{}，删除域名{}'.format(get.project_name, get.domain))
        self.set_config(get.project_name)
        self.del_hosts(domain_arr[0])
        return public.returnMsg(True, '删除域名成功')
    
    def project_get_domain(self, get):
        '''
        @name 获取指定项目的域名列表
        @author hwliang<2021-08-09>
        @param get<dict_obj>{
            project_name: string<项目名称>
        }
        @return dict
        '''
        project_id = public.M('sites').where('name=?', (get.project_name,)).getField('id')
        if not project_id:
            return public.return_data(False, '站点查询失败')
        domains = public.M('domain').where('pid=?', (project_id,)).order('id desc').select()
        # project_find = self.get_project_find(get.project_name)
        # if not project_find:
        #     return public.return_data(False, '站点查询失败')
        # if len(domains) != len(project_find['project_config']['domains']):
        #     public.M('domain').where('pid=?', (project_id,)).delete()
        #     if not project_find: return []
        #     for d in project_find['project_config']['domains']:
        #         domain = {}
        #         arr = d.split(':')
        #         if len(arr) < 2: arr.append(80)
        #         domain['name'] = arr[0]
        #         domain['port'] = int(arr[1])
        #         domain['pid'] = project_id
        #         domain['addtime'] = public.getDate()
        #         public.M('domain').insert(domain)
        #     if project_find['project_config']['domains']:
        #         domains = public.M('domain').where('pid=?', (project_id,)).select()
        return domains
    
    def project_add_domain(self, get):
        '''
        @name 为指定项目添加域名
        @author hwliang<2021-08-09>
        @param get<dict_obj>{
            project_name: string<项目名称>
            domains: list<域名列表>
        }
        @return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return public.returnMsg(False, '指定项目不存在')
        project_id = project_find['id']
        domains = get.domains
        flag = False
        res_domains = []
        for domain in domains:
            domain = domain.strip()
            if not domain: continue
            domain_arr = domain.split(':')
            domain_arr[0] = self.check_domain(domain_arr[0])
            if domain_arr[0] is False:
                res_domains.append({"name": domain, "status": False, "msg": '域名格式错误'})
                continue
            if len(domain_arr) == 1:
                domain_arr.append("")
            if domain_arr[1] == "":
                domain_arr[1] = 80
                domain += ':80'
            try:
                if not (0 < int(domain_arr[1]) < 65535):
                    res_domains.append({"name": domain, "status": False, "msg": '域名格式错误'})
                    continue
            except ValueError:
                res_domains.append({"name": domain, "status": False, "msg": '域名格式错误'})
                continue
            if not public.M('domain').where('name=?', (domain_arr[0],)).count():
                public.M('domain').add(
                    'name,pid,port,addtime', (domain_arr[0], project_id, domain_arr[1], public.getDate())
                    )
                if not domain in project_find['project_config']['domains']:
                    project_find['project_config']['domains'].append(domain)
                public.WriteLog(self._log_name, '成功添加域名{}到项目{}'.format(domain, get.project_name))
                res_domains.append({"name": domain_arr[0], "status": True, "msg": '添加成功'})
                flag = True
            else:
                public.WriteLog(self._log_name, '添加域名错误，域名{}已存在'.format(domain))
                res_domains.append(
                    {"name": domain_arr[0], "status": False, "msg": '添加错误，域名{}已存在'.format(domain)}
                    )
        if flag:
            public.M('sites').where('id=?', (project_id,)).save(
                'project_config', json.dumps(project_find['project_config'])
                )
            self.set_config(get.project_name)
        
        return self._ckeck_add_domain(get.project_name, res_domains)
    
    def get_other_pids(self, pid):
        '''
            @name 获取其他进程pid列表
            @author hwliang<2021-08-10>
            @param pid: string<项目pid>
            @return list
        '''
        plugin_name = None
        for pid_name in os.listdir(self._springboot_pid_path):
            pid_file = '{}/{}'.format(self._springboot_pid_path, pid_name)
            try:
                s_pid = int(public.readFile(pid_file))
            except:
                continue
            if pid == s_pid:
                plugin_name = pid_name[:-4]
                break
        project_find = self.get_project_find(plugin_name)
        if not project_find: return []
        if not self._pids: self._pids = psutil.pids()
        all_pids = []
        for i in self._pids:
            try:
                p = psutil.Process(i)
                if p.cwd() == project_find['project_config']['jar_path'] and p.username() == \
                        project_find['project_config']['run_user']:
                    if p.name() in ['java', 'jsvc', 'jsvc.exec']:
                        all_pids.append(i)
            except:
                continue
        return all_pids
    
    def get_project_pids(self, get=None, pid=None):
        '''
            @name 获取项目进程pid列表
            @author hwliang<2021-08-10>
            @param pid: string<项目pid>
            @return list
        '''
        if get: pid = int(get.pid)
        if not self._pids: self._pids = psutil.pids()
        project_pids = []
        if pid not in self._pids: return []
        for i in self._pids:
            try:
                p = psutil.Process(i)
                if p.status() == "zombie":
                    continue
                if p.ppid() == pid:
                    if i in project_pids:
                        continue
                    project_pids.append(i)
            except:
                continue
        other_pids = []
        for i in project_pids:
            other_pids += self.get_project_pids(pid = i)
        if os.path.exists('/proc/{}'.format(pid)):
            project_pids.append(pid)
        
        all_pids = list(set(project_pids + other_pids))
        # if not all_pids:
        # all_pids = self.get_other_pids(pid)
        return sorted(all_pids)
    
    def stop_project(self, get):
        '''
            @name 停止项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        project_info = self.get_project_find(get.project_name.strip())
        if not project_info: return public.returnMsg(False, '项目不存在')
        
        project_find = self.get_project_find(get.project_name)
        if project_find['edate'] != "0000-00-00" and project_find['edate'] < datetime.datetime.today().strftime("%Y-%m-%d"):
            return public.return_error('当前项目已过期，请重新设置项目到期时间')
        
        if project_info['project_config']['java_type'] == 'springboot':
            # pid_file = "{}/{}.pid".format(self._springboot_pid_path,get.project_name)
            pid_file = project_info['project_config']['pids']
            if not os.path.exists(pid_file): return public.returnMsg(False, '项目未启动')
            try:
                pid = int(public.readFile(pid_file))
            except:
                return public.returnMsg(False, '项目未启动')
            pids = self.get_project_pids(pid = pid)
            if not pids: return public.returnMsg(False, '项目未启动')
            self.kill_pids(pids = pids)
            if os.path.exists(pid_file): os.remove(pid_file)
            self.stop_by_user(project_info["id"])
            return public.returnMsg(True, '停止成功')
        if project_info['project_config']['java_type'] == 'duli':
            get.domain = project_info['name']
            get.type = 'stop'
            return self.pendent_tomcat_start(get)
        if project_info['project_config']['java_type'] == 'neizhi':
            get.version = project_info['project_config']['tomcat_version']
            get.type = 'stop'
            return self.start_tomcat(get)
    
    def restart_project(self, get):
        '''
            @name 重启项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if project_find['edate'] != "0000-00-00" and project_find['edate'] < datetime.datetime.today().strftime("%Y-%m-%d"):
            return public.return_error('当前项目已过期，请重新设置项目到期时间')
        res = self.stop_project(get)
        if not res['status']: return res
        res = self.start_project(get)
        if not res['status']: return res
        return public.returnMsg(True, '重启成功')
    
    def start_project(self, get):
        '''
            @name 启动项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find: return public.returnMsg(False, '项目不存在')
        
        project_find = self.get_project_find(get.project_name)
        if project_find['edate'] != "0000-00-00" and project_find['edate'] < datetime.datetime.today().strftime("%Y-%m-%d"):
            return public.return_error('当前项目已过期，请重新设置项目到期时间')
        
        self._update_project(get.project_name, project_find)
        if project_find['project_config']['java_type'] == 'duli':
            get.domain = project_find['name']
            get.type = 'start'
            return self.pendent_tomcat_start(get)
        if project_find['project_config']['java_type'] == 'neizhi':
            get.version = project_find['project_config']['tomcat_version']
            get.type = 'start'
            return self.start_tomcat(get)
        if project_find['project_config']['java_type'] == 'springboot':
            project_cmd = project_find["project_config"]['project_cmd']
            # 前置准备
            log_file = project_find["project_config"]['logs']
            pid_file = project_find["project_config"]['pids']
            nohup_log = ' &>> {log_file}'.format(log_file = log_file)
            if not int(project_find["project_config"].get('nohup_log', 1)):
                nohup_log = ''
            if 'jar_path' in project_find['project_config']:
                jar_path = project_find['project_config']['jar_path']
            else:
                jar_path = '{}'.format(self._springboot)
            # 启动脚本
            start_cmd = '''#!/bin/bash
    PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
    export PATH
    cd {jar_path}
    nohup {project_cmd}{nohup_log} &
    echo $! > {pid_file}
    '''.format(
                jar_path = jar_path,
                project_cmd = project_cmd,
                pid_file = pid_file,
                log_file = log_file,
                nohup_log = nohup_log
            )
            script_file = project_find["project_config"]['scripts']
            # 写入启动脚本
            public.writeFile(script_file, start_cmd)
            if os.path.exists(pid_file): os.remove(pid_file)
            public.ExecShell("chmod -R 777 /var/tmp/springboot/")
            # public.ExecShell("chown -R {}:{} {}".format(project_find['project_config']['run_user'],project_find['project_config']['run_user'],self._springboot))
            public.set_mode(script_file, 755)
            public.ExecShell(
                "chown  {}:{} {}".format(
                    project_find['project_config']['run_user'], project_find['project_config']['run_user'],
                    project_find['path']
                    )
                )
            if not os.path.exists(log_file): public.ExecShell("touch  {}".format(log_file))
            public.ExecShell(
                "chown  {}:{} {}".format(
                    project_find['project_config']['run_user'], project_find['project_config']['run_user'], log_file
                    )
                )
            self._pass_dir_for_user(os.path.dirname(log_file), project_find['project_config']['run_user'])
            # 判断是否在/www/  /www/wwwroot
            
            # 执行脚本文件
            p = public.ExecShell(
                "bash {}".format(script_file), user = project_find['project_config']['run_user'],
                env = os.environ.copy()
                )
            time.sleep(1)
            if not os.path.exists(pid_file):
                return public.returnMsg(False, '启动失败,请尝试切换启动用户')
            
            # 获取PID
            try:
                pid = int(public.readFile(pid_file))
            except:
                return public.returnMsg(True, '启动失败')
            time.sleep(0.4)
            pids = self.get_project_pids(pid = pid)
            # if not pids:
            #    if os.path.exists(pid_file): os.remove(pid_file)
            #    return public.returnMsg(False,'启动失败<br>{}'.format(public.GetNumLines(log_file,20)))
            self.start_by_user(project_find["id"])
            return public.returnMsg(True, '启动成功')
    
    def return_jdkcmd(self, get):
        '''
        @name  修改JDK 返回所需命令
        @param  jdK_path
        @param  cmd
        @return string cmd
        '''
        jdK_path = get.jdK_path.strip()
        cmd = get.cmd.strip()
        if not os.path.exists(jdK_path): return public.returnMsg(False, 'JDK路径不存在')
        cmd2 = cmd.split()
        if 'debug' in get:
            debug = 1
        else:
            debug = 0
        return_cmd = []
        for i in cmd2:
            if '/java' in i:
                return_cmd.append(jdK_path)
            elif '-agentlib:' in i and debug:
                continue
            else:
                return_cmd.append(i)
        
        return public.returnMsg(True, ' '.join(return_cmd))
    
    def send_cmd(self, get):
        port = get.port if 'port' in get else self.generate_random_port()
        if not hasattr(get, 'project_jdk'):
            return public.returnMsg(False, '缺少参数! project_jdk')
        project_jdk = get.project_jdk
        if not os.path.exists(project_jdk): return public.returnMsg(False, '项目JDK不存在')
        project_jar = get.project_jar.strip()
        if not os.path.exists(project_jar): return public.returnMsg(False, '项目jar不存在')
        jmx_cmd = ""
        if hasattr(get, 'jmx_status'):
            if get.jmx_status:
                jmx_port = self.generate_random_port()
                jmx_cmd = "-Dcom.sun.management.jmxremote.port={} -Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.authenticate=false -Djava.rmi.server.hostname=127.0.0.1".format(
                    jmx_port
                )
        
        if 'debug' in get:
            debug_port = self.generate_random_port()
            return public.returnMsg(
                True,
                '{} -agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address={} {} -jar -Xmx1024M -Xms256M  {} --server.port={}'.format(
                    project_jdk, debug_port, jmx_cmd, project_jar, port
                )
                )
        
        lib_path_cmd = ""
        if hasattr(get, 'lib_path') and get.lib_path:
            lib_path_cmd = "-Dloader.path={}".format(get.lib_path)
        return public.returnMsg(
            True, '{} {} {} -jar -Xmx1024M -Xms256M  {} --server.port={}'.format(
                project_jdk, lib_path_cmd, jmx_cmd, project_jar,
                port
                )
            )
    
    def return_cmd(self, get):
        '''
        @name  获取启动的命令
        @author lkq<2021-08-27>
        @param  project_jar 项目jar路径
        @param  port 项目端口号
        @param  project_jdk 项目JDK
        '''
        if 'project_cmd' not in get or not get.project_cmd.strip():
            return self.send_cmd(get)
        else:
            if not get.project_cmd:
                return self.send_cmd(get)
            # 修改port
            project_find = self.get_project_find(get.project_name)
            if not project_find:
                return self.send_cmd(get)
            project_cmd = get.project_cmd.strip()
            cmd_type = int(get.type)
            jmx_cmd = ""
            if hasattr(get, 'jmx_status'):
                project_find['project_config']['jmx_status'] = get.jmx_status
                if get.jmx_status:
                    jmx_port = self.generate_random_port()
                    jmx_cmd = "-Dcom.sun.management.jmxremote.port={} -Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.authenticate=false -Djava.rmi.server.hostname=127.0.0.1".format(
                        jmx_port
                    )
                    jmx_url = "service:jmx:rmi:///jndi/rmi://127.0.0.1:{}/jmxrmi".format(jmx_port)
                    project_find['project_config']['jmx_status'] = get.jmx_status
                    project_find['project_config']['jmx_info'] = {
                        "jmx_url": jmx_url,
                        "username": "",
                        "password": "",
                    }
            
            if cmd_type == 1:
                old_port = str(project_find['project_config']['port']).strip()
                if old_port:
                    project_cmd = project_find['project_config']['project_cmd'].replace(old_port, str(get.port))
                else:
                    res = self.send_cmd(get)
                    if not res["status"]:
                        return res
                    else:
                        project_cmd = res["msg"]
                
                project_find['project_config']['project_cmd'] = project_cmd
                project_find['project_config']['port'] = get.port
                project_find['project_config']['project_jdk'] = get.project_jdk.strip()
                pdata = {
                    'name': get.project_name.strip(),
                    'project_config': json.dumps(project_find['project_config'])
                }
                public.M('sites').where('name=?', (get.project_name,)).update(pdata)
                return public.returnMsg(True, project_cmd)
            if cmd_type == 2:
                if 'project_jdk' in project_find['project_config']:
                    project_cmd = project_find['project_config']['project_cmd'].replace(
                        str(project_find['project_config']['project_jdk']), str(get.project_jdk.strip())
                        )
                    project_cmd = project_cmd.replace(str(project_find['project_config']['port']), str(get.port))
                else:
                    project_cmd = '{} {} -jar -Xmx1024M -Xms256M  {} --server.port={}'.format(
                        get.project_jdk.strip(), jmx_cmd, get.project_jar.strip(), get.port
                        )
                
                project_find['project_config']['project_cmd'] = project_cmd
                project_find['project_config']['port'] = get.port
                project_find['project_config']['project_jdk'] = get.project_jdk.strip()
                pdata = {
                    'name': get.project_name.strip(),
                    'project_config': json.dumps(project_find['project_config'])
                }
                
                public.M('sites').where('name=?', (get.project_name,)).update(pdata)
                return public.returnMsg(True, project_cmd)
            if cmd_type == 3:
                if 'debug' in get and get.debug in (True, 1, "1", "true"):
                    if get.debug:
                        debug_port = self.generate_random_port()
                        cmd = '{} -agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address={} {} -jar -Xmx1024M -Xms256M  {} --server.port={}'.format(
                            get.project_jdk, debug_port, jmx_cmd,
                            project_find['project_config'][
                                'project_jar'],
                            project_find['project_config']['port']
                            )
                        
                        project_find['project_config']['project_cmd'] = cmd
                        project_find['project_config']['port'] = get.port
                        project_find['project_config']['project_jdk'] = get.project_jdk.strip()
                        pdata = {
                            'name': get.project_name.strip(),
                            'project_config': json.dumps(project_find['project_config'])
                        }
                        public.M('sites').where('name=?', (get.project_name,)).update(pdata)
                        return public.returnMsg(True, cmd)
                cmd = '{} {} -jar -Xmx1024M -Xms256M  {} --server.port={}'.format(
                    get.project_jdk, jmx_cmd, project_find['project_config']['project_jar'],
                    project_find['project_config']['port']
                    )
                project_find['project_config']['project_cmd'] = cmd
                project_find['project_config']['port'] = get.port
                project_find['project_config']['project_jdk'] = get.project_jdk.strip()
                pdata = {
                    'name': get.project_name.strip(),
                    'project_config': json.dumps(project_find['project_config'])
                }
                public.M('sites').where('name=?', (get.project_name,)).update(pdata)
                return public.returnMsg(True, cmd)
            if cmd_type == 4:  # jmx
                cmd = '{} {} -jar -Xmx1024M -Xms256M  {} --server.port={}'.format(
                    get.project_jdk, jmx_cmd, project_find['project_config']['project_jar'],
                    project_find['project_config']['port']
                    )
                project_find['project_config']['project_cmd'] = cmd
                project_find['project_config']['port'] = get.port
                project_find['project_config']['project_jdk'] = get.project_jdk.strip()
                pdata = {
                    'name': get.project_name.strip(),
                    'project_config': json.dumps(project_find['project_config'])
                }
                public.M('sites').where('name=?', (get.project_name,)).update(pdata)
                return public.returnMsg(True, cmd)
    
    def unbind_extranet(self, get):
        '''
            @name 解绑外网
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        project_name = get.project_name.strip()
        self.clear_config(project_name)
        public.serviceReload()
        project_find = self.get_project_find(project_name)
        project_find['project_config']['bind_extranet'] = 0
        public.M('sites').where("id=?", (project_find['id'],)).setField(
            'project_config',
            json.dumps(project_find['project_config'])
            )
        public.WriteLog(self._log_name, 'Java项目{}, 关闭外网映射'.format(project_name))
        return public.returnMsg(True, '关闭成功')
    
    def bind_extranet(self, get):
        '''
            @name 绑定外网
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        res_msg = self._check_webserver()
        if res_msg:
            return public.returnMsg(False, res_msg)
        if not public.is_apache_nginx(): return public.returnMsg(False, '请先安装Apache或者Nginx!')
        project_name = get.project_name.strip()
        project_find = self.get_project_find(project_name)
        if not project_find: return public.returnMsg(False, '项目不存在')
        if not project_find['project_config']['domains']: return public.returnMsg(
            False, '请先到【域名管理】选项中至少添加一个域名'
            )
        project_find['project_config']['bind_extranet'] = 1
        public.M('sites').where("id=?", (project_find['id'],)).setField(
            'project_config', json.dumps(project_find['project_config'])
            )
        self.set_config(project_name)
        public.WriteLog(self._log_name, 'Java项目{}, 开启外网映射'.format(project_name))
        return public.returnMsg(True, '开启外网映射成功')
    
    def create_project(self, get):
        '''
        @name 创建项目
        @author lkq<2021-08-27>
        @param  project_type  项目类型  1 内置  2 独立  3 Spring_boot 项目
        @return string
        '''
        try:
            project_type = int(get.project_type)
        except:
            return public.returnMsg(False, '项目类型参数错误')
        if project_type == 1:
            # 检查Nginx/Apache 配置文件是否OK
            isError = public.checkWebConfig()
            if isError != True:
                return public.returnMsg(
                    False, 'WEB服务器配置配置文件错误ERROR:<br><font style="color:red;">' + isError.replace(
                        "\n", '<br>'
                        ) + '</font>'
                    )
            return self.create_internal_project(get)
        elif project_type == 2:
            # 检查Nginx/Apache 配置文件是否OK
            isError = public.checkWebConfig()
            if isError != True:
                return public.returnMsg(
                    False, 'WEB服务器配置配置文件错误ERROR:<br><font style="color:red;">' + isError.replace(
                        "\n", '<br>'
                        ) + '</font>'
                    )
            return self.create_independent_project(get)
        elif project_type == 3:
            return self.create_spring_boot_project(get)
    
    def create_internal_project(self, get):
        '''
        @name 创建内置项目
        @author lkq<2021-08-27>
        @param  domain 域名
        @param  tomcat_version tomcat版本  7 8 9
        @param  project_path 项目路径
        @param  project_ps 项目描述
        @param  bind_extranet  绑定外网 默认不需要传递
        @return string
        '''
        if not public.is_apache_nginx(): return public.returnMsg(False, '未安装Apache或Nginx')
        if not 'domain' in get: return public.returnMsg(False, '请指定域名!')
        if not 'tomcat_version' in get: return public.returnMsg(False, '请指定tomcat版本!')
        if not 'project_path' in get: return public.returnMsg(False, '请指定项目路径!')
        if not 'project_name' in get:
            get.project_name = get.domain
        else:
            get.project_name = get.domain
        if not 'bind_extranet' in get:
            get.bind_extranet = 1
        else:
            get.bind_extranet = 1
        domain = get.domain.strip()
        # 判断域名是合法性
        if not self.is_domain(domain): return public.returnMsg(False, "请输入正确的域名")
        # 兼容PHP 判断域名是否存在
        if public.M('domain').where('name=?', domain).count():
            return public.returnMsg(False, '指定域名已存在: {}'.format(domain))
        tomcat_version = str(get.tomcat_version)
        project_path = get.project_path.strip()
        if not os.path.exists(project_path):
            os.makedirs(project_path)
            public.set_own(project_path, 'www')
        # project_name = get.project_name.strip()
        tomcat_list = ["7", "8", "9"]
        if not tomcat_version in tomcat_list: return public.returnMsg(False, '请指定tomcat版本!')
        # 判断tomcat是否存在
        tomcat_info = self.get_tomcat_info(tomcat_version)
        if tomcat_info['stype'] == 'uninstall': return public.returnMsg(False, '选择的tomcat不存在!')
        
        # 如果为就旧版本启动文件更改启动文件
        res = public.ExecShell('sed -n "142p" /usr/local/bttomcat/tomcat{}/bin/daemon.sh'.format(tomcat_version))[0]
        _path = '/www/wwwlogs/java/neizhi{}'.format(tomcat_version)
        if not os.path.exists(_path):
            os.makedirs(_path)
        if not res.startswith('test ".$CATALINA_OUT" = . && CATALINA_OUT="$CATALINA_BASE/logs/catalina-daemon.out"'):
            self._change_daemom_sh("/usr/local/bttomcat/tomcat%s/bin/daemon.sh" % tomcat_version, _path)
        
        # 初始化tomcat配置文件
        if not self.Initialization(tomcat_version): return public.returnMsg(
            False, "tomcat%s配置文件错误或者服务未安装" % tomcat_version
            )
        # 获取当前tomcat 的port
        tomcat_port = tomcat_info['port']
        # 判断域名是否在tomcat中
        if self.add_vhost(path = project_path, domain = domain):
            # 添加成功
            # 添加数据库信息
            pdata = {
                'name': domain,
                'path': project_path,
                'ps': get.project_ps,
                'status': 1,
                'type_id': 0,
                'project_type': 'Java',
                'project_config': json.dumps(
                    {
                        'ssl_path': '/www/wwwroot/java_node_ssl',
                        'project_name': domain,
                        'project_cwd': project_path,
                        'bind_extranet': 1,
                        'domains': [],
                        'tomcat_version': tomcat_version,
                        'java_type': 'neizhi',
                        'server_xml': '/usr/local/bttomcat/tomcat%s/conf/server.xml' % tomcat_version,
                        'port': int(tomcat_port),
                        'auth': '1',  ##默认开机自动启动
                        'nohup_log': get.nohup_log if hasattr(get, 'nohup_log') else 1
                    }
                ),
                'addtime': public.getDate()
            }
            domains = []
            if get.bind_extranet == 1:
                domains.append(domain)
            project_id = public.M('sites').insert(pdata)
            self.set_hosts(domain)
            # 建立反代项目
            if get.bind_extranet == 1:
                format_domains = []
                for domain in domains:
                    if domain.find(':') == -1: domain += ':80'
                    format_domains.append(domain)
                get.domains = format_domains
                self.project_add_domain(get)
            self.set_config(domain)
            public.WriteLog(self._log_name, '添加Java项目{}'.format(domain))
            # 重载服务
            # 检查配置文件是否OK 如果存在问题则回退配置文件
            get.version = tomcat_version
            get.type = 'reload'
            self.start_tomcat(get)
            return public.returnMsg(True, "添加成功")
        else:
            return public.returnMsg(False, "添加失败")
    
    def create_independent_project(self, get):
        '''
        @name 创建独立项目
        @author lkq<2021-08-27>
        @param  domain 域名
        @param  project_path 项目路径
        @param  port 端口号
        @param  tomcat_version 项目tomcat版本  7 8 9
        #param  project_ps 项目描述
        @param  auth    开机自动启动
        '''
        # 检查是否安装Apache或者Nginx
        if not public.is_apache_nginx(): return public.returnMsg(False, '未安装Apache或Nginx')
        if 'auto' not in get: get.auto = '0'
        port = get.port
        project_path = get.project_path.strip()
        # project_name=get.project_name.strip()
        if not hasattr(get, "tomcat_version"):
            return public.returnMsg(False, '未指定Tomcat版本')
        tomcat_version = str(get.tomcat_version)
        domain = get.domain.strip()
        if not 'project_name' in get:
            get.project_name = get.domain
        else:
            get.project_name = get.domain
        if hasattr(get, 'jdk_path'):
            jdk_path = get.jdk_path.strip()
        else:
            jdk_path = "/usr/local/btjdk/jdk8"
        # 判断域名是合法性
        if not self.is_domain(domain): return public.returnMsg(False, "请输入正确的域名")
        # 兼容PHP 判断域名是否存在
        if public.M('domain').where('name=?', domain).count():
            return public.returnMsg(False, '指定域名已存在: {}'.format(domain))
        if 'bind_extranet' in get:
            get.bind_extranet = 1
        else:
            get.bind_extranet = 1
        tomcat_list = ["7", "8", "9"]
        if not tomcat_version in tomcat_list: return public.returnMsg(False, '请指定tomcat版本!')
        if int(port) < 1 or int(port) > 65535: return public.returnMsg(False, '端口范围不合法')
        if self.check_port(port): return public.returnMsg(False, "端口被占用, 请更换其他端口")
        # 判断是否存在
        if os.path.exists(self.__site_path + domain): return public.returnMsg(
            False, "该网站已经存在。如想建立请删除%s" % self.__site_path + domain
            )
        if not os.path.exists(project_path):
            os.makedirs(project_path)
            public.set_own(project_path, 'www')
        # 首先需要先复制好文件过去
        if not os.path.exists(self.__site_path + domain):
            public.ExecShell('mkdir -p %s' % self.__site_path + domain)
        if tomcat_version == 'tomcat7' or tomcat_version == '7':
            if not os.path.exists(self.__tomcat7_path_bak + '/conf/server.xml'): return public.returnMsg(
                False, "tomcat7的配置文件不存在，请重新安装tomcat7"
                )
            public.ExecShell(
                'cp -r %s/* %s  && chown -R www:www %s' % (
                self.__tomcat7_path_bak, self.__site_path + domain, self.__site_path + domain)
                )
        if tomcat_version == 'tomcat8' or tomcat_version == '8':
            if not os.path.exists(self.__tomcat8_path_bak + '/conf/server.xml'): return public.returnMsg(
                False, "tomcat8的配置文件不存在，请重新安装tomcat8"
                )
            public.ExecShell(
                'cp -r %s/* %s && chown -R www:www %s' % (
                self.__tomcat8_path_bak, self.__site_path + domain, self.__site_path + domain)
                )
        if tomcat_version == 'tomcat9' or tomcat_version == '9':
            if not os.path.exists(self.__tomcat9_path_bak + '/conf/server.xml'): return public.returnMsg(
                False, "tomcat9的配置文件不存在，请重新安装tomcat9"
                )
            public.ExecShell(
                'cp -r %s/* %s && chown -R www:www %s' % (
                self.__tomcat9_path_bak, self.__site_path + domain, self.__site_path + domain)
                )
        # server.xml
        if os.path.exists(self.__site_path + domain + '/conf/server.xml'):
            ret = '''<Server port="{}" shutdown="SHUTDOWN">
    <Listener className="org.apache.catalina.startup.VersionLoggerListener" />
    <Listener SSLEngine="on" className="org.apache.catalina.core.AprLifecycleListener" />
    <Listener className="org.apache.catalina.core.JreMemoryLeakPreventionListener" />
    <Listener className="org.apache.catalina.mbeans.GlobalResourcesLifecycleListener" />
    <Listener className="org.apache.catalina.core.ThreadLocalLeakPreventionListener" />
    <GlobalNamingResources>
    <Resource auth="Container" description="User database that can be updated and saved" factory="org.apache.catalina.users.MemoryUserDatabaseFactory" name="UserDatabase" pathname="conf/tomcat-users.xml" type="org.apache.catalina.UserDatabase" />
    </GlobalNamingResources>
    <Service name="Catalina">
    <Connector connectionTimeout="20000" port="8083" protocol="HTTP/1.1" redirectPort="8490" />
    <Engine defaultHost="localhost" name="Catalina">
        <Realm className="org.apache.catalina.realm.LockOutRealm">
        <Realm className="org.apache.catalina.realm.UserDatabaseRealm" resourceName="UserDatabase" />
        </Realm>
        <Host appBase="webapps" autoDeploy="true" name="localhost" unpackWARs="true">
        <Valve className="org.apache.catalina.valves.AccessLogValve" directory="logs" pattern="%h %l %u %t &quot;%r&quot; %s %b" prefix="localhost_access_log" suffix=".txt" />
        </Host>
    </Engine>
    </Service>
</Server>'''.format(self.generate_random_port())
            log_path = "/www/wwwlogs/java/{}".format(get.project_name)
            if not os.path.exists(log_path) or os.path.isfile(log_path):
                os.makedirs(log_path, mode = 0o777)
            if not self._change_daemom_sh(
                    self.__site_path + domain + '/bin/daemon.sh', log_path, domain.replace(".", '_')
                    ):
                os.system('rm -rf %s' % self.__site_path + domain)
                return public.returnMsg(False, "配置文件不存在请重新安装tomcat后尝试新建网站")
            public.WriteFile(self.__site_path + domain + '/conf/server.xml', ret)
        else:
            os.system('rm -rf %s' % self.__site_path + domain)
            return public.returnMsg(False, "配置文件不存在请重新安装tomcat后尝试新建网站")
        
        if not self.Initialization2(tomcat_version, domain): return public.returnMsg(
            False, "配置文件错误或者服务未安装"
            )
        # 先改他的端口
        ret = self.set_site_port(port, tomcat_version, domain)
        if not ret['status']: return ret
        ret = self.add_vhost(path = project_path, domain = domain)
        if ret:
            self.set_hosts(domain)
            # 启动实例
            pid_path = '/www/server/web_site/%s/logs/catalina-daemon.pid' % domain
            if os.path.exists(pid_path):
                os.remove(pid_path)
            public.ExecShell('sh %s' % self.__site_path + domain + '/bin/daemon.sh start')
            # 启动成功后建立反代项目
            pdata = {
                'name': domain,
                'path': project_path,
                'ps': get.project_ps,
                'status': 1,
                'type_id': 0,
                'project_type': 'Java',
                'project_config': json.dumps(
                    {
                        'ssl_path': '/www/wwwroot/java_node_ssl',
                        'project_name': domain,
                        'project_cwd': project_path,
                        'bind_extranet': 1,
                        'domains': [],
                        'java_type': 'duli',
                        'tomcat_version': tomcat_version,
                        'server_xml': self.__site_path + domain + '/conf/server.xml',
                        'jdk_path': jdk_path,
                        'port': int(port),
                        'auth': get.auth,
                        'logs': "/www/wwwlogs/java/{}/".format(domain),
                        'nohup_log': get.nohup_log if hasattr(get, 'nohup_log') else 1
                    }
                ),
                'addtime': public.getDate()
            }
            domains = []
            if get.bind_extranet == 1:
                domains.append(domain)
            project_id = public.M('sites').insert(pdata)
            self.set_hosts(domain)
            # 建立反代项目
            if get.bind_extranet == 1:
                format_domains = []
                for domain in domains:
                    if domain.find(':') == -1: domain += ':80'
                    format_domains.append(domain)
                get.domains = format_domains
                self.project_add_domain(get)
            self.set_config(domain)
            if jdk_path != "/usr/local/btjdk/jdk8":
                self.change_duli_tomcat_jdk(domain, jdk_path)
            
            public.WriteLog(self._log_name, '添加Java项目{}'.format(domain))
            return public.returnMsg(True, "添加成功")
        else:
            return public.returnMsg(False, "域名存在")
    
    def check_port_is_used(self, port, sock=False):
        '''
            @name 检查端口是否被占用
            @author hwliang<2021-08-09>
            @param port: int<端口>
            @return bool
        '''
        if not isinstance(port, int): port = int(port)
        if port == 0: return False
        project_list = public.M('sites').where('status=? AND project_type=?', (1, 'Java')).field(
            'name,path,project_config'
            ).select()
        for project_find in project_list:
            project_config = json.loads(project_find['project_config'])
            if not 'port' in project_config: continue
            try:
                if int(project_config['port']) == port:
                    return True
            except:
                continue
        if sock: return False
        return public.check_tcp('127.0.0.1', port)
    
    def get_host_url(self, get):
        if 'port' in get:
            port = get['port']
            return 'http://127.0.0.1:'.format(port)
        else:
            return 'http://127.0.0.1:6611'
    
    def create_spring_boot_project(self, get):
        '''
        @name 创建Spring_boot项目
        @author lkq<2021-08-27>
        @param  domains 域名  可选
        @param  project_jar 项目jar路径
        @param  project_name 项目名称
        @param  port 项目端口号
        @param  project_jdk 项目JDK
        @param  project_cmd  最终执行的命令
        @parcm  run_user 项目用户
        @parcm  bind_extranet 是否绑定外网
        @param  auth 开启自启动
        @parcm  project_ps  描述
        '''
        self.set_spring_user()
        if get.run_user != 'root':
            ret = public.ReadFile('/etc/passwd')
            if isinstance(ret, str):
                rec = 'springboot'
                if not re.search(rec, ret):
                    return public.returnMsg(
                        False, 'springboot用户建立失败,疑是安全软件拦截。手动建立用户操作如下: useradd -s /sbin/nologin springboot'
                        )
            else:
                return public.returnMsg(
                    False, 'springboot用户建立失败,疑是安全软件拦截。手动建立用户操作如下: useradd -s /sbin/nologin springboot'
                    )
        if not 'project_jdk' in get: return public.returnMsg(False, "请输入你的JDK路径")
        if not 'project_jar' in get: return public.returnMsg(False, "请输入你的jar路径")
        if not 'project_name' in get and get.project_name.strip(): return public.returnMsg(False, "请输入你的项目名称")
        if not 'port' in get: return public.returnMsg(False, "请输入你的项目端口号")
        if not 'run_user' in get: return public.returnMsg(False, "请输入你的项目用户")
        # if not 'auth' in get: return public.returnMsg(False, "请输入是否开机自启动")
        if not 'project_cmd' in get: return public.returnMsg(False, "请输入你的项目启动命令")
        if not hasattr(get, 'project_ps'): return public.returnMsg(False, "请输入你的项目启动命令")
        if not 'project_ps' in get: get.project_ps = ''
        if not 'is_separation' in get: get.is_separation = 0
        get.project_name = get.project_name.strip()
        if public.M('sites').where('name=? ', (get.project_name,)).count():
            return public.return_error('指定项目名称已存在: {}'.format(get.project_name))
        project_path = os.path.dirname(get.project_jar)
        if not public.check_site_path(project_path):
            a, c = public.get_sys_path()
            return public.returnMsg(False, '请不要项目文件放到以下关键目录中: <br>{}'.format("<br>".join(a + c)))
        
        if get.is_separation:
            if public.get_webserver() == 'apache':
                return public.returnMsg(False, "前后端分离不支持Apache")
            get.is_separation = 1
        ##静态资源目录
        if get.is_separation and ('static_path' not in get or not get.static_path.strip()):
            get.static_path = '/www/wwwroot/' + get.project_name.split('/')[0]
        if 'api_url' not in get or not get.api_url.strip():
            get.api_url = '/'
        elif get.api_url != '/' and get.api_url[-1] == '/':
            get.api_url = get.api_url[:-1]
        if not hasattr(get, 'auth'):
            get.auth = '0'
        if get.is_separation:
            if 'host_url' not in get or not get.host_url.strip():
                return public.returnMsg(False, "请输入你需要的后端地址")
            else:
                if get.host_url[-1] == '/':
                    get.host_url = get.host_url[:-1]
        if 'domains' in get:
            domains = get.domains
            if len(domains) >= 1:
                get.bind_extranet = 1
                # 检查Nginx/Apache 配置文件是否OK
                isError = public.checkWebConfig()
                if isError != True:
                    return public.returnMsg(
                        False, 'WEB服务器配置配置文件错误ERROR:<br><font style="color:red;">' + isError.replace(
                            "\n", '<br>'
                            ) + '</font>'
                        )
            else:
                get.bind_extranet = 0
        else:
            get.domains = []
            get.bind_extranet = 0
        if public.M('sites').where('name=?', (get.project_name,)).count():
            return public.returnMsg(False, '指定项目名称已存在: {}'.format(get.project_name))
        project_name = get.project_name.strip()
        # if not re.match("^\w+$",project_name):
        #     return public.return_error('项目名称格式不正确，支持字母、数字、下划线，表达式: ^[0-9A-Za-z_]$')
        # 端口占用检测
        if self.check_port(get.port):
            return public.returnMsg(
                False, '指定端口已被其它应用占用，请修改您的项目配置使用其它端口, 端口: {}'.format(get.port)
                )
        # 判断JDK路径是否存在
        if not os.path.exists(get.project_jdk): return public.returnMsg(False, '请输入正确的JDK路径')
        domains = []
        if get.bind_extranet == 1:
            domains = get.domains
        for domain in domains:
            domain_arr = domain.split(':')
            if public.M('domain').where('name=?', domain_arr[0]).count():
                return public.returnMsg(False, '指定域名已存在: {}'.format(domain))
        # 获取jar包的路径
        project_jar = get.project_jar.strip()
        if not os.path.exists(project_jar): return public.returnMsg(False, '请输入正确的jar包路径')
        # 获取jar的根目录
        if not get.is_separation:
            get.host_url = False
        pdata = {
            'name': get.project_name,
            'path': get.project_jar,
            'ps': get.project_ps,
            'status': 1,
            'type_id': 0,
            'project_type': 'Java',
            'project_config': json.dumps(
                {
                    'project_jdk': get.project_jdk.strip(),
                    'ssl_path': '/www/wwwroot/java_node_ssl',
                    'project_name': get.project_name.strip(),
                    'project_jar': get.project_jar.strip(),
                    'bind_extranet': get.bind_extranet,
                    'domains': [],
                    'run_user': get.run_user.strip(),
                    'jmx_status': getattr(get, "jmx_status", False),
                    'jmx_info': {
                        "jmx_url": "service:jmx:rmi:///jndi/rmi://127.0.0.1:{}/jmxrmi".format(get.jmx_port) if hasattr(
                            get, "jmx_port"
                            ) else None,
                        "username": "",
                        "password": "",
                    },
                    'port': int(get.port),
                    'auth': get.auth,
                    'project_cmd': get.project_cmd.strip(),
                    'java_type': 'springboot',
                    'jar_path': project_path,
                    'pids': self._springboot_pid_path + '/' + get.project_name.strip() + '.pid',
                    'logs': self._springboot_logs_path + '/' + get.project_name.strip() + '.log',
                    'scripts': self._springboot_run_scripts + '/' + get.project_name.strip() + '.sh',
                    'is_separation': get.is_separation,
                    'static_path': getattr(get, "static_path", None),
                    'api_url': get.api_url,
                    'host_url': get.host_url,
                    'nohup_log': get.nohup_log if hasattr(get, 'nohup_log') else 1
                }
            ),
            'addtime': public.getDate()
        }
        project_id = public.M('sites').insert(pdata)
        if get.bind_extranet == 1:
            format_domains = []
            for domain in domains:
                if domain.find(':') == -1: domain += ':80'
                format_domains.append(domain)
            get.domains = format_domains
            self.project_add_domain(get)
        self.set_config(get.project_name)
        # 设置java启动目录为某个用户权限
        public.ExecShell("chown {}:{} {}".format(get.run_user.strip(), get.run_user.strip(), project_path))
        if get.is_separation:
            if not os.path.exists(get.static_path):
                public.ExecShell("mkdir -p {}".format(get.static_path))
                public.ExecShell("chown {}:{} {}".format(get.run_user.strip(), get.run_user.strip(), get.static_path))
            else:
                public.ExecShell(
                    "chown -R {}:{} {}".format(get.run_user.strip(), get.run_user.strip(), get.static_path)
                    )
        
        public.WriteLog(self._log_name, '添加Java Springboot项目{}'.format(get.project_name))
        self.start_project(get)
        # 将所有的监听端口找出来，用于放行
        load_info = self.get_project_load_info(project_name = get.project_name)
        if load_info:
            listen = []
            for pid in load_info.keys():
                if 'connections' not in load_info[pid]:
                    continue
                for conn in load_info[pid]['connections']:
                    if not conn['status'] == 'LISTEN':
                        continue
                    if not conn['local_port'] in listen:
                        listen.append(str(conn['local_port']))
            if listen:
                get.port = ",".join(listen)
        
        flag, tip = self._release_firewall(get)
        msg = '添加项目成功' + ("" if flag else "<br>" + tip)
        if "use_project_watch" in get and get.use_project_watch in ("1", "true", "yes", 1):
            add_project_watch(
                p_name = get.project_name.strip(),
                p_type = "java",
                site_id = project_id,
                watch_path = get.project_jar.strip()
                )
        return public.returnMsg(True, msg, project_id)
    
    def kill_pids(self, get=None, pids=None):
        '''
            @name 结束进程列表
            @author hwliang<2021-08-10>
            @param pids: string<进程pid列表>
            @return dict
        '''
        if get: pids = get.pids
        if not pids: return public.returnMsg(True, '没有进程')
        pids = sorted(pids, reverse = True)
        for i in pids:
            try:
                p = psutil.Process(i)
                p.terminate()
            except:
                pass
        return public.returnMsg(True, '进程已全部结束')
    
    def get_project_list2(self, get):
        '''
        @name 取项目列表
        @author lkq<2021-08-27>
        @param  domain 域名
        @return string
        '''
        if not 'p' in get:  get.p = 1
        if not 'limit' in get: get.limit = 12
        if not 'callback' in get: get.callback = ''
        if not 'order' in get: get.order = 'id desc'
        
        if 'search' in get:
            get.project_name = get.search.strip()
            search = "%{}%".format(get.project_name)
            count = public.M('sites').where(
                'project_type=? AND (name LIKE ? OR ps LIKE ?)', ('Java', search, search)
                ).count()
            data = public.get_page(count, int(get.p), int(get.limit), get.callback)
            data['data'] = public.M('sites').where(
                'project_type=? AND (name LIKE ? OR ps LIKE ?)', ('Java', search, search)
                ).limit(data['shift'] + ',' + data['row']).order(get.order).select()
        else:
            count = public.M('sites').where('project_type=?', 'Java').count()
            data = public.get_page(count, int(get.p), int(get.limit), get.callback)
            data['data'] = public.M('sites').where('project_type=?', 'Java').limit(
                data['shift'] + ',' + data['row']
                ).order(get.order).select()
        
        for i in range(len(data['data'])):
            project_config = json.loads(data['data'][i]['project_config'])
            # 如果内置项目被删除 则直接删除当前项目
            if project_config['java_type'] == 'neizhi' or project_config['java_type'] == 'duli':
                if not os.path.exists(project_config['server_xml']):
                    # 删除项目
                    data['data'][i]['is_file_ok'] = False
                else:
                    data['data'][i]['is_file_ok'] = True
                    # get.project_name = data['data'][i]['name']
                    # self.remove_project(get)
            
            # 独立项目如果目录被删除
        for i in range(len(data['data'])):
            data['data'][i] = self.get_project_stat(data['data'][i])
        return data
    
    def get_tomcat_domain(self, get):
        verison = str(get.version).strip()
        version_list = ["7", "8", "9"]
        if verison not in version_list: return public.returnMsg(False, '请选择版本')
        data = public.M('sites').where('project_type=?', ('Java')).select()
        ret = []
        for i in data:
            project_config = json.loads(i['project_config'])
            if project_config['java_type'] == 'neizhi':
                if project_config["tomcat_version"] == verison:
                    ret.append(i['name'])
        return ret
    
    def get_project_list(self, get):
        '''
        @name 取项目列表
        @author lkq<2021-08-27>
        @param  domain 域名
        @return string
        '''
        if not 'p' in get:  get.p = 1
        if not 'limit' in get: get.limit = 20
        if not 'callback' in get: get.callback = ''
        if not 'order' in get: get.order = 'id desc'
        type_id = None
        if "type_id" in get:
            try:
                type_id = int(get.type_id)
            except:
                type_id = None
        
        if 'search' in get:
            get.project_name = get.search.strip()
            search = "%{}%".format(get.project_name)
            if type_id is None:
                count = public.M('sites').where(
                    'project_type=? AND (name LIKE ? OR ps LIKE ?)',
                    ('Java', search, search)
                    ).count()
                data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                data['data'] = public.M('sites').where(
                    'project_type=? AND (name LIKE ? OR ps LIKE ?)',
                    ('Java', search, search)
                    ).limit(
                    data['shift'] + ',' + data['row']
                ).order(get.order).select()
            else:
                count = public.M('sites').where(
                    'project_type=? AND (name LIKE ? OR ps LIKE ?) AND type_id = ?',
                    ('Java', search, search, type_id)
                    ).count()
                data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                data['data'] = public.M('sites').where(
                    'project_type=? AND (name LIKE ? OR ps LIKE ?) AND type_id = ?',
                    ('Java', search, search, type_id)
                    ).limit(
                    data['shift'] + ',' + data['row']
                ).order(get.order).select()
        
        else:
            if type_id is None:
                count = public.M('sites').where('project_type=?', 'Java').count()
                data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                data['data'] = public.M('sites').where('project_type=?', 'Java').limit(
                    data['shift'] + ',' + data['row']
                ).order(get.order).select()
            else:
                count = public.M('sites').where('project_type=? AND type_id = ?', ('Java', type_id)).count()
                data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                data['data'] = public.M('sites').where('project_type=? AND type_id = ?', ('Java', type_id)).limit(
                    data['shift'] + ',' + data['row']
                ).order(get.order).select()
        
        if isinstance(data["data"], str) and data["data"].startswith("error"):
            raise public.PanelError("数据库查询错误：" + data["data"])
        
        # 处理内置项目和独立项目是否被删除
        for i in range(len(data['data'])):
            project_config = json.loads(data['data'][i]['project_config'])
            # 如果内置项目被删除 则直接删除当前项目
            if project_config['java_type'] == 'neizhi':
                if not os.path.exists(project_config['server_xml']):
                    # 删除项目
                    data['data'][i]['is_file_ok'] = False
                else:
                    # 判断这个域名是否存在于配置文件中
                    if not self.Initialization(project_config['tomcat_version']): data['data'][i]['is_file_ok'] = False
                    if self.get_vhost(data['data'][i]['name']):
                        data['data'][i]['is_file_ok'] = True
                    else:
                        data['data'][i]['is_file_ok'] = False
            if project_config['java_type'] == 'duli':
                if not os.path.exists(project_config['server_xml']):
                    data['data'][i]['is_file_ok'] = False
                else:
                    if not self.Initialization2(version = '7', site = data['data'][i]['name']): data['data'][i][
                        'is_file_ok'] = False
                    if self.get_vhost(data['data'][i]['name']):
                        data['data'][i]['is_file_ok'] = True
                    else:
                        data['data'][i]['is_file_ok'] = False
        for i in range(len(data['data'])):
            data['data'][i] = self.get_project_stat(data['data'][i])
            project_config = data['data'][i]['project_config']
            project_config["use_project_watch"] = use_project_watch(project_config['project_name'])
            if 'project_cmd' in project_config:
                # 检查project_cmd字段是否包含'-Dloader.path='
                if '-Dloader.path=' in project_config['project_cmd']:
                    # 使用split方法提取出lib路径
                    lib_path = project_config['project_cmd'].split("-Dloader.path=")[1].split(" ")[0]
                    # 在返回的项目数据中添加lib_path字段
                    data['data'][i]['lib_path'] = lib_path
        
        # 返回更新后的data
        return data
    
    # 修复独立项目
    def fix_project(self, get):
        '''
        @name 修复项目
        @author lkq<2021-08-27>
        @param  project_name 域名
        @return string
        '''
        if not public.is_apache_nginx(): return public.returnMsg(False, '未安装Apache或Nginx')
        project_info = self.get_project_find(get.project_name.strip())
        if not project_info: return public.returnMsg(False, '项目不存在')
        project_config = project_info['project_config']
        if project_config['java_type'] == 'duli':
            if not os.path.exists(
                    self.__bttomcat_path + "/tomcat_bak{}/conf/server.xml".format(
                            project_config['tomcat_version']
                    )
                    ): return public.returnMsg(False, '修复失败当前Tomcat版本未安装')
            tomcat_list = ["7", "8", "9"]
            if not project_config['tomcat_version'] in tomcat_list: return public.returnMsg(False, '请指定tomcat版本!')
            if self.check_port(str(project_config['port'])):
                return public.returnMsg(False, "%s端口被占用,修复失败" % str(project_config['port']))
            # 判断是否存在
            if not os.path.exists(project_info['path']):
                os.makedirs(project_info['path'])
                public.set_own(project_info['path'], 'www')
            # 确定目录存在。先删除目录
            domain = project_info['name']
            if os.path.exists(self.__site_path + domain):
                public.ExecShell('rm -rf ' + self.__site_path + domain)
            tomcat_version = project_config['tomcat_version']
            # 复制项目
            if not os.path.exists(self.__site_path + domain):
                public.ExecShell('mkdir -p %s' % self.__site_path + domain)
            if tomcat_version == 'tomcat7' or tomcat_version == '7':
                if not os.path.exists(self.__tomcat7_path_bak + '/conf/server.xml'): return public.returnMsg(
                    False, "tomcat7的配置文件不存在，请重新安装tomcat7"
                    )
                public.ExecShell(
                    'cp -r %s/* %s  && chown -R www:www %s' % (
                    self.__tomcat7_path_bak, self.__site_path + domain, self.__site_path + domain)
                    )
            if tomcat_version == 'tomcat8' or tomcat_version == '8':
                if not os.path.exists(self.__tomcat8_path_bak + '/conf/server.xml'): return public.returnMsg(
                    False, "tomcat8的配置文件不存在，请重新安装tomcat8"
                    )
                public.ExecShell(
                    'cp -r %s/* %s && chown -R www:www %s' % (
                    self.__tomcat8_path_bak, self.__site_path + domain, self.__site_path + domain)
                    )
            if tomcat_version == 'tomcat9' or tomcat_version == '9':
                if not os.path.exists(self.__tomcat9_path_bak + '/conf/server.xml'): return public.returnMsg(
                    False, "tomcat9的配置文件不存在，请重新安装tomcat9"
                    )
                public.ExecShell(
                    'cp -r %s/* %s && chown -R www:www %s' % (
                    self.__tomcat9_path_bak, self.__site_path + domain, self.__site_path + domain)
                    )
            # server.xml
            if os.path.exists(self.__site_path + domain + '/conf/server.xml'):
                ret = '''<Server port="{}" shutdown="SHUTDOWN">
        <Listener className="org.apache.catalina.startup.VersionLoggerListener" />
        <Listener SSLEngine="on" className="org.apache.catalina.core.AprLifecycleListener" />
        <Listener className="org.apache.catalina.core.JreMemoryLeakPreventionListener" />
        <Listener className="org.apache.catalina.mbeans.GlobalResourcesLifecycleListener" />
        <Listener className="org.apache.catalina.core.ThreadLocalLeakPreventionListener" />
        <GlobalNamingResources>
        <Resource auth="Container" description="User database that can be updated and saved" factory="org.apache.catalina.users.MemoryUserDatabaseFactory" name="UserDatabase" pathname="conf/tomcat-users.xml" type="org.apache.catalina.UserDatabase" />
        </GlobalNamingResources>
        <Service name="Catalina">
        <Connector connectionTimeout="20000" port="8083" protocol="HTTP/1.1" redirectPort="8490" />
        <Engine defaultHost="localhost" name="Catalina">
            <Realm className="org.apache.catalina.realm.LockOutRealm">
            <Realm className="org.apache.catalina.realm.UserDatabaseRealm" resourceName="UserDatabase" />
            </Realm>
            <Host appBase="webapps" autoDeploy="true" name="localhost" unpackWARs="true">
            <Valve className="org.apache.catalina.valves.AccessLogValve" directory="logs" pattern="%h %l %u %t &quot;%r&quot; %s %b" prefix="localhost_access_log" suffix=".txt" />
            </Host>
        </Engine>
        </Service>
    </Server>'''.format(self.generate_random_port(), get.project_name.strip())
                log_path = "/www/wwwlogs/java/{}".format(get.project_name)
                if not os.path.exists(log_path) or os.path.isfile(log_path):
                    os.makedirs(log_path, mode = 0o777)
                public.WriteFile(self.__site_path + domain + '/conf/server.xml', ret)
            else:
                os.system('rm -rf %s' % self.__site_path + domain)
                return public.returnMsg(False, "配置文件不存在请重新安装tomcat后尝试新建网站")
            if not self.Initialization2(tomcat_version, domain):
                return public.returnMsg(False, "配置文件错误或者服务未安装")
            # 先改他的端口
            ret = self.set_site_port(str(project_config['port']), tomcat_version, domain)
            if not ret['status']: return ret
            ret = self.add_vhost(path = project_info['path'], domain = domain)
            if ret:
                # 启动实例
                pid_path = '/www/server/web_site/%s/logs/catalina-daemon.pid' % domain
                if os.path.exists(pid_path):
                    os.remove(pid_path)
                public.ExecShell('sh %s' % self.__site_path + domain + '/bin/daemon.sh start')
                # 建立反代项目
                public.WriteLog(self._log_name, '修复Java项目{}成功'.format(domain))
                return public.returnMsg(True, "修复成功")
        if project_config['java_type'] == 'neizhi':
            if not os.path.exists(
                self.__bttomcat_path + "/tomcat{}/conf/server.xml".format(project_config['tomcat_version'])
                ): return public.returnMsg(False, '修复失败当前Tomcat版本未安装')
            if not self.Initialization(project_config['tomcat_version']): return public.returnMsg(
                False, "tomcat%s配置文件错误或者服务未安装" % project_config['tomcat_version']
                )
            if self.add_vhost(path = project_info['path'], domain = project_info['name']):
                res = self.stop_project(get)
                res = self.start_project(get)
                return public.returnMsg(True, '修复成功')
            else:
                if self.get_vhost(project_info['name']):
                    return public.returnMsg(True, '已经修复成功请不要重复提交')
                return public.returnMsg(True, '修复失败')
        else:
            return public.returnMsg(False, '该项目不是Tomcat独立项目或者Tomcat内置项目')
    
    def get_project_info(self, get):
        '''
            @name 获取指定项目信息
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        if not hasattr(get, 'project_name'):
            return public.returnMsg(False, '请传递项目名称!')
        project_info = public.M('sites').where('project_type=? AND name=?', ('Java', get.project_name)).find()
        if not project_info: return public.returnMsg(False, '指定项目不存在!')
        project_info = self.get_project_stat(project_info)
        return project_info
    
    def get_ssl_end_date(self, project_name):
        '''
            @name 获取SSL信息
            @author hwliang<2021-08-09>
            @param project_name <string> 项目名称
            @return dict
        '''
        import data
        return data.data().get_site_ssl_info('java_{}'.format(project_name))
    
    def get_project_stat(self, project_info):
        '''
            @name 获取项目状态信息
            @author hwliang<2021-08-09>
            @param project_info<dict> 项目信息
            @return list
        '''
        project_info['project_config'] = json.loads(project_info['project_config'])
        if "jdk_path" not in project_info['project_config']:
            project_info['project_config']["jdk_path"] = "/usr/local/btjdk/jdk8"
        project_info["use_project_watch"] = use_project_watch(project_info['name'])
        if project_info['project_config']['java_type'] == 'springboot':
            project_info['run'] = self.get_project_run_state(project_name = project_info['name'])
            project_info['load_info'] = self.get_project_load_info(project_name = project_info['name'])
            project_info['ssl'] = self.get_ssl_end_date(project_name = project_info['name'])
            project_info['listen'] = []
            project_info['listen_ok'] = True
            # 远程调试
            project_info['debug'] = False
            if '-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=' in project_info['project_config'][
                'project_cmd']:
                project_info['debug'] = True
            if project_info['load_info']:
                for pid in project_info['load_info'].keys():
                    if not 'connections' in project_info['load_info'][pid]:
                        project_info['load_info'][pid]['connections'] = []
                    for conn in project_info['load_info'][pid]['connections']:
                        if not conn['status'] == 'LISTEN': continue
                        if not conn['local_port'] in project_info['listen']:
                            project_info['listen'].append(conn['local_port'])
                if project_info['listen']:
                    project_info['listen_ok'] = project_info['project_config']['port'] in project_info['listen']
            return project_info
        if project_info['project_config']['java_type'] == 'duli':
            project_info['run'] = self.get_duli_run_state(project_name = project_info['name'])
            project_info['load_info'] = self.get_duli_load_info(project_name = project_info['name'])
            project_info['ssl'] = self.get_ssl_end_date(project_name = project_info['name'])
            project_info['tomcat_info'] = self.pendent_tomcat_info(domain = project_info['name'])
            project_info['listen'] = []
            project_info['listen_ok'] = True
            if project_info['load_info']:
                for pid in project_info['load_info'].keys():
                    for conn in project_info['load_info'][pid]['connections']:
                        if not conn['status'] == 'LISTEN': continue
                        if not conn['local_port'] in project_info['listen']:
                            project_info['listen'].append(conn['local_port'])
                if project_info['listen']:
                    project_info['listen_ok'] = project_info['project_config']['port'] in project_info['listen']
            return project_info
        if project_info['project_config']['java_type'] == 'neizhi':
            project_info['run'] = self.get_duli_run_state(
                project_name = project_info['name'],
                bt_tomcat_web = '/usr/local/bttomcat/tomcat{}'.format(project_info['project_config']['tomcat_version']),
                neizhi = True
                )
            project_info['load_info'] = self.get_duli_load_info(
                project_name = project_info['name'],
                bt_tomcat_web = '/usr/local/bttomcat/tomcat{}'.format(project_info['project_config']['tomcat_version']),
                neizhi = True
                )
            project_info['ssl'] = self.get_ssl_end_date(project_name = project_info['name'])
            project_info['tomcat_info'] = self.get_tomcat_info(
                version = project_info['project_config']['tomcat_version']
                )
            project_info['listen'] = []
            project_info['listen_ok'] = True
            if project_info['load_info']:
                for pid in project_info['load_info'].keys():
                    for conn in project_info['load_info'][pid]['connections']:
                        if not conn['status'] == 'LISTEN': continue
                        if not conn['local_port'] in project_info['listen']:
                            project_info['listen'].append(conn['local_port'])
                if project_info['listen']:
                    project_info['listen_ok'] = project_info['project_config']['port'] in project_info['listen']
            return project_info
    
    # xss 防御
    def xsssec(self, text):
        return text.replace('<', '&lt;').replace('>', '&gt;')
    
    def last_lines(self, filename, lines=1):
        return public.GetNumLines(filename, lines)

    def get_project_log_old(self, get):
        '''
        @name 取项目日志
        @author lkq<2021-08-27>
        @param  domain 域名
        @param  project_name 项目名称
        @return string
        '''
        project_info = self.get_project_find(get.project_name.strip())
        if not project_info: return public.returnMsg(False, '项目不存在')
        if project_info['project_config']['java_type'] == 'springboot':
            # log_file = "{}/{}.log".format(self._springboot_logs_path,get.project_name)
            log_file = project_info['project_config']['logs']
            if not os.path.exists(log_file): return public.returnMsg(False, '日志文件不存在')
            log_file_size = os.path.getsize(log_file)
            return {
                "status": True,
                "path": log_file.rsplit("/", 1)[0],
                "size": public.to_size(log_file_size),
                "data": self.xsssec(public.GetNumLines(log_file, 3000)) if log_file_size < 3145928 else self.xsssec(
                    self.last_lines(log_file, 3000)
                    )
            }
        if project_info['project_config']['java_type'] == 'duli':
            log_file = '/www/server/bt_tomcat_web/{}/logs/catalina-daemon.out'.format(get.project_name.strip())
            log_file_size = os.path.getsize(log_file)
            return {
                "status": True,
                "path": log_file.rsplit("/", 1)[0],
                "size": public.to_size(log_file_size),
                "data": self.xsssec(public.GetNumLines(log_file, 3000)) if log_file_size < 3145928 else self.xsssec(
                    self.last_lines(log_file, 3000)
                    )
            }
        if project_info['project_config']['java_type'] == 'neizhi':
            version = project_info['project_config']['tomcat_version']
            log_file = '/usr/local/bttomcat/tomcat%s/logs/catalina-daemon.out' % version
            log_file_size = os.path.getsize(log_file)
            return {
                "status": True,
                "path": log_file.rsplit("/", 1)[0],
                "size": public.to_size(log_file_size),
                "data": self.xsssec(public.GetNumLines(log_file, 3000)) if log_file_size < 3145928 else self.xsssec(
                    self.last_lines(log_file, 3000)
                    )
            }
    
    def get_project_log(self, get):
        '''
        @name 取项目日志
        @author lkq<2021-08-27>
        @param  domain 域名
        @param  project_name 项目名称
        @return string
        '''
        
        try:
            from mod.project.java.utils import site_tomcat, bt_tomcat
        except:
            site_tomcat = bt_tomcat = None
        
        project_info = self.get_project_find(get.project_name.strip())
        if not project_info: return public.returnMsg(False, '项目不存在')
        if project_info['project_config']['java_type'] == 'springboot':
            log_file = project_info['project_config']['logs']
            # if log_file.startswith(self._springboot_logs): return self.get_project_log_old(get)
            if not os.path.exists(log_file):
                # return public.returnMsg(False, '日志文件不存在')
                log_file_size = 0
            else:
                log_file_size = os.path.getsize(log_file)
            _path = log_file.rsplit("/", 1)[0]
            if log_file_size > 3145928:
                return {
                    "status": True,
                    "path": _path,
                    "file": log_file,
                    "data": self.xsssec(self.last_lines(log_file, 3000)),
                    "size": public.to_size(log_file_size)
                }
            return {
                "status": True,
                "path": _path,
                "file": log_file,
                "data": self.xsssec(public.GetNumLines(log_file, 3000)),
                "size": public.to_size(log_file_size)
            }
        if project_info['project_config']['java_type'] == 'duli':
            if not "logs" in project_info['project_config']: return self.get_project_log_old(get)
            log_file = log_path = None
            if site_tomcat:
                tomcat_name = project_info['project_config'].get("tomcat_name", "")
                if tomcat_name:
                    tomcat = site_tomcat(tomcat_name)
                else:
                    tomcat = site_tomcat(get.project_name.strip())
                if tomcat:
                    log_file = tomcat.log_file
                    log_path = os.path.dirname(log_file) + "/"
            if log_file is None:
                log_path = project_info['project_config']['logs']
                if log_path[-1] != "/":
                    log_path = log_path + "/"
                log_file = '{}catalina-daemon-{}.out'.format(log_path, project_info["name"].replace(".", "_"))
            if not os.path.isfile(log_file):
                log_file_size = 0
            else:
                log_file_size = os.path.getsize(log_file)
            return {
                "status": True,
                "path": log_path[:-1],
                "file": log_file,
                "size": public.to_size(log_file_size),
                "data": self.xsssec(public.GetNumLines(log_file, 3000)) if log_file_size < 3145928 else self.xsssec(
                    self.last_lines(log_file, 3000)
                )
            }
        if project_info['project_config']['java_type'] == 'neizhi':
            version = project_info['project_config']['tomcat_version']
            res = public.ExecShell('sed -n "142p" /usr/local/bttomcat/tomcat{}/bin/daemon.sh'.format(version))[0]
            if res.find('test ".$CATALINA_OUT" = . && CATALINA_OUT="$CATALINA_BASE/logs/catalina-daemon.out"') == 0:
                return self.get_project_log_old(get)
            log_file = None
            if bt_tomcat:
                tomcat = bt_tomcat(version)
                if tomcat:
                    log_file = tomcat.log_file
            if log_file is None:
                try:
                    log_file = public.readFile(
                        "/usr/local/bttomcat/tomcat%s/conf/logpath.conf" % version
                    ) + f'/catalina-daemon-{version}.out'
                except:
                    log_file = '/www/wwwlogs/java/neizhi%s/catalina-daemon.out' % version
            
            if not os.path.exists(log_file):
                log_file_size = 0
            else:
                log_file_size = os.path.getsize(log_file)
            return {
                "status": True,
                "path": log_file.rsplit("/", 1)[0],
                "file": log_file,
                "size": public.to_size(log_file_size),
                "data": self.xsssec(public.GetNumLines(log_file, 3000)) if log_file_size < 3145928 else self.xsssec(
                    self.last_lines(log_file, 3000)
                )
            }
    
    def remove_project(self, get):
        '''
            @name 删除指定项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        if not 'project_name' in get: return public.returnMsg(False, '请传递项目名称')
        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return public.returnMsg(False, '指定项目不存在: {}'.format(get.project_name))
        if not project_find: return public.returnMsg(False, '项目不存在!')
        if not project_find['project_config']: return public.returnMsg(False, '项目不存在!')
        if not project_find['project_config']['java_type']: return public.returnMsg(False, '项目不存在!')
        if project_find['project_config']['java_type'] == 'duli':
            # 关闭独立项目
            get.domain = project_find['name']
            get.type = 'stop'
            self.pendent_tomcat_start(get)
            # 删除项目
            self.clear_config(get.project_name)
            public.M('domain').where('pid=?', (project_find['id'],)).delete()
            public.M('sites').where('name=?', (get.project_name,)).delete()
            public.ExecShell("rm -rf %s/%s" % (self.__site_path, project_find['name']))
            public.WriteLog(self._log_name, '删除Java项目{}'.format(get.project_name))
            for i in project_find['project_config']['domains']:
                self.del_hosts(i)
            self.del_crontab(get.project_name)
            # self.remove_sites_service_config(get.project_name)
            return public.returnMsg(True, '删除项目成功')
        elif project_find['project_config']['java_type'] == 'neizhi':
            # 删除tomcat站点
            self.tomcat_vhost_delete(project_find['project_config']['tomcat_version'], project_find['project_config']['domains'], get)
            self.clear_config(get.project_name)
            public.M('domain').where('pid=?', (project_find['id'],)).delete()
            public.M('sites').where('name=?', (get.project_name,)).delete()
            public.WriteLog(self._log_name, '删除Java项目{}'.format(get.project_name))
            # 重启tomcat
            get.version = project_find['project_config']['tomcat_version']
            get.type = 'reload'
            # self.start_tomcat(get)
            # 删除hosts
            # self.del_hosts(get.project_name)
            # 获取域名列表
            for i in project_find['project_config']['domains']:
                self.del_hosts(i)
            self.del_crontab(get.project_name)
            # self.remove_sites_service_config(get.project_name)
            return public.returnMsg(True, '删除项目成功')
        elif project_find['project_config']['java_type'] == 'springboot':
            # 停止项目
            self.stop_project(get)
            # 删除项目
            self.clear_config(get.project_name)
            public.M('domain').where('pid=?', (project_find['id'],)).delete()
            public.M('sites').where('name=?', (get.project_name,)).delete()
            pid_file = project_find['project_config']['pids']
            if os.path.exists(pid_file): os.remove(pid_file)
            script_file = project_find['project_config']['scripts']
            if os.path.exists(script_file): os.remove(script_file)
            log_file = project_find['project_config']['logs']
            if os.path.exists(log_file): os.remove(log_file)
            public.WriteLog(self._log_name, '删除Java项目{}'.format(get.project_name))
            for i in project_find['project_config']['domains']:
                self.del_hosts(i)
            self.del_crontab(get.project_name)
            # self.remove_sites_service_config(get.project_name)
            return public.returnMsg(True, '删除项目成功')
        else:
            return public.returnMsg(False, '项目类型错误')
    
    def modify_project(self, get):
        '''
            @name 修改指定项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name  : string<项目名称>
            }
            @return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return public.return_error('指定项目不存在2: {}'.format(get.project_name))
        
        # springboot项目能修改端口 运行用户  开机启动 JDK jar  启动命令 项目名称
        if project_find['project_config']['java_type'] == 'springboot':
            return self.modify_project_springboot(get, project_find = project_find)
        if project_find['project_config']['java_type'] == 'duli':
            return self.modify_project_duli(get, project_find = project_find)
        if project_find['project_config']['java_type'] == 'neizhi':
            return self.modify_project_neizhi(get, project_find = project_find)
        return public.returnMsg(False, '项目类型错误')
    
    def modify_project_springboot(self, get, project_find):
        '''
        @修改springboot 项目配置
        @param get.port  修改的端口号
        @param get.run_user 运行目录
        @param get.auth 开机自启动
        @param get.project_jdk 项目JDK
        @param get.project_jar 项目jar
        @param get.project_ps 项目描述
        @param get.project_move_name 项目名称
        '''
        if hasattr(get, 'project_move_name'):
            if get.project_move_name.strip() != get.project_name.strip():
                project_name = get.project_move_name.strip()
            else:
                project_name = get.project_name.strip()
        else:
            project_name = get.project_name.strip()
        project_find['project_config']['project_name'] = project_name
        if hasattr(get, 'port'):
            if hasattr(get, 'port'):
                try:
                    int(get.port)
                except:
                    return public.returnMsg(False, "端口参数错误")
            if int(project_find['project_config']['port']) != int(get.port):
                if self.check_port_is_used(get.get('port/port'), True):
                    return public.returnMsg(
                        False, '指定端口已被其它应用占用，请修改您的项目配置使用其它端口, 端口: {}'.format(
                            get.port
                            )
                        )
                project_find['project_config']['port'] = int(get.port)
        if hasattr(get, 'auth'): project_find['project_config']['auth'] = get.auth
        if hasattr(get, 'run_user'): project_find['project_config']['run_user'] = get.run_user
        if hasattr(get, 'project_jdk'): project_find['project_config']['project_jdk'] = get.project_jdk.strip()
        if hasattr(get, 'project_jar'): project_find['project_config']['project_jar'] = get.project_jar.strip()
        if hasattr(get, 'project_cmd'):
            project_find['project_config']['project_cmd'] = get.project_cmd.strip()
        else:
            return public.returnMsg(False, '缺少project_cmd参数')
        # 检查jar包是否在cmd中
        if project_find['project_config']['project_cmd'].find(get.project_jar.strip()) == -1:
            return public.returnMsg(False, '项目jar包名称不在项目启动命令中，请检查')
        if hasattr(get, 'project_jar'):
            project_path = os.path.dirname(get.project_jar.strip())
            project_find['project_config']['jar_path'] = project_path
        if hasattr(get, 'jmx_status') and hasattr(get, "jmx_port"):
            jmx_url = "service:jmx:rmi:///jndi/rmi://127.0.0.1:{}/jmxrmi".format(get.jmx_port)
            project_find['project_config']['jmx_status'] = get.jmx_status
            project_find['project_config']['jmx_info'] = {
                "jmx_url": jmx_url,
                "username": "",
                "password": "",
            }
        pdata = {
            'name': project_name,
            'path': get.project_jar.strip(),
            'ps': get.project_ps.strip(),
            'project_config': json.dumps(project_find['project_config'])
        }
        public.M('sites').where('name=?', (get.project_name,)).update(pdata)
        self.set_config(get.project_name)
        # 重启项目
        # return self.restart_project(get)
        res = self.stop_project(get)
        res = self.start_project(get)
        if "use_project_watch" in get and get.use_project_watch in ("1", "true", "yes", 1):
            add_project_watch(
                p_name = get.project_name.strip(),
                p_type = "java",
                site_id = project_find["id"],
                watch_path = get.project_jar.strip()
                )
        else:
            del_project_watch(get.project_name.strip())
        public.WriteLog(self._log_name, '修改Java项目{}'.format(get.project_name))
        return public.returnMsg(True, '修改项目成功')
    
    def modify_project_duli(self, get, project_find):
        '''
        @修改独立项目配置
        @param get.project_name 项目名称
        @param get.project_path 项目路径
        @param get.port  修改的端口号
        @param get.project_ps 项目描述
        @param get.tomcat_start  tomcat启动脚本路径
        @param get.jdk_path  更换JDK的路径
        '''
        
        falg = False
        if hasattr(get, 'port'):
            if int(project_find['project_config']['port']) != int(get.port):
                if self.check_port_is_used(get.get('port/port'), True):
                    return public.returnMsg(
                        False, '指定端口已被其它应用占用，请修改您的项目配置使用其它端口, 端口: {}'.format(
                            get.port
                            )
                        )
                project_find['project_config']['port'] = int(get.port)
                # 独立项目修改端口
                ret = self.set_tomcat_duli_port(get, get_project_find = project_find)
                falg = True
                if not ret['status']: return ret
        
        # 更换项目路径
        if hasattr(get, 'project_path'):
            if (get.project_path.strip() == project_find['path']):
                pass
            else:
                ret = self.set_tomcat_duli_path(get, get_project_find = project_find)
                falg = True
                if not ret['status']: return ret
        
        # 更换JDK
        if hasattr(get, 'jdk_path'):
            ret = self.change_duli_tomcat_jdk(get.project_name, get.jdk_path)
            if not ret['status']:
                return ret
            # ret = self.pendent_tomcat_info(domain=get.project_name)
            # if ret['jdk_path']:
            #     if ret['jdk_path'] != get.jdk_path.strip():
            #         # 验证当前JDK是否可用
            #         if not os.path.exists(ret['jdk_path']):
            #             return public.returnMsg(False, '当前JDK不可用')
            #         # 验证JDK是否存在
            #         ret2 = self.replace_jdk_version(get)
            #         falg = True
            #         if not ret2['status']:
            #             # 恢复到之前的JDK
            #             get.jdk_path = ret['jdk_path']
            #             self.replace_jdk_version(get)
            #             return ret2
        
        # 开机自启动
        if hasattr(get, 'auth'):
            if str(get.auth) != str(project_find['project_config']['auth']):
                project_find['project_config']['auth'] = get.auth
                falg = True
                pdata = {
                    'project_config': json.dumps(project_find['project_config'])
                }
                public.M('sites').where('name=?', (get.project_name,)).update(pdata)
        
        # 更换描述
        if hasattr(get, 'project_ps'):
            if get.project_ps.strip() != project_find['ps']:
                falg = True
                pdata = {'ps': get.project_ps.strip()}
                public.M('sites').where('name=?', (get.project_name,)).update(pdata)
        
        if falg:
            self.set_config(get.project_name)
            # self.restart_project(get)
            self.stop_project(get)
            self.start_project(get)
        return public.returnMsg(True, '修改完成')
    
    def modify_project_neizhi(self, get, project_find):
        '''
        @name 修改内置项目配置
        @param get.project_name 项目名称
        @param get.port  修改的端口号
        @param get.project_ps 项目描述
        @param get.tomcat_start  tomcat启动脚本路径
        @param get.jdk_path  更换JDK的路径
        '''
        flag = False
        if hasattr(get, 'port'):
            if int(project_find['project_config']['port']) != int(get.port):
                if self.check_port_is_used(get.get('port/port'), True):
                    return public.returnMsg(
                        False, '指定端口已被其它应用占用，请修改您的项目配置使用其它端口, 端口: {}'.format(
                            get.port
                            )
                        )
                project_find['project_config']['port'] = int(get.port)
                # 独立项目修改端口
                flag = True
                ret = self.set_tomcat_duli_port(get, get_project_find = project_find)
                if not ret['status']: return ret
        # 更换JDK
        if hasattr(get, 'jdk_path'):
            ret = self.pendent_tomcat_info(domain = get.project_name)
            if ret['jdk_path']:
                if ret['jdk_path'] != get.jdk_path.strip():
                    # 验证当前JDK是否可用
                    flag = True
                    if not os.path.exists(ret['jdk_path']):
                        return public.returnMsg(False, '当前JDK不可用')
                    # 验证JDK是否存在
                    ret2 = self.replace_jdk_version(get)
                    if not ret2['status']:
                        # 恢复到之前的JDK
                        get.jdk_path = ret['jdk_path']
                        self.replace_jdk_version(get)
                        return ret2
        
        # 更换项目路径
        if hasattr(get, 'project_path'):
            if (get.project_path.strip() == project_find['path']):
                pass
            else:
                ret = self.set_tomcat_duli_path(get, get_project_find = project_find)
                flag = True
                if not ret['status']: return ret
        
        # 更换描述
        if hasattr(get, 'project_ps'):
            if get.project_ps.strip() != project_find['ps']:
                flag = True
                pdata = {'ps': get.project_ps.strip()}
                public.M('sites').where('name=?', (get.project_name,)).update(pdata)
        if flag:
            self.set_config(get.project_name)
            self.restart_project(get)
        return public.returnMsg(True, "修改成功")
    
    def auto_run(self):
        '''
            @name 自动启动所有项目
            @author hwliang<2021-08-09>
            @return bool
        '''
        project_list = public.M('sites').where('project_type=?', ('Java',)).field('name,path,project_config').select()
        get = public.dict_obj()
        success_count = 0
        error_count = 0
        for project_find in project_list:
            project_config = json.loads(project_find['project_config'])
            if project_config['auth'] in [0, False, '0', None]: continue
            project_name = project_find['name']
            
            if project_config['java_type'] == 'springboot':
                project_state = self.get_project_run_state(project_name = project_name)
            elif project_config['java_type'] == 'duli':
                project_state = self.get_duli_run_state(project_name = project_name)
            else:
                get.project_name = project_name
                project_state = self.get_duli_run_state(
                    project_name = project_name,
                    bt_tomcat_web = '/usr/local/bttomcat/tomcat{}'.format(
                        project_config['tomcat_version']
                    ), neizhi = True
                    )
            if not project_state:
                get.project_name = project_name
                result = self.start_project(get)
                if not result['status']:
                    error_count += 1
                    error_msg = '自动启动Java项目[' + project_name + ']失败!'
                    public.WriteLog(self._log_name, error_msg)
                else:
                    success_count += 1
                    success_msg = '自动启动Java项目[' + project_name + ']成功!'
                    public.WriteLog(self._log_name, success_msg)
        if (success_count + error_count) < 1: return False
        dene_msg = '共需要启动{}个Java项目，成功{}个，失败{}个'.format(
            success_count + error_count, success_count, error_count
            )
        public.WriteLog(self._log_name, dene_msg)
        return True
    
    def get_jmap_path(self, project_find):
        '''
        @name 获取jmap jhat jstack绝对路径
        @author lkq<2021-09-24>
        @return list
        '''
        # 获取当前的jdk路径
        ret = {}
        cmd = project_find['project_config']['project_cmd']
        if not cmd:
            return False
        # 获取java的绝对路径
        cmd = cmd.split()
        path = None
        for i in cmd:
            if 'bin/java' in i:
                path = i
                break
        if not path:
            jdk_list = self.get_local_jdk_version(None)
            if jdk_list:
                path = '/'.join(jdk_list[0][1].split('/')[:-1])
                jmap_path = path + '/jmap'
                if os.path.exists(jmap_path):
                    ret['jmap'] = jmap_path
                if os.path.exists(path + '/jhat'):
                    ret['jhat'] = path + '/jhat'
                if os.path.exists(path + '/jstack'):
                    ret['jstack'] = path + '/jstack'
            return ret
        else:
            path = '/'.join(path.split('/')[:-1])
            jmap_path = path + '/jmap'
            if os.path.exists(jmap_path):
                ret['jmap'] = jmap_path
            if os.path.exists(path + '/jhat'):
                ret['jhat'] = path + '/jhat'
            if os.path.exists(path + '/jstack'):
                ret['jstack'] = path + '/jstack'
            return ret
    
    def get_project_dump(self, get):
        '''
        @name 获取heapdump 文件列表
        @author lkq<2021-09-24>
        @return list
        '''
        ret = []
        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return ret
        if not project_find['project_config']['java_type'] == 'springboot': return ret
        if not os.path.exists(self._springoot_dump + '/' + get.project_name + '.json'): return ret
        try:
            ret = json.loads(public.ReadFile(self._springoot_dump + '/' + get.project_name + '.json'))
            return ret
        except:
            public.WriteFile(public.ReadFile(self._springoot_dump + '/' + get.project_name + '.json'), [])
            return ret
    
    def del_project_dump(self, get):
        '''
        @name 获取heapdump 文件列表
        @author lkq<2021-09-24>
        @param get.project_name 项目名称
        @param get.dump_name 文件名称
        '''
        ret = []
        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return public.returnMsg(False, '项目不存在')
        if not project_find['project_config']['java_type'] == 'springboot': return public.returnMsg(
            False, '只支持SpringBoot项目'
            )
        if not os.path.exists(self._springoot_dump + '/' + get.project_name + '.json'): return public.returnMsg(
            False, '路径不存在于当前项目中'
            )
        if not os.path.exists(get.dump_name.strip()): return public.returnMsg(False, '文件不存在')
        try:
            ret = json.loads(public.ReadFile(self._springoot_dump + '/' + get.project_name + '.json'))
            if get.dump_name.strip() in ret:
                ret.remove(get.dump_name.strip())
                public.ExecShell("rm -rf %s" % get.dump_name.strip())
            return public.returnMsg(True, '删除成功')
        except:
            public.WriteFile(public.ReadFile(self._springoot_dump + '/' + get.project_name + '.json'), [])
            return public.returnMsg(True, '删除成功')
    
    def heapdump_project(self, get):
        '''
        @name 生成headdump 文件
        @author lkq<2021-09-24>
        @param  type Finfo 代表强制获取每个类占用  info获取每个类占用   dump生成dump文件 Fdump 强制生成dump文件 heap 显示Java堆详细信息 Fheap 强制显示Java堆详细信息
        @return list
        '''
        if not hasattr(get, 'type'):
            get.type = 'info'
            type = get.type
        else:
            type = get.type
        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return public.returnMsg(False, '指定项目不存在2: {}'.format(get.project_name))
        if not project_find['project_config']['java_type'] == 'springboot': return public.returnMsg(
            False, '只支持Springboot项目'
            )
        # 获取jmap jhat jstack绝对路径
        path = self.get_jmap_path(project_find)
        # 获取运行状态
        if not self.get_project_run_state(project_name = get.project_name):
            return public.returnMsg(False, '指定项目未启动: {}'.format(get.project_name))
        # 获取pid
        pidlist = self.get_project_load_info(project_name = get.project_name)
        if not pidlist:
            return public.returnMsg(False, '指定项目未启动: {}'.format(get.project_name))
        pid = 0
        for i in pidlist:
            pid = i
            break
        if pid == 0:
            return public.returnMsg(False, '指定项目未启动: {}'.format(get.project_name))
        if 'jmap' in path:
            jmap_path = path['jmap']
            if type == 'Finfo':
                # 强制显示堆中对象的统计信息
                cmd = '{} -F -histo {} | head -n 100'.format(jmap_path, pid)
            elif type == 'info':
                # 显示堆中对象的统计信息
                cmd = '{} -histo:live {} | head -n 100'.format(jmap_path, pid)
            elif type == 'dump':
                path = self._springoot_dump + '/' + str(int(time.time())) + '.dump'
                # 生成堆转储快照
                cmd = '{} -dump:live,format=b,file={} {}'.format(jmap_path, path, pid)
                ret = public.ExecShell(cmd, user = project_find['project_config']['run_user'])
                if os.path.exists(path):
                    if os.path.exists(self._springoot_dump + '/' + get.project_name + '.json'):
                        try:
                            ret = json.loads(public.ReadFile(self._springoot_dump + '/' + get.project_name + '.json'))
                            if path not in ret:
                                ret.append(path)
                                public.WriteFile(
                                    self._springoot_dump + '/' + get.project_name + '.json', json.dumps(ret)
                                    )
                        except:
                            public.WriteFile(
                                self._springoot_dump + '/' + get.project_name + '.json', json.dumps([path])
                                )
                    else:
                        public.WriteFile(self._springoot_dump + '/' + get.project_name + '.json', json.dumps([path]))
                    return public.returnMsg(True, '生成dump文件成功内容如下:%s' % ret[0])
                else:
                    return public.returnMsg(False, '生成dump文件失败内容如下:%s' % ret[0])
            elif type == 'Fdump':
                # 强制生成堆转储快照
                cmd = '{} -F -dump:live,format=b,file={} {}'.format(
                    jmap_path, self._springoot_dump + '/' + time.strftime(
                        '%Y-%m-%d %X', time.localtime()
                        ) + '.dump', pid
                    )
                ret = public.ExecShell(cmd, user = project_find['project_config']['run_user'])
                return public.returnMsg(True, ret)
            elif type == 'heap':
                # 显示Java堆详细信息
                cmd = '{}  -heap {} '.format(jmap_path, pid)
            elif type == 'Fheap':
                # 强制显示Java堆详细信息
                cmd = '{} -F -heap {}'.format(jmap_path, pid)
            else:
                return public.returnMsg(False, '指定的类型不存在: {}'.format(type))
            ret = public.ExecShell(cmd, user = project_find['project_config']['run_user'])
            return public.returnMsg(True, ret)
        return public.returnMsg(False, '当前JDK不存在jmap')
    
    def jhat_project(self, get):
        '''
        @name jhat 分析dump文件
        @param  dump  dump文件
        @return string
        @ps :此功能消耗很大的内存和CPU。請注意使用
        '''
        pass
        dump_path = get.dump
        if not os.path.exists(dump_path):
            return public.returnMsg(False, 'dump文件不存在: {}'.format(dump_path))
        cmd = 'jhat {}'.format(dump_path)
        return cmd
    
    def jstack_project(self, get):
        '''
        @name jstack 生成虚拟线程快照
        @param pid 进程id
        @return string
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return public.returnMsg(False, '指定项目不存在2: {}'.format(get.project_name))
        # 获取jmap jhat jstack绝对路径
        if not project_find['project_config']['java_type'] == 'springboot': return public.returnMsg(
            False, '只支持Springboot项目'
            )
        path = self.get_jmap_path(project_find)
        # 获取运行状态
        if not self.get_project_run_state(project_name = get.project_name):
            return public.returnMsg(False, '指定项目未启动: {}'.format(get.project_name))
        # 获取pid
        pidlist = self.get_project_load_info(project_name = get.project_name)
        if not pidlist:
            return public.returnMsg(False, '指定项目未启动: {}'.format(get.project_name))
        pid = 0
        for i in pidlist:
            pid = i
            break
        if pid == 0:
            return public.returnMsg(False, '指定项目未启动: {}'.format(get.project_name))
        if 'jstack' in path:
            jstack_path = path['jstack']
            cmd = '{} -l {}'.format(jstack_path, pid)
            # ret=public.ExecShell(cmd,user=project_find['project_config']['run_user'])
            ret = public.ExecShell(cmd, user = project_find['project_config']['run_user'])
            return public.returnMsg(True, ret)
        return public.returnMsg(False, '当前JDK不存在jstack')
    
    # ————————————
    #  批量操作  |
    # ————————————
    
    def multi_remove_project(self, get):
        '''
            @name 批量删除项目
            @author baozi<2023-3-2>
            @param get<dict_obj>{
                project_names: list[string] <项目名称>所组成的列表
            }
            @return dict
        '''
        project_names = get.project_names
        if isinstance(project_names, list):
            pjnames = [i.strip() for i in project_names]
        else:
            pjnames = []
        
        projects = public.M('sites').where(
            f'project_type=? AND name in ({",".join(["?"] * len(pjnames))})',
            ('Java', *pjnames)
            ).select()
        if not projects:
            return public.returnMsg(False, "未选中要删除的站点")
        
        _duli, _neizh, _springboot, _error_type = [], [], [], []
        for project in projects:
            project['project_config'] = json.loads(project['project_config'])
            if project['project_config']['java_type'] == 'duli':
                _duli.append(project)
            elif project['project_config']['java_type'] == 'neizhi':
                _neizh.append(project)
            elif project['project_config']['java_type'] == 'springboot':
                _springboot.append(project)
            else:
                _error_type.append("项目:[{}], 项目类型错误\n".format(project["name"]))
        if _error_type:
            return public.return_error(data = _error_type)
        
        # 执行每种删除的独特操作
        if _duli:
            self._multi_remove_duli(_duli)
        if _neizh:
            self._multi_remove_neizhi(_neizh)
        if _springboot:
            self._multi_remove_springboot(_springboot)
        
        # 清除Nginx， Apache 配置文件，并重起服务
        self._multi_clear_config(projects)
        # 从面板数据库删除信息
        project_ids = tuple([i["id"] for i in projects])
        public.M('domain').where('pid IN ({})'.format(",".join(["?"] * len(projects))), project_ids).delete()
        public.M('sites').where(
            f'project_type=? AND name in ({",".join(["?"] * len(pjnames))})',
            ('Java', *pjnames)
            ).delete()
        public.WriteLog(self._log_name, f'批量删除Java项目:[{"; ".join([i["name"] for i in projects])}]')
        # 获取域名列表 并删除host
        for project in projects:
            self.del_crontab(project["name"])
            for i in project['project_config']['domains']:
                self.del_hosts(i)
        
        return {"status": True, "msg": "删除成功", "project_names": pjnames}
    
    def _multi_clear_config(self, projects):
        for project in projects:
            self.clear_nginx_config(project)
            self.clear_apache_config(project)
        public.serviceReload()
    
    def _multi_remove_duli(self, projects):
        get = public.dict_obj()
        for project in projects:
            # 关闭独立项目
            get.domain = project['name']
            get.type = 'stop'
            self.pendent_tomcat_start(get)
            # 删除项目
            shutil.rmtree(self.__site_path, project['name'])
    
    def _multi_remove_tomcat_vhost(self, projects):
        if not self.__ENGINE: return
        domains = [project["name"] for project in projects if project["name"] != 'localhost']
        try:
            Hosts = self.__ENGINE.getchildren()
        except:
            Hosts = list(self.__ENGINE)
        for host in Hosts:
            if host.tag != 'Host': continue
            if host.attrib['name'] in domains:
                self.__ENGINE.remove(host)
        self.save_tomcat()
    
    def _multi_remove_neizhi(self, projects):
        version_group = {}
        res_msg = []
        # 按版本分组
        for project in projects:
            if project['project_config']['tomcat_version'] in version_group:
                version_group[project['project_config']['tomcat_version']].append(project)
            else:
                version_group[project['project_config']['tomcat_version']] = [project, ]
        # 处理Tomcat配置文件
        for version, group_projects in version_group.items():
            if not self.Initialization(version):
                res_msg.append(
                    "项目[{}]".format(",".join([i["name"] for i in group_projects])) + ":配置文件错误请检查配置文件"
                )
                continue
            self._multi_remove_tomcat_vhost(group_projects)
            get = public.dict_obj()
            get.version = version
            get.type = 'reload'
            self.start_tomcat(get)
    
    def _multi_remove_springboot(self, projects):
        get = public.dict_obj()
        for project in projects:
            # 停止项目
            get.project_name = project["name"]
            self.stop_project(get)
            # 删除项目
            pid_file = project['project_config']['pids']
            if os.path.exists(pid_file): os.remove(pid_file)
            script_file = project['project_config']['scripts']
            if os.path.exists(script_file): os.remove(script_file)
            log_file = project['project_config']['logs']
            if os.path.exists(log_file): os.remove(log_file)
    
    def multi_set_project(self, get):
        '''
            @name 批量设置项目
            @author baozi<2023-3-2>
            @param get<dict_obj>{
                project_names: list[string] <项目名称>所组成的列表
            }
            @return dict
        '''
        project_names = get.project_names
        set_type = get.operation
        if set_type not in ["start", "stop"]:
            return public.returnMsg(False, "操作信息错误")
        if isinstance(project_names, list):
            pjnames = [i.strip() for i in project_names]
        else:
            pjnames = []
        
        projects = public.M('sites').where(
            f'project_type=? AND name in ({",".join(["?"] * len(pjnames))})',
            ('Java', *pjnames)
            ).select()
        if not projects:
            return public.returnMsg(False, "未选中要启动的站点")
        
        neizhi_projects = {'7': False, '8': False, '9': False}
        _check = self.get_tomcat_version(None)
        if not _check["tomcat7"]["status"]: neizhi_projects.pop("7")
        if not _check["tomcat8"]["status"]: neizhi_projects.pop("8")
        if not _check["tomcat9"]["status"]: neizhi_projects.pop("9")
        springboot_projects = []
        duli_projects = []
        error_list = []
        for project in projects:
            project['project_config'] = json.loads(project['project_config'])
            if project['project_config']['java_type'] == 'neizhi':
                if project['project_config']['tomcat_version'] in neizhi_projects:
                    neizhi_projects[project['project_config']['tomcat_version']] = True
                else:
                    error_list.append(
                        {
                            "project_name": project["name"], "msg": "启动失败,没有安装Tomcat{}".format(
                            project['project_config']['tomcat_version']
                        )
                        }
                        )
                    pjnames.remove(project["name"])
            
            if project['project_config']['java_type'] == 'duli':
                duli_projects.append(project)
            
            if project['project_config']['java_type'] == 'springboot':
                springboot_projects.append(project)
        
        for tomcat_version, flag in neizhi_projects.items():
            if flag:
                _get = public.dict_obj()
                _get.type = set_type
                _get.version = tomcat_version
                self.start_tomcat(_get)
        
        for i in springboot_projects:
            if set_type == "start":
                flag, msg = self.__start_springboot_project(i)
                if not flag:
                    error_list.append({"project_name": i["name"], "msg": msg})
                    pjnames.remove(i["name"])
            else:
                self.__stop_springboot_project(i)
        
        for i in duli_projects:
            _get = public.dict_obj()
            _get.domain = i['name']
            _get.type = set_type
            self.pendent_tomcat_start(_get)
        
        if error_list:
            return {"status": True, "msg": "部分项目启动失败", "error_list": error_list, "project_names": pjnames}
        return {"status": True, "msg": "启动成功" if set_type == "start" else "停止成功", "project_names": pjnames}
    
    # springboot 停止
    def __stop_springboot_project(self, project_info):
        pid_file = project_info['project_config']['pids']
        if not os.path.exists(pid_file): return public.returnMsg(False, '项目未启动')
        try:
            pid = int(public.readFile(pid_file))
        except:
            return False, '项目未启动'
        pids = self.get_project_pids(pid = pid)
        if not pids: return False, '项目未启动'
        self.kill_pids(pids = pids)
        if os.path.exists(pid_file): os.remove(pid_file)
        self.stop_by_user(project_info["id"])
        return True, '停止成功'
    
    # springboot 启动
    def __start_springboot_project(self, project_find):
        project_cmd = project_find["project_config"]['project_cmd']
        # 前置准备
        log_file = project_find["project_config"]['logs']
        pid_file = project_find["project_config"]['pids']
        nohup_log = ' &>> {log_file}'.format(log_file = log_file)
        if not int(project_find["project_config"].get('nohup_log', 1)):
            nohup_log = ''
        if 'jar_path' in project_find['project_config']:
            jar_path = project_find['project_config']['jar_path']
        else:
            jar_path = '{}'.format(self._springboot)
        # 启动脚本
        start_cmd = '''#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
cd {jar_path}
nohup {project_cmd}{nohup_log} &
echo $! > {pid_file}
'''.format(
            jar_path = jar_path,
            project_cmd = project_cmd,
            pid_file = pid_file,
            log_file = log_file,
            nohup_log = nohup_log,
        )
        script_file = project_find["project_config"]['scripts']
        # 写入启动脚本
        public.writeFile(script_file, start_cmd)
        if os.path.exists(pid_file): os.remove(pid_file)
        public.ExecShell("chmod -R 777 /var/tmp/springboot/")
        # public.ExecShell("chown -R {}:{} {}".format(project_find['project_config']['run_user'],project_find['project_config']['run_user'],self._springboot))
        public.set_mode(script_file, 755)
        public.ExecShell(
            "chown  {}:{} {}".format(
                project_find['project_config']['run_user'], project_find['project_config']['run_user'],
                project_find['path']
                )
            )
        # 判断是否在/www/  /www/wwwroot
        
        # 执行脚本文件
        p = public.ExecShell(
            "bash {}".format(script_file), user = project_find['project_config']['run_user'], env = os.environ.copy()
            )
        time.sleep(1)
        if not os.path.exists(pid_file):
            return False, '启动失败,请尝试切换启动用户'
        
        # 获取PID
        try:
            pid = int(public.readFile(pid_file))
        except:
            return False, '启动失败'
        time.sleep(0.4)
        pids = self.get_project_pids(pid = pid)
        # if not pids:
        #    if os.path.exists(pid_file): os.remove(pid_file)
        #    return public.returnMsg(False,'启动失败<br>{}'.format(public.GetNumLines(log_file,20)))
        self.start_by_user(project_find["id"])
        return True, None
    
    def multi_check_bind_extranet(self, get):
        """检查是否可以绑定外网，并执行绑定操作
        @author baozi <202-03-2>
        @param:
            get  ( dict ):   project_names 要操作的网站列表
        @return
        """
        if not public.is_apache_nginx(): return public.returnMsg(False, '请先安装Apache或者Nginx!')
        project_names = get.project_names
        if isinstance(project_names, list):
            pjnames = [i.strip() for i in project_names]
        else:
            pjnames = []
        
        projects = public.M('sites').where(
            f'project_type=? AND name in ({",".join(["?"] * len(pjnames))})', ('Java', *pjnames)
            ).select()
        if not projects:
            return public.returnMsg(False, "未选中要启动的站点")
        
        error_list = []
        flag = False
        for project in projects:
            project['project_config'] = json.loads(project['project_config'])
            if not project['project_config']['domains']:
                error_list.append({'project_name': project["name"], "msg": '请先到【域名管理】选项中至少添加一个域名'})
                pjnames.remove(project["name"])
                continue
            if "bind_extranet" in project['project_config'] and project['project_config']['bind_extranet'] == 1:
                continue
            else:
                flag = True
            project['project_config']['bind_extranet'] = 1
            public.M('sites').where("id=?", (project['id'],)).setField(
                'project_config', json.dumps(project['project_config'])
                )
            self.set_nginx_config(project)
            self.set_apache_config(project)
            public.WriteLog(self._log_name, 'Java项目{}, 开启外网映射'.format(project))
        
        if flag:
            public.serviceReload()
        
        if error_list:
            return {
                "status": True, "msg": "部分网站开启外网映射失败", "error_list": error_list, "project_names": pjnames
            }
        
        return {"status": True, "msg": "开启外网映射成功", "project_names": pjnames}
    
    def _change_daemom_sh(self, target_sh, logpath, suffix=''):
        if not os.path.exists(target_sh): return False
        file = public.readFile(target_sh)
        rep = r'''\n ?test ?"\.\$CATALINA_OUT" ?= ?\. && {0,3}CATALINA_OUT="[^\n]*"[^\n]*\n'''
        repl = f'\ntest ".$CATALINA_OUT" = . && CATALINA_OUT="{logpath}/catalina-daemon{"-" + suffix if suffix else ""}.out"\n'
        file = re.sub(rep, repl, file)
        public.writeFile(target_sh, file)
        return True
    
    def change_log_path(self, get):
        """"修改日志文件地址
        @author baozi <202-03-13>
        @param:
            get  ( dict ):  请求: 包含项目名称和新的路径
        @return
        """
        project_info = self.get_project_find(get.project_name.strip())
        if not project_info: return public.returnMsg(False, '项目不存在')
        new_log_path = get.path.strip() if "path" in get else None
        if not new_log_path or new_log_path[0] != "/":
            return public.returnMsg(False, "路径设置错误")
        if new_log_path[-1] == "/": new_log_path = new_log_path[:-1]
        if not os.path.exists(new_log_path):
            os.makedirs(new_log_path, mode = 0o777)
        if project_info['project_config']['java_type'] == 'springboot':
            project_info['project_config']['logs'] = new_log_path + '/' + project_info["name"] + '.log'
            pdata = {
                'name': project_info["name"],
                'project_config': json.dumps(project_info['project_config'])
            }
            public.M('sites').where('name=?', (get.project_name.strip(),)).update(pdata)
            # 重启项目
            # return self.restart_project(get)
            res = self.stop_project(get)
            res = self.start_project(get)
            public.WriteLog(self._log_name, '修改Java项目{}'.format(get.project_name))
            return public.returnMsg(True, "项目日志路径修改成功")
        if project_info['project_config']['java_type'] == 'duli':
            project_info['project_config']['logs'] = new_log_path + '/'
            if not self._change_daemom_sh(
                    self.__site_path + project_info["name"] + "/bin/daemon.sh", new_log_path,
                    project_info["name"].replace(".", "_")
                    ):
                return public.returnMsg(False, "项目日志路径修改失败")
            pdata = {
                'name': project_info["name"],
                'project_config': json.dumps(project_info['project_config'])
            }
            public.M('sites').where('name=?', (get.project_name.strip(),)).update(pdata)
            # 重启项目
            # return self.restart_project(get)
            res = self.stop_project(get)
            res = self.start_project(get)
            public.WriteLog(self._log_name, '修改Java项目{}'.format(get.project_name))
            return public.returnMsg(True, "项目日志路径修改成功")
        
        if project_info['project_config']['java_type'] == 'neizhi':
            version = project_info['project_config']['tomcat_version']
            if not self._change_daemom_sh(
                    "/usr/local/bttomcat/tomcat%s/bin/daemon.sh" % version, new_log_path, str(version)
                    ):
                return public.returnMsg(False, "项目日志路径修改失败")
            public.writeFile("/usr/local/bttomcat/tomcat%s/conf/logpath.conf" % version, new_log_path)
            res = self.stop_project(get)
            res = self.start_project(get)
            public.WriteLog(self._log_name, '修改Java-Tomcat{}内置项目路径修改成功'.format(version))
            return public.returnMsg(True, "项目日志路径修改成功")
    
    def for_split(self, logsplit, project):
        """日志切割方法调用
        @author baozi <202-03-20>
        @param:
            logsplit  ( LogSplit ):  日志切割方法，传入 pjanme:项目名称 sfile:日志文件路径 log_prefix:产生的日志文件前缀
            project  ( dict ):  项目内容
        @return
        """
        try:
            from mod.project.java.utils import site_tomcat, bt_tomcat
        except:
            site_tomcat = bt_tomcat = None
        log_file = None
        if project['project_config']['java_type'] == 'springboot':
            log_file = project['project_config']['logs']
            logsplit(project["name"], log_file, project["name"])
            return
        elif project['project_config']['java_type'] == 'duli':
            if site_tomcat:
                tomcat_name = project["project_config"].get("tomcat_name", "")
                tomcat = site_tomcat(tomcat_name) if tomcat_name else site_tomcat(project["project_config"]["project_name"])
                if tomcat:
                    log_file = tomcat.log_file
            if log_file is None:
                _log_file = project['project_config']['logs']
                log_file = '{}catalina-daemon-{}.out'.format(_log_file, project["name"].replace(".", "_"))
        if project['project_config']['java_type'] == 'neizhi':
            version = str(project['project_config']['tomcat_version']).split(".")[0]
            if bt_tomcat:
                tomcat = bt_tomcat(version)
                if tomcat:
                    log_file = tomcat.log_file
            if log_file is None:
                try:
                    log_file = public.readFile(
                        "/usr/local/bttomcat/tomcat%s/conf/logpath.conf" % version
                        ) + f'/catalina-daemon-{version}.out'
                except:
                    log_file = '/www/wwwlogs/java/neizhi%s/catalina-daemon.out' % version
            
        logsplit(project["name"], log_file, project["name"])
    
    # —————————————
    #  日志切割   |
    # —————————————
    def del_crontab(self, name):
        """
        @name 删除项目日志切割任务
        @auther hezhihong<2022-10-31>
        @return
        """
        cron_name = f'[勿删]Java项目[{name}]运行日志切割'
        cron_path = public.GetConfigValue('setup_path') + '/cron/'
        cron_list = public.M('crontab').where("name=?", (cron_name,)).select()
        if cron_list:
            for i in cron_list:
                if not i: continue
                cron_echo = public.M('crontab').where("id=?", (i['id'],)).getField('echo')
                args = {"id": i['id']}
                import crontab
                crontab.crontab().DelCrontab(args)
                del_cron_file = cron_path + cron_echo
                public.ExecShell("crontab -u root -l| grep -v '{}'|crontab -u root -".format(del_cron_file))
    
    def add_crontab(self, name, log_conf, python_path):
        """
        @name 构造站点运行日志切割任务
        """
        cron_name = f'[勿删]Java项目[{name}]运行日志切割'
        if not public.M('crontab').where('name=?', (cron_name,)).count():
            cmd = '{pyenv} {script_path} {name}'.format(
                pyenv = python_path,
                script_path = self.__log_split_script_py,
                name = name
            )
            args = {
                "name": cron_name,
                "type": 'day' if log_conf["log_size"] == 0 else "minute-n",
                "where1": "" if log_conf["log_size"] == 0 else log_conf["minute"],
                "hour": log_conf["hour"],
                "minute": log_conf["minute"],
                "sName": name,
                "sType": 'toShell',
                "notice": '0',
                "notice_channel": '',
                "save": str(log_conf["num"]),
                "save_local": '1',
                "backupTo": '',
                "sBody": cmd,
                "urladdress": ''
            }
            import crontab
            res = crontab.crontab().AddCrontab(args)
            if res and "id" in res.keys():
                return True, "新建任务成功"
            return False, res["msg"]
        return True
    
    def change_cronta(self, name, log_conf):
        """
        @name 更改站点运行日志切割任务
        """
        python_path = "/www/server/panel/pyenv/bin/python3"
        if not python_path: return False
        cronInfo = public.M('crontab').where('name=?', (f'[勿删]Java项目[{name}]运行日志切割',)).find()
        if not cronInfo:
            return self.add_crontab(name, log_conf, python_path)
        import crontab
        recrontabMode = crontab.crontab()
        id = cronInfo['id']
        del (cronInfo['id'])
        del (cronInfo['addtime'])
        cronInfo['sBody'] = '{pyenv} {script_path} {name}'.format(
            pyenv = python_path,
            script_path = self.__log_split_script_py,
            name = name
        )
        cronInfo['where_hour'] = log_conf['hour']
        cronInfo['where_minute'] = log_conf['minute']
        cronInfo['save'] = log_conf['num']
        cronInfo['type'] = 'day' if log_conf["log_size"] == 0 else "minute-n"
        cronInfo['where1'] = '' if log_conf["log_size"] == 0 else log_conf['minute']
        
        columns = 'where_hour,where_minute,sBody,save,type,where1'
        values = (
        cronInfo['where_hour'], cronInfo['where_minute'], cronInfo['sBody'], cronInfo['save'], cronInfo['type'],
        cronInfo['where1'])
        recrontabMode.remove_for_crond(cronInfo['echo'])
        if cronInfo['status'] == 0: return False, '当前任务处于停止状态,请开启任务后再修改!'
        sync_res = recrontabMode.sync_to_crond(cronInfo)
        if not sync_res['status']:
            return False, sync_res['msg']
        public.M('crontab').where('id=?', (id,)).save(columns, values)
        public.WriteLog('计划任务', '修改计划任务[' + cronInfo['name'] + ']成功')
        return True, '修改成功'
    
    def mamger_log_split(self, get):
        """管理日志切割任务
        @author baozi <202-02-27>
        @param:
            get  ( dict ):  包含name, mode, hour, minute
        @return
        """
        name = get.name.strip()
        project = self.get_project_find(name)
        if not project:
            return public.returnMsg(False, "没有该项目，请尝试刷新页面")
        try:
            _compress = False
            _log_size = float(get.log_size) if float(get.log_size) >= 0 else 0
            _hour = get.hour.strip() if 0 <= int(get.hour) < 24 else "2"
            _minute = get.minute.strip() if 0 <= int(get.minute) < 60 else '0'
            _num = int(get.num) if 0 < int(get.num) <= 1800 else 180
            if "compress" in get:
                _compress = int(get.compress) == 1
        except (ValueError, AttributeError, KeyError):
            _log_size = 0
            _hour = "2"
            _minute = "0"
            _num = 180
            _compress = False
        
        if _log_size != 0:
            _log_size = _log_size * 1024 * 1024
            _hour = 0
            _minute = 5
        
        log_conf = {
            "log_size": _log_size,
            "hour": _hour,
            "minute": _minute,
            "num": _num,
            "compress": _compress
        }
        flag, msg = self.change_cronta(name, log_conf)
        if flag:
            conf_path = '{}/data/run_log_split.conf'.format(public.get_panel_path())
            if os.path.exists(conf_path):
                try:
                    data = json.loads(public.readFile(conf_path))
                except:
                    data = {}
            else:
                data = {}
            data[name] = {
                "stype": "size" if bool(_log_size) else "day",
                "log_size": _log_size,
                "limit": _num,
                "compress": _compress
            }
            public.writeFile(conf_path, json.dumps(data))
            project["project_config"]["log_conf"] = log_conf
            pdata = {
                "project_config": json.dumps(project["project_config"])
            }
            public.M('sites').where('name=?', (name,)).update(pdata)
        return public.returnMsg(flag, msg)
    
    def set_log_split(self, get):
        """设置日志计划任务状态
        @author baozi <202-02-27>
        @param:
            get  ( dict ):  包含项目名称name
        @return  msg : 操作结果
        """
        name = get.name.strip()
        project_conf = self.get_project_find(name)
        if not project_conf:
            return public.returnMsg(False, "没有该项目，请尝试刷新页面")
        cronInfo = public.M('crontab').where('name=?', (f'[勿删]Java项目[{name}]运行日志切割',)).find()
        if not cronInfo:
            return public.returnMsg(False, "该项目没有设置运行日志的切割任务")
        
        status_msg = ['停用', '启用']
        status = 1
        import crontab
        recrontabMode = crontab.crontab()
        
        if cronInfo['status'] == status:
            status = 0
            recrontabMode.remove_for_crond(cronInfo['echo'])
        else:
            cronInfo['status'] = 1
            sync_res = recrontabMode.sync_to_crond(cronInfo)
            if not sync_res['status']:
                return public.returnMsg(False, sync_res['msg'])
        
        public.M('crontab').where('id=?', (cronInfo["id"],)).setField('status', status)
        public.WriteLog('计划任务', '修改计划任务[' + cronInfo['name'] + ']状态为[' + status_msg[status] + ']')
        return public.returnMsg(True, '设置成功')
    
    def get_log_split(self, get):
        """获取站点的日志切割任务
        @author baozi <202-02-27>
        @param:
            get  ( dict ):   name
        @return msg : 操作结果
        """
        
        name = get.name.strip()
        project_conf = self.get_project_find(name)
        if not project_conf:
            return public.returnMsg(False, "没有该项目，请尝试刷新页面")
        if self._check_old(project_conf):
            return {
                "status": False,
                "msg": "更新版本后需要重启项目，才能开启运行日志切割任务，建议您找一个合适的时间重启项目",
                "is_old": True
            }
        cronInfo = public.M('crontab').where('name=?', (f'[勿删]Java项目[{name}]运行日志切割',)).find()
        if not cronInfo:
            return public.returnMsg(False, "该项目没有设置运行日志的切割任务")
        
        if "log_conf" not in project_conf["project_config"]:
            return public.returnMsg(False, "日志切割配置丢失，请尝试重新设置")
        res = project_conf["project_config"]["log_conf"]
        res["status"] = cronInfo["status"]
        return {"status": True, "data": res}
    
    def _update_project(self, project_name, project_info):
        # 检查是否需要更新
        # 移动日志文件
        # 独立项目需要修改文件
        # 内置项目需要修改文件和备份文件
        # 保存
        if project_info['project_config']['java_type'] == 'springboot':
            target_file = "{}/{}.log".format(self._springboot_logs_path, str(project_name))
            log_file = project_info['project_config']['logs']
            if not log_file.startswith(self._springboot_logs):
                return
            if os.path.exists(log_file):
                self._move_logs(log_file, target_file)
                if not os.path.exists(target_file):
                    return
                else:
                    os.remove(log_file)
            
            project_info['project_config']["logs"] = target_file
            pdata = {
                'name': project_name,
                'project_config': json.dumps(project_info['project_config'])
            }
            public.M('sites').where('name=?', (project_name,)).update(pdata)
        
        if project_info['project_config']['java_type'] == 'duli':
            if "logs" in project_info['project_config']:
                return
            _path = '/www/wwwlogs/java/{}/'.format(project_name)
            if not os.path.exists(_path):
                os.makedirs(_path)
            target_file = '{}catalina-daemon-{}.out'.format(_path, project_info["name"].replace(".", "_"))
            s_file = '/www/server/bt_tomcat_web/{}/logs/catalina-daemon.out'.format(project_name)
            if os.path.exists(s_file):
                self._move_logs(s_file, target_file)
                if not os.path.exists(target_file):
                    return
                else:
                    os.remove(s_file)
            if not self._change_daemom_sh(
                    self.__site_path + project_info["name"] + "/bin/daemon.sh", _path[:-1],
                    project_info["name"].replace(".", "_")
                    ):
                return
            project_info['project_config']["logs"] = _path
            pdata = {
                'name': project_name,
                'project_config': json.dumps(project_info['project_config'])
            }
            public.M('sites').where('name=?', (project_name,)).update(pdata)
        
        if project_info['project_config']['java_type'] == 'neizhi':
            version = project_info['project_config']['tomcat_version']
            target_file = '/www/wwwlogs/java/neizhi{}/catalina-daemon-{}.out'.format(version, version)
            _path = '/www/wwwlogs/java/neizhi{}'.format(version)
            if not os.path.exists(_path):
                os.makedirs(_path)
            s_file = '/usr/local/bttomcat/tomcat%s/logs/catalina-daemon.out' % version
            res = public.ExecShell('sed -n "142p" /usr/local/bttomcat/tomcat{}/bin/daemon.sh'.format(version))[0]
            if not res.startswith(
                    'test ".$CATALINA_OUT" = . && CATALINA_OUT="$CATALINA_BASE/logs/catalina-daemon.out"'
            ):
                return
            if os.path.exists(s_file):
                self._move_logs(s_file, target_file)
                if not os.path.exists(target_file):
                    return
                else:
                    os.remove(s_file)
            if not self._change_daemom_sh("/usr/local/bttomcat/tomcat%s/bin/daemon.sh" % version, _path, str(version)):
                return
            
            public.writeFile("/usr/local/bttomcat/tomcat%s/conf/logpath.conf" % version, _path)
    
    def _move_logs(self, s_file, target_file):
        if os.path.getsize(s_file) > 3145928:
            res = self.last_lines(s_file, 3000)
            public.WriteFile(target_file, res)
        else:
            shutil.copyfile(s_file, target_file)
    
    def _check_old(self, project_info):
        if project_info['project_config']['java_type'] == 'springboot':
            log_file = project_info['project_config']['logs']
            if log_file.startswith(self._springboot_logs):
                return True
        
        if project_info['project_config']['java_type'] == 'duli':
            if not "logs" in project_info['project_config']:
                return True
        
        if project_info['project_config']['java_type'] == 'neizhi':
            version = project_info['project_config']['tomcat_version']
            _path = '/www/wwwlogs/java/neizhi{}'.format(version)
            if not os.path.exists(_path):
                os.makedirs(_path)
            res = public.ExecShell('sed -n "142p" /usr/local/bttomcat/tomcat{}/bin/daemon.sh'.format(version))[0]
            if res.startswith('test ".$CATALINA_OUT" = . && CATALINA_OUT="$CATALINA_BASE/logs/catalina-daemon.out"'):
                return True
    
    def _ckeck_add_domain(self, site_name, domains):
        from panelSite import panelSite
        ssl_data = panelSite().GetSSL(type("get", tuple(), {"siteName": site_name})())
        if not ssl_data["status"] or not ssl_data.get("cert_data", {}).get("dns", None):
            return {"domains": domains}
        domain_rep = []
        for i in ssl_data["cert_data"]["dns"]:
            if i.startswith("*"):
                _rep = "^[^\.]+\." + i[2:].replace(".", "\.")
            else:
                _rep = "^" + i.replace(".", "\.")
            domain_rep.append(_rep)
        no_ssl = []
        for domain in domains:
            if not domain["status"]: continue
            for _rep in domain_rep:
                if re.search(_rep, domain["name"]):
                    break
            else:
                no_ssl.append(domain["name"])
        if no_ssl:
            return {
                "domains": domains,
                "not_ssl": no_ssl,
                "tip": "本站点已启用SSL证书,但本次添加的域名：{}，无法匹配当前证书，如有需求，请重新申请证书。".format(
                    str(no_ssl)
                )
            }
        return {"domains": domains}
    
    # 获取 jmx 配置
    def get_jmx_config(self, get):
        if not hasattr(get, "site_id"):
            return public.returnMsg(False, "缺少参数! site_id")
        if not str(get.site_id).isdigit():
            return public.returnMsg(False, "参数错误! site_id")
        project_config = public.M('sites').where('project_type=? AND id=?', ('Java', get.site_id)).getField(
            "project_config"
        )
        if not project_config:
            return public.returnMsg(False, "网站信息不存在!")
        
        # 安装 jmxquery
        try:
            from jmxquery import JMXConnection, JMXQuery
        except:
            public.ExecShell("btpip install jmxquery==0.6.0")
        
        try:
            project_config = json.loads(project_config)
        except:
            project_config = {}
        
        jmx_info = project_config.get("jmx_info", {})
        if jmx_info.get("jmx_url") is None:
            jmx_info["jmx_url"] = ""
        if jmx_info.get("username") is None:
            jmx_info["username"] = ""
        if jmx_info.get("password") is None:
            jmx_info["password"] = ""
        return {"status": True, "msg": "ok", "data": jmx_info}
    
    # 设置 jmx 配置
    def set_jmx_config(self, get):
        if not hasattr(get, "site_id"):
            return public.returnMsg(False, "缺少参数! site_id")
        if not str(get.site_id).isdigit():
            return public.returnMsg(False, "参数错误! site_id")
        jmx_url = getattr(get, "jmx_url")
        username = getattr(get, "username", "")
        password = getattr(get, "password", "")
        
        project_config = public.M('sites').where('project_type=? AND id=?', ('Java', get.site_id)).getField(
            "project_config"
        )
        if not project_config:
            return public.returnMsg(False, "网站信息不存在!")
        
        # 安装 jmxquery
        try:
            from jmxquery import JMXConnection, JMXQuery
        except:
            public.ExecShell("btpip install jmxquery==0.6.0")
        from jmxquery import JMXConnection
        try:
            # 创建 JMXConnection
            JMXConnection(connection_uri = jmx_url, jmx_username = username, jmx_password = password)
        except Exception:
            return public.returnMsg(False, "连接失败！")
        
        try:
            project_config = json.loads(project_config)
        except:
            project_config = {}
        
        jmx_info = {}
        
        if jmx_url:
            jmx_info["jmx_url"] = jmx_url
        if username:
            jmx_info["username"] = username
        if password:
            jmx_info["password"] = password
        
        project_config["jmx_info"] = jmx_info
        public.M('sites').where('project_type=? AND id=?', ('Java', get.site_id,)).update(
            {"project_config": json.dumps(project_config)}
        )
        return public.returnMsg(True, "设置成功!")
    
    # 获取 jmx 状态信息
    def get_status_info(self, get):
        if not hasattr(get, "site_id"):
            return public.returnMsg(False, "缺少参数! site_id")
        
        project_config = public.M('sites').where('project_type=? AND id=?', ('Java', get.site_id)).getField(
            "project_config"
        )
        if not project_config:
            return public.returnMsg(False, "网站信息不存在!")
        
        project_config = json.loads(project_config)
        
        if not project_config.get("jmx_status", False):
            return public.returnMsg(False, "您未启用 jmx 监控")
        
        jmx_info = project_config.get("jmx_info")
        if jmx_info is None:
            return public.returnMsg(False, "请先设置 jmx 监控")
        
        java_path = project_config.get("project_jdk", '')
        jmx_url = jmx_info.get("jmx_url")
        username = jmx_info.get("username", "")
        password = jmx_info.get("password", "")
        if not jmx_url:
            return public.returnMsg(False, "未设置 jmx 监控")
        
        # 安装 jmxquery
        try:
            from jmxquery import JMXConnection, JMXQuery
        except:
            public.ExecShell("btpip install jmxquery==0.6.0")
        from jmxquery import JMXConnection, JMXQuery
        import types
        try:
            # 替换源库中存在问题的JSON解析函数
            def my_load_from_json(the, jsonOutput: str):
                if "\n" in jsonOutput:
                    jsonOutput = jsonOutput.replace("\n", "")
                if "\t" in jsonOutput:
                    jsonOutput = jsonOutput.replace("\t", "")
                jsonMetrics = json.loads(jsonOutput)
                metrics = []
                for jsonMetric in jsonMetrics:
                    mBeanName = jsonMetric['mBeanName']
                    attribute = jsonMetric['attribute']
                    attributeType = jsonMetric['attributeType']
                    metric_name = None
                    if 'metricName' in jsonMetric:
                        metric_name = jsonMetric['metricName']
                    metric_labels = None
                    if 'metricLabels' in jsonMetric:
                        metric_labels = jsonMetric['metricLabels']
                    attributeKey = None
                    if 'attributeKey' in jsonMetric:
                        attributeKey = jsonMetric['attributeKey']
                    value = None
                    if 'value' in jsonMetric:
                        value = jsonMetric['value']
                    
                    metrics.append(
                        JMXQuery(mBeanName, attribute, attributeKey, value, attributeType, metric_name, metric_labels)
                    )
                return metrics
            
            # 创建 JMXConnection
            # JMX 连接信息
            # jmx_host = '127.0.0.1'
            # jmx_port = 9001  # 根据你的 Java 程序配置的 JMX 端口修改
            # jmx_url = f'service:jmx:rmi:///jndi/rmi://{jmx_host}:{jmx_port}/jmxrmi'
            jmxConnection = JMXConnection(
                connection_uri = jmx_url, jmx_username = username, jmx_password = password,
                java_path = java_path
                )
            setattr(jmxConnection, "_JMXConnection__load_from_json", types.MethodType(my_load_from_json, jmxConnection))
            jmxQuery = [JMXQuery("*:*")]
            # 执行查询
            metrics = jmxConnection.query(jmxQuery)
        except Exception:
            return public.returnMsg(False, "连接失败！ {}".format(jmx_url))
        
        # 创建 JMX 查询
        jmx_status_info = {}
        
        type_list = ["MemoryPool", "GarbageCollector"]
        percent_list = ["SystemCpuLoad", "ProcessCpuLoad"]
        
        microsecond_list = ["StartTime", "Uptime", "endTime", "startTime", "CollectionTime", "CurrentThreadCpuTime",
                            "CurrentThreadUserTime", "endTime", "startTime", "CollectionTime",
                            "TotalCompilationTime", ]
        nanoseconds_list = ["ProcessCpuTime", ]
        size_list = ["FreePhysicalMemorySize", "TotalPhysicalMemorySize", "committed", "init", "max", "used"]
        value_dict = {
            "True": "是",
            "False": "否",
            "None": "无",
        }
        
        # 解析结果
        for metric in metrics:
            java_type_obj = re.search("type=([\w\s]+)", metric.mBeanName)
            if not java_type_obj:
                continue
            java_type = java_type_obj.group(1)
            
            name_obj = re.search("name=([\w\s]+)", metric.mBeanName)
            name = None
            if name_obj:
                name = name_obj.group(1)
            
            if jmx_status_info.get(java_type) is None:
                if java_type in type_list:
                    jmx_status_info[java_type] = []
                else:
                    jmx_status_info[java_type] = {}
            type_info = jmx_status_info[java_type]
            
            if name is not None:
                name = name.replace(" ", "_")
                if isinstance(type_info, list):
                    for info in type_info:
                        if info["name"] == name:
                            type_info = info
                            break
                    else:
                        info = {"name": name}
                        type_info.append(info)
                        type_info = info
                else:
                    if type_info.get(name) is None:
                        type_info[name] = {}
                    type_info = type_info[name]
            
            value = value_dict.get(str(metric.value))
            if value is None:
                value = metric.value
            
            if metric.attributeKey:
                if metric.attribute is not None and type_info.get(metric.attribute) is None:
                    type_info[metric.attribute] = {}
                
                if value == -1:
                    value = "无限制"
                elif metric.attributeKey in size_list:
                    value = public.to_size(value)
                elif metric.attributeKey in microsecond_list:
                    value = datetime.datetime.fromtimestamp(int(value) / 1000).strftime('%Y-%m-%d %H:%M:%S')
                elif metric.attributeKey in nanoseconds_list:
                    value = "{} 秒".format(int(value) / 1e9)
                
                type_info[metric.attribute][metric.attributeKey] = value
            else:
                if metric.attribute in size_list:
                    value = public.to_size(value)
                elif metric.attribute in percent_list:
                    value = "{}%".format(round(int(value) * 100, 2))
                elif metric.attribute in microsecond_list:
                    value = datetime.datetime.fromtimestamp(int(value) / 1000).strftime('%Y-%m-%d %H:%M:%S')
                elif metric.attribute in nanoseconds_list:
                    value = "{} 秒".format(int(value) / 1e9)
                type_info[metric.attribute] = value
        return {"status": True, "msg": "ok", "data": jmx_status_info}
    
    def get_project_status(self, project_id):
        # 仅使用在项目停止告警中
        project_info = public.M('sites').where('project_type=? AND id=?', ('Java', project_id)).find()
        if not project_info:
            return None, ""
        
        project_info["project_config"] = json.loads(project_info["project_config"])
        if project_info['project_config']['java_type'] == 'springboot':
            if self.is_stop_by_user(project_id):
                return True, project_info["name"]
            return self.get_project_run_state(project_name = project_info['name']), project_info["name"]
        
        if project_info['project_config']['java_type'] == 'duli':
            if self.is_stop_by_user(self.__site_path + "/" + project_info["name"]):
                return True, project_info["name"]
            return self.get_duli_run_state(project_name = project_info['name']), project_info["name"]
        
        if project_info['project_config']['java_type'] == 'neizhi':
            version = project_info['project_config']['tomcat_version']
            if self.is_stop_by_user("/etc/init.d/bttomcat{}".format(version)):
                return True, project_info["name"]
            tomcat_path = '/usr/local/bttomcat/tomcat{}'.format(version)
            return self.get_duli_run_state(
                project_name = project_info["name"], bt_tomcat_web = tomcat_path,
                neizhi = True
                ), project_info["name"]
    
    def set_jdk_environment(self, get):
        # 解析前端发送的数据
        jdk_name = get.name
        jdk_path = "/www/server/java/{}/bin/java".format(jdk_name)
        
        # 检查提供的JDK路径是否有效
        if not os.path.exists(jdk_path):
            return "提供的JDK路径不存在。"
        
        # 获取JAVA_HOME的新值
        new_java_home = os.path.dirname(os.path.dirname(jdk_path))
        
        # 写入全局的shell配置文件
        profile_path = '/etc/profile'
        java_home_line = "export JAVA_HOME={}".format(new_java_home)
        path_line = "export PATH=$JAVA_HOME/bin:$PATH"
        
        # 检查文件是否存在
        if os.path.exists(profile_path):
            
            # 读取/etc/profile文件并更新JAVA_HOME和PATH
            with open(profile_path, 'r') as file:
                lines = file.readlines()
            
            try:
                # 检查是否已经设置了JAVA_HOME
                with open(profile_path, 'w') as file:
                    java_home_set = False
                    for line in lines:
                        if 'export JAVA_HOME=' in line:
                            file.write(java_home_line + '\n')
                            java_home_set = True
                        elif 'export PATH=$JAVA_HOME/bin:$PATH' in line:
                            # 如果已经更新了JAVA_HOME，则跳过旧的PATH设置
                            continue
                        else:
                            file.write(line)
                    if not java_home_set:
                        # 如果/etc/profile中没有JAVA_HOME设置，则添加它
                        file.write(java_home_line + '\n')
                    
                    file.write(path_line + '\n')
                    public.ExecShell("source /etc/profile")
                
                return public.returnMsg(True, "设置成功！")
            except:
                return public.returnMsg(False, "设置失败，请查看您是否开启了系统加固！")
        
        else:
            return public.returnMsg(False, "设置失败！")

    def get_system_user_list(self, get):
        """
        默认只返回uid>= 1000 的用户 和 root
        get中包含 sys_user 返回 uid>= 100 的用户 和 root
        get中包含 all_user 返回所有的用户
        """
        is_spring_boot = get.get("springboot/d", 0)
        if is_spring_boot:
            self.set_spring_user()
        sys_user = False
        all_user = False
        if get is not None:
            if hasattr(get, "sys_user"):
                sys_user = True
            if hasattr(get, "all_user"):
                all_user = True
        
        user_set = set()
        try:
            for tmp_uer in pwd.getpwall():
                # if is_spring_boot and tmp_uer.pw_shell.find("nologin") != -1:
                #     continue
                if tmp_uer.pw_uid == 0:
                    user_set.add(tmp_uer.pw_name)
                elif tmp_uer.pw_uid >= 1000:
                    user_set.add(tmp_uer.pw_name)
                elif sys_user and tmp_uer.pw_uid >= 100:
                    user_set.add(tmp_uer.pw_name)
                elif all_user:
                    user_set.add(tmp_uer.pw_name)
        except Exception:
            pass
        return list(user_set)


    def generate_port(self, get):
        return public.returnMsg(True, self.generate_random_port())