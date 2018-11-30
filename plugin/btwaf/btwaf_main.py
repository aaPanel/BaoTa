#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   宝塔网站防火墙
#+--------------------------------------------------------------------
import sys
sys.path.append('/www/server/panel/class');
import json,os,time,public,string
from panelAuth import panelAuth

class btwaf_main:
    __path = '/www/server/btwaf/'
    __state = {True:'开启',False:'关闭',0:'停用',1:'启用'}
    __config = None
    
    def get_config(self,get):
        config = json.loads(public.readFile(self.__path + 'config.json'));
        if not 'retry_cycle' in config:
            config['retry_cycle'] = 60;
            self.__write_config(config);
        if config['start_time'] == 0:
            config['start_time'] = time.time();
            self.__write_config(config);
        return config
    
    def get_site_config(self,get):
        site_config = public.readFile(self.__path + 'site.json');
        data =  self.__check_site(json.loads(site_config))
        if get:
            total_all = self.get_total(None)['sites']
            site_list = []
            for k in data.keys():
                if not k in total_all: total_all[k] = {}
                data[k]['total'] = self.__format_total(total_all[k])
                siteInfo = data[k];
                siteInfo['siteName'] = k;
                site_list.append(siteInfo);
            data = sorted(site_list,key=lambda x : x['log_size'], reverse=True)
        return data
    
    def get_site_config_byname(self,get):
        site_config = self.get_site_config(None);
        config = site_config[get.siteName]
        config['top'] = self.get_config(None)
        return config
    
    def set_open(self,get):
        config = self.get_config(None)
        if config['open']: 
            config['open'] = False
            config['start_time'] = 0
        else:
            config['open'] = True
            config['start_time'] = int(time.time())
        self.__write_log(self.__state[config['open']] + '网站防火墙(WAF)');
        self.__write_config(config)
        return public.returnMsg(True,'设置成功!');
    
    def set_obj_open(self,get):
        config = self.get_config(None)
        if type(config[get.obj]) != bool:
            if config[get.obj]['open']:
                config[get.obj]['open'] = False
            else:
                config[get.obj]['open'] = True
            self.__write_log(self.__state[config[get.obj]['open']] + '【'+get.obj+'】功能');
        else:
            if config[get.obj]:
                config[get.obj] = False
            else:
                config[get.obj] = True
            self.__write_log(self.__state[config[get.obj]] + '【'+get.obj+'】功能');
            
        self.__write_config(config)
        return public.returnMsg(True,'设置成功!');
    
    def set_site_obj_open(self,get):
        site_config = self.get_site_config(None)
        if type(site_config[get.siteName][get.obj]) != bool:
            if site_config[get.siteName][get.obj]['open']:
                site_config[get.siteName][get.obj]['open'] = False
            else:
                site_config[get.siteName][get.obj]['open'] = True
            self.__write_log(self.__state[site_config[get.siteName][get.obj]['open']] + '网站【' + get.siteName +'】【'+get.obj+'】功能');
        else:
            if site_config[get.siteName][get.obj]:
                site_config[get.siteName][get.obj] = False
            else:
                site_config[get.siteName][get.obj] = True
            self.__write_log(self.__state[site_config[get.siteName][get.obj]] + '网站【' + get.siteName +'】【'+get.obj+'】功能');
        
        if get.obj == 'drop_abroad': self.__auto_sync_cnlist();
        self.__write_site_config(site_config)
        return public.returnMsg(True,'设置成功!');
    
    def set_obj_status(self,get):
        config = self.get_config(None)
        config[get.obj]['status'] = int(get.statusCode)
        self.__write_config(config)
        return public.returnMsg(True,'设置成功!');
    
    def set_cc_conf(self,get):
        config = self.get_config(None)
        config['cc']['cycle'] = int(get.cycle)
        config['cc']['limit'] = int(get.limit)
        config['cc']['endtime'] = int(get.endtime)
        config['cc']['increase'] = (get.increase == '1') | False
        self.__write_config(config)
        self.__write_log('设置全局CC配置为：' +get.cycle+ ' 秒内累计请求超过 ' + get.limit + ' 次后,封锁 ' + get.endtime + ' 秒' + ',增强:' + get.increase);
        return public.returnMsg(True,'设置成功!');
    
    def set_site_cc_conf(self,get):
        site_config = self.get_site_config(None)
        site_config[get.siteName]['cc']['cycle'] = int(get.cycle)
        site_config[get.siteName]['cc']['limit'] = int(get.limit)
        site_config[get.siteName]['cc']['endtime'] = int(get.endtime)
        site_config[get.siteName]['cc']['increase'] = (get.increase == '1') | False
        self.__write_site_config(site_config)
        self.__write_log('设置站点【'+get.siteName+'】CC配置为：' +get.cycle+ ' 秒内累计请求超过 ' + get.limit + ' 次后,封锁 ' + get.endtime + ' 秒' + ',增强:' + get.increase);
        return public.returnMsg(True,'设置成功!');
    
    def add_cnip(self,get):
        ipn = [self.__format_ip(get.start_ip),self.__format_ip(get.end_ip)]
        if not ipn[0] or not ipn[1]: return public.returnMsg(False,'IP段格式不正确');
        if not self.__is_ipn(ipn): return public.returnMsg(False,'起始IP不能大于结束IP');
        iplist = self.__get_rule('cn')
        if ipn in iplist: return public.returnMsg(False,'指定IP段已存在!');
        iplist.insert(0,ipn)
        self.__write_rule('cn', iplist)
        self.__write_log('添加IP段['+get.start_ip+'-'+get.end_ip+']到国内IP库');
        return public.returnMsg(True,'添加成功!');
    
    def remove_cnip(self,get):
        index = int(get.index)
        iplist = self.__get_rule('cn')
        ipn = iplist[index]
        del(iplist[index])
        self.__write_rule('cn', iplist)
        self.__write_log('从国内IP库删除[' + '.'.join(map(str,ipn[0])) + '-' + '.'.join(map(str,ipn[1]))+']');
        return public.returnMsg(True,'删除成功!');
    
    def add_ip_white(self,get):
        ipn = [self.__format_ip(get.start_ip),self.__format_ip(get.end_ip)]
        if not ipn[0] or not ipn[1]: return public.returnMsg(False,'IP段格式不正确');
        if not self.__is_ipn(ipn): return public.returnMsg(False,'起始IP不能大于结束IP');
        iplist = self.__get_rule('ip_white')
        if ipn in iplist: return public.returnMsg(False,'指定IP段已存在!');
        iplist.insert(0,ipn)
        self.__write_rule('ip_white', iplist)
        self.__write_log('添加IP段['+get.start_ip+'-'+get.end_ip+']到IP白名单');
        return public.returnMsg(True,'添加成功!');
    
    def remove_ip_white(self,get):
        index = int(get.index)
        iplist = self.__get_rule('ip_white')
        ipn = iplist[index]
        del(iplist[index])
        self.__write_rule('ip_white', iplist)
        self.__write_log('从IP白名单删除[' + '.'.join(map(str,ipn[0])) + '-' + '.'.join(map(str,ipn[1]))+']');
        return public.returnMsg(True,'删除成功!');
    
    def import_data(self,get):
        name = get.s_Name;        
        pdata = json.loads(get.pdata)
        if not pdata: return public.returnMsg(False,'数据格式不正确');
        iplist = self.__get_rule(name);
        for ips in pdata:            
            if ips in iplist: continue;
            iplist.insert(0,ips)
        self.__write_rule(name, iplist)  
        return public.returnMsg(True,'导入成功!')

    def output_data(self,get):
        iplist = self.__get_rule(get.s_Name)
        return iplist;

    def add_ip_black(self,get):
        ipn = [self.__format_ip(get.start_ip),self.__format_ip(get.end_ip)]
        if not ipn[0] or not ipn[1]: return public.returnMsg(False,'IP段格式不正确');
        if not self.__is_ipn(ipn): return public.returnMsg(False,'起始IP不能大于结束IP');
        iplist = self.__get_rule('ip_black')
        if ipn in iplist: return public.returnMsg(False,'指定IP段已存在!');
        iplist.insert(0,ipn)
        self.__write_rule('ip_black', iplist)
        self.__write_log('添加IP段['+get.start_ip+'-'+get.end_ip+']到IP黑名单');
        return public.returnMsg(True,'添加成功!');
    
    def remove_ip_black(self,get):
        index = int(get.index)
        iplist = self.__get_rule('ip_black')
        ipn = iplist[index]
        del(iplist[index])
        self.__write_rule('ip_black', iplist)
        self.__write_log('从IP黑名单删除[' + '.'.join(map(str,ipn[0])) + '-' + '.'.join(map(str,ipn[1]))+']');
        return public.returnMsg(True,'删除成功!');
    
    def add_url_white(self,get):
        url_white = self.__get_rule('url_white')
        url_rule = get.url_rule.strip()
        if get.url_rule in url_white: return public.returnMsg(False,'您添加的URL已存在')
        url_white.insert(0,url_rule)
        self.__write_rule('url_white', url_white)
        self.__write_log('添加url规则['+url_rule+']到URL白名单');
        return public.returnMsg(True,'添加成功!');
    
    def remove_url_white(self,get):
        url_white = self.__get_rule('url_white')
        index = int(get.index)
        url_rule = url_white[index]
        del(url_white[index])
        self.__write_rule('url_white', url_white)
        self.__write_log('从URL白名单删除URL规则['+url_rule+']');
        return public.returnMsg(True,'删除成功!');
    
    def add_url_black(self,get):
        url_white = self.__get_rule('url_black')
        url_rule = get.url_rule.strip()
        if get.url_rule in url_white: return public.returnMsg(False,'您添加的URL已存在')
        url_white.insert(0,url_rule)
        self.__write_rule('url_black', url_white)
        self.__write_log('添加url规则['+url_rule+']到URL黑名单');
        return public.returnMsg(True,'添加成功!');
    
    def remove_url_black(self,get):
        url_white = self.__get_rule('url_black')
        index = int(get.index)
        url_rule = url_white[index]
        del(url_white[index])
        self.__write_rule('url_black', url_white)
        self.__write_log('从URL黑名单删除URL规则['+url_rule+']');
        return public.returnMsg(True,'删除成功!');
    
    def save_scan_rule(self,get):
        scan_rule = {'header':get.header,'cookie':get.cookie,'args':get.args}
        self.__write_rule('scan_black', scan_rule)
        self.__write_log('修改扫描器过滤规则');
        return public.returnMsg(True,'设置成功')
    
    def set_retry(self,get):
        config = self.get_config(None)
        config['retry'] = int(get.retry)
        config['retry_cycle'] = int(get.retry_cycle)
        config['retry_time'] = int(get.retry_time)
        self.__write_config(config)
        self.__write_log('设置非法请求容忍阈值: ' + get.retry_cycle + ' 秒内累计超过 ' + get.retry + ' 次, 封锁 ' + get.retry_time + ' 秒');
        return public.returnMsg(True,'设置成功!');
    
    def set_site_retry(self,get):
        site_config = self.get_site_config(None)
        site_config[get.siteName]['retry'] = int(get.retry)
        site_config[get.siteName]['retry_cycle'] = int(get.retry_cycle)
        site_config[get.siteName]['retry_time'] = int(get.retry_time)
        self.__write_site_config(site_config)
        self.__write_log('设置网站【'+get.siteName+'】非法请求容忍阈值: ' + get.retry_cycle + ' 秒内累计超过 ' + get.retry + ' 次, 封锁 ' + get.retry_time + ' 秒');
        return public.returnMsg(True,'设置成功!');
    
    def set_site_cdn_state(self,get):
        site_config = self.get_site_config(None)
        if site_config[get.siteName]['cdn']:
            site_config[get.siteName]['cdn'] = False
        else:
            site_config[get.siteName]['cdn'] = True
        self.__write_site_config(site_config)
        self.__write_log(self.__state[site_config[get.siteName]['cdn']] + '站点【'+get.siteName+'】CDN模式');
        return public.returnMsg(True,'设置成功!');
    
    def get_site_cdn_header(self,get):
        site_config = self.get_site_config(None)
        return site_config[get.siteName]['cdn_header']
    
    def add_site_cdn_header(self,get):
        site_config = self.get_site_config(None)
        get.cdn_header = get.cdn_header.strip().lower();
        if get.cdn_header in site_config[get.siteName]['cdn_header']: return public.returnMsg(False,'您添加的请求头已存在!');
        site_config[get.siteName]['cdn_header'].append(get.cdn_header)
        self.__write_site_config(site_config)
        self.__write_log('添加站点【'+get.siteName+'】CDN-Header【'+get.cdn_header+'】');
        return public.returnMsg(True,'添加成功!');
    
    def remove_site_cdn_header(self,get):
        site_config = self.get_site_config(None)
        get.cdn_header = get.cdn_header.strip().lower();
        if not get.cdn_header in site_config[get.siteName]['cdn_header']: return public.returnMsg(False,'指定请求头不存在!');
        for i in range(len(site_config[get.siteName]['cdn_header'])):
            if get.cdn_header == site_config[get.siteName]['cdn_header'][i]:
                self.__write_log('删除站点【'+get.siteName+'】CDN-Header【'+site_config[get.siteName]['cdn_header'][i]+'】');
                del(site_config[get.siteName]['cdn_header'][i])
                break;
        self.__write_site_config(site_config)
        return public.returnMsg(True,'删除成功!');
    
    def get_site_rule(self,get):
        site_config = self.get_site_config(None)
        return site_config[get.siteName][get.ruleName]
    
    def add_site_rule(self,get):
        site_config = self.get_site_config(None)
        if not get.ruleName in site_config[get.siteName]: return public.returnMsg(False,'指定规则不存在!');
        mt = type(site_config[get.siteName][get.ruleName])
        if mt == bool: return public.returnMsg(False,'指定规则不存在!');
        if mt == str: site_config[get.siteName][get.ruleName] = get.ruleValue
        if mt == list:
            if get.ruleName == 'url_rule' or get.ruleName == 'url_tell':
                for ruleInfo in site_config[get.siteName][get.ruleName]:
                    if ruleInfo[0] == get.ruleUri: return public.returnMsg(False,'指定URI已存在!');
                tmp = []
                tmp.append(get.ruleUri)
                tmp.append(get.ruleValue)
                if get.ruleName == 'url_tell': 
                    self.__write_log('添加站点【'+get.siteName+'】URI【'+get.ruleUri+'】保护规则,参数【'+get.ruleValue+'】,参数值【'+get.rulePass+'】');
                    tmp.append(get.rulePass)
                else:
                    self.__write_log('添加站点【'+get.siteName+'】URI【'+get.ruleUri+'】过滤规则【'+get.ruleValue+'】');
                site_config[get.siteName][get.ruleName].insert(0,tmp)
            else:
                if get.ruleValue in site_config[get.siteName][get.ruleName]: return public.returnMsg(False,'指定规则已存在!');
                site_config[get.siteName][get.ruleName].insert(0,get.ruleValue)
                self.__write_log('添加站点【'+get.siteName+'】【'+get.ruleName+'】过滤规则【'+get.ruleValue+'】');
        self.__write_site_config(site_config)
        return public.returnMsg(True,'添加成功!');
    
    
    def remove_site_rule(self,get):
        site_config = self.get_site_config(None)
        index = int(get.index)
        if not get.ruleName in site_config[get.siteName]: return public.returnMsg(False,'指定规则不存在!');
        site_rule = site_config[get.siteName][get.ruleName][index]
        del(site_config[get.siteName][get.ruleName][index])
        self.__write_site_config(site_config)
        self.__write_log('删除站点【'+get.siteName+'】【'+get.ruleName+'】过滤规则【'+json.dumps(site_rule)+'】');
        return public.returnMsg(True,'删除成功!');
    
    def get_rule(self,get):
        rule = self.__get_rule(get.ruleName)
        if not rule: return [];
        return rule
    
    def add_rule(self,get):
        rule = self.__get_rule(get.ruleName)
        ruleValue = [1, get.ruleValue.strip(),get.ps,1]
        for ru in rule:
            if ru[1] == ruleValue[1]: return public.returnMsg(False,'指定规则已存在，请勿重复添加');
        rule.append(ruleValue)
        self.__write_rule(get.ruleName, rule)
        self.__write_log('添加全局规则【'+get.ruleName+'】【'+get.ps+'】');
        return public.returnMsg(True,'添加成功!');
    
    def remove_rule(self,get):
        rule = self.__get_rule(get.ruleName)
        index = int(get.index)
        ps = rule[index][2]
        del(rule[index])
        self.__write_rule(get.ruleName, rule)
        self.__write_log('删除全局规则【'+get.ruleName+'】【'+ps+'】');
        return public.returnMsg(True,'删除成功!');
    
    def modify_rule(self,get):
        rule = self.__get_rule(get.ruleName)
        index = int(get.index)
        rule[index][1] = get.ruleBody
        rule[index][2] = get.rulePs
        self.__write_rule(get.ruleName, rule)
        self.__write_log('修改全局规则【'+get.ruleName+'】【'+get.rulePs+'】');
        return public.returnMsg(True,'修改成功!');
    
    def set_rule_state(self,get):
        rule = self.__get_rule(get.ruleName)
        index = int(get.index)
        if rule[index][0] == 0:
            rule[index][0] = 1;
        else:
            rule[index][0] = 0;
        self.__write_rule(get.ruleName, rule)
        self.__write_log(self.__state[rule[index][0]] + '全局规则【'+get.ruleName+'】【'+rule[index][2]+'】');
        return public.returnMsg(True,'设置成功!');
    
    def get_site_disable_rule(self,get):
        rule = self.__get_rule(get.ruleName)
        site_config = self.get_site_config(None)
        site_rule = site_config[get.siteName]['disable_rule'][get.ruleName]
        for i in range(len(rule)):
            if rule[i][0] == 0: rule[i][0] = -1;
            if i in site_rule: rule[i][0] = 0;
        return rule;
    
    def set_site_disable_rule(self,get):
        site_config = self.get_site_config(None)
        index = int(get.index)
        if index in site_config[get.siteName]['disable_rule'][get.ruleName]:
            for i in range(len(site_config[get.siteName]['disable_rule'][get.ruleName])):
                if index == site_config[get.siteName]['disable_rule'][get.ruleName][i]:
                    del(site_config[get.siteName]['disable_rule'][get.ruleName][i])
                    break
        else:
            site_config[get.siteName]['disable_rule'][get.ruleName].append(index)
        self.__write_log('设置站点【'+get.siteName+'】应用规则【'+get.ruleName+'】状态');
        self.__write_site_config(site_config)
        return public.returnMsg(True,'设置成功!');

    def get_safe_logs(self,get):
        try:
            import cgi
            pythonV = sys.version_info[0]
            if 'drop_ip' in get:
                path = '/www/server/btwaf/drop_ip.log';
                num = 14;
            else:
                path = '/www/wwwlogs/btwaf/' + get.siteName + '_' + get.toDate + '.log';
                num = 10;
            if not os.path.exists(path): return [];
            p = 1;
            if 'p' in get:
                p = int(get.p);
            
            start_line = (p - 1) * num;
            count = start_line + num;
            fp = open(path,'rb')
            buf = ""
            try:
                fp.seek(-1, 2)
            except: return []
            if fp.read(1) == "\n": fp.seek(-1, 2)
            data = []
            b = True
            n = 0;
            for i in range(count):
                while True:
                    newline_pos = str.rfind(buf, "\n")
                    pos = fp.tell()
                    if newline_pos != -1:
                        if n >= start_line:
                            line = buf[newline_pos + 1:]
                            try:
                                data.append(json.loads(cgi.escape(line)))
                            except: pass
                        buf = buf[:newline_pos]
                        n += 1;
                        break;
                    else:
                        if pos == 0:
                            b = False
                            break
                        to_read = min(4096, pos)
                        fp.seek(-to_read, 1)
                        t_buf = fp.read(to_read)
                        if pythonV == 3: t_buf = t_buf.decode('utf-8')
                        buf = t_buf + buf
                        fp.seek(-to_read, 1)
                        if pos - to_read == 0:
                            buf = "\n" + buf
                if not b: break;
            fp.close()
            if 'drop_ip' in get:
                drop_iplist = self.get_waf_drop_ip(None)
                stime = time.time()
                setss = []
                for i in range(len(data)):
                    if (stime - data[i][0]) < data[i][4] and not data[i][1] in setss:
                        setss.append(data[i][1])
                        data[i].append(data[i][1] in drop_iplist)
                    else:
                        data[i].append(False)
        except: data = []         
        return data
    
    def get_logs_list(self,get):
        path = '/www/wwwlogs/btwaf/'
        sfind = get.siteName + '_'
        data = []
        for fname in os.listdir(path):
            if fname.find(sfind) != 0: continue;
            tmp = fname.replace(sfind,'').replace('.log','')
            data.append(tmp)
        return sorted(data,reverse=True);
    
    def get_waf_drop_ip(self,get):
        try:
            return json.loads(public.httpGet('http://127.0.0.1/get_btwaf_drop_ip'))
        except:
            return [];
    def remove_waf_drop_ip(self,get):
        try:
            data = json.loads(public.httpGet('http://127.0.0.1/remove_btwaf_drop_ip?ip=' + get.ip))
            self.__write_log('从防火墙解封IP【'+get.ip+'】');
            return data
        except:
            return public.returnMsg(False,'获取数据失败');
    
    def clean_waf_drop_ip(self,get):
        try:
            return json.loads(public.httpGet('http://127.0.0.1/clean_btwaf_drop_ip'))
            self.__write_log('从防火墙解封所有IP');
        except:
            return public.returnMsg(False,'获取数据失败');
        
    def get_gl_logs(self,get):
        import page
        page = page.Page();
        count = public.M('logs').where('type=?',(u'网站防火墙',)).count();
        limit = 12;
        info = {}
        info['count'] = count
        info['row']   = limit
        info['p'] = 1
        if hasattr(get,'p'):
            info['p']    = int(get['p'])
        info['uri']      = get
        info['return_js'] = ''
        if hasattr(get,'tojs'):
            info['return_js']   = get.tojs
        
        data = {}
        
        #获取分页数据
        data['page'] = page.GetPage(info,'1,2,3,4,5,8');
        data['data'] = public.M('logs').where('type=?',(u'网站防火墙',)).order('id desc').limit(str(page.SHIFT)+','+str(page.ROW)).field('log,addtime').select();
        return data;
            
    def get_total(self,get):
        total = json.loads(public.readFile(self.__path + 'total.json'))
        if type(total['rules']) != dict:
            new_rules = {}
            for rule in total['rules']:
                new_rules[rule['key']] = rule['value'];
            total['rules'] = new_rules;
            self.__write_total(total);
        total['rules'] = self.__format_total(total['rules'])
        return total;
    
    def __format_total(self,total):
        total['get'] = 0;
        if 'args' in total:
            total['get'] += total['args'];
            del(total['args'])
        if 'url' in total:
            total['get'] += total['url'];
            del(total['url'])
        cnkey = [
                 ['post',u'POST渗透'],
                 ['get',u'GET渗透'],
                 ['cc',u"CC攻击"],
                 ['user_agent',u'恶意User-Agent'],
                 ['cookie',u'Cookie渗透'],
                 ['scan',u'恶意扫描'],
                 ['head',u'恶意HEAD请求'],
                 ['url_rule',u'URI自定义拦截'],
                 ['url_tell',u'URI保护'],
                 ['disable_upload_ext',u'恶意文件上传'],
                 ['disable_ext',u'禁止的扩展名'],
                 ['disable_php_path',u'禁止PHP脚本']
                 ]
        data = []
        for ck in cnkey:
            tmp = {}
            tmp['name'] = ck[1]
            tmp['key'] = ck[0]
            tmp['value'] = 0;
            if ck[0] in total: tmp['value'] = total[ck[0]]
            data.append(tmp)
        return data
    
    def get_total_all(self,get):
        self.__check_cjson();
        nginxconf = '/www/server/nginx/conf/nginx.conf';
        if not os.path.exists(nginxconf): return public.returnMsg(False,'只支持nginx服务器');
        if public.readFile(nginxconf).find('luawaf.conf') == -1: return public.returnMsg(False,'当前nginx不支持防火墙,请重装nginx');
        data = {}
        data['total'] = self.get_total(None)
        del(data['total']['sites'])
        data['drop_ip'] = []
        data['open'] = self.get_config(None)['open']
        conf = self.get_config(None)
        data['safe_day'] = 0
        if 'start_time' in conf:
            if conf['start_time'] != 0: data['safe_day'] = int((time.time() - conf['start_time']) / 86400)

        self.__write_site_domains()
        return data

    def __write_site_domains(self):
        sites = public.M('sites').field('name,id').select();
        my_domains = []
        for my_site in sites:
            tmp = {}
            tmp['name'] = my_site['name']
            tmp_domains = public.M('domain').where('pid=?',(my_site['id'],)).field('name').select()
            tmp['domains'] = []
            for domain in tmp_domains:
                tmp['domains'].append(domain['name'])
            my_domains.append(tmp)
        public.writeFile(self.__path + '/domains.json',json.dumps(my_domains))
        return my_domains
    
    #设置自动同步
    def __auto_sync_cnlist(self):       
        id = public.M('crontab').where('name=?',(u'宝塔网站防火墙自动同步中国IP库',)).getField('id');
        import crontab
        if id: crontab.crontab().DelCrontab({'id':id})
        data = {}
        data['name'] = u'宝塔网站防火墙自动同步中国IP库'
        data['type'] = 'day'
        data['where1'] = ''
        data['sBody'] = 'python /www/server/panel/plugin/btwaf/btwaf_main.py'
        data['backupTo'] = 'localhost'
        data['sType'] = 'toShell'
        data['hour'] = '5'
        data['minute'] = '30'
        data['week'] = ''
        data['sName'] = ''
        data['urladdress'] = ''
        data['save'] = ''
        crontab.crontab().AddCrontab(data)
        return public.returnMsg(True,'设置成功!');

    def __get_rule(self,ruleName):
        path = self.__path + 'rule/' + ruleName + '.json';
        rules = public.readFile(path)
        if not rules: return False
        return json.loads(rules)
    
    def __write_rule(self,ruleName,rule):
        path = self.__path + 'rule/' + ruleName + '.json';
        public.writeFile(path,json.dumps(rule))
        public.serviceReload();
    
    def __check_site(self,site_config):
        sites = public.M('sites').field('name').select();
        siteNames = []
        n = 0
        for siteInfo in sites:
            siteNames.append(siteInfo['name'])
            if siteInfo['name'] in site_config: continue
            site_config[siteInfo['name']] = self.__get_site_conf()
            n += 1
        old_site_config = site_config.copy()
        for sn in site_config.keys():
            if sn in siteNames: 
                if not 'retry_cycle' in site_config[sn]:
                    site_config[sn]['retry_cycle'] = 60;
                    n += 1;
                continue
            del(old_site_config[sn])
            self.__remove_log_file(sn)
            n += 1
        

        if n > 0: 
            site_config = old_site_config.copy()
            self.__write_site_config(site_config)
        
        config = self.get_config(None)
        logList = os.listdir(config['logs_path'])
        mday = time.strftime('%Y-%m-%d',time.localtime());
        for sn in siteNames:
            site_config[sn]['log_size'] = 0;
            day_log = config['logs_path'] + '/' + sn + '_' + mday + '.log';
            if os.path.exists(day_log):
                site_config[sn]['log_size'] = os.path.getsize(day_log)
            
            tmp = []
            for logName in logList:
                if logName.find(sn + '_') == -1: continue;
                tmp.append(logName)
            
            length = len(tmp) - config['log_save'];
            if length > 0:
                tmp = sorted(tmp)
                for i in range(length):
                    filename = config['logs_path'] + '/' + tmp[i];
                    if not os.path.exists(filename): continue
                    os.remove(filename)
        return site_config;
    
    def __is_ipn(self,ipn):
        for i in range(4):
            if ipn[0][i] == ipn[1][i]: continue;
            if ipn[0][i] < ipn[1][i]: break;
            return False
        return True
    
    def __format_ip(self,ip):
        tmp = ip.split('.')
        if len(tmp) < 4: return False
        tmp[0] = int(tmp[0])
        tmp[1] = int(tmp[1])
        tmp[2] = int(tmp[2])
        tmp[3] = int(tmp[3])
        return tmp;
    
    def __get_site_conf(self):
        if not self.__config: self.__config = self.get_config(None)
        conf = {
                'open': True,
                'project':'',
                'log': True,
                'cdn': False,
                'cdn_header': ['x-forwarded-for', 'x-real-ip'],
                'retry': self.__config['retry'],
                'retry_cycle': self.__config['retry_cycle'],
                'retry_time': self.__config['retry_time'],
                'disable_php_path': ['^/images/','^/js/','^/css/','^/upload/','^/static/'],
                'disable_path': [],
                'disable_ext': [],
                'disable_upload_ext':['php','jsp'],
                'url_white': [],
                'url_rule': [],
                'url_tell': [],
                'disable_rule': {
                    'url': [],
                    'post': [],
                    'args': [],
                    'cookie': [],
                    'user_agent': []
                },
                'cc': {
                    'open': self.__config['cc']['open'],
                    'cycle': self.__config['cc']['cycle'],
                    'limit': self.__config['cc']['limit'],
                    'endtime': self.__config['cc']['endtime']
                },
                'get': self.__config['get']['open'],
                'post': self.__config['post']['open'],
                'cookie': self.__config['cookie']['open'],
                'user-agent': self.__config['user-agent']['open'],
                'scan': self.__config['scan']['open'],
                'drop_abroad': False
                }
        return conf
    
    def sync_cnlist(self,get):
        if not get:
            self.get_config(None)
            self.get_site_config(None)
        rcnlist = public.httpGet(public.get_url() + '/cnlist.json')
        if not rcnlist: return public.returnMsg(False,'连接云端失败')
        cloudList = json.loads(rcnlist)
        cnlist = self.__get_rule('cn')
        n = 0
        for ipd in cloudList:
            if ipd in cnlist: continue;
            cnlist.append(ipd)
            n += 1
        self.__write_rule('cn', cnlist)
        print('同步成功，本次共增加 ' + str(n) + ' 个IP段');
        if get: return public.returnMsg(True,'同步成功!');
        
    def __remove_log_file(self,siteName):
        public.ExecShell('/www/wwwlogs/btwaf/' + siteName + '_*.log')
        total = json.loads(public.readFile(self.__path + 'total.json'))
        if siteName in total['sites']:
            del(total['sites'][siteName])
            self.__write_total(total)
        return True
            
    def __write_total(self,total):
        return public.writeFile(self.__path + 'total.json',json.dumps(total))

    
    def __write_config(self,config):
        public.writeFile(self.__path + 'config.json',json.dumps(config))
        public.serviceReload();
    
    def __write_site_config(self,site_config):
        public.writeFile(self.__path + 'site.json',json.dumps(site_config))
        public.serviceReload();
    
    def __write_log(self,msg):
        public.WriteLog('网站防火墙',msg)
        
    def __check_cjson(self):
        cjson = '/usr/local/lib/lua/5.1/cjson.so'
        if os.path.exists(cjson): 
            if os.path.exists('/usr/lib64/lua/5.1'):
                if not os.path.exists('/usr/lib64/lua/5.1/cjson.so'):
                    public.ExecShell("ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib64/lua/5.1/cjson.so");
            if os.path.exists('/usr/lib/lua/5.1'):
                if not os.path.exists('/usr/lib/lua/5.1/cjson.so'):
                    public.ExecShell("ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib/lua/5.1/cjson.so");
            return True
        
        c = '''wget -O lua-cjson-2.1.0.tar.gz http://download.bt.cn/install/src/lua-cjson-2.1.0.tar.gz -T 20
tar xvf lua-cjson-2.1.0.tar.gz
rm -f lua-cjson-2.1.0.tar.gz
cd lua-cjson-2.1.0
make
make install
cd ..
rm -rf lua-cjson-2.1.0
ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib64/lua/5.1/cjson.so
ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib/lua/5.1/cjson.so
/etc/init.d/nginx reload
'''
        public.writeFile('/root/install_cjson.sh',c)
        public.ExecShell('cd /root && bash install_cjson.sh')
        return True
    