# coding: utf-8
# +-------------------------------------------------------------------
# | version :1.0
# +-------------------------------------------------------------------
# | Author: 梁凯强 <1249648969@qq.com>
# +-------------------------------------------------------------------
# | 快速检索
# +--------------------------------------------------------------------
import os,public,re
import zipfile,time,json
import db
class panel_search:
    __backup_path = '/www/server/panel/backup/panel_search/'

    def __init__(self):
        if not os.path.exists(self.__backup_path):
            os.makedirs(self.__backup_path)
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'panel_search_log')).count():
            csql = '''CREATE TABLE `panel_search_log` (`id` INTEGER PRIMARY KEY AUTOINCREMENT, `rtext` TEXT,`exts` TEXT,`path` TEXT,`mode` TEXT,`isword` TEXT,`iscase` TEXT,`noword` TEXT,`backup_path` TEXT,`time` TEXT)'''
            public.M('sqlite_master').execute(csql,())

    def dtchg(self, x):
        try:
            time_local = time.localtime(float(x))
            dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
            return dt
        except:
            return False

    def insert_settings(self, rtext, exts, path, mode, isword,iscase,noword,backup_path):
        inser_time = self.dtchg(int(time.time()))
        data = {"rtext": rtext, "exts": json.dumps(exts), "path": path, "mode": mode,
                "isword": isword, "iscase": iscase,"noword":noword,"backup_path":backup_path,"time":inser_time}
        return public.M('panel_search_log').insert(data)

    '''目录下所有的文件'''
    def get_dir(self, path,exts,text,mode=0,isword=0,iscase=0,noword=0,is_backup=0,rtext=False):
        if rtext or noword:
            result=[]
        else:
            result={}
        if is_backup:
            t = time.strftime('%Y%m%d%H%M%S')
            back_zip = os.path.join(self.__backup_path, "%s.zip" % t)
            zfile = zipfile.ZipFile(back_zip, "w", compression=zipfile.ZIP_DEFLATED)
        else:
            zfile=False
            back_zip=False
        return_data = []
        [[return_data.append(os.path.join(root, file)) for file in files] for root, dirs, files in os.walk(path)]
        for i in return_data:
            for i2 in exts:
                i3 = i.split('.')
                if i3[-1] == i2:

                    temp = self.get_files_lin(i, text, mode, isword, iscase, noword,is_backup,rtext,zfile)
                    if temp:
                        if rtext or noword:
                            if isinstance(result,list):
                                result.append(temp)
                        else:
                            result[i] = temp
        if is_backup:
            if zfile:
                zfile.close()
            self.insert_settings(rtext, exts, path, mode, isword, iscase, noword, back_zip)
            return True
        return result

    '''获取单目录'''
    def get_dir_files(self,path,exts,text,mode=0,isword=0,iscase=0,noword=0,is_backup=0,rtext=False):
        is_list = rtext or noword
        if is_list:
            result=[]
        else:
            result={}
        if is_backup:
            t = time.strftime('%Y%m%d%H%M%S')
            back_zip = os.path.join(self.__backup_path, "%s.zip" % t)
            zfile = zipfile.ZipFile(back_zip, "w", compression=zipfile.ZIP_DEFLATED)
        else:
            zfile=False
            back_zip=False
        list_data=[]
        for root, dirs, files in os.walk(path):
            list_data=files
            break
        for i in exts:
            for i2 in list_data:
                i3=i2.split('.')
                if i3[-1]==i:
                    temp=self.get_files_lin(path+'/'+i2, text,mode,isword,iscase,noword,is_backup,rtext,zfile)
                    if temp:
                        if isinstance(result,list):
                            result.append(path+'/'+i2)
                        else:
                            result[path+'/'+i2]=temp
        if is_backup:
            if zfile:
                zfile.close()
            self.insert_settings(rtext, exts, path, mode, isword, iscase, noword, back_zip)
        return result
    '''
        获取目录下所有的后缀文件
    '''
    def get_exts_files(self,path,exts,text,mode=0,isword=0,iscase=0,noword=0,is_subdir=0,is_backup=0,rtext=False):
        if len(exts)==0:return []
        if is_subdir==0:
            return self.get_dir_files(path,exts,text,mode,isword,iscase,noword,is_backup,rtext)
        elif is_subdir==1:
            return self.get_dir(path,exts,text,mode,isword,iscase,noword,is_backup,rtext)

    '''
       获取文件内的关键词
    '''
    def get_files_lin(self, files, text,mode=0,isword=0,iscase=0,noword=0,is_backup=0,rtext=False,back_zip=False):
        if not os.path.exists(files):return  False
        if os.path.getsize(files) > 1024 * 1024 * 20: return False
        #文件替换部分
        if rtext:
            resutl=[]
            try:
                fp = open(files, 'r', encoding='UTF-8')
            except:
                fp = open(files, 'r')
            content = fp.read()
            fp.close()
            if mode==2:
                    if iscase:
                        if not re.search(text, content, flags=re.I): return False
                        content = re.sub(text, rtext, content, flags=re.I)
                    else:
                        if not re.search(text, content): return False
                        content = re.sub(text, rtext, content)
            else:
                if content.find(text) == -1: return False
                content = content.replace(text, rtext)
            if is_backup and back_zip:
                bf = files.strip('/')
                back_zip.write(files, bf)
            with open(files, 'w') as f:
                f.write(content)
                f.close()
            return files
        else:
            #查找部分
            if noword:
                resutl = []
            else:
                resutl={}
            try:
                fp = open(files, 'r', encoding='UTF-8')
            except:
                fp = open(files, 'r')
            i = 0
            try:
                for line in fp:
                    i += 1
                    if mode==1:
                        if iscase and not re.search(text, line, flags=re.I):
                            continue
                        elif not iscase and not re.search(text, line):
                            continue
                    else:
                        if line.find(text) == -1: continue
                    if noword:
                        return files
                    resutl[i]=line
            except:
                pass
            if resutl:
                return resutl
            return False
    '''
        text 搜索内容
        exts 后缀名   参数例子 php,html
        path 目录
        is_subdir  0 不包含子目录  1 包含子目录
        mode  0 为普通模式  1 为正则模式
        isword  1 全词匹配  0  默认
        iscase  1 不区分大小写 0 默认
        noword 1 不输出行信息  0 默认
    '''
    def get_search(self, args):
        if 'text' not in args or not args.text: return {'error': '搜索信息不能为空'}
        if 'exts' not in args or not args.exts: return {'error': '后缀不能为空；所有文件请输入*.*'}
        if 'path' not in args or not args.path or args.path == '/': return {'error': '目录不能为空或者不能为/'}
        if not os.path.isdir(args.path): return {'error': '目录不存在'}
        text=args.text
        exts=args.exts
        path=args.path
        mode = int(args.mode) if 'mode' in args else 0
        is_subdir = int(args.is_subdir) if 'is_subdir' in args else 0
        iscase = int(args.iscase) if 'iscase' in args else 0
        isword = int(args.isword) if 'isword' in args else 0
        noword = int(args.noword) if 'noword' in args else 0
        exts=exts.split(',')
        is_tmpe_files=self.get_exts_files(path,exts,text,mode,isword,iscase,noword,is_subdir)
        return is_tmpe_files

    '''
        text 搜索内容
        rtext  替换成的内容
        exts 后缀名   参数例子 php,html
        path 目录
        is_subdir  0 不包含子目录  1 包含子目录
        mode  0 为普通模式  1 为正则模式
        isword  1 全词匹配  0  默认
        iscase  1 不区分大小写 0 默认
        noword 1 不输出行信息  0 默认
    '''
    def get_replace(self, args):
        if 'text' not in args or not args.text: return {'error': '搜索信息不能为空'}
        if 'rtext' not in args or not args.text: return {'error': '需要替换的内容不能为空'}
        if 'exts' not in args or not args.exts: return {'error': '后缀不能为空；所有文件请输入*.*'}
        if 'path' not in args or not args.path or args.path == '/': return {'error': '目录不能为空或者不能为/'}
        if not os.path.isdir(args.path): return {'error': '目录不存在'}
        is_backup = int(args.isbackup) if 'isbackup' in args else 0
        text = args.text
        rtext = args.rtext
        exts = args.exts
        path = args.path
        mode = int(args.mode) if 'mode' in args else 0
        is_subdir = int(args.is_subdir) if 'is_subdir' in args else 0
        iscase = int(args.iscase) if 'iscase' in args else 0
        isword = int(args.isword) if 'isword' in args else 0
        noword = int(args.noword) if 'noword' in args else 0
        exts = exts.split(',')
        is_tmpe_files = self.get_exts_files(path, exts, text, mode, isword, iscase, noword, is_subdir,is_backup,rtext)
        return is_tmpe_files

    #替換日志
    def get_replace_logs(self,get):
        import page
        page = page.Page()
        count = public.M('panel_search_log').order('id desc').count()
        limit = 12
        info = {}
        info['count'] = count
        info['row'] = limit
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        info['uri'] = get
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs
        data = {}
        data['page'] = page.GetPage(info, '1,2,3,4,5,8')
        data['data'] = public.M('panel_search_log').field('id,rtext,exts,path,mode,isword,iscase,noword,backup_path,time').order('id desc').limit(str(page.SHIFT) + ',' + str(page.ROW)).select()
        if isinstance(data['data'],str): return public.returnMsg(False,[])
        for i in data['data']:
            if not isinstance(i,dict): continue
            if 'backup_path' in i :
                path=i['backup_path']
                if os.path.exists(path):
                    i['is_path_status']=True
                else:
                    i['is_path_status'] = False
        return public.returnMsg(True, data)