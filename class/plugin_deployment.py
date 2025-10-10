# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

# +--------------------------------------------------------------------
# |   自动部署网站
# +--------------------------------------------------------------------

import public, json, os, time, sys, re

try:
    from BTPanel import session, cache
except:
    pass


class obj: id = 0


class plugin_deployment:
    __panelPath = '/www/server/panel'
    __setupPath = '{}/data'.format(__panelPath)
    logPath = 'data/deployment_speed.log'
    __tmp = '/www/server/panel/temp/'
    timeoutCount = 0
    oldTime = 0
    _speed_key = 'dep_download_speed'

    def GetSiteList(self, get):
        """
        @name 获取网站一键部署列表
        """
        jsonFile = self.__panelPath + '/data/deployment_list.json'
        if not os.path.exists(jsonFile) or hasattr(get, 'force'):
            self.GetCloudList(get)

        if not os.path.exists(jsonFile): return public.returnMsg(False, '配置文件不存在!')
        data = {}
        data = self.get_input_list(json.loads(public.readFile(jsonFile)))

        if not hasattr(get, 'type'):
            get.type = 0
        else:
            get.type = int(get.type)
        if not hasattr(get, 'search'):
            search = None
            m = 0
        else:
            m = 1

        tmp = []

        for d in data['list']:
            i = 0
            if get.type > 0:
                if get.type == d['type']: i += 1
            else:
                i += 1
            if search:
                if d['name'].lower().find(search) != -1: i += 1
                if d['title'].lower().find(search) != -1: i += 1
                if d['ps'].lower().find(search) != -1: i += 1
                if get.type > 0 and get.type != d['type']: i -= 1

            if i > m:
                del (d['versions'][0]['download'])
                del (d['versions'][0]['md5'])
                d = self.get_icon(d)

                if 'is_site_show' in d and d['is_site_show']:
                    d['is_many'] = 0
                    if d['is_site_show'] >= 1000: d['is_many'] = 1

                    tmp.append(d)

        tmp = sorted(tmp, key=lambda x: x['is_site_show'], reverse=False)
        data['list'] = tmp
        return data

    # 获取列表
    def GetList(self, get):
        jsonFile = self.__panelPath + '/data/deployment_list.json'
        if not os.path.exists(jsonFile) or hasattr(get, 'force'):
            self.GetCloudList(get)

        if not os.path.exists(jsonFile): return public.returnMsg(False, '配置文件不存在!')
        data = {}
        data = self.get_input_list(json.loads(public.readFile(jsonFile)))

        if not hasattr(get, 'type'):
            get.type = 0
        else:
            get.type = int(get.type)
        if not hasattr(get, 'search'):
            search = None
            m = 0
        else:
            if sys.version_info[0] == 2:
                search = get.search.encode('utf-8').lower()
            else:
                search = get.search.lower()
            m = 1
            public.set_search_history('GetList', 'GetList', search)

        tmp = []
        for d in data['list']:
            i = 0
            if get.type > 0:
                if get.type == d['type']: i += 1
            else:
                i += 1
            if search:
                if d['name'].lower().find(search) != -1: i += 1
                if d['title'].lower().find(search) != -1: i += 1
                if d['ps'].lower().find(search) != -1: i += 1
                if get.type > 0 and get.type != d['type']: i -= 1

            if i > m:
                del (d['versions'][0]['download'])
                del (d['versions'][0]['md5'])
                d = self.get_icon(d)
                tmp.append(d)
        data['search_history'] = public.get_search_history('GetList', 'GetList')
        data['list'] = tmp
        return data

    # 获取图标
    def get_icon(self, pinfo):
        path = '/www/server/panel/BTPanel/static/img/dep_ico'
        if not os.path.exists(path): os.makedirs(path, 384)
        filename = "%s/%s.png" % (path, pinfo['name'])
        m_uri = pinfo['min_image']
        pinfo['min_image'] = '/static/img/dep_ico/%s.png' % pinfo['name']
        if sys.version_info[0] == 2: filename = filename.encode('utf-8')
        if os.path.exists(filename):
            if os.path.getsize(filename) > 100: return pinfo
        public.ExecShell("wget -O " + filename + ' https://www.bt.cn' + m_uri + " &")
        return pinfo

    # 获取插件列表
    def GetDepList(self, get):
        jsonFile = self.__setupPath + '/deployment_list.json'
        if not os.path.exists(jsonFile): return public.returnMsg(False, '配置文件不存在!')
        data = {}
        data = json.loads(public.readFile(jsonFile))
        return self.get_input_list(data)

    # 获取本地导入的插件
    def get_input_list(self, data):
        try:
            jsonFile = self.__setupPath + '/deployment_list_other.json'
            if not os.path.exists(jsonFile): return data
            i_data = json.loads(public.readFile(jsonFile))
            for d in i_data:
                data['list'].append(d)
            return data
        except:
            return data

    # 从云端获取列表
    def GetCloudList(self, get):
        try:
            jsonFile = self.__setupPath + '/deployment_list.json'
            downloadUrl = 'https://www.bt.cn/api/panel/get_deplist'
            pdata = public.get_pdata()
            pdata["version"] = "v2"
            tmp = public.httpPost(downloadUrl, pdata, 30)
            tmp = json.loads(tmp)
            if not tmp: return public.returnMsg(False, '从云端获取失败!')
            public.writeFile(jsonFile, json.dumps(tmp))
            return public.returnMsg(True, '更新成功!')
        except:
            return public.returnMsg(False, '从云端获取失败!')

    # 判断是否存在
    def CheckPackage(self, name):
        data = self.GetDepList(None)
        for info in data["list"]:
            if info["name"] == name:
                return True
        return False

    # 导入程序包
    def AddPackage(self, get):
        jsonFile = self.__setupPath + '/deployment_list_other.json'
        if not os.path.exists(jsonFile):
            public.writeFile(jsonFile, '[]')

        if self.CheckPackage(get.name):
            return public.returnMsg(False, '{} 英文名称已存在!'.format(get.name))
        pinfo = {}
        project_type = get.get("project_type", "php")
        pinfo['name'] = get.name
        pinfo['title'] = get.title
        pinfo['version'] = get.version

        if project_type == "php":
            # php版本
            pinfo['php'] = get.php
            # 被解禁PHP函数
            pinfo['enable_functions'] = get.enable_functions

        if project_type == "java":
            # jdk版本
            pinfo['java'] = get.java_version.strip()
            # mysql版本
            pinfo['mysql'] = get.mysql_version.strip()

        pinfo['ps'] = get.get("ps", "")
        pinfo['official'] = '#'
        pinfo['sort'] = 1000
        pinfo['min_image'] = ''
        pinfo['id'] = 0
        pinfo['type'] = 100
        pinfo['author'] = '本地导入'
        from werkzeug.utils import secure_filename
        from flask import request
        f = request.files['dep_zip']
        # 获取安全的文件名
        filename = secure_filename(f.filename)

        # 检查文件扩展名是否为 .zip
        if not filename.endswith('.zip'):
            # 如果文件扩展名不是 .zip，则返回错误
            return public.returnMsg(False, '仅允许上传 zip 格式的文件')

        s_path = self.__panelPath + '/package'
        if not os.path.exists(s_path): os.makedirs(s_path, 384)
        s_file = s_path + '/' + pinfo['name'] + '.zip'
        if os.path.exists(s_file): os.remove(s_file)
        f.save(s_file)
        os.chmod(s_file, 384)
        con = {}
        try:
            import zipfile
            with zipfile.ZipFile(s_file, 'r') as zfile:
                with zfile.open('auto_install.json') as f:
                    con = json.loads(f.read())
        except:
            con["project_type"] = "php"
        pinfo['project_type'] = con.get("project_type", 'php').lower()
        pinfo['config'] = con
        pinfo['versions'] = []
        version = {
            "cpu_limit": 1,
            "dependnet": "",
            "m_version": pinfo['version'],
            "mem_limit": 32,
            "os_limit": 0,
            "size": os.path.getsize(s_file),
            "version": "0",
            "download": "",
            "version_msg": "测试2"
        }
        version['md5'] = self.GetFileMd5(s_file)
        pinfo['versions'].append(version)
        data = json.loads(public.readFile(jsonFile))
        is_exists = False
        for i in range(len(data)):
            if data[i]['name'] == pinfo['name']:
                data[i] = pinfo
                is_exists = True

        if not is_exists: data.append(pinfo)

        public.writeFile(jsonFile, json.dumps(data))
        return public.returnMsg(True, '导入成功!')

    # 取本地包信息
    def GetPackageOther(self, get):
        p_name = get.p_name
        jsonFile = self.__setupPath + '/deployment_list_other.json'
        if not os.path.exists(jsonFile): public.returnMsg(False, '没有找到[{}]'.format(p_name))
        data = json.loads(public.readFile(jsonFile))

        for i in range(len(data)):
            if data[i]['name'] == p_name: return data[i]
        return public.returnMsg(False, '没有找到[%s]' % p_name)

    # 删除程序包
    def DelPackage(self, get):
        jsonFile = self.__setupPath + '/deployment_list_other.json'
        if not os.path.exists(jsonFile): return public.returnMsg(False, '配置文件不存在!')

        data = {}
        data = json.loads(public.readFile(jsonFile))

        tmp = []
        for d in data:
            if d['name'] == get.dname:
                s_file = self.__panelPath + '/package/' + d['name'] + '.zip'
                if os.path.exists(s_file): os.remove(s_file)
                continue
            tmp.append(d)

        data = tmp
        public.writeFile(jsonFile, json.dumps(data))
        return public.returnMsg(True, '删除成功!')

    # 下载文件
    def DownloadFile(self, url, filename):
        import requests
        self.pre = 0
        self.oldTime = time.time()
        self.WriteLogs("正在下载文件【{}】...".format(filename))

        try:
            download_res = requests.get(url, headers=public.get_requests_headers(), timeout=30, stream=True)
            headers_total_size = int(download_res.headers['content-length'])
            res_chunk_size = 8192 * 2
            count = 0
            with open(filename, 'wb+') as with_res_f:
                for download_chunk in download_res.iter_content(chunk_size=res_chunk_size):
                    if download_chunk:
                        count += 1
                        with_res_f.write(download_chunk)
                        speed_last_size = len(download_chunk)
                        self.DownloadHook(count, speed_last_size, headers_total_size)
                with_res_f.close()
        except requests.exceptions.RequestException as e:
            error_message = "ERROR：下载文件【{}】失败: {}".format(filename, str(e))
            self.WriteLogs(error_message)

    # 下载文件进度回调
    def DownloadHook(self, count, blockSize, totalSize):
        used = count * blockSize
        pre1 = int((100.0 * used / totalSize))
        if self.pre != pre1:
            dspeed = used / (time.time() - self.oldTime)
            # 构建进度日志信息
            log_message = "下载进度: {}%, 速度: {} B/s, 已下载: {}/{}".format(
                pre1, int(dspeed), used, totalSize
            )
            self.WriteLogs(log_message)
            self.pre = pre1

    # 写输出日志
    def WriteLogs(self, msg):
        if msg.find('ERROR：') != -1 or msg.find('Success：') != -1:
            public.writeFile(self.logPath, '{}\n'.format(msg), 'a+')
            status = False
            if msg.find('Success：') != -1:
                status = True
            data = {
                'status': status,
                'msg': msg,
                'data': public.GetNumLines(self.logPath, 100)
            }
            public.writeFile(self.logPath, json.dumps(data))
        else:
            try:
                logs = public.readFile(self.logPath)
                data = json.loads(logs)
                data['data'] = '{}\n{}'.format(data['data'], msg)
                public.writeFile(self.logPath, json.dumps(data))
            except:
                public.writeFile(self.logPath, '{}\n'.format(msg), 'a+')

    # 需要特殊处理的项目
    def set_complex_conf(self, get, path, find):
        if get.dname == "CatchAdmin":
            return self.set_catchadmin_conf(get, path, find)

        return public.returnMsg(False, '暂未支持')

    # 处理deepseek_r1的配置的配置
    def set_catchadmin_conf(self, get, path, find):
        # 前后端分离处理替换配置文件
        config_path = path + '/public/admin/static/config.js'
        if os.path.exists(config_path):
            self.WriteLogs('正在替换配置文件...')
            url_data = public.readFile(config_path)
            url_data = url_data.replace("${BT_APP_URL}", "http://{}/api".format(get.site_name.strip()))
            public.writeFile(config_path, url_data)

        index_js = path + '/public/admin/assets/js/index-CMy4Wf15.js'
        if os.path.exists(index_js):
            url_data = public.readFile(index_js)
            url_data = url_data.replace("${BT_APP_URL}", "http://{}/api".format(get.site_name.strip()))
            public.writeFile(index_js, url_data)

        # 创建的数据库信息
        if os.path.exists(path + '/.env'):
            databaseInfo = public.M('databases').where('pid=?', (find['id'],)).field('username,password').find()
            if databaseInfo:
                env_data = public.readFile(path + '/.env')
                env_data = env_data.replace('${BT_APP_URL}', 'http://{}'.format(get.site_name.strip()))
                env_data = env_data.replace('${BT_MYSQL_PORT}', self.__mysql_info())
                env_data = env_data.replace('${BT_DB_NAME}', databaseInfo['username'])
                env_data = env_data.replace('${BT_DB_USERNAME}', databaseInfo['username'])
                env_data = env_data.replace('${BT_DB_PASSWORD}', databaseInfo['password'])
                public.writeFile(path + '/.env', env_data)

        # 配置文件 适配请求前端文件
        nginx_conf = "/www/server/panel/vhost/nginx/{}.conf".format(get.site_name.strip())
        if os.path.exists(nginx_conf):
            content = public.readFile(nginx_conf)

            # 移除静态文件location
            patt = 'location[\s~\.\*\\\\]+\((gif|js).+?\s+\}'  # 非贪婪匹配
            rep_compile = re.compile(patt, re.S)
            if rep_compile:
                content = rep_compile.sub('', content)
            public.writeFile(nginx_conf, content)

    def __setup_php_environment(self, get, name, packinfo, path, find):
        if hasattr(get, "php_version"): php_version = get.php_version.strip()
        # 检查本地包
        self.WriteLogs('正在校验软件包...')
        pack_path = self.__panelPath + '/package'
        if not os.path.exists(pack_path): os.makedirs(pack_path, 384)
        packageZip = pack_path + '/' + name + '.zip'
        isDownload = False
        if os.path.exists(packageZip):
            md5str = self.GetFileMd5(packageZip)
            if md5str != packinfo['versions'][0]['md5']:
                isDownload = True
                self.WriteLogs('本地包的MD5校验失败，准备重新下载...')
            else:
                self.WriteLogs('本地包已存在且通过MD5校验')
        else:
            isDownload = True
            self.WriteLogs('本地包不存在，准备下载...')

        # 下载文件
        if isDownload:
            try:
                if packinfo['versions'][0]['download']:
                    self.DownloadFile(public.GetConfigValue('home') + '/api/Pluginother/get_file?fname=' + packinfo['versions'][0]['download'], packageZip)
                else:
                    self.WriteLogs('ERROR：下载链接无效，无法下载文件。')
                    return public.returnMsg(False, '下载链接无效，无法下载文件。')
            except Exception as e:
                self.WriteLogs('ERROR：下载文件时发生错误: {}'.format(str(e)))
                return public.returnMsg(False, '下载文件时发生错误，请检查日志以获取详细信息。')

        if not os.path.exists(packageZip):
            return public.returnMsg(False, '文件{}下载失败'.format(packageZip))

        pinfo = self.set_temp_file(packageZip, path)
        if not pinfo:
            self.WriteLogs('ERROR：文件下载失败，文件不存在: {}'.format(packageZip))
            return public.returnMsg(False, '在安装包中找不到【宝塔自动部署配置文件】')

        if 'source' in get and int(get.source) == 1:
            public.set_module_logs('plugin_deployment', 'SetupPackage')

        # 设置权限
        try:
            self.WriteLogs('正在设置权限...')
            public.ExecShell('chmod -R 755 ' + path)
            public.ExecShell('chown -R www.www ' + path)
            if 'chmod' in pinfo:
                if pinfo['chmod']:
                    for chm in pinfo['chmod']:
                        public.ExecShell('chmod -R ' + str(chm['mode']) + ' ' + (path + '/' + chm['path']).replace('//', '/'))
        except Exception as e:
            pinfo["install_status"] = False
            self.WriteLogs('ERROR：设置权限时发生错误: {}'.format(str(e)))
        # 安装PHP扩展
        self.WriteLogs('开始安装项目PHP扩展...')
        if 'php_ext' in pinfo:
            try:
                import files
                mfile = files.files()
                if type(pinfo['php_ext']) != list: pinfo['php_ext'] = pinfo['php_ext'].strip().split(',')
                for ext in pinfo['php_ext']:
                    self.WriteLogs('正在安装PHP扩展: {}'.format(ext))
                    if ext == 'pathinfo':
                        import config
                        con = config.config()
                        get.version = php_version
                        get.type = 'on'
                        con.setPathInfo(get)
                    else:
                        get.name = ext
                        get.version = php_version
                        get.type = '1'
                        mfile.InstallSoft(get)
            except Exception as e:
                pinfo["install_status"] = False
                self.WriteLogs('ERROR：安装PHP扩展失败: {}'.format(str(e)))

        # 解禁PHP函数
        if 'enable_functions' in pinfo:
            try:
                if type(pinfo['enable_functions']) == str: pinfo['enable_functions'] = pinfo['enable_functions'].strip().split(',')
                php_f = public.GetConfigValue('setup_path') + '/php/' + php_version + '/etc/php.ini'
                php_c = public.readFile(php_f)
                rep = "disable_functions\s*=\s{0,1}(.*)\n"
                tmp = re.search(rep, php_c).groups()
                disable_functions = tmp[0].split(',')
                for fun in pinfo['enable_functions']:
                    fun = fun.strip()
                    if fun in disable_functions: disable_functions.remove(fun)
                disable_functions = ','.join(disable_functions)
                php_c = re.sub(rep, 'disable_functions = ' + disable_functions + "\n", php_c)
                public.writeFile(php_f, php_c)
                public.phpReload(php_version)
            except:
                pass

        # 执行额外shell进行依赖安装
        self.WriteLogs('正在执行额外SHELL依赖安装...')
        if os.path.exists(path + '/install.sh'):
            public.ExecShell('cd ' + path + ' && bash ' + 'install.sh ' + find['name'])
            public.ExecShell('rm -f ' + path + '/install.sh')

        # 是否执行Composer
        if os.path.exists(path + '/composer.json'):
            self.WriteLogs('正在执行Composer...')
            if not os.path.exists(path + '/composer.lock'):
                execPHP = '/www/server/php/' + php_version + '/bin/php'
                if execPHP:
                    if public.get_url().find('125.88'):
                        public.ExecShell('cd ' + path + ' && ' + execPHP + ' /usr/bin/composer config repo.packagist composer https://packagist.phpcomposer.com')
                    import panelSite;
                    phpini = '/www/server/php/' + php_version + '/etc/php.ini'
                    phpiniConf = public.readFile(phpini)
                    phpiniConf = phpiniConf.replace('proc_open,proc_get_status,', '')
                    public.writeFile(phpini, phpiniConf)
                    public.ExecShell('nohup cd ' + path + ' && ' + execPHP + ' /usr/bin/composer install -vvv > /tmp/composer.log 2>&1 &')

        # 处理复杂一些的项目配置
        self.set_complex_conf(get, path, find)

        # 写伪静态
        self.WriteLogs('正在设置伪静态...')
        swfile = path + '/nginx.rewrite'
        if os.path.exists(swfile):
            rewriteConf = public.readFile(swfile)
            rewriteConf = rewriteConf.replace('${BT_PROJECT_PATH}', path)
            dwfile = self.__panelPath + '/vhost/rewrite/' + get.site_name.strip() + '.conf'
            public.writeFile(dwfile, rewriteConf)
        else:
            self.WriteLogs('未找到nginx.rewrite文件，跳过设置伪静态。')

        swfile = path + '/.htaccess'
        if os.path.exists(swfile):
            swpath = (path + '/' + pinfo['run_path'] + '/.htaccess').replace('//', '/')
            if pinfo['run_path'] != '/' and not os.path.exists(swpath):
                public.writeFile(swpath, public.readFile(swfile))
        else:
            self.WriteLogs('未找到.htaccess文件，跳过设置伪静态。')

        # 删除伪静态文件
        try:
            public.ExecShell("rm -f " + path + '/*.rewrite')
        except Exception as e:
            self.WriteLogs('ERROR：删除伪静态文件时发生错误: {}'.format(str(e)))

        # 删除多余文件
        rm_file = path + '/index.html'
        if os.path.exists(rm_file):
            rm_file_body = public.readFile(rm_file)
            if rm_file_body.find('panel-heading') != -1: os.remove(rm_file)

        # 设置运行目录
        try:
            self.WriteLogs('正在设置运行目录...')
            if 'run_path' in pinfo:
                if pinfo['run_path'] != '/':
                    import panelSite
                    siteObj = panelSite.panelSite()
                    mobj = obj()
                    mobj.id = find['id']
                    mobj.runPath = pinfo['run_path']
                    siteObj.SetSiteRunPath(mobj)
        except Exception as e:
            pinfo["install_status"] = False
            self.WriteLogs('ERROR：设置运行目录时发生错误: {}'.format(str(e)))

        # 导入数据
        try:
            self.WriteLogs('正在导入数据库...')
            if os.path.exists(path + '/import.sql'):
                databaseInfo = public.M('databases').where('pid=?', (find['id'],)).field('username,password').find()
                if databaseInfo:
                    public.ExecShell('/www/server/mysql/bin/mysql -u' + databaseInfo['username'] + ' -p' + databaseInfo['password'] + ' ' + databaseInfo['username'] + ' < ' + path + '/import.sql')
                    public.ExecShell('rm -f ' + path + '/import.sql')
                    if pinfo['db_config']:
                        siteConfigFile = (path + '/' + pinfo['db_config']).replace('//', '/')
                        if os.path.exists(siteConfigFile):
                            siteConfig = public.readFile(siteConfigFile)
                            siteConfig = siteConfig.replace('BT_DB_USERNAME', databaseInfo['username'])
                            siteConfig = siteConfig.replace('BT_DB_PASSWORD', databaseInfo['password'])
                            siteConfig = siteConfig.replace('BT_DB_NAME', databaseInfo['username'])
                            public.writeFile(siteConfigFile, siteConfig)
                    self.WriteLogs('导入数据库成功')

        except Exception as e:
            pinfo["install_status"] = False
            self.WriteLogs('ERROR：导入数据库时发生错误: {}'.format(str(e)))

        # 清理文件和目录
        try:
            self.WriteLogs('正在清理临时文件...')
            if 'remove_file' in pinfo:
                if type(pinfo['remove_file']) == str: pinfo['remove_file'] = pinfo['remove_file'].strip().split(',')
                for f_path in pinfo['remove_file']:
                    if not f_path: continue
                    filename = (path + '/' + f_path).replace('//', '/')
                    if os.path.exists(filename):
                        if not os.path.isdir(filename):
                            if f_path.find('.user.ini') != -1:
                                public.ExecShell("chattr -i " + filename)
                            os.remove(filename)
                        else:
                            public.ExecShell("rm -rf " + filename)
        except Exception as e:
            pinfo["install_status"] = False
            self.WriteLogs('ERROR：清理临时文件时发生错误: {}'.format(str(e)))

        public.serviceReload()
        self.start_php_async(get.site_name.strip())
        return pinfo

    # java安装环境
    def __setup_java_environment(self, get, path):
        info_file = "/www/wwwroot/{}/auto_install.json".format(get.site_name.strip())
        if not os.path.exists(info_file):
            return public.returnMsg(False, 'auto_install.json配置文件不存在!')

        # 替换配置文件
        filepath = "/www/wwwroot/{}/config".format(get.site_name.strip())
        if not os.path.exists(filepath):
            self.WriteLogs('配置文件config目录不存在: {}'.format(filepath))
            return public.returnMsg(False, '配置文件目录不存在!')

        if os.path.exists(filepath):
            self.WriteLogs('正在配置数据库...')
            for file in os.listdir(filepath):
                full_file_path = os.path.join(filepath, file)
                if os.path.isfile(full_file_path):
                    self.__replace_and_update_config(get, full_file_path)

        self.WriteLogs('数据库配置文件修改完成！')

        if hasattr(get, 'datauser') and hasattr(get, 'datapassword'):
            self.WriteLogs('正在创建数据库【{}】'.format(get.datauser))

            mysql_data = {
                "name": get.datauser,
                "db_user": get.datauser,
                "password": get.datapassword,
                "dataAccess": "ip",
                "address": "127.0.0.1",
                "codeing": "utf8mb4",
                "ps": "{}一键部署".format(get.dname),
                "listen_ip": "0.0.0.0/0",
                "host": "",
                "dtype": "MySQL"
            }

            from database import database as database
            database = database()
            result = database.AddDatabase(public.to_dict_obj(mysql_data))
            if not result["status"]:
                self.WriteLogs('数据库【{}】创建失败,请在面板手动创建对应数据库'.format(get.datauser))

            self.WriteLogs('数据库【{}】创建成功'.format(get.datauser))

        if os.path.exists(path + '/import.sql'):
            self.WriteLogs('正在导入数据库...')
            from database import database as database
            database = database()
            data = {
                "file": path + '/import.sql',
                "name": get.datauser.strip(),
            }

            database.InputSql(public.to_dict_obj(data))
        self.WriteLogs('数据库导入完成！')
        # 重载服务
        public.serviceReload()
        self.start_java_project(get)
        try:
            pinfo = json.loads(public.readFile(info_file))
        except Exception as e:
            pinfo = {}
        return pinfo

    # 获取数据库配置信息
    def __mysql_info(self):
        try:
            public.CheckMyCnf()
            myfile = '/etc/my.cnf'
            mycnf = public.readFile(myfile)
            rep = "port\s*=\s*([0-9]+)\s*\n"
            port = re.search(rep, mycnf).groups()[0]
        except:
            port = '3306'
        return port

    def __replace_and_update_config(self, get, config_file):
        """替换配置文件中的变量"""
        try:
            # 替换变量的值
            replacement_values = {
                'BT_MYSQL_PORT': self.__mysql_info(),
                'BT_DB_NAME': get.datauser.strip(),
                'BT_DB_USERNAME': get.datauser.strip(),
                'BT_DB_PASSWORD': get.datapassword.strip(),
            }

            # 读取配置文件内容
            content = public.readFile(config_file)

            # 替换变量
            pattern = re.compile(r'\$\{(BT_[A-Z_]+)\}')

            # 查找配置文件当前的端口号
            re_port = re.compile(r'\s*server\.port\s*=\s*(\d+)', re.M)
            server_port = re_port.search(content)

            if server_port:
                server_port = server_port.group(1)

            import random
            # 检查端口是否被占用
            status = public.check_tcp("127.0.0.1", server_port)
            if status:
                # 端口被占用，生成一个新的随机端口
                server_port = random.randint(2000, 65535)
                # 替换内容中的端口号
                content = re_port.sub('\nserver.port={}'.format(server_port), content)

            # 使用正则表达式和 lambda 函数替换变量
            formatted_content = pattern.sub(
                lambda match: replacement_values.get(match.group(1), match.group(0)),
                content
            )

            # 写回配置文件
            public.writeFile(config_file, formatted_content)

            self.WriteLogs('配置文件 {} 替换成功'.format(config_file))
        except Exception as e:
            self.WriteLogs('替换配置文件{}失败: {}'.format(config_file, str(e)))

    # 一键安装网站程序
    # param string name 程序名称
    # param string site_name 网站名称
    # param string php_version PHP版本
    def SetupPackage(self, get):
        param_list = ['dname', 'site_name']
        for param in param_list:
            if not hasattr(get, param):
                return public.returnMsg(False, '缺少参数{}'.format(param))

        name = get.dname.strip()
        site_name = get.site_name.strip()
        project_type = get.get('project_type', 'php').strip()

        # 取基础信息
        if project_type == "java":
            project_name = get.project_name.strip()
            find = public.M('sites').where('name=?', (project_name,)).field('id,path,name').find()
        else:
            find = public.M('sites').where('name=?', (site_name,)).field('id,path,name').find()

        if 'path' not in find:
            find = self.solve_chinese_domain(site_name)
            if find is None:
                return public.returnMsg(False, '网站不存在!')
        path = "/www/wwwroot/{}".format(site_name) if project_type == "java" else find['path']

        if path.replace('//', '/') == '/': return public.returnMsg(False, '危险的网站根目录!')

        # 获取包信息
        packinfo = self.GetPackageInfo(name)
        id = packinfo['id']
        if not packinfo: return public.returnMsg(False, '指定软件包不存在!')

        public.writeFile(self.logPath, "")

        result = {
            "admin_username": "",
            "admin_password": "",
            "success_url": "",
        }
        if project_type == "php" or project_type == "php_async":
            php_result = self.__setup_php_environment(get, name, packinfo, path, find)
            # 更新 result 字典
            if isinstance(php_result, dict):
                # 只更新特定的键
                for key in ["admin_username", "admin_password", "success_url"]:
                    if key in php_result:
                        result[key] = php_result[key]
        elif project_type == "java":
            java_result = self.__setup_java_environment(get, path)
            # 更新 result 字典
            if isinstance(java_result, dict):
                # 只更新特定的键
                for key in ["admin_username", "admin_password", "success_url"]:
                    if key in java_result:
                        result[key] = java_result[key]
        time.sleep(1)
        self.WriteLogs('Success：部署【{}】成功...'.format(name))
        if id: self.depTotal(id)
        return public.returnMsg(True, result)

    # 获取网站类型
    def start_php_async(self, site_name):
        try:
            # 获取网站类型
            if '/www/server/panel' not in sys.path:
                sys.path.insert(0, '/www/server/panel')
            from mod.project.php.php_asyncMod import main as php_asyncMod
            php_asyncMod().modify_project_run_state(public.to_dict_obj({"sitename": site_name, "project_action": 'start'}))
        except:
            print(public.get_error_info())

    def start_java_project(self, get):
        # 获取网站类型
        if '/www/server/panel' not in sys.path:
            sys.path.insert(0, '/www/server/panel')
        from mod.project.java.projectMod import main as java_project
        java_project = java_project()
        # 启动项目
        java_project.start_project(public.to_dict_obj({"project_name": get.project_name.strip()}))

        # 获取项目监听端口
        filepath = "/www/wwwroot/{}/config".format(get.site_name.strip())
        if not os.path.exists(filepath):
            self.WriteLogs('ERROR：配置文件config目录不存在: {}'.format(filepath))
            return public.returnMsg(False, '配置文件目录不存在!')

        server_port = None
        for file in os.listdir(filepath):
            full_file_path = os.path.join(filepath, file)
            if os.path.isfile(full_file_path):
                # 读取配置文件内容
                content = public.readFile(full_file_path)
                # 查找配置文件当前的端口号
                re_port = re.compile(r'\s*server\.port\s*=\s*(\d+)', re.M)
                server_port = re_port.search(content)
                if server_port:
                    server_port = server_port.group(1)
                    self.test_port(server_port)

        if server_port:
            # 开启外网映射 代理/目录
            result = java_project.add_server_proxy(public.to_dict_obj({
                "proxy_dir": "/",
                "proxy_port": server_port,
                "site_name": get.project_name.strip(),
                "rewrite": {"status": False, "src_path": "/", "target_path": "/"},
                "add_headers": [],
                "status": "1",
            }))

    # 处理临时文件
    def set_temp_file(self, filename, path):
        public.ExecShell("rm -rf " + self.__tmp + '/*')
        self.WriteLogs('正在解压软件包【{}】...'.format(filename))
        public.ExecShell('unzip -o ' + filename + ' -d ' + self.__tmp)
        auto_config = 'auto_install.json'
        p_info = self.__tmp + '/' + auto_config
        p_tmp = self.__tmp
        p_config = None
        if not os.path.exists(p_info):
            d_path = None
            for df in os.walk(self.__tmp):
                if len(df[2]) < 3: continue
                if not auto_config in df[2]: continue
                if not os.path.exists(df[0] + '/' + auto_config): continue
                d_path = df[0]
            if d_path:
                tmp_path = d_path
                auto_file = tmp_path + '/' + auto_config
                if os.path.exists(auto_file):
                    p_info = auto_file
                    p_tmp = tmp_path
        if os.path.exists(p_info):
            try:
                p_config = json.loads(public.readFile(p_info))
                # os.remove(p_info)
                i_ndex_html = path + '/index.html'
                if os.path.exists(i_ndex_html): os.remove(i_ndex_html)
                if not self.copy_to(p_tmp, path): public.ExecShell(("\cp -arf " + p_tmp + '/. ' + path + '/').replace('//', '/'))
            except json.decoder.JSONDecodeError as e:
                error_message = "ERROR：解析auto_install.json文件错误\n【{}】: {}".format(filename, str(e))
                self.WriteLogs(error_message)
            except:
                pass
        public.ExecShell("rm -rf " + self.__tmp + '/*')
        self.WriteLogs('解压【{}】成功...'.format(filename))
        return p_config

    def copy_to(self, src, dst):
        try:
            if src[-1] == '/': src = src[:-1]
            if dst[-1] == '/': dst = dst[:-1]
            if not os.path.exists(src): return False
            if not os.path.exists(dst): os.makedirs(dst)
            import shutil
            for p_name in os.listdir(src):
                f_src = src + '/' + p_name
                f_dst = dst + '/' + p_name
                if os.path.isdir(f_src):
                    print(shutil.copytree(f_src, f_dst))
                else:
                    print(shutil.copyfile(f_src, f_dst))
            return True
        except:
            return False

    # 提交安装统计
    def depTotal(self, id):
        import panelAuth
        p = panelAuth.panelAuth()
        pdata = p.create_serverid(None)
        pdata['pid'] = id
        p_url = public.GetConfigValue('home') + '/api/pluginother/create_order_okey'
        public.httpPost(p_url, pdata)

    # 获取进度  未使用,目前使用  GetInLog
    def GetSpeed(self, get):
        try:
            result = cache.get(self._speed_key)
            if not result: public.returnMsg(False, '当前没有部署任务!')
            return result
        except:
            return {'name': '准备部署', 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}

    # 获取包信息
    def GetPackageInfo(self, name):
        data = self.GetDepList(None)
        if not data: return False
        for info in data['list']:
            if info['name'].strip() == name:
                return info
        return False

    # 检查指定包是否存在
    def CheckPackageExists(self, name):
        data = self.GetDepList(None)
        if not data: return False
        for info in data['list']:
            if info['name'] == name: return True

        return False

    # 文件的MD5值
    def GetFileMd5(self, filename):
        if not os.path.isfile(filename): return False
        import hashlib;
        myhash = hashlib.md5()
        f = open(filename, 'rb')
        while True:
            b = f.read(8096)
            if not b:
                break
            myhash.update(b)
        f.close()
        return myhash.hexdigest()

    # 获取站点标识
    def GetSiteId(self, get):
        return public.M('sites').where('name=?', (get.webname,)).getField('id')

    def solve_chinese_domain(self, site_name):
        """处理中文域名导致的站点名称查询错误问题"""
        from panelSite import panelSite
        name = panelSite.ToPunycode(object(), site_name.strip().split(':')[0]).strip().lower()
        find = public.M('sites').where('name=?', (name,)).field('id,path,name').find()
        if "path" in find:
            return find
        return None

    # 获取安装日志
    def GetInLog(self, get):
        """
        @name 获取安装日志
        """
        if not os.path.exists(self.logPath):
            return public.returnMsg(True, '')
        logs = public.GetNumLines(self.logPath, 500)
        try:
            logs = json.loads(logs)
            return logs
        except:
            pass

        return public.returnMsg(True, logs)

    # java项目解压jar包到指定路径，并返回路径
    def GetJarPath(self, get):
        try:
            param_list = ['dname', 'sitename']
            for param in param_list:
                if not hasattr(get, param):
                    return public.returnMsg(False, '缺少参数{}'.format(param))

            name = get.dname.strip()
            site_name = get.sitename.strip()
            # 获取包信息
            pinfo = self.GetPackageInfo(name)
            if not pinfo: return public.returnMsg(False, '指定软件包不存在!')
            pack_path = self.__panelPath + '/package'
            if not os.path.exists(pack_path): os.makedirs(pack_path, 384)

            # 压缩包路径
            packageZip = pack_path + '/' + name + '.zip'

            # 检查是否需要下载
            if not os.path.exists(packageZip) or self.GetFileMd5(packageZip) != pinfo['versions'][0]['md5']:
                self.WriteLogs('正在下载文件【{}】'.format(packageZip))
                if pinfo['versions'][0]['download']:
                    self.DownloadFile(public.GetConfigValue('home') + '/api/Pluginother/get_file?fname=' + pinfo['versions'][0]['download'], packageZip)

            if not os.path.exists(packageZip): return public.returnMsg(False, '文件下载失败!' + packageZip)

            # 创建解压目录
            path = "/www/wwwroot/{}".format(site_name)
            if not os.path.exists(path):
                os.makedirs(path, mode=0o755)
            elif os.listdir(path):
                self.WriteLogs('目录【{}】已存在且不为空，请清理后再进行部署。'.format(path))
                return public.returnMsg(False, '目录【{}】已存在且不为空，请清理或重命名后再进行部署。'.format(path))
            else:
                # 如果目录已经存在，检查 .jar 文件
                jar_path = self.__find_jar_file(path)
                if jar_path:
                    return public.returnMsg(True, jar_path)

            pinfo = self.set_temp_file(packageZip, path)
            if not pinfo: return public.returnMsg(False, '在安装包中找不到【宝塔自动部署配置文件】')

            #  查找 .jar 文件
            jar_path = self.__find_jar_file(path)
            if jar_path:
                return public.returnMsg(True, jar_path)

            return public.returnMsg(False, '未找到.jar文件!')
        except Exception as e:
            return public.returnMsg(False, '未找到.jar文件! err:{}'.format(str(e)))

    def __find_jar_file(self, directory):
        """在指定目录中查找 .jar 文件"""
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".jar"):
                    return os.path.join(root, file)
        return None

    # 检查端口是否放行  没有则放行防火墙
    def test_port(self, server_port):
        from safeModel.firewallModel import main

        firewall = main()
        rules = firewall.get_sys_firewall_rules()
        for r in rules:
            if r["types"] == "accept" and r["ports"] == server_port and r["protocol"].find("tcp") != -1:
                return
        new_get = public.dict_obj()
        new_get.protocol = "tcp"
        new_get.ports = server_port
        new_get.choose = "all"
        new_get.address = ""
        new_get.domain = ""
        new_get.types = "accept"
        new_get.brief = ""
        new_get.source = ""
        firewall.create_rules(new_get)

    # 环境类前置检查 mysql ftp redis
    def check_project_env(self, get):
        data = {
            'mysql_version': '',
            'redis_version': ''
        }
        from panelModel.publicModel import main as soft_model
        soft_model = soft_model()
        try:
            for services in ['ftp', 'mysql', 'redis', 'nginx']:
                install_status = soft_model.get_soft_status(public.to_dict_obj({'name': services}))
                data[services] = install_status['setup']
                if install_status["setup"]:
                    if services == 'mysql':
                        data['mysql_version'] = self.get_mysql_version()
                    elif services == 'redis':
                        data['redis_version'] = self.get_redis_version()
        except:
            pass
        return data

    # 获取Mysql版本
    def get_mysql_version(self):
        try:
            version_str = public.ExecShell("/www/server/mysql/bin/mysql  --version")[0]
            # 使用正则表达式提取版本号  8.x
            match = re.search(r'Ver (\d+\.\d+\.\d+)', version_str)
            if not match:
                #  5.x
                match = re.search(r'Distrib\s+(\d+\.\d+\.\d+|\d+\.\d+|\d+)', version_str)

            if match:
                return match.group(1)
            else:
                return ""

        except Exception as e:
            return ""

    def get_redis_version(self):
        try:
            version_str = public.ExecShell("redis-cli info |grep redis_version")[0]
            version = version_str.split(':')[1].strip()
            return version

        except:
            return ""
