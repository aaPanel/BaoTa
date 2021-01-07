#!/usr/bin/env python
# coding:utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import sys
import os
import public
import time
import json
import pwd
import cgi
import shutil
import re
from BTPanel import session, request


class files:
    run_path = None
    download_list = None
    download_is_rm = None
    # 检查敏感目录

    def CheckDir(self, path):
        path = path.replace('//', '/')
        if path[-1:] == '/':
            path = path[:-1]

        nDirs = ('',
                 '/',
                 '/*',
                 '/www',
                 '/root',
                 '/boot',
                 '/bin',
                 '/etc',
                 '/home',
                 '/dev',
                 '/sbin',
                 '/var',
                 '/usr',
                 '/tmp',
                 '/sys',
                 '/proc',
                 '/media',
                 '/mnt',
                 '/opt',
                 '/lib',
                 '/srv',
                 '/selinux',
                 '/www/server',
                 '/www/server/data',
                 public.GetConfigValue('logs_path'),
                 public.GetConfigValue('setup_path'))

        return not path in nDirs

    # 网站文件操作前置检测
    def site_path_check(self, get):
        try:
            if not 'site_id' in get:
                return True
            if not self.run_path:
                self.run_path, self.path, self.site_name = self.GetSiteRunPath(
                    get.site_id)
            if 'path' in get:
                if get.path.find(self.path) != 0:
                    return False
            if 'sfile' in get:
                if get.sfile.find(self.path) != 0:
                    return False
            if 'dfile' in get:
                if get.dfile.find(self.path) != 0:
                    return False
            return True
        except:
            return True

    # 网站目录后续安全处理
    def site_path_safe(self, get):
        try:
            if not 'site_id' in get:
                return True
            run_path, path, site_name = self.GetSiteRunPath(get.site_id)
            if not os.path.exists(run_path):
                os.makedirs(run_path)
            ini_path = run_path + '/.user.ini'
            if os.path.exists(ini_path):
                return True
            sess_path = '/www/php_session/%s' % site_name
            if not os.path.exists(sess_path):
                os.makedirs(sess_path)
            ini_conf = '''open_basedir={}/:/tmp/:/proc/:{}/
session.save_path={}/
session.save_handler = files'''.format(path, sess_path, sess_path)
            public.writeFile(ini_path, ini_conf)
            public.ExecShell("chmod 644 %s" % ini_path)
            public.ExecShell("chdir +i %s" % ini_path)
            return True
        except:
            return False

    # 取当站点前运行目录
    def GetSiteRunPath(self, site_id):
        try:
            find = public.M('sites').where(
                'id=?', (site_id,)).field('path,name').find()
            siteName = find['name']
            sitePath = find['path']
            if public.get_webserver() == 'nginx':
                filename = '/www/server/panel/vhost/nginx/' + siteName + '.conf'
                if os.path.exists(filename):
                    conf = public.readFile(filename)
                    rep = '\s*root\s+(.+);'
                    tmp1 = re.search(rep, conf)
                    if tmp1:
                        path = tmp1.groups()[0]
            else:
                filename = '/www/server/panel/vhost/apache/' + siteName + '.conf'
                if os.path.exists(filename):
                    conf = public.readFile(filename)
                    rep = '\s*DocumentRoot\s*"(.+)"\s*\n'
                    tmp1 = re.search(rep, conf)
                    if tmp1:
                        path = tmp1.groups()[0]
            return path, sitePath, siteName
        except:
            return sitePath, sitePath, siteName

    # 检测文件名
    def CheckFileName(self, filename):
        nots = ['\\', '&', '*', '|', ';', '"', "'", '<', '>']
        if filename.find('/') != -1:
            filename = filename.split('/')[-1]
        for n in nots:
            if n in filename:
                return False
        return True

    # 名称输出过滤
    def xssencode(self, text):
        list = ['<', '>']
        ret = []
        for i in text:
            if i in list:
                i = ''
            ret.append(i)
        str_convert = ''.join(ret)
        if sys.version_info[0] == 3:
            import html
            text2 = html.escape(str_convert, quote=True)
        else:
            text2 = cgi.escape(str_convert, quote=True)
        return text2

    # 上传文件
    def UploadFile(self, get):
        from werkzeug.utils import secure_filename
        from BTPanel import request
        if sys.version_info[0] == 2:
            get.path = get.path.encode('utf-8')
        if not os.path.exists(get.path):
            os.makedirs(get.path)
        f = request.files['zunfile']
        filename = os.path.join(get.path, f.filename)
        if sys.version_info[0] == 2:
            filename = filename.encode('utf-8')
        s_path = get.path
        if os.path.exists(filename):
            s_path = filename
        p_stat = os.stat(s_path)
        f.save(filename)
        os.chown(filename, p_stat.st_uid, p_stat.st_gid)
        os.chmod(filename, p_stat.st_mode)
        public.WriteLog('TYPE_FILE', 'FILE_UPLOAD_SUCCESS',
                        (filename, get['path']))
        return public.returnMsg(True, 'FILE_UPLOAD_SUCCESS')

    # 上传文件2
    def upload(self, args):
        if not 'f_name' in args:
            args.f_name = request.form.get('f_name')
            args.f_path = request.form.get('f_path')
            args.f_size = request.form.get('f_size')
            args.f_start = request.form.get('f_start')

        if sys.version_info[0] == 2:
            args.f_name = args.f_name.encode('utf-8')
            args.f_path = args.f_path.encode('utf-8')

        if args.f_path == '/':
            return public.returnMsg(False,'不能直接上传文件到系统根目录!')

        if args.f_name.find('./') != -1 or args.f_path.find('./') != -1:
            return public.returnMsg(False, '错误的参数')
        if not os.path.exists(args.f_path):
            os.makedirs(args.f_path, 493)
            if not 'dir_mode' in args or not 'file_mode' in args:
                self.set_mode(args.f_path)

        save_path = os.path.join(
            args.f_path, args.f_name + '.' + str(int(args.f_size)) + '.upload.tmp')
        d_size = 0
        if os.path.exists(save_path):
            d_size = os.path.getsize(save_path)
        if d_size != int(args.f_start):
            return d_size
        f = open(save_path, 'ab')
        if 'b64_data' in args:
            import base64
            b64_data = base64.b64decode(args.b64_data)
            f.write(b64_data)
        else:
            upload_files = request.files.getlist("blob")
            for tmp_f in upload_files:
                f.write(tmp_f.read())
        f.close()
        f_size = os.path.getsize(save_path)
        if f_size != int(args.f_size):
            return f_size
        new_name = os.path.join(args.f_path, args.f_name)
        if os.path.exists(new_name):
            if new_name.find('.user.ini') != -1:
                public.ExecShell("chattr -i " + new_name)
            try:
                os.remove(new_name)
            except:
                public.ExecShell("rm -f %s" % new_name)
        os.renames(save_path, new_name)
        if 'dir_mode' in args and 'file_mode' in args:
            mode_tmp1 = args.dir_mode.split(',')
            public.set_mode(args.f_path, mode_tmp1[0])
            public.set_own(args.f_path, mode_tmp1[1])
            mode_tmp2 = args.file_mode.split(',')
            public.set_mode(new_name, mode_tmp2[0])
            public.set_own(new_name, mode_tmp2[1])

        else:
            self.set_mode(new_name)
        if new_name.find('.user.ini') != -1:
            public.ExecShell("chattr +i " + new_name)

        public.WriteLog('TYPE_FILE', 'FILE_UPLOAD_SUCCESS',
                        (args.f_name, args.f_path))
        return public.returnMsg(True, '上传成功!')

    # 设置文件和目录权限
    def set_mode(self, path):
        s_path = os.path.dirname(path)
        p_stat = os.stat(s_path)
        os.chown(path, p_stat.st_uid, p_stat.st_gid)
        os.chmod(path, p_stat.st_mode)

    # 是否包含composer.json
    def is_composer_json(self,path):
        if os.path.exists(path + '/composer.json'):
            return '1'
        return '0'

    def __check_favorite(self,filepath,favorites_info):
        for favorite in favorites_info:
            if filepath == favorite['path']:
                return '1'
        return '0'

    def __check_share(self,filename):
        my_table = 'download_token'
        result = public.M(my_table).where('filename=?',(filename,)).getField('id')
        if result:
            return str(result)
        return '0'

    # 取文件/目录列表
    def GetDir(self, get):
        if not hasattr(get, 'path'):
            # return public.returnMsg(False,'错误的参数!')
            get.path = '/www/wwwroot'
        if sys.version_info[0] == 2:
            get.path = get.path.encode('utf-8')
        if get.path == '':
            get.path = '/www'
        if not os.path.exists(get.path):
            return public.ReturnMsg(False, '指定目录不存在!')
        if get.path == '/www/Recycle_bin':
            return public.returnMsg(False, '此为回收站目录，请在右上角按【回收站】按钮打开')
        if not os.path.isdir(get.path):
            get.path = os.path.dirname(get.path)

        if not os.path.isdir(get.path):
            return public.returnMsg(False, '这不是一个目录!')

        import pwd
        dirnames = []
        filenames = []

        search = None
        if hasattr(get, 'search'):
            search = get.search.strip().lower()
        if hasattr(get, 'all'):
            return self.SearchFiles(get)

        # 包含分页类
        import page
        # 实例化分页类
        page = page.Page()
        info = {}
        info['count'] = self.GetFilesCount(get.path, search)
        info['row'] = 100
        if 'disk' in get:
            if get.disk == 'true': info['row'] = 2000
        if 'share' in get and get.share:
            info['row'] = 5000
        info['p'] = 1
        if hasattr(get, 'p'):
            try:
                info['p'] = int(get['p'])
            except:
                info['p'] = 1

        info['uri'] = {}
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs
        if hasattr(get, 'showRow'):
            info['row'] = int(get.showRow)

        # 获取分页数据
        data = {}
        data['PAGE'] = page.GetPage(info, '1,2,3,4,5,6,7,8')

        i = 0
        n = 0

        data['STORE'] = self.get_files_store(None)
        data['FILE_RECYCLE'] = os.path.exists('data/recycle_bin.pl')

        if not hasattr(get, 'reverse'):
            for filename in os.listdir(get.path):
                filename = self.xssencode(filename)

                if search:
                    if filename.lower().find(search) == -1:
                        continue
                i += 1
                if n >= page.ROW:
                    break
                if i < page.SHIFT:
                    continue

                try:
                    
                    if sys.version_info[0] == 2:
                        filename = filename.encode('utf-8')
                    else:
                        filename.encode('utf-8')
                    filePath = get.path+'/'+filename
                    link = ''
                    if os.path.islink(filePath):
                        filePath = os.readlink(filePath)
                        link = ' -> ' + filePath
                        if not os.path.exists(filePath):
                            filePath = get.path + '/' + filePath
                        if not os.path.exists(filePath):
                            continue
                    stat = os.stat(filePath)
                    accept = str(oct(stat.st_mode)[-3:])
                    mtime = str(int(stat.st_mtime))
                    user = ''
                    try:
                        user = pwd.getpwuid(stat.st_uid).pw_name
                    except:
                        user = str(stat.st_uid)
                    size = str(stat.st_size)
                    # 判断文件是否已经被收藏
                    favorite = self.__check_favorite(filePath,data['STORE'])
                    if os.path.isdir(filePath):
                        dirnames.append(filename+';'+size+';' + mtime+';'+accept+';'+user+';'+link + ';' +
                                        self.get_download_id(filePath)+';'+ self.is_composer_json(filePath)+';'
                                        +favorite+';'+self.__check_share(filePath))
                    else:
                        filenames.append(filename+';'+size+';'+mtime+';'+accept+';'+user+';'+link+';'
                                         +self.get_download_id(filePath)+';' + self.is_composer_json(filePath)+';'
                                         +favorite+';'+self.__check_share(filePath))
                    n += 1
                except:
                    continue

            data['DIR'] = sorted(dirnames)
            data['FILES'] = sorted(filenames)
        else:
            reverse = bool(get.reverse)
            if get.reverse == 'False':
                reverse = False
            for file_info in self.__list_dir(get.path, get.sort, reverse):
                filename = os.path.join(get.path, file_info[0])
                if search:
                    if file_info[0].lower().find(search) == -1:
                        continue
                i += 1
                if n >= page.ROW:
                    break
                if i < page.SHIFT:
                    continue
                if not os.path.exists(filename): continue
                file_info = self.__format_stat(filename, get.path)
                if not file_info: continue
                favorite = self.__check_favorite(filename, data['STORE'])
                r_file = file_info['name'] + ';' + str(file_info['size']) + ';' + str(file_info['mtime']) + ';' + str(
                    file_info['accept']) + ';' + file_info['user'] + ';' + file_info['link']+';'\
                         + self.get_download_id(filename) + ';' + self.is_composer_json(filename)+';'\
                         + favorite+';'+self.__check_share(filename)
                if os.path.isdir(filename):
                    dirnames.append(r_file)
                else:
                    filenames.append(r_file)
                n += 1

            data['DIR'] = dirnames
            data['FILES'] = filenames
        data['PATH'] = str(get.path)
        for i in range(len(data['DIR'])):
            data['DIR'][i] += ';' + self.get_file_ps( os.path.join(data['PATH'] , data['DIR'][i].split(';')[0]))
        
        for i in range(len(data['FILES'])):
            data['FILES'][i] += ';' + self.get_file_ps( os.path.join(data['PATH'] , data['FILES'][i].split(';')[0]))
        
        if hasattr(get, 'disk'):
            import system
            data['DISK'] = system.system().GetDiskInfo()
        return data


    def get_file_ps(self,filename):
        '''
            @name 获取文件或目录备注
            @author hwliang<2020-10-22>
            @param filename<string> 文件或目录全路径
            @return string
        '''
        ps_path = '/www/server/panel/data/files_ps'
        f_key1 = '/'.join((ps_path,public.md5(filename)))
        if os.path.exists(f_key1):
            return public.readFile(f_key1)
        
        f_key2 = '/'.join((ps_path,public.md5(os.path.basename(filename))))
        if os.path.exists(f_key2):
            return public.readFile(f_key2)
        return ''


    def set_file_ps(self,args):
        '''
            @name 设置文件或目录备注
            @author hwliang<2020-10-22>
            @param filename<string> 文件或目录全路径
            @param ps_type<int> 备注类型 0.完整路径 1.文件名称
            @param ps_body<string> 备注内容
            @return dict
        '''
        filename = args.filename.strip()
        ps_type = int(args.ps_type)
        ps_body = args.ps_body
        ps_path = '/www/server/panel/data/files_ps'
        if not os.path.exists(ps_path):
            os.makedirs(ps_path,384)
        if ps_type == 1:
            f_name = os.path.basename(filename)
        else:
            f_name = filename
        ps_key = public.md5(f_name)

        f_key = '/'.join((ps_path,ps_key))
        if ps_body:
            public.writeFile(f_key,ps_body)
            public.WriteLog('文件管理','设置文件名[{}],备注为: {}'.format(f_name,ps_body))
        else:
            if os.path.exists(f_key):os.remove(f_key)
            public.WriteLog('文件管理','清除文件备注[{}]'.format(f_name))
        return public.returnMsg(True,'设置成功')

        


    def __list_dir(self, path, my_sort='name', reverse=False):
        '''
            @name 获取文件列表，并排序
            @author hwliang<2020-08-01>
            @param path<string> 路径
            @param my_sort<string> 排序字段
            @param reverse<bool> 是否降序
            @param list
        '''
        if not os.path.exists(path):
            return []
        py_v = sys.version_info[0]
        tmp_files = []
    
        for f_name in os.listdir(path):
            try:
                if py_v == 2:
                    f_name = f_name.encode('utf-8')
                else:
                    f_name.encode('utf-8')

                #使用.join拼接效率更高
                filename = "/".join((path,f_name))
                sort_key = 1
                sort_val = None
                
                #此处直接做异常处理比先判断文件是否存在更高效
                if my_sort == 'name':
                    sort_key = 0
                elif my_sort == 'size':
                    sort_val = os.stat(filename).st_size
                elif my_sort == 'mtime':
                    sort_val =  os.stat(filename).st_mtime
                elif my_sort == 'accept':
                    sort_val = os.stat(filename).st_mode
                elif my_sort == 'user':
                    sort_val =  os.stat(filename).st_uid
            except:
                continue
            #使用list[tuple]排序效率更高
            tmp_files.append((f_name,sort_val))
            
        tmp_files = sorted(tmp_files, key=lambda x: x[sort_key], reverse=reverse)
        return tmp_files

    def __format_stat(self, filename, path):
        try:
            stat = self.__get_stat(filename, path)
            if not stat:
                return None
            tmp_stat = stat.split(';')
            file_info = {'name': self.xssencode(tmp_stat[0].replace('/', '')), 'size': int(tmp_stat[1]), 'mtime': int(
                tmp_stat[2]), 'accept': int(tmp_stat[3]), 'user': tmp_stat[4], 'link': tmp_stat[5]}
            return file_info
        except:
            return None

    def SearchFiles(self, get):
        if not hasattr(get, 'path'):
            get.path = '/www/wwwroot'
        if sys.version_info[0] == 2:
            get.path = get.path.encode('utf-8')
        if not os.path.exists(get.path):
            get.path = '/www'
        search = get.search.strip().lower()
        my_dirs = []
        my_files = []
        count = 0
        max = 3000
        for d_list in os.walk(get.path):
            if count >= max:
                break
            for d in d_list[1]:
                if count >= max:
                    break
                d = self.xssencode(d)
                if d.lower().find(search) != -1:
                    filename = d_list[0] + '/' + d
                    if not os.path.exists(filename):
                        continue
                    my_dirs.append(self.__get_stat(filename, get.path))
                    count += 1

            for f in d_list[2]:
                if count >= max:
                    break
                f = self.xssencode(f)
                if f.lower().find(search) != -1:
                    filename = d_list[0] + '/' + f
                    if not os.path.exists(filename):
                        continue
                    my_files.append(self.__get_stat(filename, get.path))
                    count += 1
        data = {}
        data['DIR'] = sorted(my_dirs)
        data['FILES'] = sorted(my_files)
        data['PATH'] = str(get.path)
        data['PAGE'] = public.get_page(
            len(my_dirs) + len(my_files), 1, max, 'GetFiles')['page']
        data['STORE'] = self.get_files_store(None)
        return data

    def __get_stat(self, filename, path=None):
        stat = os.stat(filename)
        accept = str(oct(stat.st_mode)[-3:])
        mtime = str(int(stat.st_mtime))
        user = ''
        try:
            user = pwd.getpwuid(stat.st_uid).pw_name
        except:
            user = str(stat.st_uid)
        size = str(stat.st_size)
        link = ''
        down_url = self.get_download_id(filename)
        if os.path.islink(filename):
            link = ' -> ' + os.readlink(filename)
        tmp_path = (path + '/').replace('//', '/')
        if path and tmp_path != '/':
            filename = filename.replace(tmp_path, '',1)
        favorite = self.__check_favorite(filename, self.get_files_store(None))
        return filename + ';' + size + ';' + mtime + ';' + accept + ';' + user + ';' + link+';'+ down_url+';'+ \
               self.is_composer_json(filename)+';'+favorite+';'+self.__check_share(filename)

    #获取指定目录下的所有视频或音频文件
    def get_videos(self,args):
        path = args.path.strip()
        v_data = []
        if not os.path.exists(path): return v_data
        import mimetypes
        for fname in os.listdir(path):
            try:
                filename = os.path.join(path,fname)
                if not os.path.exists(filename): continue
                if not os.path.isfile(filename): continue
                v_tmp = {}
                v_tmp['name'] = fname
                v_tmp['type'] = mimetypes.guess_type(filename)[0]
                v_tmp['size'] = os.path.getsize(filename)
                if not v_tmp['type'].split('/')[0] in ['video']:
                    continue
                v_data.append(v_tmp)
            except:continue
        return sorted(v_data,key=lambda x:x['name'])
    
    # 计算文件数量
    def GetFilesCount(self, path, search):
        if os.path.isfile(path):
            return 1
        if not os.path.exists(path):
            return 0
        i = 0
        for name in os.listdir(path):
            if search:
                if name.lower().find(search) == -1:
                    continue
            i += 1
        return i

    # 创建文件
    def CreateFile(self, get):
        if sys.version_info[0] == 2:
            get.path = get.path.encode('utf-8').strip()
        try:
            if get.path[-1] == '.':
                return public.returnMsg(False, '文件结尾不建议使用 "."，因为可能存在安全隐患')
            if not self.CheckFileName(get.path):
                return public.returnMsg(False, '文件名中不能包含特殊字符!')
            if os.path.exists(get.path):
                return public.returnMsg(False, 'FILE_EXISTS')
            path = os.path.dirname(get.path)
            if not os.path.exists(path):
                os.makedirs(path)
            open(get.path, 'w+').close()
            self.SetFileAccept(get.path)
            public.WriteLog('TYPE_FILE', 'FILE_CREATE_SUCCESS', (get.path,))
            return public.returnMsg(True, 'FILE_CREATE_SUCCESS')
        except:
            return public.returnMsg(False, 'FILE_CREATE_ERR')

    # 创建目录
    def CreateDir(self, get):
        if sys.version_info[0] == 2:
            get.path = get.path.encode('utf-8').strip()
        try:
            if get.path[-1] == '.':
                return public.returnMsg(False, '目录结尾不建议使用 "."，因为可能存在安全隐患')
            if not self.CheckFileName(get.path):
                return public.returnMsg(False, '目录名中不能包含特殊字符!')
            if os.path.exists(get.path):
                return public.returnMsg(False, 'DIR_EXISTS')
            os.makedirs(get.path)
            self.SetFileAccept(get.path)
            public.WriteLog('TYPE_FILE', 'DIR_CREATE_SUCCESS', (get.path,))
            return public.returnMsg(True, 'DIR_CREATE_SUCCESS')
        except:
            return public.returnMsg(False, 'DIR_CREATE_ERR')

    # 删除目录
    def DeleteDir(self, get):
        if sys.version_info[0] == 2:
            get.path = get.path.encode('utf-8')
        if get.path == '/www/Recycle_bin':
            return public.returnMsg(False, '不能直接操作回收站目录，请在右上角按【回收站】按钮打开')
        if not os.path.exists(get.path):
            return public.returnMsg(False, 'DIR_NOT_EXISTS')

        # 检查是否敏感目录
        if not self.CheckDir(get.path):
            return public.returnMsg(False, 'FILE_DANGER')

        try:
            # 检查是否存在.user.ini
            # if os.path.exists(get.path+'/.user.ini'):
            #    public.ExecShell("chattr -i '"+get.path+"/.user.ini'")
            public.ExecShell("chattr -R -i " + get.path)
            if hasattr(get, 'empty'):
                if not self.delete_empty(get.path):
                    return public.returnMsg(False, 'DIR_ERR_NOT_EMPTY')

            if os.path.exists('data/recycle_bin.pl') and session.get('debug') != 1:
                if self.Mv_Recycle_bin(get):
                    self.site_path_safe(get)
                    return public.returnMsg(True, 'DIR_MOVE_RECYCLE_BIN')

            import shutil
            shutil.rmtree(get.path)
            self.site_path_safe(get)
            public.WriteLog('TYPE_FILE', 'DIR_DEL_SUCCESS', (get.path,))
            return public.returnMsg(True, 'DIR_DEL_SUCCESS')
        except:
            return public.returnMsg(False, 'DIR_DEL_ERR')

    # 删除 空目录
    def delete_empty(self, path):
        if sys.version_info[0] == 2:
            path = path.encode('utf-8')
        if len(os.listdir(path)) > 0:
            return False
        return True

    # 删除文件
    def DeleteFile(self, get):
        if sys.version_info[0] == 2:
            get.path = get.path.encode('utf-8')
        if not os.path.exists(get.path):
            return public.returnMsg(False, 'FILE_NOT_EXISTS')

        # 检查是否为.user.ini
        if get.path.find('.user.ini') != -1:
            public.ExecShell("chattr -i '"+get.path+"'")
        try:
            if os.path.exists('data/recycle_bin.pl') and session.get('debug') != 1:
                if self.Mv_Recycle_bin(get):
                    self.site_path_safe(get)
                    return public.returnMsg(True, 'FILE_MOVE_RECYCLE_BIN')
            os.remove(get.path)
            self.site_path_safe(get)
            public.WriteLog('TYPE_FILE', 'FILE_DEL_SUCCESS', (get.path,))
            return public.returnMsg(True, 'FILE_DEL_SUCCESS')
        except:
            return public.returnMsg(False, 'FILE_DEL_ERR')

    # 移动到回收站
    def Mv_Recycle_bin(self, get):
        rPath = '/www/Recycle_bin/'
        if not os.path.exists(rPath):
            public.ExecShell('mkdir -p ' + rPath)
        rFile = rPath + \
            get.path.replace('/', '_bt_') + '_t_' + str(time.time())
        try:
            import shutil
            shutil.move(get.path, rFile)
            public.WriteLog('TYPE_FILE', 'FILE_MOVE_RECYCLE_BIN', (get.path,))
            return True
        except:
            public.WriteLog(
                'TYPE_FILE', 'FILE_MOVE_RECYCLE_BIN_ERR', (get.path,))
            return False

    # 从回收站恢复
    def Re_Recycle_bin(self, get):
        rPath = '/www/Recycle_bin/'
        if sys.version_info[0] == 2:
            get.path = get.path.encode('utf-8')
        dFile = get.path.replace('_bt_', '/').split('_t_')[0]
        get.path = rPath + get.path
        if dFile.find('BTDB_') != -1:
            import database
            return database.database().RecycleDB(get.path)
        try:
            import shutil
            shutil.move(get.path, dFile)
            public.WriteLog('TYPE_FILE', 'FILE_RE_RECYCLE_BIN', (dFile,))
            return public.returnMsg(True, 'FILE_RE_RECYCLE_BIN')
        except:
            public.WriteLog('TYPE_FILE', 'FILE_RE_RECYCLE_BIN_ERR', (dFile,))
            return public.returnMsg(False, 'FILE_RE_RECYCLE_BIN_ERR')

    # 获取回收站信息
    def Get_Recycle_bin(self, get):
        rPath = '/www/Recycle_bin/'
        if not os.path.exists(rPath):
            public.ExecShell('mkdir -p ' + rPath)
        data = {}
        data['dirs'] = []
        data['files'] = []
        data['status'] = os.path.exists('data/recycle_bin.pl')
        data['status_db'] = os.path.exists('data/recycle_bin_db.pl')
        for file in os.listdir(rPath):
            file = self.xssencode(file)
            try:
                tmp = {}
                fname = rPath + file
                if sys.version_info[0] == 2:
                    fname = fname.encode('utf-8')
                else:
                    fname.encode('utf-8')
                tmp1 = file.split('_bt_')
                tmp2 = tmp1[len(tmp1)-1].split('_t_')
                tmp['rname'] = file
                tmp['dname'] = file.replace('_bt_', '/').split('_t_')[0]
                tmp['name'] = tmp2[0]
                tmp['time'] = int(float(tmp2[1]))
                if os.path.islink(fname):
                    filePath = os.readlink(fname)
                    if os.path.exists(filePath):
                        tmp['size'] = os.path.getsize(filePath)
                    else:
                        tmp['size'] = 0
                else:
                    tmp['size'] = os.path.getsize(fname)
                if os.path.isdir(fname):
                    data['dirs'].append(tmp)
                else:
                    data['files'].append(tmp)
            except:
                continue
        return data

    # 彻底删除
    def Del_Recycle_bin(self, get):
        rPath = '/www/Recycle_bin/'
        if sys.version_info[0] == 2:
            get.path = get.path.encode('utf-8')
        dFile = get.path.split('_t_')[0]
        filename = rPath + get.path
        tfile = get.path.replace('_bt_', '/').split('_t_')[0]
        if not os.path.exists(filename):
            return public. returnMsg(True, 'FILE_DEL_RECYCLE_BIN', (tfile,))
        if dFile.find('BTDB_') != -1:
            import database
            return database.database().DeleteTo(filename)
        if not self.CheckDir(filename):
            return public.returnMsg(False, 'FILE_DANGER')

        public.ExecShell('chattr -R -i ' + filename)
        if os.path.isdir(filename):
            import shutil
            try:
                shutil.rmtree(filename)
            except:
                public.ExecShell("rm -rf " + filename)
        else:
            try:
                os.remove(filename)
            except:
                public.ExecShell("rm -f " + filename)
        public.WriteLog('TYPE_FILE', 'FILE_DEL_RECYCLE_BIN', (tfile,))
        return public.returnMsg(True, 'FILE_DEL_RECYCLE_BIN', (tfile,))

    # 清空回收站
    def Close_Recycle_bin(self, get):
        rPath = '/www/Recycle_bin/'
        public.ExecShell('chattr -R -i ' + rPath)
        import database
        import shutil
        rlist = os.listdir(rPath)
        i = 0
        l = len(rlist)
        for name in rlist:
            i += 1
            path = rPath + name
            public.writeSpeed(name, i, l)
            if name.find('BTDB_') != -1:
                database.database().DeleteTo(path)
                continue
            if os.path.isdir(path):
                try:
                    shutil.rmtree(path)
                except:
                    public.ExecShell('rm -rf ' + path)
            else:
                try:
                    os.remove(path)
                except:
                    public.ExecShell('rm -f ' + path)

        public.writeSpeed(None, 0, 0)
        public.WriteLog('TYPE_FILE', 'FILE_CLOSE_RECYCLE_BIN')
        return public.returnMsg(True, 'FILE_CLOSE_RECYCLE_BIN')

    # 回收站开关
    def Recycle_bin(self, get):
        c = 'data/recycle_bin.pl'
        if hasattr(get, 'db'):
            c = 'data/recycle_bin_db.pl'
        if os.path.exists(c):
            os.remove(c)
            public.WriteLog('TYPE_FILE', 'FILE_OFF_RECYCLE_BIN')
            return public.returnMsg(True, 'FILE_OFF_RECYCLE_BIN')
        else:
            public.writeFile(c, 'True')
            public.WriteLog('TYPE_FILE', 'FILE_ON_RECYCLE_BIN')
            return public.returnMsg(True, 'FILE_ON_RECYCLE_BIN')

    # 复制文件
    def CopyFile(self, get):
        if sys.version_info[0] == 2:
            get.sfile = get.sfile.encode('utf-8')
            get.dfile = get.dfile.encode('utf-8')
        if get.dfile[-1] == '.':
            return public.returnMsg(False, '文件结尾不建议使用 "."，因为可能存在安全隐患')
        if not os.path.exists(get.sfile):
            return public.returnMsg(False, 'FILE_NOT_EXISTS')

        # if os.path.exists(get.dfile):
        #    return public.returnMsg(False,'FILE_EXISTS')

        if os.path.isdir(get.sfile):
            return self.CopyDir(get)

        import shutil
        try:
            shutil.copyfile(get.sfile, get.dfile)
            public.WriteLog('TYPE_FILE', 'FILE_COPY_SUCCESS',
                            (get.sfile, get.dfile))
            stat = os.stat(get.sfile)
            os.chmod(get.dfile,stat.st_mode)
            os.chown(get.dfile, stat.st_uid, stat.st_gid)
            return public.returnMsg(True, 'FILE_COPY_SUCCESS')
        except:
            return public.returnMsg(False, 'FILE_COPY_ERR')

    # 复制文件夹
    def CopyDir(self, get):
        if sys.version_info[0] == 2:
            get.sfile = get.sfile.encode('utf-8')
            get.dfile = get.dfile.encode('utf-8')
        if get.dfile[-1] == '.':
            return public.returnMsg(False, '目录结尾不建议使用 "."，因为可能存在安全隐患')
        if not os.path.exists(get.sfile):
            return public.returnMsg(False, 'DIR_NOT_EXISTS')

        # if os.path.exists(get.dfile):
        #    return public.returnMsg(False,'DIR_EXISTS')

        # if not self.CheckDir(get.dfile):
        #    return public.returnMsg(False,'FILE_DANGER')

        try:
            self.copytree(get.sfile, get.dfile)
            stat = os.stat(get.sfile)
            os.chmod(get.dfile,stat.st_mode)
            os.chown(get.dfile, stat.st_uid, stat.st_gid)
            public.WriteLog('TYPE_FILE', 'DIR_COPY_SUCCESS',
                            (get.sfile, get.dfile))
            return public.returnMsg(True, 'DIR_COPY_SUCCESS')
        except:
            return public.returnMsg(False, 'DIR_COPY_ERR')

    # 移动文件或目录
    def MvFile(self, get):
        if sys.version_info[0] == 2:
            get.sfile = get.sfile.encode('utf-8')
            get.dfile = get.dfile.encode('utf-8')
        if get.dfile[-1] == '.':
            return public.returnMsg(False, '文件结尾不建议使用 "."，因为可能存在安全隐患')
        if not self.CheckFileName(get.dfile):
            return public.returnMsg(False, '文件名中不能包含特殊字符!')
        if get.sfile == '/www/Recycle_bin':
            return public.returnMsg(False, '不能直接操作回收站目录，请在右上角按【回收站】按钮打开')
        if not os.path.exists(get.sfile):
            return public.returnMsg(False, 'FILE_NOT_EXISTS')

        if os.path.exists(get.dfile):
            return public.returnMsg(False,'目标文件名已存在!')

        if get.dfile[-1] == '/':
            get.dfile = get.dfile[:-1]

        if get.dfile == get.sfile:
            return public.returnMsg(False, '无意义操作')

        if not self.CheckDir(get.sfile):
            return public.returnMsg(False, 'FILE_DANGER')
        try:
            self.move(get.sfile, get.dfile)
            self.site_path_safe(get)
            if hasattr(get, 'rename'):
                public.WriteLog('TYPE_FILE', '[%s]重命名为[%s]' % (get.sfile, get.dfile))
                return public.returnMsg(True, '重命名成功!')
            else:
                public.WriteLog('TYPE_FILE', 'MOVE_SUCCESS',
                                (get.sfile, get.dfile))
                return public.returnMsg(True, 'MOVE_SUCCESS')
        except:
            return public.returnMsg(False, 'MOVE_ERR')

    # 检查文件是否存在
    def CheckExistsFiles(self, get):
        if sys.version_info[0] == 2:
            get.dfile = get.dfile.encode('utf-8')
        data = []
        filesx = []
        if not hasattr(get, 'filename'):
            if not 'selected' in session:
                return []
            filesx = json.loads(session['selected']['data'])
        else:
            filesx.append(get.filename)

        for fn in filesx:
            if fn == '.':
                continue
            filename = get.dfile + '/' + fn
            if os.path.exists(filename):
                tmp = {}
                stat = os.stat(filename)
                tmp['filename'] = fn
                tmp['size'] = os.path.getsize(filename)
                tmp['mtime'] = str(int(stat.st_mtime))
                data.append(tmp)
        return data

    # 取文件扩展名
    def __get_ext(self, filename):
        tmp = filename.split('.')
        return tmp[-1]

    # 获取文件内容
    def GetFileBody(self, get):
        if sys.version_info[0] == 2:
            get.path = get.path.encode('utf-8')
        if not os.path.exists(get.path):
            if get.path.find('rewrite') == -1:
                return public.returnMsg(False, 'FILE_NOT_EXISTS', (get.path,))
            public.writeFile(get.path, '')
        if self.__get_ext(get.path) in ['gz', 'zip', 'rar', 'exe', 'db', 'pdf', 'doc', 'xls', 'docx', 'xlsx', 'ppt', 'pptx', '7z', 'bz2', 'png', 'gif', 'jpg', 'jpeg', 'bmp', 'icon', 'ico', 'pyc', 'class', 'so', 'pyd']:
            return public.returnMsg(False, '该文件格式不支持在线编辑!')
        if os.path.getsize(get.path) > 3145928:
            return public.returnMsg(False, u'不能在线编辑大于3MB的文件!')
        if os.path.isdir(get.path):
            return public.returnMsg(False, '这不是一个文件!')
        
        #处理my.cnf为空的情况
        myconf_file = '/etc/my.cnf'
        if get.path == myconf_file:
            if os.path.getsize(myconf_file) < 10:
                mycnf_file_bak = '/etc/my.cnf.bak'
                if os.path.exists(mycnf_file_bak):
                    public.writeFile(myconf_file,public.readFile(mycnf_file_bak))


        fp = open(get.path, 'rb')
        data = {}
        data['status'] = True

        try:
            if fp:
                srcBody = fp.read()
                fp.close()
                try:
                    data['encoding'] = 'utf-8'
                    data['data'] = srcBody.decode(data['encoding'])
                except:
                    try:
                        data['encoding'] = 'GBK'
                        data['data'] = srcBody.decode(data['encoding'])
                    except:
                        try:
                            data['encoding'] = 'BIG5'
                            data['data'] = srcBody.decode(data['encoding'])
                        except:
                            return public.returnMsg(False, u'文件编码不被兼容，无法正确读取文件!')
            else:
                return public.returnMsg(False, '打开文件失败，文件可能被其它进程占用!')
            if hasattr(get, 'filename'):
                get.path = get.filename
            data['historys'] = self.get_history(get.path)
            data['auto_save'] = self.get_auto_save(get.path)
            return data
        except Exception as ex:
            return public.returnMsg(False, u'文件编码不被兼容，无法正确读取文件!' + str(ex))

    # 保存文件
    def SaveFileBody(self, get):
        if not 'path' in get:
            return public.returnMsg(False, 'path参数不能为空!')
        if sys.version_info[0] == 2:
            get.path = get.path.encode('utf-8')
        if not os.path.exists(get.path):
            if get.path.find('.htaccess') == -1:
                return public.returnMsg(False, 'FILE_NOT_EXISTS')

        his_path = '/www/backup/file_history/'
        if get.path.find(his_path) != -1:
            return public.returnMsg(False, '不能直接修改历史副本!')
        try:
            if 'base64' in get:
                import base64
                get.data = base64.b64decode(get.data)
            isConf = -1
            if os.path.exists('/etc/init.d/nginx') or os.path.exists('/etc/init.d/httpd'):
                isConf = get.path.find('nginx')
                if isConf == -1:
                    isConf = get.path.find('apache')
                if isConf == -1:
                    isConf = get.path.find('rewrite')
                if isConf != -1:
                    public.ExecShell('\\cp -a '+get.path+' /tmp/backup.conf')

            data = get.data
            if data == 'undefined': return public.returnMsg(False,'错误的文件内容,请重新保存!')
            userini = False
            if get.path.find('.user.ini') != -1:
                userini = True
                public.ExecShell('chattr -i ' + get.path)

            if get.path.find('/www/server/cron') != -1:
                try:
                    import crontab
                    data = crontab.crontab().CheckScript(data)
                except:
                    pass

            if get.encoding == 'ascii':
                get.encoding = 'utf-8'
            self.save_history(get.path)
            try:
                if sys.version_info[0] == 2:
                    data = data.encode(get.encoding, errors='ignore')
                    fp = open(get.path, 'w+')
                else:
                
                    data = data.encode(get.encoding , errors='ignore').decode(get.encoding)
                    fp = open(get.path, 'w+', encoding=get.encoding)
            except:
                fp = open(get.path, 'w+')

            fp.write(data)
            fp.close()

            if isConf != -1:
                isError = public.checkWebConfig()
                if isError != True:
                    public.ExecShell('\\cp -a /tmp/backup.conf '+get.path)
                    return public.returnMsg(False, 'ERROR:<br><font style="color:red;">'+isError.replace("\n", '<br>')+'</font>')
                public.serviceReload()

            if userini:
                public.ExecShell('chattr +i ' + get.path)

            public.WriteLog('TYPE_FILE', 'FILE_SAVE_SUCCESS', (get.path,))
            return public.returnMsg(True, 'FILE_SAVE_SUCCESS')
        except Exception as ex:
            return public.returnMsg(False, 'FILE_SAVE_ERR' + str(ex))

    # 保存历史副本
    def save_history(self, filename):
        if os.path.exists('/www/server/panel/data/not_file_history.pl'):
            return True
        try:
            his_path = '/www/backup/file_history/'
            if filename.find(his_path) != -1:
                return
            save_path = (his_path + filename).replace('//', '/')
            if not os.path.exists(save_path):
                os.makedirs(save_path, 384)

            his_list = sorted(os.listdir(save_path), reverse=True)
            num = public.readFile('data/history_num.pl')
            if not num:
                num = 10
            else:
                num = int(num)
            d_num = len(his_list)
            is_write = True
            new_file_md5 = public.FileMd5(filename)
            for i in range(d_num):
                rm_file = save_path + '/' + his_list[i]
                if i == 0:  # 判断是否和上一份副本相同
                    old_file_md5 = public.FileMd5(rm_file)
                    if old_file_md5 == new_file_md5:
                        is_write = False

                if i+1 >= num:  # 删除多余的副本
                    if os.path.exists(rm_file):
                        os.remove(rm_file)
                    continue
            # 写入新的副本
            if is_write:
                public.writeFile(
                    save_path + '/' + str(int(time.time())), public.readFile(filename, 'rb'), 'wb')
        except:
            pass

    # 取历史副本
    def get_history(self, filename):
        try:
            save_path = ('/www/backup/file_history/' +
                         filename).replace('//', '/')
            if not os.path.exists(save_path):
                return []
            return sorted(os.listdir(save_path))
        except:
            return []

    # 读取指定历史副本
    def read_history(self, args):
        save_path = ('/www/backup/file_history/' +
                     args.filename).replace('//', '/')
        args.path = save_path + '/' + args.history
        return self.GetFileBody(args)

    # 恢复指定历史副本
    def re_history(self, args):
        save_path = ('/www/backup/file_history/' +
                     args.filename).replace('//', '/')
        args.path = save_path + '/' + args.history
        if not os.path.exists(args.path):
            return public.returnMsg(False, '指定历史副本不存在!')
        import shutil
        shutil.copyfile(args.path, args.filename)
        return self.GetFileBody(args)

    # 自动保存配置
    def auto_save_temp(self, args):
        save_path = '/www/backup/file_auto_save/'
        if not os.path.exists(save_path):
            os.makedirs(save_path, 384)
        filename = save_path + args.filename
        if os.path.exists(filename):
            f_md5 = public.FileMd5(filename)
            s_md5 = public.md5(args.body)
            if f_md5 == s_md5:
                return public.returnMsg(True, '未修改!')
        public.writeFile(filename, args.body)
        return public.returnMsg(True, '自动保存成功!')

    # 取上一次自动保存的结果
    def get_auto_save_body(self, args):
        save_path = '/www/backup/file_auto_save/'
        args.path = save_path + args.filename
        return self.GetFileBody(args)

    # 取自动保存结果
    def get_auto_save(self, filename):
        try:
            save_path = ('/www/backup/file_auto_save/' +
                         filename).replace('//', '/')
            if not os.path.exists(save_path):
                return None
            return os.stat(save_path).st_mtime
        except:
            return None

    # 文件压缩
    def Zip(self, get):
        if not 'z_type' in get:
            get.z_type = 'rar'
        import panelTask
        task_obj = panelTask.bt_task()
        task_obj.create_task('压缩文件', 3, get.path, json.dumps(
            {"sfile": get.sfile, "dfile": get.dfile, "z_type": get.z_type}))
        public.WriteLog("TYPE_FILE", 'ZIP_SUCCESS', (get.sfile, get.dfile))
        return public.returnMsg(True, '已将压缩任务添加到消息队列!')

    # 文件解压
    def UnZip(self, get):
        import panelTask
        if not 'password' in get:
            get.password = ''
        task_obj = panelTask.bt_task()
        task_obj.create_task('解压文件', 2, get.sfile, json.dumps(
            {"dfile": get.dfile, "password": get.password}))
        public.WriteLog("TYPE_FILE", 'UNZIP_SUCCESS', (get.sfile, get.dfile))
        return public.returnMsg(True, '已将解压任务添加到消息队列!')

    # 获取文件/目录 权限信息
    def GetFileAccess(self, get):
        if sys.version_info[0] == 2:
            get.filename = get.filename.encode('utf-8')
        data = {}
        try:
            import pwd
            stat = os.stat(get.filename)
            data['chmod'] = str(oct(stat.st_mode)[-3:])
            data['chown'] = pwd.getpwuid(stat.st_uid).pw_name
        except:
            data['chmod'] = 755
            data['chown'] = 'www'
        return data

    # 设置文件权限和所有者
    def SetFileAccess(self, get, all='-R'):
        if sys.version_info[0] == 2:
            get.filename = get.filename.encode('utf-8')
        if 'all' in get:
            if get.all == 'False':
                all = ''
        try:
            if not self.CheckDir(get.filename):
                return public.returnMsg(False, 'FILE_DANGER')
            if not os.path.exists(get.filename):
                return public.returnMsg(False, 'FILE_NOT_EXISTS')
            public.ExecShell('chmod '+all+' '+get.access+" '"+get.filename+"'")
            public.ExecShell('chown '+all+' '+get.user+':' +
                             get.user+" '"+get.filename+"'")
            public.WriteLog('TYPE_FILE', 'FILE_ACCESS_SUCCESS',
                            (get.filename, get.access, get.user))
            return public.returnMsg(True, 'SET_SUCCESS')
        except:
            return public.returnMsg(False, 'SET_ERROR')

    def SetFileAccept(self, filename):
        public.ExecShell('chown -R www:www ' + filename)
        public.ExecShell('chmod -R 755 ' + filename)

    # 取目录大小

    def GetDirSize(self, get):
        if sys.version_info[0] == 2:
            get.path = get.path.encode('utf-8')
        return public.to_size(public.get_path_size(get.path))

    # 取目录大小2
    def get_path_size(self, get):
        if sys.version_info[0] == 2:
            get.path = get.path.encode('utf-8')
        data = {}
        data['path'] = get.path
        data['size'] = public.get_path_size(get.path)
        return data

    def CloseLogs(self, get):
        get.path = public.GetConfigValue('root_path')
        public.ExecShell('rm -f '+public.GetConfigValue('logs_path')+'/*')
        if public.get_webserver() == 'nginx':
            public.ExecShell(
                'kill -USR1 `cat '+public.GetConfigValue('setup_path')+'/nginx/logs/nginx.pid`')
        else:
            public.ExecShell('/etc/init.d/httpd reload')

        public.WriteLog('TYPE_FILE', 'SITE_LOG_CLOSE')
        get.path = public.GetConfigValue('logs_path')
        return self.GetDirSize(get)

    # 批量操作
    def SetBatchData(self, get):
        if sys.version_info[0] == 2:
            get.path = get.path.encode('utf-8')
        if get.type == '1' or get.type == '2':
            session['selected'] = get
            return public.returnMsg(True, 'FILE_ALL_TIPS')
        elif get.type == '3':
            for key in json.loads(get.data):
                try:
                    if sys.version_info[0] == 2:
                        key = key.encode('utf-8')
                    filename = get.path+'/'+key
                    if not self.CheckDir(filename):
                        return public.returnMsg(False, 'FILE_DANGER')
                    ret = ' -R '
                    if 'all' in get:
                        if get.all == 'False':
                            ret = ''
                    public.ExecShell('chmod '+ret+get.access+" '"+filename+"'")
                    public.ExecShell('chown '+ret+get.user +
                                     ':'+get.user+" '"+filename+"'")
                except:
                    continue
            public.WriteLog('TYPE_FILE', 'FILE_ALL_ACCESS')
            return public.returnMsg(True, 'FILE_ALL_ACCESS')
        else:
            isRecyle = os.path.exists('data/recycle_bin.pl') and session.get('debug') != 1
            path = get.path
            get.data = json.loads(get.data)
            l = len(get.data)
            i = 0
            for key in get.data:
                try:
                    if sys.version_info[0] == 2:
                        key = key.encode('utf-8')
                    filename = path + '/'+key
                    get.path = filename
                    if not os.path.exists(filename):
                        continue
                    i += 1
                    public.writeSpeed(key, i, l)
                    if os.path.isdir(filename):
                        if not self.CheckDir(filename):
                            return public.returnMsg(False, 'FILE_DANGER')
                        public.ExecShell("chattr -R -i " + filename)
                        if isRecyle:
                            self.Mv_Recycle_bin(get)
                        else:
                            shutil.rmtree(filename)
                    else:
                        if key == '.user.ini':
                            if l > 1:
                                continue
                            public.ExecShell('chattr -i ' + filename)
                        if isRecyle:

                            self.Mv_Recycle_bin(get)
                        else:
                            os.remove(filename)
                except:
                    continue
                public.writeSpeed(None, 0, 0)
            self.site_path_safe(get)
            public.WriteLog('TYPE_FILE', 'FILE_ALL_DEL')
            return public.returnMsg(True, 'FILE_ALL_DEL')

    # 批量粘贴
    def BatchPaste(self, get):
        import shutil
        if sys.version_info[0] == 2:
            get.path = get.path.encode('utf-8')
        if not self.CheckDir(get.path):
            return public.returnMsg(False, 'FILE_DANGER')
        if not 'selected' in session:
            return public.returnMsg(False, '操作失败,请重新操作复制或剪切过程')
        i = 0
        if not 'selected' in session:
            return public.returnMsg(False, '操作失败,请重新操作')
        myfiles = json.loads(session['selected']['data'])
        l = len(myfiles)
        if get.type == '1':
            for key in myfiles:
                i += 1
                public.writeSpeed(key, i, l)
                try:
                    if sys.version_info[0] == 2:
                        sfile = session['selected']['path'] + \
                            '/' + key.encode('utf-8')
                        dfile = get.path + '/' + key.encode('utf-8')
                    else:
                        sfile = session['selected']['path'] + '/' + key
                        dfile = get.path + '/' + key

                    if os.path.isdir(sfile):
                        self.copytree(sfile, dfile)
                    else:
                        shutil.copyfile(sfile, dfile)
                    stat = os.stat(sfile)
                    os.chown(dfile, stat.st_uid, stat.st_gid)
                except:
                    continue
            public.WriteLog('TYPE_FILE', 'FILE_ALL_COPY',
                            (session['selected']['path'], get.path))
        else:
            for key in myfiles:
                try:
                    i += 1
                    public.writeSpeed(key, i, l)
                    if sys.version_info[0] == 2:
                        sfile = session['selected']['path'] + \
                            '/' + key.encode('utf-8')
                        dfile = get.path + '/' + key.encode('utf-8')
                    else:
                        sfile = session['selected']['path'] + '/' + key
                        dfile = get.path + '/' + key
                    self.move(sfile, dfile)
                except:
                    continue
            self.site_path_safe(get)
            public.WriteLog('TYPE_FILE', 'FILE_ALL_MOTE',
                            (session['selected']['path'], get.path))
        public.writeSpeed(None, 0, 0)
        errorCount = len(myfiles) - i
        del(session['selected'])
        return public.returnMsg(True, 'FILE_ALL', (str(i), str(errorCount)))

    # 移动和重命名
    def move(self, sfile, dfile):
        sfile = sfile.replace('//', '/')
        dfile = dfile.replace('//', '/')
        if sfile == dfile:
            return False
        if not os.path.exists(sfile):
            return False
        is_dir = os.path.isdir(sfile)
        if not os.path.exists(dfile) or not is_dir:
            if os.path.exists(dfile):
                os.remove(dfile)
            shutil.move(sfile, dfile)
        else:
            self.copytree(sfile, dfile)
            if os.path.exists(sfile) and os.path.exists(dfile):
                if is_dir:
                    shutil.rmtree(sfile)
                else:
                    os.remove(sfile)
        return True


    #创建软链
    def create_link(self,args):
        pass

    # 复制目录
    def copytree(self, sfile, dfile):
        if sfile == dfile:
            return False
        if not os.path.exists(dfile):
            os.makedirs(dfile)
        for f_name in os.listdir(sfile):
            src_filename = (sfile + '/' + f_name).replace('//', '/')
            dst_filename = (dfile + '/' + f_name).replace('//', '/')
            mode_info = public.get_mode_and_user(src_filename)
            if os.path.isdir(src_filename):
                if not os.path.exists(dst_filename):
                    os.makedirs(dst_filename)
                    public.set_mode(dst_filename, mode_info['mode'])
                    public.set_own(dst_filename, mode_info['user'])
                self.copytree(src_filename, dst_filename)
            else:
                try:
                    shutil.copy2(src_filename, dst_filename)
                    public.set_mode(dst_filename, mode_info['mode'])
                    public.set_own(dst_filename, mode_info['user'])
                except:
                    pass
        return True

    # 下载文件

    def DownloadFile(self, get):
        import panelTask
        task_obj = panelTask.bt_task()
        task_obj.create_task('下载文件', 1, get.url, get.path + '/' + get.filename)
        #if sys.version_info[0] == 2: get.path = get.path.encode('utf-8')
        #import db,time
        #isTask = '/tmp/panelTask.pl'
        #execstr = get.url +'|bt|'+get.path+'/'+get.filename
        #sql = db.Sql()
        #sql.table('tasks').add('name,type,status,addtime,execstr',('下载文件['+get.filename+']','download','0',time.strftime('%Y-%m-%d %H:%M:%S'),execstr))
        # public.writeFile(isTask,'True')
        # self.SetFileAccept(get.path+'/'+get.filename)
        public.WriteLog('TYPE_FILE', 'FILE_DOWNLOAD', (get.url, get.path))
        return public.returnMsg(True, 'FILE_DOANLOAD')

    # 添加安装任务
    def InstallSoft(self, get):
        import db
        import time
        path = public.GetConfigValue('setup_path') + '/php'
        if not os.path.exists(path):
            public.ExecShell("mkdir -p " + path)
        if session['server_os']['x'] != 'RHEL':
            get.type = '3'
        apacheVersion = 'false'
        if public.get_webserver() == 'apache':
            apacheVersion = public.readFile(
                public.GetConfigValue('setup_path')+'/apache/version.pl')
        public.writeFile('/var/bt_apacheVersion.pl', apacheVersion)
        public.writeFile('/var/bt_setupPath.conf',
                         public.GetConfigValue('root_path'))
        isTask = '/tmp/panelTask.pl'
        execstr = "cd " + public.GetConfigValue('setup_path') + "/panel/install && /bin/bash install_soft.sh " + \
            get.type + " install " + get.name + " " + get.version
        if public.get_webserver() == "openlitespeed":
            execstr = "cd " + public.GetConfigValue('setup_path') + "/panel/install && /bin/bash install_soft.sh " + \
                      get.type + " install " + get.name + "-ols " + get.version
        sql = db.Sql()
        if hasattr(get, 'id'):
            id = get.id
        else:
            id = None
        sql.table('tasks').add('id,name,type,status,addtime,execstr', (None,
                                                                       '安装['+get.name+'-'+get.version+']', 'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), execstr))
        public.writeFile(isTask, 'True')
        public.WriteLog('TYPE_SETUP', 'PLUGIN_ADD', (get.name, get.version))
        time.sleep(0.1)
        return public.returnMsg(True, 'PLUGIN_ADD')

    # 删除任务队列
    def RemoveTask(self, get):
        try:
            name = public.M('tasks').where('id=?', (get.id,)).getField('name')
            status = public.M('tasks').where(
                'id=?', (get.id,)).getField('status')
            public.M('tasks').delete(get.id)
            if status == '-1':
                public.ExecShell(
                    "kill `ps -ef |grep 'python panelSafe.pyc'|grep -v grep|grep -v panelExec|awk '{print $2}'`")
                public.ExecShell(
                    "kill `ps -ef |grep 'install_soft.sh'|grep -v grep|grep -v panelExec|awk '{print $2}'`")
                public.ExecShell(
                    "kill `ps aux | grep 'python task.pyc$'|awk '{print $2}'`")
                public.ExecShell('''
pids=`ps aux | grep 'sh'|grep -v grep|grep install|awk '{print $2}'`
arr=($pids)

for p in ${arr[@]}
do
    kill -9 $p
done
            ''')

                public.ExecShell(
                    'rm -f ' + name.replace('扫描目录[', '').replace(']', '') + '/scan.pl')
                isTask = '/tmp/panelTask.pl'
                public.writeFile(isTask, 'True')
                public.ExecShell('/etc/init.d/bt start')
        except:
            public.ExecShell('/etc/init.d/bt start')
        return public.returnMsg(True, 'PLUGIN_DEL')

    # 重新激活任务
    def ActionTask(self, get):
        isTask = '/tmp/panelTask.pl'
        public.writeFile(isTask, 'True')
        return public.returnMsg(True, 'PLUGIN_ACTION')

    # 卸载软件
    def UninstallSoft(self, get):
        public.writeFile('/var/bt_setupPath.conf',
                         public.GetConfigValue('root_path'))
        get.type = '0'
        if session['server_os']['x'] != 'RHEL':
            get.type = '3'
        if public.get_webserver() == "openlitespeed":
            default_ext = ["bz2","calendar","sysvmsg","exif","imap","readline","sysvshm","xsl"]
            if get.version == "73":
                default_ext.append("opcache")
            if not os.path.exists("/etc/redhat-release"):
                default_ext.append("gmp")
                default_ext.append("opcache")
            if get.name.lower() in default_ext:
                return public.returnMsg(False, "这是OpenLiteSpeed的默认扩展不可以卸载")
        execstr = "cd " + public.GetConfigValue('setup_path') + "/panel/install && /bin/bash install_soft.sh " + \
            get.type+" uninstall " + get.name.lower() + " " + get.version.replace('.', '')
        if public.get_webserver() == "openlitespeed":
            execstr = "cd " + public.GetConfigValue('setup_path') + "/panel/install && /bin/bash install_soft.sh " + \
                      get.type + " uninstall " + get.name.lower() + "-ols " + get.version.replace('.', '')
        public.ExecShell(execstr)
        public.WriteLog('TYPE_SETUP', 'PLUGIN_UNINSTALL',
                        (get.name, get.version))
        return public.returnMsg(True, "PLUGIN_UNINSTALL")

    # 取任务队列进度
    def GetTaskSpeed(self, get):
        tempFile = '/tmp/panelExec.log'
        #freshFile = '/tmp/panelFresh'
        import db
        find = db.Sql().table('tasks').where('status=? OR status=?',
                                             ('-1', '0')).field('id,type,name,execstr').find()
        if(type(find) == str):
            return public.returnMsg(False, "查询发生错误，"+find)
        if not len(find):
            return public.returnMsg(False, '当前没有任务队列在执行-2!')
        isTask = '/tmp/panelTask.pl'
        public.writeFile(isTask, 'True')
        echoMsg = {}
        echoMsg['name'] = find['name']
        echoMsg['execstr'] = find['execstr']
        if find['type'] == 'download':
            try:
                tmp = public.readFile(tempFile)
                if len(tmp) < 10:
                    return public.returnMsg(False, '当前没有任务队列在执行-3!')
                echoMsg['msg'] = json.loads(tmp)
                echoMsg['isDownload'] = True
            except:
                db.Sql().table('tasks').where(
                    "id=?", (find['id'],)).save('status', ('0',))
                return public.returnMsg(False, '当前没有任务队列在执行-4!')
        else:
            echoMsg['msg'] = self.GetLastLine(tempFile, 20)
            echoMsg['isDownload'] = False

        echoMsg['task'] = public.M('tasks').where("status!=?", ('1',)).field(
            'id,status,name,type').order("id asc").select()
        return echoMsg

    # 取执行日志
    def GetExecLog(self, get):
        return self.GetLastLine('/tmp/panelExec.log', 100)

    # 读文件指定倒数行数
    def GetLastLine(self, inputfile, lineNum):
        result = public.GetNumLines(inputfile, lineNum)
        if len(result) < 1:
            return public.getMsg('TASK_SLEEP')
        return result

    # 执行SHELL命令
    def ExecShell(self, get):
        disabled = ['vi', 'vim', 'top', 'passwd', 'su']
        get.shell = get.shell.strip()
        tmp = get.shell.split(' ')
        if tmp[0] in disabled:
            return public.returnMsg(False, 'FILE_SHELL_ERR', (tmp[0],))
        shellStr = '''#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
cd %s
%s
''' % (get.path, get.shell)
        public.writeFile('/tmp/panelShell.sh', shellStr)
        public.ExecShell(
            'nohup bash /tmp/panelShell.sh > /tmp/panelShell.pl 2>&1 &')
        return public.returnMsg(True, 'FILE_SHELL_EXEC')

    # 取SHELL执行结果
    def GetExecShellMsg(self, get):
        fileName = '/tmp/panelShell.pl'
        if not os.path.exists(fileName):
            return 'FILE_SHELL_EMPTY'
        status = not public.process_exists('bash', None, '/tmp/panelShell.sh')
        return public.returnMsg(status, public.GetNumLines(fileName, 200))

    # 文件搜索
    def GetSearch(self, get):
        if not os.path.exists(get.path):
            return public.returnMsg(False, 'DIR_NOT_EXISTS')
        return public.ExecShell("find "+get.path+" -name '*"+get.search+"*'")

    # 保存草稿
    def SaveTmpFile(self, get):
        save_path = '/www/server/panel/temp'
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        get.path = os.path.join(save_path, public.Md5(get.path) + '.tmp')
        public.writeFile(get.path, get.body)
        return public.returnMsg(True, '已保存')

    # 获取草稿
    def GetTmpFile(self, get):
        self.CleanOldTmpFile()
        save_path = '/www/server/panel/temp'
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        src_path = get.path
        get.path = os.path.join(save_path, public.Md5(get.path) + '.tmp')
        if not os.path.exists(get.path):
            return public.returnMsg(False, '没有可用的草稿!')
        data = self.GetFileInfo(get.path)
        data['file'] = src_path
        if 'rebody' in get:
            data['body'] = public.readFile(get.path)
        return data

    # 清除过期草稿
    def CleanOldTmpFile(self):
        if 'clean_tmp_file' in session:
            return True
        save_path = '/www/server/panel/temp'
        max_time = 86400 * 30
        now_time = time.time()
        for tmpFile in os.listdir(save_path):
            filename = os.path.join(save_path, tmpFile)
            fileInfo = self.GetFileInfo(filename)
            if now_time - fileInfo['modify_time'] > max_time:
                os.remove(filename)
        session['clean_tmp_file'] = True
        return True

    # 取指定文件信息
    def GetFileInfo(self, path):
        if not os.path.exists(path):
            return False
        stat = os.stat(path)
        fileInfo = {}
        fileInfo['modify_time'] = int(stat.st_mtime)
        fileInfo['size'] = os.path.getsize(path)
        return fileInfo

    # 安装rar组件
    def install_rar(self, get):
        unrar_file = '/www/server/rar/unrar'
        rar_file = '/www/server/rar/rar'
        bin_unrar = '/usr/local/bin/unrar'
        bin_rar = '/usr/local/bin/rar'
        if os.path.exists(unrar_file) and os.path.exists(bin_unrar):
            try:
                import rarfile
            except:
                public.ExecShell("pip install rarfile")
            return True

        import platform
        os_bit = ''
        if platform.machine() == 'x86_64':
            os_bit = '-x64'
        download_url = public.get_url() + '/src/rarlinux'+os_bit+'-5.6.1.tar.gz'

        tmp_file = '/tmp/bt_rar.tar.gz'
        public.ExecShell('wget -O ' + tmp_file + ' ' + download_url)
        if os.path.exists(unrar_file):
            public.ExecShell("rm -rf /www/server/rar")
        public.ExecShell("tar xvf " + tmp_file + ' -C /www/server/')
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
        if not os.path.exists(unrar_file):
            return False

        if os.path.exists(bin_unrar):
            os.remove(bin_unrar)
        if os.path.exists(bin_rar):
            os.remove(bin_rar)

        public.ExecShell('ln -sf ' + unrar_file + ' ' + bin_unrar)
        public.ExecShell('ln -sf ' + rar_file + ' ' + bin_rar)
        public.ExecShell("pip install rarfile")
        # public.writeFile('data/restart.pl','True')
        return True

    def get_store_data(self):
        data = []
        path = 'data/file_store.json'
        try:
            if os.path.exists(path):
                data = json.loads(public.readFile(path))
        except:
            data = []
        if type(data) == dict:
            result = []
            for key in data:
                for path in data[key]:
                    result.append(path)
            self.set_store_data(result)
            return result
        return data

    def set_store_data(self, data):
        public.writeFile('data/file_store.json', json.dumps(data))
        return True

    # 获取收藏夹
    def get_files_store(self, get):
        data = self.get_store_data()
        result = []
        for path in data:
            if type(path) == dict:
                path = path['path']
            info = {'path': path, 'name': os.path.basename(path)}
            if os.path.isdir(path):
                info['type'] = 'dir'
            else:
                info['type'] = 'file'
            result.append(info)
        return result

    # 添加收藏夹
    def add_files_store(self, get):
        path = get.path
        if not os.path.exists(path):
            return public.returnMsg(False, '文件或目录不存在!')
        data = self.get_store_data()
        if path in data:
            return public.returnMsg(False, '请勿重复添加!')
        data.append(path)
        self.set_store_data(data)
        return public.returnMsg(True, '添加成功!')

    # 删除收藏夹
    def del_files_store(self, get):
        path = get.path
        data = self.get_store_data()
        if not path in data:
            is_go = False
            for info in data:
                if type(info) == dict:
                    if info['path'] == path:
                        path = info
                        is_go = True
                        break
            if not is_go:
                return public.returnMsg(False, '找不到此收藏对象!')

        data.remove(path)
        if len(data) <= 0:
            data = []
        self.set_store_data(data)
        return public.returnMsg(True, '删除成功!')
        
        
    #单文件木马扫描
    def file_webshell_check(self,get):
        if not 'filename' in get: return public.returnMsg(True, '文件不存在!')
        import webshell_check
        if webshell_check.webshell_check().upload_file_url(get.filename.strip()):
            return public.returnMsg(False,'警告 %s文件为webshell'%get.filename.strip().split('/')[-1])
        else:
            return public.returnMsg(True, '无风险')

    #目录扫描木马
    def dir_webshell_check(self,get):
        if not 'path' in get: return public.returnMsg(False, '请输入有效目录!')
        path=get.path.strip()
        if os.path.exists(path):
            #启动消息队列
            exec_shell = public.get_python_bin() + ' /www/server/panel/class/webshell_check.py dir %s mail'%path
            task_name = "扫描目录%s 的木马文件"%path
            import panelTask
            task_obj = panelTask.bt_task()
            task_obj.create_task(task_name, 0, exec_shell)
            return public.returnMsg(True, '正在启动木马查杀进程。详细信息会在面板安全日志中')

    #获取下载地址列表
    def get_download_url_list(self,get):
        my_table = 'download_token'
        count = public.M(my_table).count()
        
        if not 'p' in get:
            get.p = 1
        if not 'collback' in get:
            get.collback = ''
        data = public.get_page(count,int(get.p),12, get.collback)
        data['data'] = public.M(my_table).order('id desc').field('id,filename,token,expire,ps,total,password,addtime').limit(data['shift'] +','+ data['row']).select()
        return data
    #获取短列表
    def get_download_list(self):
        if self.download_list: return self.download_list
        my_table = 'download_token'
        data = public.M(my_table).field('id,filename,expire').select()
        self.download_list = data
        return data

    #获取id
    def get_download_id(self,filename):
        download_list = self.get_download_list()
        my_table = 'download_token'
        m_time = time.time()
        result = '0'
        for d in download_list:
            if filename == d['filename']:
                result = str(d['id'])
                break

            #清理过期和无效
            if self.download_is_rm: continue
            if not os.path.exists(d['filename']) or m_time > d['expire']:
                public.M(my_table).where('id=?',(d['id'],)).delete()
        #标记清理
        if not self.download_is_rm: 
            self.download_is_rm = True
        return result

    #获取指定下载地址
    def get_download_url_find(self,get):
        if not 'id' in get: return public.returnMsg(False,'错误的参数!')
        id = int(get.id)
        my_table = 'download_token'
        data = public.M(my_table).where('id=?',(id,)).find()
        if not data: return public.returnMsg(False,'指定地址不存在!')
        return data

    #删除下载地址
    def remove_download_url(self,get):
        if not 'id' in get: return public.returnMsg(False,'错误的参数!')
        id = int(get.id)
        my_table = 'download_token'
        public.M(my_table).where('id=?',(id,)).delete()
        return public.returnMsg(True,'删除成功!')

    #修改下载地址
    def modify_download_url(self,get):
        if not 'id' in get: return public.returnMsg(False,'错误的参数!')
        id = int(get.id)
        my_table = 'download_token'
        if not public.M(my_table).where('id=?',(id,)).count():
            return public.returnMsg(False,'指定地址不存在!')
        pdata = {}
        if 'expire' in get: pdata['expire'] = get.expire
        if 'password' in get: pdata['password'] = get.password
        if 'ps' in get: pdata['ps'] = get.ps
        public.M(my_table).where('id=?',(id,)).update(pdata)
        return public.returnMsg(True,'修改成功!')


    #生成下载地址
    def create_download_url(self,get):
        if not os.path.exists(get.filename):
            return public.returnMsg(False,'指定文件不存在!')
        my_table = 'download_token'
        mtime = int(time.time())
        pdata = {
            "filename": get.filename,               #文件名
            "token": public.GetRandomString(12),    #12位随机密钥，用于URL
            "expire": mtime + (int(get.expire) * 3600), #过期时间
            "ps":get.ps, #备注
            "total":0,  #下载计数
            "password":str(get.password), #提取密码
            "addtime": mtime #添加时间
        }
        if len(pdata['password']) < 4 and len(pdata['password']) > 0:
            return public.returnMsg(False,'提取密码长度不能小于4位')
        #更新 or 插入
        token = public.M(my_table).where('filename=?',(get.filename,)).getField('token')
        if token:
            return public.returnMsg(False,'已经分享过了!')
            #pdata['token'] = token
            #del(pdata['total'])
            #public.M(my_table).where('token=?',(token,)).update(pdata)
        else:
            id = public.M(my_table).insert(pdata)
            pdata['id'] = id

        return public.returnMsg(True,pdata)


    #取PHP-CLI执行命令
    def __get_php_bin(self,php_version=None):
        php_vs = ["80","74","73","72","71","70","56","55","54","53","52"]
        if php_version:
            if php_version != 'auto':
                if not php_version in php_vs: return False
            else:
                php_version = None
        
        #判段兼容的PHP版本是否安装
        php_path = "/www/server/php/"
        php_v = None
        for pv in php_vs:
            if php_version:
                if php_version != pv: continue
            php_bin = php_path + pv + "/bin/php"
            if os.path.exists(php_bin): 
                php_v = pv
                break
        #如果没安装直接返回False
        if not php_v: return False
        #处理PHP-CLI-INI配置文件
        php_ini = '/tmp/composer_php_cli_'+php_v+'.ini'
        if not os.path.exists(php_ini):
            #如果不存在，则从PHP安装目录下复制一份
            src_php_ini = php_path + php_v + '/etc/php.ini'
            import shutil
            shutil.copy(src_php_ini,php_ini)
            #解除所有禁用函数
            php_ini_body = public.readFile(php_ini)
            php_ini_body = re.sub(r"disable_functions\s*=.*","disable_functions = ",php_ini_body)
            public.writeFile(php_ini,php_ini_body)
        return php_path + php_v + '/bin/php -c ' + php_ini


    # 执行git
    def exec_git(self,get):
        if get.git_action == 'option':
            public.ExecShell("nohup {} &> /tmp/panelExec.pl &".format(get.giturl))
        else:
            public.ExecShell("nohup git clone {} &> /tmp/panelExec.pl &".format(get.giturl))
        return public.returnMsg(True,'命令已发送!')

    # 安装composer
    def get_composer_bin(self):
        composer_bin = '/usr/bin/composer'
        if not os.path.exists(composer_bin): 
            public.ExecShell('wget -O {} {}/install/src/composer.phper -T 5'.format(composer_bin,public.get_url()))
        public.ExecShell('chmod +x {}'.format(composer_bin))
        if not os.path.exists(composer_bin): 
            return False
        return composer_bin

    # 执行composer
    def exec_composer(self,get):
        #准备执行环境
        composer_bin = self.get_composer_bin()
        if not composer_bin: 
            return public.returnMsg(False,'没有找到可用的composer!')

        #取执行PHP版本
        php_version = None
        if 'php_version' in get:
            php_version = get.php_version
        php_bin = self.__get_php_bin(php_version)
        if not php_bin: 
            return public.returnMsg(False,'没有找到可用的PHP版本，或指定PHP版本未安装!')
        if not os.path.exists(get.path + '/composer.json'): 
            return public.returnMsg(False,'指定目录中没有找到composer.json配置文件!')
        #设置指定源
        if 'repo' in get:
            if get.repo != 'repos.packagist':
                public.ExecShell('{} {} config -g repo.packagist composer {}'.format(php_bin,composer_bin,get.repo))
            else:
                public.ExecShell('{} {} config -g --unset repos.packagist'.format(php_bin,composer_bin))
        #执行composer命令
        composer_exec_str = '{} {} {} -vvv'.format(php_bin,composer_bin,get.composer_args)
        public.ExecShell("cd {} && nohup {} &> /tmp/panelExec.pl &".format(get.path,composer_exec_str))
        public.WriteLog('Composer',composer_exec_str)
        return public.returnMsg(True,'命令已发送!')

    # 取composer版本
    def get_composer_version(self,get):
        composer_bin = self.get_composer_bin()
        if not composer_bin: 
            return public.returnMsg(False,'没有找到可用的composer!')
        
        try:
            bs = str(public.readFile(composer_bin,'rb'))
            result = re.findall(r"const VERSION\s*=\s*.{0,2}'([\d\.]+)",bs)[0]
        except:
            php_bin = self.__get_php_bin()
            composer_exec_str = php_bin + ' ' + composer_bin +' --version 2>/dev/null|grep \'Composer version\'|awk \'{print $3}\''
            result = public.ExecShell(composer_exec_str)[0].strip()
        data = public.returnMsg(True,result)
        import panelSite
        data['php_versions'] = panelSite.panelSite().GetPHPVersion(get)
        return data

    # 升级composer版本
    def update_composer(self,get):
        composer_bin = self.get_composer_bin()
        if not composer_bin: 
            return public.returnMsg(False,'没有找到可用的composer!')
        php_bin = self.__get_php_bin()

        #设置指定源
        if 'repo' in get:
            if get.repo:
                public.ExecShell('{} {} config -g repo.packagist composer {}'.format(php_bin,composer_bin,get.repo))

        version1 = self.get_composer_version(get)['msg']
        composer_exec_str = '{} {} self-update -vvv'.format(php_bin,composer_bin)
        public.ExecShell(composer_exec_str)[0]
        version2 = self.get_composer_version(get)['msg']
        if version1 == version2:
            msg = "当前已经是最新版本，无需升级!"
        else:
            msg = "升级composer从{}到{}".format(version1,version2)
            public.WriteLog('Composer',msg)
        return public.returnMsg(True,msg)

        

