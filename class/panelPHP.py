#coding:utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

# +-------------------------------------------------------------------
# | PHP插件兼容模块
# +-------------------------------------------------------------------

import json,os,public,time,re
from BTPanel import request
class panelPHP:
    
    def __init__(self,plugin_name):
        self.__plugin_name = plugin_name
        self.__plugin_path = "/www/server/panel/plugin/%s" % plugin_name
        self.__args_dir = self.__plugin_path + '/args'
        self.__args_tmp = self.__args_dir + '/' + public.GetRandomString(32)
        if not os.path.exists(self.__args_dir): os.makedirs(self.__args_dir, 384)
        
    #调用PHP插件
    def exec_php_script(self,args):
        #取PHP执行文件和CLI配置参数
        php_bin = self.__get_php_bin()
        if not php_bin: return public.returnMsg(False,'没有找到兼容的PHP版本，请先安装')
        #是否将参数写到文件
        self.__write_args(args)
        result = os.popen("cd " + self.__plugin_path + " && %s /www/server/panel/class/panel_php_run.php --args_tmp=\"%s\" --plugin_name=\"%s\" --fun=\"%s\"" % 
                          (php_bin,self.__args_tmp,self.__plugin_name,args.s)).read()
        try:
            #解析执行结果
            result = json.loads(result)
        except: pass
        #删除参数文件
        if os.path.exists(self.__args_tmp): 
            os.remove(self.__args_tmp)
        return result
    
    #将参数写到文件
    def __write_args(self,args):
        if os.path.exists(self.__args_tmp): os.remove(self.__args_tmp)
        self.__clean_args_file()
        data = {}
        data['GET'] = request.args.to_dict()
        data['POST'] = request.form.to_dict()
        data['POST']['client_ip'] = public.GetClientIp()
        data = json.dumps(data)
        public.writeFile(self.__args_tmp,data)
    
    #清理参数文件
    def __clean_args_file(self):
        args_dir = self.__plugin_path + '/args'
        if not os.path.exists(args_dir): return False
        now_time = time.time()
        for f_name in os.listdir(args_dir):
            filename = args_dir + '/' + f_name
            if not os.path.exists(filename): continue
            #清理创建时间超过60秒的参数文件
            if now_time - os.path.getctime(filename) > 60: os.remove(filename)
    
    #取PHP-CLI执行命令
    def __get_php_bin(self):
        #如果有指定兼容的PHP版本
        php_v_file = self.__plugin_path + '/php_version.json'
        if os.path.exists(php_v_file): 
             php_vs = json.loads(public.readFile(php_v_file).replace('.',''))
        else:
            #否则兼容所有版本
            php_vs = ["80","74","73","72","71","70","56","55","54","53","52"]
        #判段兼容的PHP版本是否安装
        php_path = "/www/server/php/"
        php_v = None
        for pv in php_vs:
            php_bin = php_path + pv + "/bin/php"
            if os.path.exists(php_bin): 
                php_v = pv
                break
        #如果没安装直接返回False
        if not php_v: return False
        #处理PHP-CLI-INI配置文件
        php_ini = self.__plugin_path + '/php_cli_'+php_v+'.ini'
        if not os.path.exists(php_ini):
            #如果不存在，则从PHP安装目录下复制一份
            src_php_ini = php_path + php_v + '/etc/php.ini'
            import shutil
            shutil.copy(src_php_ini,php_ini)
            #解除所有禁用函数
            php_ini_body = public.readFile(php_ini)
            php_ini_body = re.sub(r"disable_functions\s*=.*","disable_functions = ",php_ini_body)
            php_ini_body = re.sub(r".*bt_filter.+","",php_ini_body)
            public.writeFile(php_ini,php_ini_body)
        return php_path + php_v + '/bin/php -c ' + php_ini
            
        
    