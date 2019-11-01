#!/usr/bin/env python
#coding:utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------
import sys,os,public,time,json,pwd,cgi,shutil,re
from BTPanel import session,request
class files:
    run_path = None
    #检查敏感目录
    def CheckDir(self,path):
        path = path.replace('//','/');
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

    #网站文件操作前置检测
    def site_path_check(self,get):
        try:
            if not 'site_id' in get: return True
            if not self.run_path:
                self.run_path,self.path,self.site_name = self.GetSiteRunPath(get.site_id)
            if 'path' in get:
                if get.path.find(self.path) != 0: return False
            if 'sfile' in get:
                if get.sfile.find(self.path) != 0: return False
            if 'dfile' in get:
                if get.dfile.find(self.path) != 0: return False
            return True
        except: return True

    #网站目录后续安全处理
    def site_path_safe(self,get):
        try:
            if not 'site_id' in get: return True
            run_path,path,site_name = self.GetSiteRunPath(get.site_id)
            if not os.path.exists(run_path): os.makedirs(run_path)
            ini_path = run_path + '/.user.ini'
            if os.path.exists(ini_path): return True
            sess_path = '/www/php_session/%s' % site_name
            if not os.path.exists(sess_path): os.makedirs(sess_path)
            ini_conf = '''open_basedir={}/:/tmp/:/proc/:{}/
session.save_path={}/
session.save_handler = files'''.format(path,sess_path,sess_path)
            public.writeFile(ini_path, ini_conf)
            public.ExecShell("chmod 644 %s" % ini_path)
            public.ExecShell("chdir +i %s" % ini_path)
            return True
        except: return False


    #取当站点前运行目录
    def GetSiteRunPath(self,site_id):
        try:
            find = public.M('sites').where('id=?',(site_id,)).field('path,name').find();
            siteName = find['name']
            sitePath = find['path']
            if public.get_webserver() == 'nginx':
                filename = '/www/server/panel/vhost/nginx/' + siteName + '.conf'
                if os.path.exists(filename):
                    conf = public.readFile(filename)
                    rep = '\s*root\s*(.+);'
                    tmp1 = re.search(rep,conf)
                    if tmp1: path = tmp1.groups()[0];
            else:
                filename = '/www/server/panel/vhost/apache/' + siteName + '.conf'
                if os.path.exists(filename):
                    conf = public.readFile(filename)
                    rep = '\s*DocumentRoot\s*"(.+)"\s*\n'
                    tmp1 = re.search(rep,conf)
                    if tmp1: path = tmp1.groups()[0];
            return path,sitePath,siteName
        except:
            return sitePath,sitePath,siteName
    
    #检测文件名
    def CheckFileName(self,filename):
        nots = ['\\','&','*','|',';','"',"'",'<','>']
        if filename.find('/') != -1: filename = filename.split('/')[-1]
        for n in nots:
            if n in filename: return False
        return True

    #名称输出过滤
    def xssencode(self,text):
        list=['<','>']
        ret=[]
        for i in text:
            if i in list:
                i=''
            ret.append(i)
        str_convert = ''.join(ret)
        text2=cgi.escape(str_convert, quote=True)
        return text2
    
    #上传文件
    def UploadFile(self,get):
        from werkzeug.utils import secure_filename
        from flask import request
        if sys.version_info[0] == 2: get.path = get.path.encode('utf-8');
        if not os.path.exists(get.path): os.makedirs(get.path)
        f = request.files['zunfile']
        filename = os.path.join(get.path, f.filename)
        if sys.version_info[0] == 2: filename = filename.encode('utf-8');
        s_path = get.path
        if os.path.exists(filename):s_path = filename
        p_stat = os.stat(s_path)
        f.save(filename)
        os.chown(filename,p_stat.st_uid,p_stat.st_gid)
        os.chmod(filename,p_stat.st_mode)
        public.WriteLog('TYPE_FILE','FILE_UPLOAD_SUCCESS',(filename,get['path']));
        return public.returnMsg(True,'FILE_UPLOAD_SUCCESS');

    #上传文件2
    def upload(self,args):
        if not 'f_name' in args:
            args.f_name = request.form.get('f_name')
            args.f_path = request.form.get('f_path')
            args.f_size = request.form.get('f_size')
            args.f_start = request.form.get('f_start')

        if sys.version_info[0] == 2: 
            args.f_name = args.f_name.encode('utf-8')
            args.f_path = args.f_path.encode('utf-8')

        if args.f_name.find('./') != -1 or args.f_path.find('./') != -1: 
            return public.returnMsg(False,'错误的参数')
        if not os.path.exists(args.f_path): 
            os.makedirs(args.f_path,493)
            if not 'dir_mode' in args or not 'file_mode' in args:
                self.set_mode(args.f_path)

        save_path =  os.path.join(args.f_path,args.f_name + '.' + str(int(args.f_size)) + '.upload.tmp')
        d_size = 0
        if os.path.exists(save_path): d_size = os.path.getsize(save_path)
        if d_size != int(args.f_start): return d_size
        upload_files = request.files.getlist("blob")
        f = open(save_path,'ab')
        for tmp_f in upload_files:
            f.write(tmp_f.read())
        f.close()
        f_size = os.path.getsize(save_path)
        if f_size != int(args.f_size):  return f_size
        new_name = os.path.join(args.f_path ,args.f_name)
        if os.path.exists(new_name): 
            if new_name.find('.user.ini') != -1:
                public.ExecShell("chattr -i " + new_name)
            try:
                os.remove(new_name)
            except:
                os.system("rm -f %s" % new_name)
        os.renames(save_path, new_name)
        if 'dir_mode' in args and 'file_mode' in args:
            mode_tmp1 = args.dir_mode.split(',')
            public.set_mode(args.f_path,mode_tmp1[0])
            public.set_own(args.f_path,mode_tmp1[1])
            mode_tmp2 = args.file_mode.split(',')
            public.set_mode(new_name,mode_tmp2[0])
            public.set_own(new_name,mode_tmp2[1])

        else:
            self.set_mode(new_name)
        if new_name.find('.user.ini') != -1:
                public.ExecShell("chattr +i " + new_name)
        
        public.WriteLog('TYPE_FILE','FILE_UPLOAD_SUCCESS',(args.f_name,args.f_path));
        return public.returnMsg(True,'上传成功!')

    #设置文件和目录权限
    def set_mode(self,path):
        s_path = os.path.dirname(path)
        p_stat = os.stat(s_path)
        os.chown(path,p_stat.st_uid,p_stat.st_gid)
        os.chmod(path,p_stat.st_mode)
        
        
    #取文件/目录列表
    def GetDir(self,get):
        if not hasattr(get,'path'): 
            #return public.returnMsg(False,'错误的参数!')
            get.path = '/www/wwwroot'
        if sys.version_info[0] == 2: get.path = get.path.encode('utf-8');
        if get.path == '': get.path = '/www';
        if not os.path.exists(get.path): 
            return public.ReturnMsg(False,'指定目录不存在!')
        if not os.path.isdir(get.path):
            get.path = os.path.dirname(get.path)

        if not os.path.isdir(get.path): return public.returnMsg(False,'这不是一个目录!')
            
        import pwd 
        dirnames = []
        filenames = []
        
        search = None
        if hasattr(get,'search'): search = get.search.strip().lower();
        if hasattr(get,'all'): return self.SearchFiles(get)
        
        #包含分页类
        import page
        #实例化分页类
        page = page.Page();
        info = {}
        info['count'] = self.GetFilesCount(get.path,search);
        info['row']   = 100
        info['p'] = 1
        if hasattr(get,'p'):
            try:
                info['p']     = int(get['p'])
            except:
                info['p'] = 1

        info['uri']   = {}
        info['return_js'] = ''
        if hasattr(get,'tojs'):
            info['return_js']   = get.tojs
        if hasattr(get,'showRow'):
            info['row'] = int(get.showRow);
        
        #获取分页数据
        data = {}
        data['PAGE'] = page.GetPage(info,'1,2,3,4,5,6,7,8')
        
        i = 0;
        n = 0;

        if not hasattr(get,'reverse'):
            for filename in os.listdir(get.path):
                filename = self.xssencode(filename)



                if search:
                    if filename.lower().find(search) == -1: continue;
                i += 1;
                if n >= page.ROW: break;
                if i < page.SHIFT: continue;
            
                try:
                    if sys.version_info[0] == 2: filename = filename.encode('utf-8');
                    filePath = get.path+'/'+filename
                    link = '';
                    if os.path.islink(filePath): 
                        filePath = os.readlink(filePath);
                        link = ' -> ' + filePath;
                        if not os.path.exists(filePath): filePath = get.path + '/' + filePath;
                        if not os.path.exists(filePath): continue;
                
                    stat = os.stat(filePath)
                    accept = str(oct(stat.st_mode)[-3:]);
                    mtime = str(int(stat.st_mtime))
                    user = ''
                    try:
                        user = pwd.getpwuid(stat.st_uid).pw_name
                    except:
                        user = str(stat.st_uid)
                    size = str(stat.st_size)
                    if os.path.isdir(filePath):
                        dirnames.append(filename+';'+size+';'+mtime+';'+accept+';'+user+';'+link);
                    else:
                        filenames.append(filename+';'+size+';'+mtime+';'+accept+';'+user+';'+link);
                    n += 1;
                except:
                    continue;
        
        
            data['DIR'] = sorted(dirnames);
            data['FILES'] = sorted(filenames);
        else:
            reverse = bool(get.reverse)
            if get.reverse == 'False': reverse = False
            for file_info in  self.__list_dir(get.path,get.sort,reverse):
                filename = os.path.join(get.path,file_info['name'])
                if not os.path.exists(filename): continue
                if search:
                    if file_info['name'].lower().find(search) == -1: continue;
                i += 1;
                if n >= page.ROW: break;
                if i < page.SHIFT: continue;

                r_file = file_info['name'] + ';' + str(file_info['size']) + ';' + str(file_info['mtime']) + ';' + str(file_info['accept']) + ';' + file_info['user']+ ';' + file_info['link']
                if os.path.isdir(filename):
                    dirnames.append(r_file)
                else:
                    filenames.append(r_file)
                n += 1;

            data['DIR'] = dirnames
            data['FILES'] = filenames

        data['PATH'] = str(get.path)
        data['STORE'] = self.get_files_store(None)
        if hasattr(get,'disk'):
            import system
            data['DISK'] = system.system().GetDiskInfo();
        return data


    def __list_dir(self,path,my_sort = 'name',reverse = False):
        if not os.path.exists(path): return []
        py_v = sys.version_info[0]
        tmp_files = []
        tmp_dirs = []
        for f_name in os.listdir(path):
            try:
                if py_v == 2: f_name = f_name.encode('utf-8');
                filename = os.path.join(path,f_name)
                if not os.path.exists(filename): continue
                file_info = self.__format_stat(filename,path)
                if not file_info: continue
                if os.path.isdir(filename):
                    tmp_dirs.append(file_info)
                else:
                    tmp_files.append(file_info)
            except: continue
        tmp_dirs = sorted(tmp_dirs,key=lambda x:x[my_sort],reverse=reverse)
        tmp_files = sorted(tmp_files,key=lambda x:x[my_sort],reverse=reverse)
        
        for f in tmp_files: tmp_dirs.append(f)
        return tmp_dirs

    def __save_list_history(self,path):
        max_num = 20
        path = path.strip()
        save_path = '/www/server/panel/config/list_history.json'
        if not os.path.exists(save_path): public.writeFile(save_path,'{}')
        list_history = json.loads(public.readFile(save_path))
        if path in list_history:
            list_history[path] += 1
        else:
            list_history[path] = 1

        #sorted(list_history,key=lambda x:x )



    def __format_stat(self,filename,path):
        try:
            stat = self.__get_stat(filename,path)
            if not stat: return None
            tmp_stat = stat.split(';')
            file_info = {'name': self.xssencode(tmp_stat[0].replace('/','')),'size':int(tmp_stat[1]),'mtime':int(tmp_stat[2]),'accept':int(tmp_stat[3]),'user':tmp_stat[4],'link':tmp_stat[5]}
            return file_info
        except: return None
        

    def SearchFiles(self,get):
        if not hasattr(get,'path'): get.path = '/www/wwwroot'
        if sys.version_info[0] == 2: get.path = get.path.encode('utf-8');
        if not os.path.exists(get.path): get.path = '/www';
        search = get.search.strip().lower();
        my_dirs = []
        my_files = []
        count = 0
        max = 3000
        for d_list in os.walk(get.path):
            if count >= max: break;
            for d in d_list[1]:
                if count >= max: break;
                d = self.xssencode(d)
                if d.lower().find(search) != -1: 
                    filename = d_list[0] + '/' + d
                    if not os.path.exists(filename): continue
                    my_dirs.append(self.__get_stat(filename,get.path))
                    count += 1
                    
            for f in d_list[2]:
                if count >= max: break;
                f = self.xssencode(f)
                if f.lower().find(search) != -1: 
                    filename = d_list[0] + '/' + f
                    if not os.path.exists(filename): continue
                    my_files.append(self.__get_stat(filename,get.path))
                    count += 1
        data = {}
        data['DIR'] = sorted(my_dirs)
        data['FILES'] = sorted(my_files)
        data['PATH'] = str(get.path)
        data['PAGE'] = public.get_page(len(my_dirs) + len(my_files),1,max,'GetFiles')['page']
        data['STORE'] = self.get_files_store(None)
        return data


    def __get_stat(self,filename,path = None):
        stat = os.stat(filename)
        accept = str(oct(stat.st_mode)[-3:]);
        mtime = str(int(stat.st_mtime))
        user = ''
        try:
            user = pwd.getpwuid(stat.st_uid).pw_name
        except:
            user = str(stat.st_uid)
        size = str(stat.st_size)
        link = '';
        if os.path.islink(filename): link = ' -> ' + os.readlink(filename)
        tmp_path = (path + '/').replace('//','/')
        if path and tmp_path != '/':filename = filename.replace(tmp_path,'')
        return filename + ';' + size + ';' + mtime+ ';' +accept+ ';' +user+ ';' +link

    
    #计算文件数量
    def GetFilesCount(self,path,search):
        if os.path.isfile(path): return 1
        if not os.path.exists(path):return 0
        i=0;
        for name in os.listdir(path):
            if search:
                if name.lower().find(search) == -1: continue;
            i += 1;
        return i;
    
    #创建文件
    def CreateFile(self,get):
        if sys.version_info[0] == 2: get.path = get.path.encode('utf-8').strip();
        try:
            if not self.CheckFileName(get.path): return public.returnMsg(False,'文件名中不能包含特殊字符!');
            if os.path.exists(get.path):
                return public.returnMsg(False,'FILE_EXISTS')
            path = os.path.dirname(get.path)
            if not os.path.exists(path):
                os.makedirs(path)
            open(get.path,'w+').close()
            self.SetFileAccept(get.path);
            public.WriteLog('TYPE_FILE','FILE_CREATE_SUCCESS',(get.path,))
            return public.returnMsg(True,'FILE_CREATE_SUCCESS')
        except:
            return public.returnMsg(False,'FILE_CREATE_ERR')
    
    #创建目录
    def CreateDir(self,get):
        if sys.version_info[0] == 2: get.path = get.path.encode('utf-8').strip();
        try:
            if not self.CheckFileName(get.path): return public.returnMsg(False,'目录名中不能包含特殊字符!');
            if os.path.exists(get.path):
                return public.returnMsg(False,'DIR_EXISTS')
            os.makedirs(get.path)
            self.SetFileAccept(get.path);
            public.WriteLog('TYPE_FILE','DIR_CREATE_SUCCESS',(get.path,))
            return public.returnMsg(True,'DIR_CREATE_SUCCESS')
        except:
            return public.returnMsg(False,'DIR_CREATE_ERR')
    
    
    #删除目录
    def DeleteDir(self,get) :
        if sys.version_info[0] == 2: get.path = get.path.encode('utf-8');
        #if get.path.find('/www/wwwroot') == -1: return public.returnMsg(False,'此为演示服务器,禁止删除此目录!');
        if not os.path.exists(get.path):
            return public.returnMsg(False,'DIR_NOT_EXISTS')
        
        #检查是否敏感目录
        if not self.CheckDir(get.path):
            return public.returnMsg(False,'FILE_DANGER');
        
        try:
            #检查是否存在.user.ini
            #if os.path.exists(get.path+'/.user.ini'):
            #    os.system("chattr -i '"+get.path+"/.user.ini'")
            os.system("chattr -R -i " + get.path)
            if hasattr(get,'empty'):
                if not self.delete_empty(get.path): return public.returnMsg(False,'DIR_ERR_NOT_EMPTY');
            
            if os.path.exists('data/recycle_bin.pl'):
                if self.Mv_Recycle_bin(get): 
                    self.site_path_safe(get)
                    return public.returnMsg(True,'DIR_MOVE_RECYCLE_BIN');
            
            import shutil
            shutil.rmtree(get.path)
            self.site_path_safe(get)
            public.WriteLog('TYPE_FILE','DIR_DEL_SUCCESS',(get.path,))
            return public.returnMsg(True,'DIR_DEL_SUCCESS')
        except:
            return public.returnMsg(False,'DIR_DEL_ERR')
    
    #删除 空目录 
    def delete_empty(self,path):
        if sys.version_info[0] == 2: get.path = get.path.encode('utf-8');
        for files in os.listdir(path):
            return False
        return True
    
    #删除文件
    def DeleteFile(self,get):
        if sys.version_info[0] == 2: get.path = get.path.encode('utf-8');
        if not os.path.exists(get.path):
            return public.returnMsg(False,'FILE_NOT_EXISTS')
        
        #检查是否为.user.ini
        if get.path.find('.user.ini') != -1:
            os.system("chattr -i '"+get.path+"'")
        try:
            if os.path.exists('data/recycle_bin.pl'):
                if self.Mv_Recycle_bin(get): 
                    self.site_path_safe(get)
                    return public.returnMsg(True,'FILE_MOVE_RECYCLE_BIN');
            os.remove(get.path)
            self.site_path_safe(get)
            public.WriteLog('TYPE_FILE','FILE_DEL_SUCCESS',(get.path,))
            return public.returnMsg(True,'FILE_DEL_SUCCESS')
        except:
            return public.returnMsg(False,'FILE_DEL_ERR')
    
    #移动到回收站
    def Mv_Recycle_bin(self,get):
        rPath = '/www/Recycle_bin/'
        if not os.path.exists(rPath): os.system('mkdir -p ' + rPath);
        rFile = rPath + get.path.replace('/','_bt_') + '_t_' + str(time.time());
        try:
            import shutil
            shutil.move(get.path, rFile)
            public.WriteLog('TYPE_FILE','FILE_MOVE_RECYCLE_BIN',(get.path,))
            return True;
        except:
            public.WriteLog('TYPE_FILE','FILE_MOVE_RECYCLE_BIN_ERR',(get.path,))
            return False;
    
    #从回收站恢复
    def Re_Recycle_bin(self,get):
        rPath = '/www/Recycle_bin/'
        if sys.version_info[0] == 2: get.path = get.path.encode('utf-8');
        dFile = get.path.replace('_bt_','/').split('_t_')[0];
        get.path = rPath + get.path
        if dFile.find('BTDB_') != -1:
            import database;
            return database.database().RecycleDB(get.path);
        try:
            import shutil
            shutil.move(get.path, dFile)
            public.WriteLog('TYPE_FILE','FILE_RE_RECYCLE_BIN',(dFile,))
            return public.returnMsg(True,'FILE_RE_RECYCLE_BIN');
        except:
            public.WriteLog('TYPE_FILE','FILE_RE_RECYCLE_BIN_ERR',(dFile,))
            return public.returnMsg(False,'FILE_RE_RECYCLE_BIN_ERR');
    
    #获取回收站信息
    def Get_Recycle_bin(self,get):
        rPath = '/www/Recycle_bin/'
        if not os.path.exists(rPath): os.system('mkdir -p ' + rPath);
        data = {};
        data['dirs'] = [];
        data['files'] = [];
        data['status'] = os.path.exists('data/recycle_bin.pl');
        data['status_db'] = os.path.exists('data/recycle_bin_db.pl');
        for file in os.listdir(rPath):
            file = self.xssencode(file)
            try:
                tmp = {};
                fname = rPath + file;
                tmp1 = file.split('_bt_');
                tmp2 = tmp1[len(tmp1)-1].split('_t_');
                tmp['rname'] = file;
                tmp['dname'] = file.replace('_bt_','/').split('_t_')[0];
                tmp['name'] = tmp2[0];
                tmp['time'] = int(float(tmp2[1]));
                if os.path.islink(fname): 
                    filePath = os.readlink(fname);
                    link = ' -> ' + filePath;
                    if os.path.exists(filePath): 
                        tmp['size'] = os.path.getsize(filePath);
                    else:
                        tmp['size'] = 0;
                else:
                    tmp['size'] = os.path.getsize(fname);
                if os.path.isdir(fname):
                    data['dirs'].append(tmp);
                else:
                    data['files'].append(tmp);
            except:
                continue;
        return data;
    
    #彻底删除
    def Del_Recycle_bin(self,get):
        rPath = '/www/Recycle_bin/'
        if sys.version_info[0] == 2: get.path = get.path.encode('utf-8');
        dFile = get.path.split('_t_')[0];
        filename = rPath + get.path
        tfile = get.path.replace('_bt_','/').split('_t_')[0];
        if not os.path.exists(filename): return public. returnMsg(True,'FILE_DEL_RECYCLE_BIN',(tfile,))
        if dFile.find('BTDB_') != -1:
            import database;
            return database.database().DeleteTo(filename);
        if not self.CheckDir(filename):
            return public.returnMsg(False,'FILE_DANGER');
        
        os.system('chattr -R -i ' + filename)
        if os.path.isdir(filename):
            import shutil
            try:
                shutil.rmtree(filename);
            except:
                os.system("rm -rf " + filename)
        else:
            try:
                os.remove(filename);
            except:
                os.system("rm -f " + filename)
        public.WriteLog('TYPE_FILE','FILE_DEL_RECYCLE_BIN',(tfile,));
        return public.returnMsg(True,'FILE_DEL_RECYCLE_BIN',(tfile,));
    
    #清空回收站
    def Close_Recycle_bin(self,get):
        rPath = '/www/Recycle_bin/'
        os.system('chattr -R -i ' + rPath)
        import database,shutil;
        rlist = os.listdir(rPath)
        i = 0;
        l = len(rlist);
        for name in rlist:
            i += 1;
            path = rPath + name;
            public.writeSpeed(name,i,l);
            if name.find('BTDB_') != -1:
                database.database().DeleteTo(path);
                continue;
            if os.path.isdir(path):
                try:
                    shutil.rmtree(path);
                except:
                    os.system('rm -rf ' + path);
            else:
                try:
                    os.remove(path);
                except:
                    os.system('rm -f ' + path);

        public.writeSpeed(None,0,0);
        public.WriteLog('TYPE_FILE','FILE_CLOSE_RECYCLE_BIN');
        return public.returnMsg(True,'FILE_CLOSE_RECYCLE_BIN');
    
    #回收站开关
    def Recycle_bin(self,get):        
        c = 'data/recycle_bin.pl';
        if hasattr(get,'db'): c = 'data/recycle_bin_db.pl';
        if os.path.exists(c):
            os.remove(c)
            public.WriteLog('TYPE_FILE','FILE_OFF_RECYCLE_BIN');
            return public.returnMsg(True,'FILE_OFF_RECYCLE_BIN');
        else:
            public.writeFile(c,'True');
            public.WriteLog('TYPE_FILE','FILE_ON_RECYCLE_BIN');
            return public.returnMsg(True,'FILE_ON_RECYCLE_BIN');
    
    #复制文件
    def CopyFile(self,get) :
        if sys.version_info[0] == 2:
            get.sfile = get.sfile.encode('utf-8');
            get.dfile = get.dfile.encode('utf-8');
        if not os.path.exists(get.sfile):
            return public.returnMsg(False,'FILE_NOT_EXISTS')
        
        #if os.path.exists(get.dfile):
        #    return public.returnMsg(False,'FILE_EXISTS')
        
        if os.path.isdir(get.sfile):
            return self.CopyDir(get)
        
        import shutil
        try:
            shutil.copyfile(get.sfile, get.dfile)
            public.WriteLog('TYPE_FILE','FILE_COPY_SUCCESS',(get.sfile,get.dfile))
            stat = os.stat(get.sfile)
            os.chown(get.dfile,stat.st_uid,stat.st_gid)
            return public.returnMsg(True,'FILE_COPY_SUCCESS')
        except:
            return public.returnMsg(False,'FILE_COPY_ERR')
    
    #复制文件夹
    def CopyDir(self,get):
        if sys.version_info[0] == 2:
            get.sfile = get.sfile.encode('utf-8');
            get.dfile = get.dfile.encode('utf-8');
        if not os.path.exists(get.sfile):
            return public.returnMsg(False,'DIR_NOT_EXISTS');
        
        #if os.path.exists(get.dfile):
        #    return public.returnMsg(False,'DIR_EXISTS');
        
        #if not self.CheckDir(get.dfile):
        #    return public.returnMsg(False,'FILE_DANGER');
        
        try:
            self.copytree(get.sfile, get.dfile)
            stat = os.stat(get.sfile)
            os.chown(get.dfile,stat.st_uid,stat.st_gid)
            public.WriteLog('TYPE_FILE','DIR_COPY_SUCCESS',(get.sfile,get.dfile))
            return public.returnMsg(True,'DIR_COPY_SUCCESS')
        except:
            return public.returnMsg(False,'DIR_COPY_ERR')
        
    
    
    #移动文件或目录
    def MvFile(self,get):
        if sys.version_info[0] == 2:
            get.sfile = get.sfile.encode('utf-8');
            get.dfile = get.dfile.encode('utf-8');
        if not self.CheckFileName(get.dfile): return public.returnMsg(False,'文件名中不能包含特殊字符!');
        if not os.path.exists(get.sfile):
            return public.returnMsg(False,'FILE_NOT_EXISTS')
        
        if get.dfile == get.sfile:
            return public.returnMsg(False,'无意义操作');
        
        if not self.CheckDir(get.sfile):
            return public.returnMsg(False,'FILE_DANGER');
        try:
            self.move(get.sfile,get.dfile)
            self.site_path_safe(get)
            if hasattr(get,'rename'):
                public.WriteLog('TYPE_FILE','[%s]重命名为[%s]' % (get.sfile,get.dfile))
                return public.returnMsg(True,'重命名成功!')
            else:
                public.WriteLog('TYPE_FILE','MOVE_SUCCESS',(get.sfile,get.dfile))
                return public.returnMsg(True,'MOVE_SUCCESS')
        except:
            return public.returnMsg(False,'MOVE_ERR')
        
    #检查文件是否存在
    def CheckExistsFiles(self,get):
        if sys.version_info[0] == 2: get.dfile = get.dfile.encode('utf-8');
        data = [];
        filesx = [];
        if not hasattr(get,'filename'):
            if not 'selected' in session: return []
            filesx = json.loads(session['selected']['data']);
        else:
            filesx.append(get.filename);
        
        for fn in filesx:
            if fn == '.': continue
            filename = get.dfile + '/' + fn;
            if os.path.exists(filename):
                tmp = {}
                stat = os.stat(filename)
                tmp['filename'] = fn;
                tmp['size'] = os.path.getsize(filename);
                tmp['mtime'] = str(int(stat.st_mtime));
                data.append(tmp);
        return data;
            
    
    #获取文件内容
    def GetFileBody(self,get) :
        if sys.version_info[0] == 2: get.path = get.path.encode('utf-8');
        if not os.path.exists(get.path):
            if get.path.find('rewrite') == -1:
                return public.returnMsg(False,'FILE_NOT_EXISTS',(get.path,))
            public.writeFile(get.path,'');
        
        if os.path.getsize(get.path) > 3145928: return public.returnMsg(False,u'不能在线编辑大于3MB的文件!');
        if not os.path.isfile(get.path): return public.returnMsg(False,'这不是一个文件!')
        fp = open(get.path,'rb')
        data = {}
        data['status'] = True
        
        try:
            if fp:
                from chardet.universaldetector import UniversalDetector
                detector = UniversalDetector()
                srcBody = b""
                for line in fp.readlines():
                    detector.feed(line)
                    srcBody += line
                detector.close()
                char = detector.result
                data['encoding'] = char['encoding']
                if char['encoding'] == 'GB2312' or not char['encoding'] or char['encoding'] == 'TIS-620' or char['encoding'] == 'ISO-8859-9': data['encoding'] = 'GBK';
                if char['encoding'] == 'ascii' or char['encoding'] == 'ISO-8859-1': data['encoding'] = 'utf-8';
                if char['encoding'] == 'Big5': data['encoding'] = 'BIG5';
                if not char['encoding'] in ['GBK','utf-8','BIG5']: data['encoding'] = 'utf-8';
                try:
                    if sys.version_info[0] == 2: 
                        data['data'] = srcBody.decode(data['encoding']).encode('utf-8',errors='ignore');
                    else:
                        data['data'] = srcBody.decode(data['encoding'])
                except:
                    data['encoding'] = char['encoding'];
                    if sys.version_info[0] == 2: 
                        data['data'] = srcBody.decode(data['encoding']).encode('utf-8',errors='ignore');
                    else:
                        data['data'] = srcBody.decode(data['encoding'])
            else:
               return public.returnMsg(False,'打开文件失败，文件可能被其它进程占用!')
            if hasattr(get,'filename'): get.path = get.filename
            data['historys'] = self.get_history(get.path)
            return data;
        except Exception as ex:
            return public.returnMsg(False,u'文件编码不被兼容，无法正确读取文件!' + str(ex));
    
    
    #保存文件
    def SaveFileBody(self,get):
        if not 'path' in get: return public.returnMsg(False,'path参数不能为空!')
        #if not 'data' in get: return public.returnMsg(False,'data参数不能为空!')
        if sys.version_info[0] == 2: get.path = get.path.encode('utf-8');
        if not os.path.exists(get.path):
            if get.path.find('.htaccess') == -1:
                return public.returnMsg(False,'FILE_NOT_EXISTS')
        
        try:
            isConf = -1
            if os.path.exists('/etc/init.d/nginx') or os.path.exists('/etc/init.d/httpd'):
                isConf = get.path.find('nginx');
                if isConf == -1: isConf = get.path.find('apache');
                if isConf == -1: isConf = get.path.find('rewrite');
                if isConf != -1:
                    os.system('\\cp -a '+get.path+' /tmp/backup.conf');
            
            data = get.data;
            userini = False;
            if get.path.find('.user.ini') != -1:
                userini = True;
                public.ExecShell('chattr -i ' + get.path);
                
            
            if get.path.find('/www/server/cron') != -1:
                    try:
                        import crontab
                        data = crontab.crontab().CheckScript(data);
                    except:
                        pass
            
            if get.encoding == 'ascii':get.encoding = 'utf-8';
            self.save_history(get.path)
            if sys.version_info[0] == 2:
                data = data.encode(get.encoding,errors='ignore');
                fp = open(get.path,'w+')
            else:
                data = data.encode(get.encoding,errors='ignore').decode(get.encoding);
                fp = open(get.path,'w+',encoding=get.encoding)
            
            fp.write(data)
            fp.close()
            
            if isConf != -1:
                isError = public.checkWebConfig();
                if isError != True:
                    os.system('\\cp -a /tmp/backup.conf '+get.path);
                    return public.returnMsg(False,'ERROR:<br><font style="color:red;">'+isError.replace("\n",'<br>')+'</font>');
                public.serviceReload();
            
            if userini: public.ExecShell('chattr +i ' + get.path);
            
            public.WriteLog('TYPE_FILE','FILE_SAVE_SUCCESS',(get.path,));
            return public.returnMsg(True,'FILE_SAVE_SUCCESS');
        except Exception as ex:
            return public.returnMsg(False,'FILE_SAVE_ERR' + str(ex));
        
    #保存历史副本
    def save_history(self,filename):
        try:
            save_path = ('/www/backup/file_history/' + filename).replace('//','/')
            if not os.path.exists(save_path): os.makedirs(save_path,384)
            
            his_list = sorted(os.listdir(save_path),reverse=True)
            num =  public.readFile('data/history_num.pl')
            if not num: 
                num = 10
            else:
                num = int(num)
            d_num = len(his_list)
            is_write = True
            new_file_md5 = public.FileMd5(filename)
            for i in range(d_num):
                rm_file = save_path + '/' + his_list[i]
                if i == 0: #判断是否和上一份副本相同
                    old_file_md5 = public.FileMd5(rm_file)
                    if old_file_md5 == new_file_md5: is_write = False

                if i+1 >= num: #删除多余的副本
                    if os.path.exists(rm_file): os.remove(rm_file)
                    continue
            #写入新的副本
            if is_write: public.writeFile(save_path + '/' + str(int(time.time())),public.readFile(filename,'rb'),'wb')
        except:pass

    #取历史副本
    def get_history(self,filename):
        try:
            save_path = ('/www/backup/file_history/' + filename).replace('//','/')
            if not os.path.exists(save_path): return []
            return sorted(os.listdir(save_path))
        except: return []

    #读取指定历史副本
    def read_history(self,args):
        save_path = ('/www/backup/file_history/' + args.filename).replace('//','/')
        args.path = save_path + '/' + args.history
        return self.GetFileBody(args)

    #文件压缩
    def Zip(self,get) :
        if not 'z_type' in get: get.z_type = 'rar'
        import panelTask
        task_obj = panelTask.bt_task()
        task_obj.create_task('压缩文件',3,get.path,json.dumps({"sfile":get.sfile,"dfile":get.dfile,"z_type":get.z_type}))
        public.WriteLog("TYPE_FILE", 'ZIP_SUCCESS',(get.sfile,get.dfile));
        return public.returnMsg(True,'已将压缩任务添加到消息队列!')
    
    
    #文件解压
    def UnZip(self,get):
        import panelTask
        if not 'password' in get:get.password = '' 
        task_obj = panelTask.bt_task()
        task_obj.create_task('解压文件',2,get.sfile,json.dumps({"dfile":get.dfile,"password":get.password}))
        public.WriteLog("TYPE_FILE", 'UNZIP_SUCCESS',(get.sfile,get.dfile));
        return public.returnMsg(True,'已将解压任务添加到消息队列!')
    
    
    #获取文件/目录 权限信息
    def GetFileAccess(self,get):
        if sys.version_info[0] == 2: get.filename = get.filename.encode('utf-8');
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
    
    
    #设置文件权限和所有者
    def SetFileAccess(self,get,all = '-R'):
        if sys.version_info[0] == 2: get.filename = get.filename.encode('utf-8');
        if 'all' in get:
            if get.all == 'False': all = ''
        try:
            if not self.CheckDir(get.filename): return public.returnMsg(False,'FILE_DANGER');
            if not os.path.exists(get.filename):
                return public.returnMsg(False,'FILE_NOT_EXISTS')
            os.system('chmod '+all+' '+get.access+" '"+get.filename+"'")
            os.system('chown '+all+' '+get.user+':'+get.user+" '"+get.filename+"'")
            public.WriteLog('TYPE_FILE','FILE_ACCESS_SUCCESS',(get.filename,get.access,get.user))
            return public.returnMsg(True,'SET_SUCCESS')
        except:
            return public.returnMsg(False,'SET_ERROR')

    def SetFileAccept(self,filename):
        os.system('chown -R www:www ' + filename)
        os.system('chmod -R 755 ' + filename)
    
    
    
    #取目录大小
    def GetDirSize(self,get):
        if sys.version_info[0] == 2: get.path = get.path.encode('utf-8');
        return public.to_size(public.get_path_size(get.path))

    #取目录大小2
    def get_path_size(self,get):
        if sys.version_info[0] == 2: get.path = get.path.encode('utf-8');
        data = {}
        data['path'] = get.path
        data['size'] = public.get_path_size(get.path)
        return data
    
    def CloseLogs(self,get):
        get.path = public.GetConfigValue('root_path')
        os.system('rm -f '+public.GetConfigValue('logs_path')+'/*')
        if public.get_webserver() == 'nginx':
            os.system('kill -USR1 `cat '+public.GetConfigValue('setup_path')+'/nginx/logs/nginx.pid`');
        else:
            os.system('/etc/init.d/httpd reload');
        
        public.WriteLog('TYPE_FILE','SITE_LOG_CLOSE')
        get.path = public.GetConfigValue('logs_path')
        return self.GetDirSize(get)
            
    #批量操作
    def SetBatchData(self,get):
        if sys.version_info[0] == 2: get.path = get.path.encode('utf-8');
        if get.type == '1' or get.type == '2':
            session['selected'] = get
            return public.returnMsg(True,'FILE_ALL_TIPS')
        elif get.type == '3':
            for key in json.loads(get.data):
                try:
                    if sys.version_info[0] == 2: key = key.encode('utf-8')
                    filename = get.path+'/'+key
                    if not self.CheckDir(filename): return public.returnMsg(False,'FILE_DANGER');
                    ret = ' -R '
                    if 'all' in get:
                        if get.all == 'False': ret = ''
                    os.system('chmod '+ret+get.access+" '"+filename+"'")
                    os.system('chown '+ret+get.user+':'+get.user+" '"+filename+"'")
                except:
                    continue;
            public.WriteLog('TYPE_FILE','FILE_ALL_ACCESS')
            return public.returnMsg(True,'FILE_ALL_ACCESS')
        else:
            isRecyle = os.path.exists('data/recycle_bin.pl')
            path = get.path
            get.data = json.loads(get.data)
            l = len(get.data);
            i = 0;
            for key in get.data:
                try:
                    if sys.version_info[0] == 2: key = key.encode('utf-8')
                    filename = path + '/'+key
                    get.path = filename;
                    if not os.path.exists(filename): continue
                    i += 1;
                    public.writeSpeed(key,i,l);
                    if os.path.isdir(filename):
                        if not self.CheckDir(filename): return public.returnMsg(False,'FILE_DANGER');
                        os.system("chattr -R -i " + filename)
                        if isRecyle:
                            self.Mv_Recycle_bin(get)
                        else:
                            shutil.rmtree(filename)
                    else:
                        if key == '.user.ini': 
                            if l > 1: continue
                            os.system('chattr -i ' + filename);
                        if isRecyle:
                            
                            self.Mv_Recycle_bin(get)
                        else:
                            os.remove(filename)
                except:
                    continue;
                public.writeSpeed(None,0,0);
            self.site_path_safe(get)
            public.WriteLog('TYPE_FILE','FILE_ALL_DEL')
            return public.returnMsg(True,'FILE_ALL_DEL')
    
    
    #批量粘贴
    def BatchPaste(self,get):
        import shutil
        if sys.version_info[0] == 2: get.path = get.path.encode('utf-8');
        if not self.CheckDir(get.path): return public.returnMsg(False,'FILE_DANGER');
        if not 'selected' in session: return public.returnMsg(False,'操作失败,请重新操作复制或剪切过程')
        i = 0;
        if not 'selected' in session:return public.returnMsg(False,'操作失败,请重新操作');
        myfiles = json.loads(session['selected']['data'])
        l = len(myfiles);
        if get.type == '1':
            for key in myfiles:
                i += 1
                public.writeSpeed(key,i,l);
                try:
                    if sys.version_info[0] == 2:
                        sfile = session['selected']['path'] + '/' + key.encode('utf-8')
                        dfile = get.path + '/' + key.encode('utf-8')
                    else:
                        sfile = session['selected']['path'] + '/' + key
                        dfile = get.path + '/' + key

                    if os.path.isdir(sfile):
                        self.copytree(sfile,dfile)
                    else:
                        shutil.copyfile(sfile,dfile)
                    stat = os.stat(sfile)
                    os.chown(dfile,stat.st_uid,stat.st_gid)
                except:
                    continue;
            public.WriteLog('TYPE_FILE','FILE_ALL_COPY',(session['selected']['path'],get.path))
        else:
            for key in myfiles:
                try:
                    i += 1
                    public.writeSpeed(key,i,l);
                    if sys.version_info[0] == 2:
                        sfile = session['selected']['path'] + '/' + key.encode('utf-8')
                        dfile = get.path + '/' + key.encode('utf-8')
                    else:
                        sfile = session['selected']['path'] + '/' + key
                        dfile = get.path + '/' + key
                    self.move(sfile,dfile)
                except:
                    continue;
            self.site_path_safe(get)
            public.WriteLog('TYPE_FILE','FILE_ALL_MOTE',(session['selected']['path'],get.path))
        public.writeSpeed(None,0,0);
        errorCount = len(myfiles) - i
        del(session['selected'])
        return public.returnMsg(True,'FILE_ALL',(str(i),str(errorCount)));

    #移动和重命名
    def move(self,sfile,dfile):
        sfile = sfile.replace('//','/')
        dfile = dfile.replace('//','/')
        if sfile == dfile: return False
        if not os.path.exists(sfile): return False
        is_dir = os.path.isdir(sfile)
        if not os.path.exists(dfile) or not is_dir:
            if os.path.exists(dfile): os.remove(dfile)
            shutil.move(sfile, dfile)
        else:
            self.copytree(sfile,dfile)
            if os.path.exists(sfile):
                if is_dir: 
                    shutil.rmtree(sfile)
                else:
                    os.remove(sfile)
        return True

    #复制目录
    def copytree(self,sfile,dfile):
        if sfile == dfile: return False
        if not os.path.exists(dfile): os.makedirs(dfile)
        for f_name in os.listdir(sfile):
            src_filename = (sfile + '/' + f_name).replace('//','/')
            dst_filename = (dfile + '/' + f_name).replace('//','/')
            mode_info = public.get_mode_and_user(src_filename)
            if os.path.isdir(src_filename):
                if not os.path.exists(dst_filename):
                    os.makedirs(dst_filename)
                    public.set_mode(dst_filename,mode_info['mode'])
                    public.set_own(dst_filename,mode_info['user'])
                self.copytree(src_filename,dst_filename)
            else:
                try:
                    shutil.copy2(src_filename,dst_filename)
                    public.set_mode(dst_filename,mode_info['mode'])
                    public.set_own(dst_filename,mode_info['user'])
                except:pass
        return True


    
    #下载文件
    def DownloadFile(self,get):
        import panelTask
        task_obj = panelTask.bt_task()
        task_obj.create_task('下载文件',1,get.url,get.path + '/' + get.filename)
        #if sys.version_info[0] == 2: get.path = get.path.encode('utf-8');
        #import db,time
        #isTask = '/tmp/panelTask.pl'
        #execstr = get.url +'|bt|'+get.path+'/'+get.filename
        #sql = db.Sql()
        #sql.table('tasks').add('name,type,status,addtime,execstr',('下载文件['+get.filename+']','download','0',time.strftime('%Y-%m-%d %H:%M:%S'),execstr))
        #public.writeFile(isTask,'True')
        #self.SetFileAccept(get.path+'/'+get.filename);
        public.WriteLog('TYPE_FILE','FILE_DOWNLOAD',(get.url , get.path));
        return public.returnMsg(True,'FILE_DOANLOAD')
    
    #添加安装任务
    def InstallSoft(self,get):
        import db,time
        path = public.GetConfigValue('setup_path') + '/php'
        if not os.path.exists(path): os.system("mkdir -p " + path);
        if session['server_os']['x'] != 'RHEL': get.type = '3'
        apacheVersion='false';
        if public.get_webserver() == 'apache':
            apacheVersion = public.readFile(public.GetConfigValue('setup_path')+'/apache/version.pl');
        public.writeFile('/var/bt_apacheVersion.pl',apacheVersion)
        public.writeFile('/var/bt_setupPath.conf',public.GetConfigValue('root_path'))
        isTask = '/tmp/panelTask.pl'
        execstr = "cd " + public.GetConfigValue('setup_path') + "/panel/install && /bin/bash install_soft.sh " + get.type + " install " + get.name + " "+ get.version;
        sql = db.Sql()
        if hasattr(get,'id'):
            id = get.id;
        else:
            id = None;
        sql.table('tasks').add('id,name,type,status,addtime,execstr',(None,'安装['+get.name+'-'+get.version+']','execshell','0',time.strftime('%Y-%m-%d %H:%M:%S'),execstr))
        public.writeFile(isTask,'True')
        public.WriteLog('TYPE_SETUP','PLUGIN_ADD',(get.name,get.version));
        time.sleep(0.1);
        return public.returnMsg(True,'PLUGIN_ADD');
    
    #删除任务队列
    def RemoveTask(self,get):
        try:
            name = public.M('tasks').where('id=?',(get.id,)).getField('name');
            status = public.M('tasks').where('id=?',(get.id,)).getField('status');
            public.M('tasks').delete(get.id);
            if status == '-1':
                os.system("kill `ps -ef |grep 'python panelSafe.pyc'|grep -v grep|grep -v panelExec|awk '{print $2}'`");
                os.system("kill `ps -ef |grep 'install_soft.sh'|grep -v grep|grep -v panelExec|awk '{print $2}'`");
                os.system("kill `ps aux | grep 'python task.pyc$'|awk '{print $2}'`");
                os.system('''
pids=`ps aux | grep 'sh'|grep -v grep|grep install|awk '{print $2}'`
arr=($pids)

for p in ${arr[@]}
do
    kill -9 $p
done
            ''');
            
                os.system('rm -f ' + name.replace('扫描目录[','').replace(']','') + '/scan.pl');
                isTask = '/tmp/panelTask.pl';
                public.writeFile(isTask,'True');
                os.system('/etc/init.d/bt start');
        except:
            os.system('/etc/init.d/bt start');
        return public.returnMsg(True,'PLUGIN_DEL');
    
    #重新激活任务
    def ActionTask(self,get):
        isTask = '/tmp/panelTask.pl'
        public.writeFile(isTask,'True');
        return public.returnMsg(True,'PLUGIN_ACTION');
        
    
    #卸载软件
    def UninstallSoft(self,get):
        public.writeFile('/var/bt_setupPath.conf',public.GetConfigValue('root_path'))
        get.type = '0'
        if session['server_os']['x'] != 'RHEL': get.type = '3'
        execstr = "cd " + public.GetConfigValue('setup_path') + "/panel/install && /bin/bash install_soft.sh "+get.type+" uninstall " + get.name.lower() + " "+ get.version.replace('.','');
        os.system(execstr);
        public.WriteLog('TYPE_SETUP','PLUGIN_UNINSTALL',(get.name,get.version));
        return public.returnMsg(True,"PLUGIN_UNINSTALL");
        
    
    #取任务队列进度
    def GetTaskSpeed(self,get):
        tempFile = '/tmp/panelExec.log'
        freshFile = '/tmp/panelFresh'
        import db
        find = db.Sql().table('tasks').where('status=? OR status=?',('-1','0')).field('id,type,name,execstr').find()
        if(type(find) == str): return public.returnMsg(False,"查询发生错误，"+find)
        if not len(find): return public.returnMsg(False,'当前没有任务队列在执行-2!')
        isTask = '/tmp/panelTask.pl'
        public.writeFile(isTask,'True');
        echoMsg = {}
        echoMsg['name'] = find['name']
        echoMsg['execstr'] = find['execstr']
        if find['type'] == 'download':
            try:
                tmp = public.readFile(tempFile)
                if len(tmp) < 10:
                    return public.returnMsg(False,'当前没有任务队列在执行-3!')
                echoMsg['msg'] = json.loads(tmp)
                echoMsg['isDownload'] = True
            except:
                db.Sql().table('tasks').where("id=?",(find['id'],)).save('status',('0',))
                return public.returnMsg(False,'当前没有任务队列在执行-4!')
        else:
            echoMsg['msg'] = self.GetLastLine(tempFile,20)
            echoMsg['isDownload'] = False
        
        echoMsg['task'] = public.M('tasks').where("status!=?",('1',)).field('id,status,name,type').order("id asc").select()
        return echoMsg
    
    #取执行日志
    def GetExecLog(self,get):
        return self.GetLastLine('/tmp/panelExec.log',100);
                 
    #读文件指定倒数行数
    def GetLastLine(self,inputfile,lineNum):
        result = public.GetNumLines(inputfile,lineNum)
        if len(result) < 1:
            return public.getMsg('TASK_SLEEP');
        return result
        
    
    #执行SHELL命令
    def ExecShell(self,get):
        disabled = ['vi','vim','top','passwd','su']
        get.shell = get.shell.strip()
        tmp = get.shell.split(' ');
        if tmp[0] in disabled: return public.returnMsg(False,'FILE_SHELL_ERR',(tmp[0],));
        shellStr = '''#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
cd %s
%s
''' % (get.path,get.shell)
        public.writeFile('/tmp/panelShell.sh',shellStr);
        os.system('nohup bash /tmp/panelShell.sh > /tmp/panelShell.pl 2>&1 &');
        return public.returnMsg(True,'FILE_SHELL_EXEC');
    
    #取SHELL执行结果
    def GetExecShellMsg(self,get):
        fileName = '/tmp/panelShell.pl';
        if not os.path.exists(fileName): return 'FILE_SHELL_EMPTY';
        status = not public.process_exists('bash',None,'/tmp/panelShell.sh')
        return public.returnMsg(status,public.GetNumLines(fileName,200));
    
    #文件搜索
    def GetSearch(self,get):
        if not os.path.exists(get.path): return public.returnMsg(False,'DIR_NOT_EXISTS');
        return public.ExecShell("find "+get.path+" -name '*"+get.search+"*'");

    #保存草稿
    def SaveTmpFile(self,get):
        save_path = '/www/server/panel/temp'
        if not os.path.exists(save_path): os.makedirs(save_path)
        get.path = os.path.join(save_path,public.Md5(get.path) + '.tmp')
        public.writeFile(get.path,get.body)
        return public.returnMsg(True,'已保存')

    #获取草稿
    def GetTmpFile(self,get):
        self.CleanOldTmpFile()
        save_path = '/www/server/panel/temp'
        if not os.path.exists(save_path): os.makedirs(save_path)
        src_path = get.path
        get.path = os.path.join(save_path,public.Md5(get.path) + '.tmp')
        if not os.path.exists(get.path): return public.returnMsg(False,'没有可用的草稿!')
        data = self.GetFileInfo(get.path)
        data['file'] = src_path
        if 'rebody' in get: data['body'] = public.readFile(get.path)
        return data

    #清除过期草稿
    def CleanOldTmpFile(self):
        if 'clean_tmp_file' in session: return True
        save_path = '/www/server/panel/temp'
        max_time = 86400 * 30
        now_time = time.time()
        for tmpFile in os.listdir(save_path):
            filename = os.path.join(save_path,tmpFile)
            fileInfo = self.GetFileInfo(filename)
            if now_time - fileInfo['modify_time'] > max_time: os.remove(filename)
        session['clean_tmp_file'] = True
        return True

    #取指定文件信息
    def GetFileInfo(self,path):
        if not os.path.exists(path): return False
        stat = os.stat(path)
        fileInfo = {}
        fileInfo['modify_time'] = int(stat.st_mtime)
        fileInfo['size'] = os.path.getsize(path)
        return fileInfo

    #安装rar组件
    def install_rar(self,get):
        unrar_file = '/www/server/rar/unrar'
        rar_file = '/www/server/rar/rar'
        bin_unrar = '/usr/local/bin/unrar'
        bin_rar = '/usr/local/bin/rar'
        if os.path.exists(unrar_file) and os.path.exists(bin_unrar):
            try:
                import rarfile
            except: 
                os.system("pip install rarfile")
            return True

        import platform
        os_bit = ''
        if platform.machine() == 'x86_64': os_bit = '-x64';
        download_url = public.get_url() + '/src/rarlinux'+os_bit+'-5.6.1.tar.gz';

        tmp_file = '/tmp/bt_rar.tar.gz'
        os.system('wget -O ' + tmp_file + ' ' + download_url)
        if os.path.exists(unrar_file): os.system("rm -rf /www/server/rar")
        os.system("tar xvf " + tmp_file + ' -C /www/server/')
        if os.path.exists(tmp_file): os.remove(tmp_file)
        if not os.path.exists(unrar_file): return False
                
        if os.path.exists(bin_unrar): os.remove(bin_unrar)
        if os.path.exists(bin_rar): os.remove(bin_rar)

        os.system('ln -sf ' + unrar_file + ' ' + bin_unrar)
        os.system('ln -sf ' + rar_file + ' ' + bin_rar)
        os.system("pip install rarfile")
        #public.writeFile('data/restart.pl','True')
        return True
    
    def get_store_data(self):
        data = {}
        path = 'data/file_store.json'
        try:
            if os.path.exists(path):
                data = json.loads(public.readFile(path))
        except :
            data = {}
        if not data:
            data['默认分类'] = []
        return data

    def set_store_data(self,data):
        public.writeFile('data/file_store.json',json.dumps(data))
        return True

    #添加收藏夹分类
    def add_files_store_types(self,get):
        file_type = get.file_type
        if sys.version_info[0] == 2: file_type = file_type.decode('utf-8')
        data = self.get_store_data()
        if file_type in data:  return public.returnMsg(False,'请勿重复添加分类!') 
        
        data[file_type] = []
        self.set_store_data(data)
        return public.returnMsg(True,'添加收藏夹分类成功!') 
     
    #删除收藏夹分类
    def del_files_store_types(self,get):
        file_type = get.file_type
        if sys.version_info[0] == 2: file_type = file_type.decode('utf-8')
        if file_type == '默认分类': return public.returnMsg(False,'默认分类不可被删除!') 
        data = self.get_store_data()
        if file_type in data:
            del data[file_type]
            self.set_store_data(data)
            return public.returnMsg(True,'删除[' + file_type + ']成功!') 
        return public.returnMsg(False,'删除[' + file_type + ']失败!')

    #获取收藏夹
    def get_files_store(self,get):
        data = self.get_store_data()
        result = []
        for key in data:
            rlist = []
            for path in data[key]:
                info = { 'path': path,'name':os.path.basename(path)}

                if os.path.isdir(path) :
                    info['type'] = 'dir'
                else:
                    info['type'] = 'file'
                rlist.append(info)
            result.append({'name':key,'data':rlist})    
       
        return result

    #添加收藏夹
    def add_files_store(self,get):
        file_type = get.file_type
        if sys.version_info[0] == 2: file_type = file_type.decode('utf-8')
        path = get.path
        if not os.path.exists(path):  return public.returnMsg(False,'文件或目录不存在!') 
            
        data = self.get_store_data()
        if path in data[file_type]:  return public.returnMsg(False,'请勿重复添加!') 
        
        data[file_type].append(path)
        self.set_store_data(data)
        return public.returnMsg(True,'添加成功!') 

    #删除收藏夹
    def del_files_store(self,get):
        file_type = get.file_type
        if sys.version_info[0] == 2: file_type = file_type.decode('utf-8')
        path = get.path
        data = self.get_store_data()
        if not file_type in data:  return public.returnMsg(False,'找不到此收藏夹分类!') 
        data[file_type].remove(path)
        if len(data[file_type]) <= 0: data[file_type] = []

        self.set_store_data(data)
        return public.returnMsg(True,'删除成功!') 