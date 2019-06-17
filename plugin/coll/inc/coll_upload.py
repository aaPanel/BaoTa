#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 6.x
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   微架构 - 文件上传
#+--------------------------------------------------------------------
import re,sys,os,time,json,hashlib,requests

if __name__ != '__main__':
    from inc.coll_db import M,write_log
    from BTPanel import session, redirect,cache,request

class coll_upload:
    __tmp_path = '/www/server/panel/tmp'
    __BT_PANEL = 'http://192.168.1.8:8888'
    __BT_KEY = 'yL2kd0twH2oKE0E7KrfoZRevNTaPUdhE'
    _request = None

    def __init__(self):
        pass


    def __get_md5(self, s):
        m = hashlib.md5()
        m.update(s.encode('utf-8'))
        return m.hexdigest()

    def get_key_data(self):
        now_time = int(time.time())
        p_data = {
            'request_token': self.__get_md5(str(now_time) + '' + self.__get_md5(self.__BT_KEY)),
            'request_time': now_time,
        }
        return p_data

    def upload_file(self,args):
        upload_path = '/www/test'
        file_path='/www/wwwroot/w2.hao.com'
        pdata = self.get_key_data()
        pdata['f_path'] = upload_path
        self._request = requests.session()
        if not os.path.isdir(file_path): return self.start_upload(pdata,file_path)
        n = 0
        size = 0
        for d_info in os.walk(file_path):
            pdata['f_path'] =  os.path.join(upload_path, d_info[0].replace(file_path,''))
            for name in d_info[2]:
                filename = os.path.join(d_info[0], name)
                pdata['f_size'] = os.path.getsize(filename)
                print(filename + ',size:%s' % pdata['f_size']),
                self.start_upload(pdata,filename)
                print(' ==> OK')
                n+=1
                size += pdata['f_size']
        print('successify: %s,size:%s' % (n,(size/1024/1024)))


    
    def get_filename(self,filename):
        return filename.split('/')[-1]
        
        


    def start_upload(self,pdata,filename):
        pdata['f_start'] = 0
        pdata['f_name'] =self.get_filename(filename)
        pdata['action'] = 'upload'
        f = open(filename,'rb')
        ret=self.send_file_to(pdata,f)
        return ret


    def send_file_to(self,data,f):
        max_size = 1024 * 1024 * 2
        f.seek(data['f_start'])
        f_end = max_size
        t_end = data['f_size'] - data['f_start']
        if t_end < max_size: f_end = t_end
        files = {'blob':f.read(f_end)}
        
        ret = self._request.post(self.__BT_PANEL + '/files',data=data,files=files)
        if re.search('^\d+$',ret.text):
            data['f_start'] = int(ret.text)
            return self.send_file_to(data,f)
        else:
            return ret.text


    #上传转发
    def upload_to(self,args):
        if not 'f_name' in args or not 'f_path' in args or args.f_name.find('./') != -1 or args.f_path.find('./') != -1: 
            return public.returnMsg(False,'错误的参数')
        headers = {}
        data = request.form.to_dict()
        data['m'] = 'coll_upload'
        data['f'] = 'upload'

        files = {'blob':(args.f_name,request.files.get("blob").read(),'application/octet-stream',{'Expires': '0'})}
        import requests
        url = 'http://tx002601.if22.cn:8888/coll/ajax.json'
        result = requests.post(url,data=data,files=files)
        return json.loads(result.text)


    #以分片的方式上传文件
    #@param f_path 保存位置
    #@param f_name 文件名
    #@return mixed  int=下一个分片索引位置  dict=错误或成功
    def upload(self,args):
        #校验参数合法性
        if not 'f_name' in args or not 'f_path' in args or args.f_name.find('./') != -1 or args.f_path.find('./') != -1: 
            return public.returnMsg(False,'错误的参数')
        if not os.path.exists(args.f_path): 
            os.makedirs(args.f_path,493)
            self.set_mode(args.f_path)
            

        #检查分片数据位置是否正确
        save_path =  os.path.join(args.f_path,args.f_name+ '.upload.tmp')
        d_size = 0
        if os.path.exists(save_path): d_size = os.path.getsize(save_path)
        if d_size != int(args.f_start): return d_size  #返回正确的分片位置


        #将分片写入临时文件
        upload_files = request.files.getlist("blob")
        f = open(save_path,'ab')
        for tmp_f in upload_files:
            f.write(tmp_f.read())
        f.close()
        
        #返回下一个分片开始长度
        f_size = os.path.getsize(save_path)
        if f_size != int(args.f_size):  return f_size

        #最后处理
        new_name = os.path.join(args.f_path ,args.f_name)
        if os.path.exists(new_name): os.remove(new_name)
        os.renames(save_path, new_name)
        self.set_mode(new_name)
        return public.returnMsg(True,'上传成功!')

    #设置文件和目录权限
    def set_mode(self,path):
        s_path = os.path.dirname(path)
        p_stat = os.stat(s_path)
        os.chown(path,p_stat.st_uid,p_stat.st_gid)
        os.chmod(path,p_stat.st_mode)






                
if __name__ == '__main__':
    p = coll_upload()
    print(p.upload_file(None))