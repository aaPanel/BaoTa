#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------
#+--------------------------------------------------------------------
#|   宝塔网站监控报表
#+--------------------------------------------------------------------
import sys 
sys .path .append ('/www/server/panel/class');
import json ,os ,time ,public ,string  ,re
from panelAuth import panelAuth
from BTPanel import session,get_input
class total_main:
    __plugin_path = '/www/server/total'
    __config = None
    
    def __init__(self):
        pass
    
    def get_config(self,get):
        self.__read_config()
        return self.__config;
    
    def set_status(self,get):
        self.__read_config()
        self.__config['open'] = not self.__config['open']
        self.__write_config()
        self.__write_logs("设置网站监控插件状态为[%s]" % (self.__config['open'],))
        return public.returnMsg(False,'设置成功!')
    
    def set_site_value(self,get):
        self.__read_config()
        if type(self.__config['sites'][get.siteName][get.s_key]) == bool:
            get.s_value = not self.__config['sites'][get.siteName][get.s_key]
        elif type(self.__config['sites'][get.siteName][get.s_key]) == int:
            get.s_value = int(get.s_value)
        self.__config['sites'][get.siteName][get.s_key] = get.s_value
        self.__write_logs("设置网站[%s]的[%s]配置项为[%s]" % (get.siteName,get.s_key,get.s_value))
        self.__write_config()
        return public.returnMsg(True,'设置成功!');
    
    def get_total_ip(self,get):
        self.__read_config()
        data = {}
        data['total_ip'] = self.__config['sites'][get.siteName]['total_ip']
        data['total_uri'] = self.__config['sites'][get.siteName]['total_uri']
        return data
    
    def add_total_ip(self,get):
        self.__read_config()
        if get.ip in self.__config['sites'][get.siteName]['total_ip']: return public.returnMsg(False,'指定URI已存在!');
        self.__config['sites'][get.siteName]['total_uri'][get.uri_name] = 0;
        self.__write_logs("向网站[%s]添加自定义统计IP[%s]" % (get.siteName,get.ip))
        self.__write_config()
        return public.returnMsg(False,'添加成功!');
    
    def remove_total_ip(self,get):
        self.__read_config()
        del(self.__config['sites'][get.siteName]['total_ip'][get.ip])
        self.__write_logs("从网站[%s]删除自定义统计IP[%s]" % (get.siteName,get.ip))
        self.__write_config()
        return public.returnMsg(False,'删除成功!');
    
    def get_total_uri(self,get):
        self.__read_config()
        return self.__config['sites'][get.siteName]['total_uri']
    
    def add_total_uri(self,get):
        self.__read_config()
        if get.uri_name in self.__config['sites'][get.siteName]['total_uri']: return public.returnMsg(False,'指定URI已存在!');
        self.__config['sites'][get.siteName]['total_uri'][get.uri_name] = 0;
        self.__write_logs("向网站[%s]添加自定义统计URI[%s]" % (get.siteName,get.uri_name))
        self.__write_config()
        return public.returnMsg(False,'添加成功!');
    
    def remove_total_uri(self,get):
        self.__read_config()
        del(self.__config['sites'][get.siteName]['total_uri'][get.uri_name])
        self.__write_logs("从网站[%s]删除自定义统计URI[%s]" % (get.siteName,get.uri_name))
        self.__write_config()
        return public.returnMsg(False,'删除成功!');
    
    def get_log_exclude_status(self,get):
        self.__read_config()
        return self.__config['sites'][get.siteName]['log_exclude_status']
    
    def add_log_exclude_status(self,get):
        self.__read_config()
        if get.status in self.__config['sites'][get.siteName]['log_exclude_status']: return public.returnMsg(False,'指定响应状态已存在!');
        self.__config['sites'][get.siteName]['log_exclude_status'].insert(0,get.status)
        self.__write_logs("向网站[%s]添加响应状态排除[%s]" % (get.siteName,get.status))
        self.__write_config()
        return public.returnMsg(False,'添加成功!');
    
    def remove_log_exclude_status(self,get):
        self.__read_config()
        status = get.status
        self.__write_logs("从网站[%s]删除响应状态排除[%s]" % (status,))
        self.__config['sites'][get.siteName]['log_exclude_status'].remove(status)
        self.__write_config()
        return public.returnMsg(False,'删除成功!');
    
    def get_log_exclude_extension(self,get):
        return self.__config['sites'][get.siteName]['log_exclude_extension']
    
    def add_log_exclude_extension(self,get):
        self.__read_config()
        if get.ext_name in self.__config['sites'][get.siteName]['log_exclude_extension']: return public.returnMsg(False,'指定扩展名已存在!');
        self.__config['sites'][get.siteName]['log_exclude_extension'].insert(0,get.ext_name)
        self.__write_logs("向网站[%s]添加扩展名排除[%s]" % (get.siteName,get.ext_name))
        self.__write_config()
        return public.returnMsg(False,'添加成功!');
    
    def remove_log_exclude_extension(self,get):
        self.__read_config()
        ext_name = get.ext_name
        self.__write_logs("从网站[%s]删除扩展名排除[%s]" % (ext_name,))
        self.__config['sites'][get.siteName]['log_exclude_extension'].remove(ext_name)
        self.__write_config()
        return public.returnMsg(False,'删除成功!');
    
    def get_global_total(self,get):
        self.__read_config()
        data = {}
        data['client'] = self.__get_file_json(self.__plugin_path + '/total/client.json')
        data['area'] = self.__get_file_json(self.__plugin_path + '/total/area.json')
        data['network'] = self.__get_file_json(self.__plugin_path + '/total/network.json')
        data['request'] = self.__get_file_json(self.__plugin_path + '/total/request.json')
        data['spider'] = self.__get_file_json(self.__plugin_path + '/total/spider.json')
        data['open'] = self.__config['open']
        return data
    
    def get_sites(self,get):
        self._check_site()
        if os.path.exists('/www/server/apache'):
            if not os.path.exists('/usr/local/memcached/bin/memcached'): 
                session['bt_total'] = False
                return public.returnMsg(False,'需要memcached,请先到【软件管理】页面安装!');
            if not os.path.exists('/var/run/memcached.pid'): 
                session['bt_total'] = False
                return public.returnMsg(False,'memcached未启动,请先启动!');

        modc = self.__get_mod(get)
        if not 'bt_total' in session:  return modc;
        result = {}
        data = []
        for siteName in self.__config['sites'].keys():
            tmp = self.__config['sites'][siteName]
            tmp['total'] = self.__get_site_total(siteName)
            tmp['site_name'] = siteName
            del(tmp['log_exclude_extension'])
            del(tmp['log_exclude_status'])
            del(tmp['cdn_headers'])
            del(tmp['total_uri'])
            del(tmp['total_ip'])
            data.append(tmp)
        data = sorted(data, key=lambda x : x['total']['request'], reverse=True);
        data = sorted(data, key=lambda x : x['total']['day_request'], reverse=True);
        result['data'] = data
        result['open'] = self.__config['open']
        self.__write_site_domains()
        return result
    
    def __get_mod(self,get):
        #filename = '/www/server/panel/plugin/bt_total/bt_total_init.py';
        #if os.path.exists(filename): os.remove(filename);
        if 'bt_total' in session: return public.returnMsg(True,'OK!');
        tu = '/proc/sys/net/ipv4/tcp_tw_reuse'
        if public.readFile(tu) != '1': public.writeFile(tu,'1');
        params = {}
        params['pid'] = '100000014';
        result = panelAuth().send_cloud('check_plugin_status',params)
        try:
            if not result['status']: 
                if 'bt_total' in session: del(session['bt_total'])
                return result;
        except: pass;
        session['bt_total'] = True
        return result
    
    def get_total_bysite(self,get):
        self.__read_config()
        tmp = self.__config['sites'][get.siteName]
        tmp['total'] = self.__get_site_total(get.siteName)
        tmp['site_name'] = get.siteName
        get.s_type = 'request'
        tmp['days'] = self.get_site_total_days(get)
        return tmp
        
    def get_site_total_days(self,get):
        get.siteName = self.__get_siteName(get.siteName)
        path = self.__plugin_path + '/total/' + get.siteName + '/' + get.s_type;
        data = []
        if not os.path.exists(path): return data
        for fname in os.listdir(path):
            if fname == 'total.json': continue;
            data.append(fname.split('.')[0])
        
        return sorted(data,reverse=True)
    
    def get_site_network_all(self,get):
        get.siteName = self.__get_siteName(get.siteName)
        path = self.__plugin_path + '/total/' + get.siteName + '/network';
        data = {}
        data['total_size'] = 0;
        network_days = []
        if os.path.exists(path):
            for fname in os.listdir(path):
                if fname == 'total.json': continue;
                day_net = {}
                day_net['date'] = fname.split('.')[0]
                day_net['size'] = 0
                tmp = self.__get_file_json(path + '/' + fname)
                for d in tmp.values(): day_net['size'] += d
                data['total_size'] += day_net['size']
                network_days.append(day_net)
        request_days = []
        data['total_request'] = 0
        path = self.__plugin_path + '/total/' + get.siteName + '/request';
        if os.path.exists(path):
            for fname in os.listdir(path):
                if fname == 'total.json': continue;
                day_req = {}
                day_req['date'] = fname.split('.')[0]
                tmp = self.__get_file_json(path + '/' + fname)
                day_req['request'] = 0
                day_req['ip'] = 0
                day_req['pv'] = 0
                day_req['uv'] = 0
                day_req['post'] = 0
                day_req['get'] = 0
                day_req['put'] = 0
                day_req['500'] = 0
                day_req['502'] = 0
                day_req['503'] = 0
                for c in tmp.values():
                    for d in c:
                        if re.match("^\d+$",d): day_req['request'] += c[d]
                        if 'ip' == d: day_req['ip'] += c['ip']
                        if 'pv' == d: day_req['pv'] += c['pv']
                        if 'uv' == d: day_req['uv'] += c['uv']
                        if 'POST' == d: day_req['post'] += c['POST']
                        if 'GET' == d: day_req['get'] += c['GET']
                        if 'PUT' == d: day_req['put'] += c['PUT']
                        if '500' == d: day_req['500'] += c['500']
                        if '503' == d: day_req['503'] += c['503']
                        if '502' == d: day_req['502'] += c['502']
                data['total_request'] += day_req['request']
                request_days.append(day_req)
                
        data['days'] = []
        for request in request_days:
            request['size'] = 0;
            for s_network in network_days:
                if request['date'] == s_network['date']: request['size'] = s_network['size']
            data['days'].append(request)
        
        data['days'] = sorted(data['days'], key=lambda x : x['date'], reverse=True);
        return data
    
    def get_site_total_byday(self,get):
        get.siteName = self.__get_siteName(get.siteName)
        filename = self.__plugin_path + '/total/' + get.siteName + '/' + get.s_type + '/' + get.s_day + '.json'
        if not os.path.exists(filename): return []
        return self.__sort_json(self.__get_file_json(filename),False)
    
    
    def get_site_total_byspider(self,get):
        get.siteName = self.__get_siteName(get.siteName)
        path = self.__plugin_path + '/total/' + get.siteName + '/spider';
        data = {}
        data['total_day'] = 0
        data['total_all'] = 0
        data['days'] = []
        if not os.path.exists(path): return data
        filename = path + '/total.json'
        data['total_all'] = self.__sum_dict(self.__get_file_json(filename))
        
        today = time.strftime('%Y-%m-%d',time.localtime())
        filename = path + '/'+today+'.json'
        data['total_day'] = self.__sum_dict(self.__get_file_json(filename))
        for fname in os.listdir(path):
            if fname == 'total.json': continue
            filename = path + '/' + fname
            day_data = self.__get_file_json(filename)
            tmp = {}
            tmp['date'] = fname.split('.')[0]
            for s_data in day_data.values():
                for s_key in s_data.keys():
                    if not s_key in tmp: 
                        tmp[s_key] = s_data[s_key]
                    else:
                        tmp[s_key] += s_data[s_key]
            data['days'].append(tmp)
        data['days'] = sorted(data['days'], key=lambda x : x['date'], reverse=True);
        return data
    
    def get_site_total_byclient(self,get):
        get.siteName = self.__get_siteName(get.siteName)
        path = self.__plugin_path + '/total/' + get.siteName + '/client';
        data = []
        if not os.path.exists(path): return data   
        for fname in os.listdir(path):
            if fname == 'total.json': continue
            filename = path + '/' + fname
            day_data = self.__get_file_json(filename)
            tmp = {}
            tmp['date'] = fname.split('.')[0]
            for s_data in day_data.values():
                for s_key in s_data.keys():
                    if not s_key in tmp: 
                        tmp[s_key] = s_data[s_key]
                    else:
                        tmp[s_key] += s_data[s_key]
            data.append(tmp)
        data = sorted(data, key=lambda x : x['date'], reverse=True);
        return data
    
    def get_site_total_byarea(self,get):
        get.siteName = self.__get_siteName(get.siteName)
        if not 's_day' in get: get.s_day = 'total';
        path = self.__plugin_path + '/total/' + get.siteName + '/area/' + get.s_day + '.json';
        data = {}
        data['date'] = get.s_day
        data['num'] = 0
        data['total'] = []
        if not os.path.exists(path): return data
        day_data = self.__get_file_json(path)
        data['num'] = self.__sum_dict(day_data)
        for s_key in day_data.keys():
            tmp1 = {}
            tmp1['area'] = s_key
            tmp1['num'] = day_data[s_key]
            tmp1['percentage'] = round((float(tmp1['num']) / float(data['num'])) * 100.0,2)
            data['total'].append(tmp1)
        data['total'] = sorted(data['total'], key=lambda x:x['num'], reverse=True)
        return data
        
    def __sum_dict(self,data):
        num = 0
        for v in data.values(): 
            if type(v) == int:
                num += v
            else:
                for d in v.values(): num += d
        return num
            
    
    def __sort_json(self,data,dest = True):
        result = []
        for k in data.keys():
            if type(data[k]) == int:
                tmp = {}
                tmp['value'] = data[k]
            else:
                tmp = data[k]
            tmp['key'] = k
            result.append(tmp)
        return sorted(result, key=lambda x : x['key'], reverse=dest)
    
    def get_site_log_days(self,get):
        srcSiteName = get.siteName
        get.siteName = self.__get_siteName(get.siteName)
        self.__read_config()
        data = {}
        data['log_open'] = self.__config['sites'][srcSiteName]['log_open']
        data['save_day'] = self.__config['sites'][srcSiteName]['save_day']
        path = self.__plugin_path + '/logs/' + get.siteName
        data['days'] = []
        if not os.path.exists(path): return data
        for fname in os.listdir(path):
            if fname == 'error': continue;
            data['days'].append(fname.split('.')[0])
        data['days'] = sorted(data['days'], key=lambda x : x, reverse=True)
        return data
    
    def remove_site_log_byday(self,get):
        get.siteName = self.__get_siteName(get.siteName)
        s_path = self.__plugin_path + '/logs/' + get.siteName
        if not 'error_log' in get:
            path = s_path + '/' + get.s_day + '.log'
        else:
            path = s_path + '/error/' + get.s_status + '.log'
        
        if os.path.exists(path): os.remove(path)
        return public.returnMsg(True,'日志清除成功!');
    
    def get_site_log_byday(self,get):
        get.siteName = self.__get_siteName(get.siteName)
        s_path = self.__plugin_path + '/logs/' + get.siteName
        result = {}
        result['total_size'] = 0
        result['size'] = 0
        result['data'] = []
        if not os.path.exists(s_path): return result
        if not 'error_log' in get:
            if not 's_day' in get: return public.returnMsg(False,'请指定日期!')
            path = s_path + '/' + get.s_day + '.log'
            if os.path.exists(path): result['size'] = os.path.getsize(path)
            for uname in os.listdir(s_path):
                filename = s_path + '/' + uname
                if os.path.isdir(filename): continue
                result['total_size'] += os.path.getsize(filename) 
        else:
            if not 's_status' in get: return public.returnMsg(False,'请指定状态!')
            s_path += '/error'
            if not os.path.exists(s_path): return result
            path = s_path + '/' + get.s_status + '.log'
            if os.path.exists(path): result['size'] = os.path.getsize(path)
            for uname in os.listdir(s_path):
                filename = s_path + '/' + uname
                if os.path.isdir(filename): continue
                result['total_size'] += os.path.getsize(filename) 
        try:
            import cgi
            pyVersion = sys.version_info[0]
            num = 10;
            if not os.path.exists(path): return [];
            p = 1;
            if 'p' in get:
                p = int(get.p);
            
            start_line = (p - 1) * num;
            count = start_line + num;
            fp = open(path,'rb')
            buf = ""
            fp.seek(-1, 2)
            if fp.read(1) == "\n": fp.seek(-1, 2)
            data = []
            b = True
            n = 0;
            for i in range(count):
                while True:
                    newline_pos = str.rfind(str(buf), "\n")
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
                        if pyVersion == 3:
                            if type(t_buf) == bytes: t_buf = t_buf.decode('utf-8')
                        buf = t_buf + buf
                        fp.seek(-to_read, 1)
                        if pos - to_read == 0:
                            buf = "\n" + buf
                if not b: break;
            fp.close()
        except: data = []
        result['data'] = data  
        return result
    
    def get_site_error_logs(self,get):
        get.siteName = self.__get_siteName(get.siteName)
        path = self.__plugin_path + '/logs/' + get.siteName + '/error'
        if not os.path.exists(path): return []
        data = []
        for fname in os.listdir(path):
            data.append(fname.split('.')[0])
        return data
    
    
    def _check_site(self):
        self.__read_config()
        sites = public.M('sites').field('name').select();
        siteNames = []
        n = 0
        for siteInfo in sites:
            siteNames.append(siteInfo['name'])
            if siteInfo['name'] in self.__config['sites']: continue
            self.__config['sites'][siteInfo['name']] = self.__get_site_conf()
            n += 1
        
        for sn in self.__config['sites'].keys():
            if sn in siteNames:
                self.__remove_end_logs(sn)
                continue
            del(self.__config['sites'][sn])
            self.__remove_log_file(sn)
            n += 1
        if n > 0: self.__write_config()
        
    def __remove_end_logs(self,siteName):
        s_types = ['client','area','network','request','spider','logs']
        srcSiteName = siteName
        siteName = self.__get_siteName(siteName)
        for types in s_types:
            path = self.__plugin_path + '/logs/' + siteName if types == 'logs' else self.__plugin_path + '/total/' + siteName + '/' + types
            if not os.path.exists(path): continue;
            data = os.listdir(path)
            if 'total.json' in data: data.remove('total.json')
            if 'error' in data: data.remove('error')
            num = len(data) - self.__config['sites'][srcSiteName]['save_day']
            if num <= 0: continue;
            for i in xrange(num):
                log_file = path + '/' + data[i]
                if os.path.exists(log_file): os.remove(log_file)
        
    def __get_site_total(self,siteName):
        data = {}
        get = get_input()
        if hasattr(get,'today'):
            today = get['today']
        else:
            today = time.strftime('%Y-%m-%d',time.localtime())
        data['client'] = 0
        siteName = self.__get_siteName(siteName)
        spdata = self.__get_file_json(self.__plugin_path + '/total/'+siteName+'/client/total.json')
        for c in spdata.values(): data['client'] += c
        
        data['network'] = self.__get_file_json(self.__plugin_path + '/total/'+siteName+'/network/total.json',0)
        data['day_network'] = 0
        path = self.__plugin_path + '/total/'+siteName+'/network/'+today+'.json'
        if os.path.exists(path):
            spdata = self.__get_file_json(path)
            for c in spdata.values(): data['day_network'] += c       
        data['request'] = self.__total_request(self.__plugin_path + '/total/'+siteName+'/request/total.json')
        data['day_request'],data['day_ip'],data['day_pv'],data['day_uv'],data['day_post'],data['day_get'],data['day_put'],data['day_500'],data['day_502'],data['day_503'] = self.__total_request(self.__plugin_path + '/total/'+siteName+'/request/'+today+'.json')
        data['spider'] = 0
        
        spdata = self.__get_file_json(self.__plugin_path + '/total/'+siteName+'/spider/total.json')
        for c in spdata.values(): data['spider'] += c
        
        data['day_spider'] = 0
        path = self.__plugin_path + '/total/'+siteName+'/spider/'+today+'.json'
        if os.path.exists(path):
            spdata = self.__get_file_json(path)
            for c in spdata.values():
                for d in c.values(): data['day_spider'] += d
        return data
    
    def __get_site_total_bysite(self,siteName):
        data= {}
        siteName = self.__get_siteName(siteName)
        data['client'] = self.__get_file_json(self.__plugin_path + '/total/'+siteName+'/client/total.json')
        data['area'] = self.__get_file_json(self.__plugin_path + '/total/'+siteName+'/area/total.json')
        data['network'] = self.__get_file_json(self.__plugin_path + '/total/'+siteName+'/network/total.json',0)
        data['request'] = self.__get_file_json(self.__plugin_path + '/total/'+siteName+'/request/total.json')
        data['spider'] = self.__get_file_json(self.__plugin_path + '/total/'+siteName+'/spider/total.json')
        return data

    def __get_siteName(self,siteName):
        today = time.strftime('%Y-%m-%d',time.localtime())
        s_dir = self.__plugin_path + '/total/'+siteName + '/client/' + today + '.json'
        if os.path.exists(s_dir): return siteName
        pid = public.M('sites').where('name=?',(siteName,)).getField('id');
        if not pid: return siteName
        domains = public.M('domain').where('pid=?',(pid,)).field('name').select()
        public.writeFile('/tmp/1.txt',json.dumps(domains) + ',' + siteName)
        for domain in domains:
            s_dir = self.__plugin_path + '/total/'+domain['name'] + '/client/' + today + '.json'
            if os.path.exists(s_dir): return domain['name']
        return siteName

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
        public.writeFile(self.__plugin_path + '/domains.json',json.dumps(my_domains))
        return my_domains
    
    
    def __total_request(self,path):
        day_request = 0
        day_ip = 0
        day_pv = 0
        day_uv = 0
        day_post = 0
        day_get = 0
        day_put = 0
        day_500 = 0
        day_503 = 0
        day_502  = 0
        if os.path.exists(path):
            spdata = self.__get_file_json(path)
            if path.find('total.json') != -1:
                for c in spdata:
                    if re.match("^\d+$",c): day_request += spdata[c]
                return day_request
           
            for c in spdata.values():
                for d in c:
                    if re.match("^\d+$",d): day_request += c[d]
                    if 'ip' == d: day_ip += c['ip']
                    if 'pv' == d: day_pv += c['pv']
                    if 'uv' == d: day_uv += c['uv']
                    if 'POST' == d: day_post += c['POST']
                    if 'GET' == d: day_get += c['GET']
                    if 'PUT' == d: day_put += c['PUT']
                    if '500' == d: day_500 += c['500']
                    if '503' == d: day_503 += c['503']
                    if '502' == d: day_502 += c['502']
                    
        if path.find('total.json') != -1: return day_request
        return day_request,day_ip,day_pv,day_uv,day_post,day_get,day_put,day_500,day_502,day_503
    
    def __remove_log_file(self,siteName):
        siteName = self.__get_siteName(siteName)
        path = self.__plugin_path + '/total/' + siteName
        if os.path.exists(path): public.ExecShell("rm -rf " + path)
        path = self.__plugin_path + '/logs/' + siteName
        if os.path.exists(path): public.ExecShell("rm -rf " + path)
    
    def __get_site_conf(self):
        if not self.__config: self.__config = self.get_config(None)
        conf = {
                "open":True,
                "log_open":True,
                "save_day":90,
                "cdn":True,
                "cdn_headers":["x-forwarded-for","x-real-ip"],
                "log_exclude_extension":["png","gif","jpg","css","js"],
                "log_exclude_status":[301,302,303,404],
                "total_uri":{},
                "total_ip":{}
                }
        return conf 
        
    def __get_file_json(self,filename,defaultv = {}):
        try:
            if not os.path.exists(filename): return defaultv;
            return json.loads(public.readFile(filename))
        except:
            os.remove(filename)
            return defaultv
    
    def __write_config(self):
        public.writeFile(self.__plugin_path + '/config.json',json.dumps(self.__config))
        public.serviceReload();
    
    def __read_config(self):
        if self.__config: return True
        data = public.readFile(self.__plugin_path + '/config.json')
        self.__config = json.loads(data)
    
    def get_test(self,get):
        return self.__read_config();
        
    def __write_logs(self,logstr):
        public.WriteLog('网站监控',logstr)
