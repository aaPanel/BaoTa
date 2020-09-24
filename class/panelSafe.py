#!/usr/bin/env python
# encoding: utf-8
  
import os,sys,hashlib,time,re,threading,chardet,json
import public

class safe:
  
    rulelist = [
        {'msg':'GET/POST可能被利用后门','level':'危险','code':'(\$_(GET|POST|REQUEST)\[.{0,15}\]\s{0,10}\(\s{0,10}\$_(GET|POST|REQUEST)\[.{0,15}\]\))'},
        {'msg':'一句话木马','level':'高危','code':'((eval|assert)(\s|\n)*\((\s|\n)*\$_(POST|GET|REQUEST)\[.{0,15}\]\))'},
        {'msg':'一句话木马','level':'高危','code':'(eval(\s|\n)*\(base64_decode(\s|\n)*\((.|\n){1,200})'},
        {'msg':'WebShell行为','level':'危险','code':'(function\_exists\s*\(\s*[\'|\"](shell\_exec|system|popen|exec|proc\_open|passthru)+[\'|\"]\s*\))'},
        {'msg':'WebShell行为','level':'危险','code':'((exec|shell\_exec|passthru)+\s*\(\s*\$\_(\w+)\[(.*)\]\s*\))'},
        {'msg':'可被利用漏洞','level':'危险','code':'(\$(\w+)\s*\(\s.chr\(\d+\)\))'},
        {'msg':'WebShell行为','level':'危险','code':'(\$(\w+)\s*\$\{(.*)\})'},
        {'msg':'GET/POST/COOKIE可能被利用后门','level':'危险','code':'(\$(\w+)\s*\(\s*\$\_(GET|POST|REQUEST|COOKIE|SERVER)+\[(.*)\]\s*\))'},
        {'msg':'GET/POST/COOKIE可能被利用后门','level':'危险','code':'(\$\_(GET|POST|REQUEST|COOKIE|SERVER)+\[(.*)\]\(\s*\$(.*)\))'},
        {'msg':'WebShell行为','level':'危险','code':'(\$\_\=(.*)\$\_)'},
        {'msg':'WebShell行为','level':'危险','code':'(\$(.*)\s*\((.*)\/e(.*)\,\s*\$\_(.*)\,(.*)\))'},
        {'msg':'WebShell行为','level':'危险','code':'(new com\s*\(\s*[\'|\"]shell(.*)[\'|\"]\s*\))'},
        {'msg':'WebShell行为','level':'危险','code':'(echo\s*curl\_exec\s*\(\s*\$(\w+)\s*\))'},
        {'msg':'危险文件操作漏洞','level':'高危','code':'((fopen|fwrite|fputs|file\_put\_contents)+\s*\((.*)\$\_(GET|POST|REQUEST|COOKIE|SERVER)+\[(.*)\](.*)\))'},
        {'msg':'危险上传漏洞','level':'危险','code':'(\(\s*\$\_FILES\[(.*)\]\[(.*)\]\s*\,\s*\$\_(GET|POST|REQUEST)+\[(.*)\]\[(.*)\]\s*\))'},
        {'msg':'危险引用','level':'高危','code':'(\$\_(\w+)(.*)(eval|assert|include|require|include\_once|require\_once)+\s*\(\s*\$(\w+)\s*\))'},
        {'msg':'危险引用','level':'高危','code':'((include|require|include\_once|require\_once)+\s*\(\s*[\'|\"](\w+)\.(jpg|gif|ico|bmp|png|txt|zip|rar|htm|css|js)+[\'|\"]\s*\))'},
        {'msg':'可被利用漏洞','level':'危险','code':'(eval\s*\(\s*\(\s*\$\$(\w+))'},
        {'msg':'一句话木马','level':'高危','code':'((eval|assert|include|require|include\_once|require\_once|array\_map|array\_walk)+\s*\(\s*\$\_(GET|POST|REQUEST|COOKIE|SERVER|SESSION)+\[(.*)\]\s*\))'},
        {'msg':'一句话木马','level':'危险','code':'(preg\_replace\s*\((.*)\(base64\_decode\(\$)'}
        ]
    
    ruleFile = '/www/server/panel/data/ruleList.conf';
    if not os.path.exists(ruleFile): public.writeFile(ruleFile,json.dumps(rulelist));
    rulelist = json.loads(public.readFile(ruleFile));
    
    result = {};
    result['data'] = []
    result['phpini'] = []
    result['userini'] = result['sshd'] = result['scan'] = True;
    result['outime'] = result['count'] = result['error'] = 0
    
    def scan(self,path):
        start = time.time();
        ce = ['.jsp','.asp','.html','.htm','.php','.tpl','.xml']
        for root,dirs,files in os.walk(path):
            for filespath in files:
                if not os.path.splitext(filespath)[1] in ce: continue;
                if os.path.getsize(os.path.join(root,filespath)) < 262144:
                    filename = os.path.join(root,filespath);
                    self.threadto(filename);
        end = time.time();
        self.result['outime'] = int(end - start)
    
    def threadto(self,filename):
        print 'scanning ' + filename,
        file= open(filename)
        filestr = file.read()
        char=chardet.detect(filestr)
        try:
            filestr = filestr.decode(char['encoding'])
        except:
            return;
        file.close()
        for rule in self.rulelist:
            tmps = re.compile(rule['code']).findall(filestr)
            if tmps:
                tmp = {}
                tmp['msg'] = rule['msg'];
                tmp['level'] = rule['level'];
                tmp['filename'] = filename;
                tmp['code'] = str(tmps[0][0:200])
                tmp['etime'] = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(os.path.getmtime(filename)))
                self.result['data'].append(tmp);
                self.result['error'] += 1
                break
        print '  done'
        self.result['count'] += 1
        public.writeFile(self.result['path'] + '/scan.pl',json.dumps(self.result));
        del(filestr)
        
    def md5sum(self,md5_file):
        m = hashlib.md5()
        fp = open(md5_file)
        m.update(fp.read())
        return m.hexdigest()
        fp.close()
        
    
    def checkUserINI(self,path):
        self.result['userini'] =  os.path.exists(path+'/.user.ini');
        if not self.result['userini']: self.result['error'] += 1;
        public.writeFile(self.result['path'] + '/scan.pl',json.dumps(self.result));
    
    def checkPHPINI(self):
        setupPath = '/www/server';
        phps = ['52','53','54','55','56','70','71']
        rep = "disable_functions\s*=\s*(.+)\n"
        defs = ['passthru','exec','system','chroot','chgrp','chown','shell_exec','popen','ini_alter','ini_restore','dl','openlog','syslog','readlink','symlink','popepassthru']
        data = []
        for phpv in phps:
            phpini = setupPath + '/php/'+phpv+'/etc/php.ini';
            if not os.path.exists(phpini): continue;
            conf = public.readFile(phpini);
            tmp = re.search(rep,conf).groups();
            disables = tmp[0].split(',');
            for defstr in defs:
                if defstr in disables: continue;
                tmp = {}
                tmp['function'] = defstr;
                tmp['version'] = phpv;
                self.result['phpini'].append(tmp);
        self.result['error'] += len(self.result['phpini']);
        public.writeFile(self.result['path'] + '/scan.pl',json.dumps(self.result));
            
        
        
    def checkSSH(self):
        if self.md5sum('/etc/issue') == '3e3c7c4194b12af573ab11c16990c477':
            if self.md5sum('/usr/sbin/sshd') != 'abf7a90c36705ef679298a44af80b10b':  self.result['sshd'] = False
                
        if self.md5sum('/etc/issue') == '6c9222ee501323045d85545853ebea55':
            if self.md5sum('/usr/sbin/sshd') != '4bbf2b12d6b7f234fa01b23dc9822838': self.result['sshd'] = False
        self.result['sshd'] = True
        public.writeFile(self.result['path'] + '/scan.pl',json.dumps(self.result));
    
    
                
    def suspect(self,path):
        self.result['path'] = path;
        self.checkSSH();
        self.checkPHPINI();
        self.checkUserINI(path);
        public.writeFile(self.result['path'] + '/scan.pl',json.dumps(self.result));
        self.scan(path);
        self.result['scan'] = False
        public.writeFile(self.result['path'] + '/scan.pl',json.dumps(self.result));
        return self.result;

if __name__=='__main__':
  
    if len(sys.argv)!=2:
        print('参数错误')
        exit();
    if os.path.lexists(sys.argv[1]) == False:
        print("目录不存在")
        exit();
    if len(sys.argv) ==2:
        safe().suspect(sys.argv[1]);
    else:
        exit()