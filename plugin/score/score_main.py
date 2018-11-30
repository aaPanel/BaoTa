#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <2879625666@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   服务器测试
#+--------------------------------------------------------------------

import time,psutil,random,os,urllib,binascii,json,public,re,sys;
class score_main:
    
    __APIURL = 'http://www.bt.cn/api/Auth';
    __UPATH = 'data/userInfo.json';
    __userInfo = None;
    __PDATA = None;
    
    def CheckToken(self):
        pdata = {}
        data = {}
        if os.path.exists(self.__UPATH):
            self.__userInfo = json.loads(public.readFile(self.__UPATH));
            if self.__userInfo:
                pdata['access_key'] = self.__userInfo['access_key'];
                data['secret_key'] = self.__userInfo['secret_key'];
        else:
            pdata['access_key'] = 'test';
            data['secret_key'] = '123456';
        pdata['data'] = data;
        self.__PDATA = pdata;
            
    #修正信息
    def SetScore(self,get):
        if hasattr(get,'ips'):
            return self.SubmitSetScore('ips',get.ips);
        if hasattr(get,'virt'):
            return self.SubmitSetScore('virt',get.virt);
    
    #发送信息修正
    def SubmitSetScore(self,key,value):
        self.CheckToken();
        self.__PDATA['data'][key] = value
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data']);
        result = json.loads(public.httpPost(self.__APIURL+'/SetSocre',self.__PDATA));
        result['data'] = self.En_Code(result['data']);
        return result;
    
    #获取得分列表
    def GetScore(self,get):
        self.CheckToken();
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data']);
        result = json.loads(public.httpPost(self.__APIURL+'/GetSocre',self.__PDATA));
        result['data'] = self.En_Code(result['data']);
        return result;
    
    #获取配置信息
    def GetConfig(self,get=None):
        virt = '/usr/sbin/virt-what'
        if not os.path.exists(virt): 
            if os.path.exists('/etc/yum.repos.d/epel.repo'):
                os.system('mv /etc/yum.repos.d/epel.repo /etc/yum.repos.d/epel.repo_backup');
            os.system('yum install virt-what -y');
            if os.path.exists('/etc/yum.repos.d/epel.repo_backup'): 
                os.system('mv /etc/yum.repos.d/epel.repo_backup /etc/yum.repos.d/epel.repo');
        
        data = {}
        data['virt'] = public.ExecShell('virt-what')[0].strip();
        cpuinfo = open('/proc/cpuinfo','r').read();
        rep = "model\s+name\s+:\s+(.+)"
        tmp = re.search(rep,cpuinfo);
        
        data['cpu'] = tmp.groups()[0];
        data['core'] = psutil.cpu_count();
        data['memory'] = psutil.virtual_memory().total/1024/1024
        data['system'] = self.GetSystemVersion();
        
        scoreInfo = self.readScore();
        data['disk'] = str(scoreInfo['read'])+','+str(scoreInfo['write'])
        data['mem_score'] = scoreInfo['mem'];
        data['cpu_score'] = scoreInfo['cpu1'] + scoreInfo['cpu2'] + scoreInfo['cpu3'] + scoreInfo['cpu4'];
        data['disk_score'] = scoreInfo['disk_score'];
        data['total_score'] = scoreInfo['mem']+data['cpu_score']+scoreInfo['disk_score'];
        return data;
    
    #提交到云端
    def SubmitScore(self,get):
        try:
            self.CheckToken();
            pdata = self.GetConfig(get);
            if not pdata['total_score']: return public.returnMsg(False,'请先跑分!');
            pdata['secret_key'] = self.__userInfo['secret_key'];
            self.__PDATA['data'] = self.De_Code(pdata);
            result = json.loads(public.httpPost(self.__APIURL+'/SubmitScore',self.__PDATA));
            result['data'] = self.En_Code(result['data']);
            return result;
        except:
            return None;
        
    #取操作系统版本
    def GetSystemVersion(self):
        version = public.readFile('/etc/redhat-release')
        if not version:
            version = public.readFile('/etc/issue').replace('\\n \\l','').strip();
        else:
            version = version.replace('release ','').strip();
        return version
    
    #写当前得分
    def writeScore(self,type,value):
        scoreFile = 'plugin/score/score.json';
        tmp = public.readFile(scoreFile)
        if not tmp:
            data = {}
            data['cpu1'] = 0;
            data['cpu2'] = 0;
            data['cpu3'] = 0;
            data['cpu4'] = 0;
            data['mem'] = 0;
            data['disk_score'] = 0;
            data['read'] = 0;
            data['write'] = 0;
            public.writeFile(scoreFile,json.dumps(data));
            tmp = public.readFile(scoreFile)
        
        data = json.loads(tmp);
        data[type] = value;
        public.writeFile(scoreFile,json.dumps(data));
    
    #读当前得分
    def readScore(self):
        scoreFile = 'plugin/score/score.json';
        tmp = public.readFile(scoreFile)
        if not tmp:
            data = {}
            data['cpu1'] = 0;
            data['cpu2'] = 0;
            data['cpu3'] = 0;
            data['cpu4'] = 0;
            data['mem'] = 0;
            data['disk_score'] = 0;
            data['read'] = 0;
            data['write'] = 0;
            public.writeFile(scoreFile,json.dumps(data));
            tmp = public.readFile(scoreFile)
        data = json.loads(tmp);
        return data;
                        
    
    #测试CPU
    def testCpu(self,get,n = 1):
        data = {}
        data['cpuCount'] = psutil.cpu_count();
        if not hasattr(get,'type'): get.type = '0';
        import re;
        cpuinfo = open('/proc/cpuinfo','r').read();
        rep = "model\s+name\s+:\s+(.+)"
        tmp = re.search(rep,cpuinfo);
        data['cpuType'] = ""
        if tmp:
            data['cpuType'] = tmp.groups()[0];
        
        import system
        data['system'] = system.system().GetSystemVersion();
        path = 'plugin/score/testcpu';
        if not os.path.exists(path): os.system('gcc '+path+'.c -o ' +path + ' -lpthread');
        start = time.time();
        os.system(path + ' 32 ' + get.type);
        end = time.time();
        data['score'] = int(400 * 10 / (end - start));
        if not os.path.exists(path): data['score'] = 0;
        self.writeScore('cpu'+get.type, data['score'])
        return data;
        pass
    
    #测试整数运算
    def testInt(self):
        return self.testIntOrFloat(1);
    
    #测试浮点运行
    def testFloat(self):
        return self.testIntOrFloat(1.01);
        
    #CPU测试体
    def testIntOrFloat(self,n=1):
        start = time.time();
        num  = 10000 * 100;
        for i in range(num):
            if i == 0: continue;
            a = n + i;
            b = n - i;
            c = n * i;
            d = n / i;
            n = n + 1;
            
        end = time.time();
        usetime = end - start;
        return num / 100 / usetime;
    
    #冒泡算法测试
    def testBubble(self):
        start = time.time();
        num  = 10000 * 5;
        xx = 'qwertyuiopasdfghjklzxcvbnm1234567890'
        for c in xrange(num):
            lst = []
            for k in range(10):
                lst.append(xx[random.randint(0,len(xx)-1)])
            lst = self.bubbleSort(lst)
        end = time.time();
        usetime = end - start;
        return num / 5 / usetime;
    
    #冒泡排序
    def bubbleSort(self,lst):
        length = len(lst)
        for i in xrange(0, length, 1):
            for j in xrange(0, length-1-i, 1):
                if lst[j] < lst[j+1]:
                    temp = lst[j]
                    lst[j] = lst[j+1]
                    lst[j+1] = temp
        return lst
    
    #二叉树算法测试
    def testTree(self):
        import testTree
        
        start = time.time();
        elems = range(3000)              #生成树节点
        tree = testTree.Tree()           #新建一个树对象
        for elem in elems:                  
            tree.add(elem)               #逐个加入树的节点
    
        tree.level_queue(tree.root)
        tree.front_digui(tree.root)
        tree.middle_digui(tree.root)
        tree.later_digui(tree.root)
        tree.front_stack(tree.root)
        tree.middle_stack(tree.root)
        tree.later_stack(tree.root)
        
        end = time.time();
        usetime = end - start;
        return 3000 / usetime;
    
    
    
    #测试内存
    def testMem(self,get):
        mem = psutil.virtual_memory()
        self.writeScore('mem', mem.total/1024/1024)
        #提交数据
        self.SubmitScore(get)
        return int(mem.total/1024/1024);
    
    #测试磁盘
    def testDisk(self,get):
        import os
        data = {}
        os.system('rm -f testDisk_*');
        filename = "testDisk_" + time.strftime('%Y%m%d%H%M%S',time.localtime());
        data['write'] =  self.testDiskWrite(filename);
        import shutil
        filename2 = "testDisk_" + time.strftime('%Y%m%d%H%M%S',time.localtime());
        shutil.move(filename,filename2);
        data['read'] =  self.testDiskRead(filename2);
        diskIo = psutil.disk_partitions()
        diskInfo = []
        for disk in diskIo:
            tmp = {}
            tmp['path'] = disk[1]
            tmp['size'] = psutil.disk_usage(disk[1])[0]
            diskInfo.append(tmp)
        data['diskInfo'] = diskInfo;
        writeDisk = data['write'];
        if data['write'] > 1000: writeDisk = 1000;
        readDisk = data['read'];
        if data['read'] > 1000: readDisk = 1000;
        
        data['score'] = (writeDisk * 6) + (readDisk * 6)
        os.remove(filename2);
        
        self.writeScore('disk_score', data['score'])
        self.writeScore('write', data['write'])
        self.writeScore('read', data['read'])
        return data;
        pass
    
    #测试磁盘写入速度
    def testDiskWrite(self,filename):
        import random
        start = time.time();
        fp = open(filename,'w+');
        strTest = "";
        strTmp = "";
        for n in range(4):
            strTmp += chr(random.randint(97, 122))
        for n in range(1024):
            strTest += strTmp;
    
        for i in range(1024 * 256):
            fp.write(strTest);
            
        del(strTest);
        del(strTmp);
        fp.close()
        end = time.time();
        usetime = end - start;
        return int(1024/usetime);
        
    #测试磁盘读取速度    
    def testDiskRead(self,filename):
        os.system('echo 3 > /proc/sys/vm/drop_caches');
        import random
        start = time.time();
        fp = open(filename,'r');
        size = 4096;
        while True:
            tmp = fp.read(size);
            if not tmp: break;
            del(tmp);
        fp.close()
        end = time.time();
        usetime = end - start;
        return int(1024/usetime);
    
    def testWorkNet(self):
        pass
    
    
    #加密数据
    def De_Code(self,data):
        if sys.version_info[0] == 2:
            pdata = urllib.urlencode(data);
        else:
            pdata = urllib.parse.urlencode(data);
            if type(pdata) == str: pdata = pdata.encode('utf-8')
        return binascii.hexlify(pdata);
    
    #解密数据
    def En_Code(self,data):
        if sys.version_info[0] == 2:
            result = urllib.unquote(binascii.unhexlify(data));
        else:
            if type(data) == str: data = data.encode('utf-8')
            tmp = binascii.unhexlify(data)
            if type(tmp) != str: tmp = tmp.decode('utf-8')
            result = urllib.parse.unquote(tmp)

        if type(result) != str: result = result.decode('utf-8')
        return json.loads(result);
    