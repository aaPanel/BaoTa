 #coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2019 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 戴艺森 <623815825@qq.com>
# +-------------------------------------------------------------------
import re, os, sys, time
sys.path.append("class/")
os.chdir('/www/server/panel')
import public, db
from cgi import escape
from urllib import unquote
import MySQLdb


class mysql_conn():
    def __init__(self, user, passwd, db):
        self.conn = MySQLdb.connect(
            host='localhost',
            port=3306,
            user=user,
            passwd=passwd,
            charset="utf8",
            db=db
        )
        self.cur = self.conn.cursor()

    def query(self, sql, params):
        self.cur.execute(sql, params)
        return self

    def findall(self):
        results = self.cur.fetchall()
        return results

    def find(self):
        results = self.cur.fetchone()
        return results
    
    def execute(self, sql):
        self.cur.execute(sql)
        
    def insert_normllog(self, params):
        insert_sql = "INSERT INTO normallog (site,ip, status, size, referer, headers, logtime, mode, url, agreement, spider, browser, terminal)\
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        self.cur.execute(insert_sql, params)
 
    def insert_errorlog(self, params):
        insert_sql = "INSERT INTO errorlog (site,logtime,errorid,level,errorinfo)\
        VALUES (%s,%s,%s,%s,%s);"
        self.cur.execute(insert_sql, params)
        
    def commit(self):
        self.conn.commit()
  
    def close(self):
        self.conn.close()
    
class logs_main():
    
    def __init__(self):
        self._mysql = self.init_mysql_conn()
        self.log_type = public.get_webserver()
        if public.get_webserver() == "nginx":
            self.suffix_access = ".log"
            self.suffix_error = "_error.log"
            
        else:
            self.suffix_access = "-access_log"
            self.suffix_error = "-error_log"
            
        self.file_path = "/www/wwwlogs/"
        self.default_expired_time = 3600*24*30*3
        self.progress_file = "/www/server/panel/plugin/logs/progress.json"
        self.progress = 0
        
    # 解析日志文件
    def parseLog(self, specify_site=None, fromInstart=None):
        if os.path.exists(self.progress_file):
            return False;
        # 记录进度
        sites = [i['name'].encode("utf-8") for i in db.Sql().dbfile('default').table("domain").field("name").select()]
        self.sites_num = len(sites)
        isRevise = False
        for site in sites:
            print "正在分析: ", site
            if specify_site and specify_site != site:
                self.__write_progress_file(0.6)
                continue
            # 记录进度
            self.__write_progress_file(0.05)
            self.site = site
            filename = self.file_path + site+self.suffix_error
            if os.path.exists(filename) and os.path.getsize(filename):
                # 解析error文件
                isRevise = True
                insertFunc = self._mysql.insert_errorlog
                self.run_parse(filename, insertFunc, self.__parseErrorLog)
            # 记录进度
            self.__write_progress_file(0.15)
            filename = self.file_path + site+self.suffix_access
            if os.path.exists(filename) and os.path.getsize(filename):
                # 解析access文件
                isRevise = True
                insertFunc = self._mysql.insert_normllog
                self.run_parse(filename, insertFunc, self.__parseNormalLog)
            # 记录进度
            self.__write_progress_file(0.4)
        # 处理数据表
        # 删除无效站点的日志数据
        sites_tuple = str(tuple(sites))
        if self._mysql.query('select * from logs where site not in %s;' % sites_tuple, "").find():
            self._mysql.execute('DELETE FROM normallog  where site not in %s;' % sites_tuple)
            self._mysql.execute('DELETE FROM errorlog  where site not in %s;' % sites_tuple)
            self._mysql.execute('DELETE FROM logs  where site not in %s;' % sites_tuple)
            self._mysql.commit()
            
        if not isRevise:
            self.__write_progress_file(0.4*self.sites_num)
            # 没有数据提交时， 跳过以下的统计执行
            if os.path.exists(self.progress_file):
                # 删除进度文件
                os.remove(self.progress_file)
            return True
        # 统计总值并删除过期数据
        # 获取最后请求时间
        for site in sites:
            # 统计每个站点的 总流量 最后请求时间
            print "\n正在统计: %s\t" % site,
            site_info = self._mysql.query("select count(*), sum(size),count(mode='GET' OR NULL), count(mode='POST' OR NULL) from normallog where site=%s", [site]).find()
            last_time = self._mysql.query("select logtime from normallog where site=%s order by logtime desc", [site]).find()

            if not site_info or not last_time:
                self.__write_progress_file(0.4)
                continue

            
            access_num, total_size, get_num, post_num = site_info
            last_time = last_time[0]
            site_setinfo =  self._mysql.query("select expiredtime from logs where site=%s limit 1", [site]).find()
            # 从数据库 获取保存时间
            if site_setinfo:
                expired_time = int(time.time())-int(site_setinfo[0])
            else:
                #默认120
                 expired_time = int(time.time())-self.default_expired_time
            # 删除太久远的数据
            # print "expired_time",site, expired_time
            self._mysql.query("DELETE FROM normallog WHERE logtime < %s", [expired_time])
            self._mysql.query("DELETE FROM errorlog WHERE logtime < %s", [expired_time])
            
            self._mysql.query("DELETE FROM times_traffic WHERE start_time < %s", [expired_time])
            self._mysql.query("DELETE FROM ip_days WHERE start_time < %s", [expired_time])
            self._mysql.query("DELETE FROM url_days WHERE start_time < %s", [expired_time])
            self._mysql.query("DELETE FROM referer_days WHERE start_time < %s", [expired_time])
            
            self._mysql.commit()
            if site_setinfo:
                sql = "UPDATE logs SET total_size=%s, access_num=%s, get_num=%s, post_num=%s, lasttime=%s  WHERE site=%s;" ;
                self._mysql.query(sql, [total_size, access_num, get_num, post_num, last_time, site]).find()
            else:
                #add
                sql = "INSERT INTO logs (site, total_size, access_num, post_num, get_num, expiredtime, lasttime) VALUES (%s, %s,%s,%s,%s,%s,%s);"
                self._mysql.query(sql, [site, total_size, access_num, post_num, get_num, self.default_expired_time, last_time])
            self._mysql.commit()
            
        
            
            '''
            last_time     站点的最后一次请求时间
            first_time[0]    站点的第一次请求时间
            last_statis_time     上一次统计时间
            '''
            sql = "select logtime from normallog where site=%s order by logtime asc"
            first_time = self._mysql.query(sql, [site]).find()
            lasttime =last_time - last_time %10
            
            
            # 每隔十分钟统计   请求数 总流量 
            status_list = ('502', '500', '200', '404', '403')
            terminal_list = ("Windows", "Android", "iPhone", "iPad", "Mac OS", "linux")
            status_fields = ",count(status='%s' OR NULL)"*len(status_list) % status_list
            terminal_fields = ",count(terminal='%s' OR NULL)"*len(terminal_list) % terminal_list
            fields = "count(*)" + status_fields + terminal_fields
            
            interval_time = 60*10    #数据的时间间隔
            # 获取上一次统计的最后一个时间段
            sql = "select start_time from times_traffic where site=%s order by start_time desc limit 1"
            last_statis_time = self._mysql.query(sql, [site]).find()
            if last_statis_time:
                firsttime = last_statis_time[0]
            else:
                if first_time:
                    firsttime=first_time[0]
                else:
                    self.__write_progress_file(0.4)
                    break
                firsttime = firsttime - firsttime %10
            fortims = (lasttime - firsttime)/interval_time
            # print "fortims", fortims, lasttime, firsttime
            for n in xrange(fortims):
                start_time, end_time = lasttime-interval_time*n, lasttime-interval_time*(n+1)
                time_limit = "and logtime < %s and logtime > %s" % (start_time, end_time)
                sql = "select %s from normallog where site=%%s %s" % (fields, time_limit)
                num,s502,s500,s200,s404,s403,Windows,Android,iPhone,iPad,Mac_OS,linux = self._mysql.query(sql, [site]).find()
                insert_sql = "INSERT INTO times_traffic (site, start_time, access_num, s502, s500,s200,s404,s403,Windows,Android,iPhone,iPad,Mac_OS,linux)\
                 VALUES (%s, %s, %s, %s, %s,%s, %s, %s, %s, %s,%s, %s, %s, %s);"
                self._mysql.query(insert_sql, [site, start_time,num,s502,s500,s200,s404,s403,Windows,Android,iPhone,iPad,Mac_OS,linux])
            self._mysql.commit()
            self.__write_progress_file(0.1)
            
            # 以下的 一天仅需触发一次，所以选择在 凌晨2点定时触发执行
            if not time.localtime(time.time()).tm_hour == 2 and not fromInstart:
                self.__write_progress_file(0.3)
                continue
            
            # 统计 一天内的url
            print "正在统计URL...\t",
            # 获取上一次统计的最后一个时间段
            self.statistical_day(site,last_time, first_time, "url", "url_days")
            self.__write_progress_file(0.1)
            # 统计 一天内的ip
            print "正在统计请求IP...",
            self.statistical_day(site,last_time, first_time, "ip", "ip_days")
            self.__write_progress_file(0.1)
            # 统计 一天内的 referer
            print "正在统计来路...\t",
            self.statistical_day(site,last_time, first_time, "referer", "referer_days")
            self.__write_progress_file(0.1)

        # 删除进度文件
        os.remove(self.progress_file)
        return True


    def statistical_day(self, site, last_time, first_time, field, table):
        sql = "select start_time from %s where site=%%s  order by start_time desc" % table
        url_last_statis_time = self._mysql.query(sql, [site]).find()
        firsttime = url_last_statis_time[0] if url_last_statis_time else first_time[0]

        insert_sql = "INSERT INTO %s (site, %s, num, start_time) VALUES (%%s, %%s, %%s, %%s);" % (table, field)
        lasttime = last_time-last_time%86400 
        firsttime = firsttime-firsttime%86400 
        interval_time = 60*60*24    #数据的时间间隔
        fortims = (lasttime - firsttime)/interval_time
        # print "fortims", fortims, lasttime, firsttime   
        for n in xrange(fortims):
            start_time, end_time = lasttime-interval_time*n, lasttime-interval_time*(n+1)
            time_limit = "and logtime < %s and logtime > %s" % (start_time, end_time)
            sql = "select %s,count(*) from normallog where site=%%s %s and %s not in ('', '-') group by %s" % (field, time_limit, field, field)
            for info in self._mysql.query(sql, [site]).findall():
                self._mysql.query(insert_sql, [site, info[0],info[1], start_time])
            self._mysql.commit()
                    

                    
    def run_parse(self, filename, insertFunc, parseFunc):
        with open(filename, "r") as logtxt:
            for n, line in enumerate(logtxt):
                try:
                    logsinfo = parseFunc(line)
                except IndexError, e:
                    continue
                res = insertFunc(logsinfo)
                # 每1000条提交一次
                if n % 1000 == 0 and n !=0: self._mysql.commit()
            self._mysql.commit()
  
        # 清空日志文件
        with open(filename, "w") as logtxt:
            logtxt.truncate()
    

    def __write_progress_file(self, weight):
        self.progress += weight
        p = self.progress *100 / self.sites_num
        print '%.1f%%' % p
        public.writeFile(self.progress_file, str(p))
        

    # 解析正常的日志文件
    def __parseNormalLog(self, line):
        spider = ""
        browser = ""
        terminal = ""
        spiderList = ["YandexBot", "AhrefsBot", "Twitterbot", "UptimeRobot", "Yahoo!", "Yisouspider", "ToutiaoSpider",
                        "Sosospider", "EtaoSpider", "Sogou web", "YisouSpider", "Baiduspider", "Auto Shell Spider", "360Spider", "Googlebot","bingbot","ia_archiver"]
        __browser_list = ["UCBrowser", "AppleWebKit", "Firefox", "Chrome", "MSIE", "Trident"]
        terminal_list = ["Windows", "Android", "iPhone", "iPad", "Mac OS", "linux"]
    
        ip = re.findall('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|::1', line)[0]
        [status, size] = re.findall('(\d{3}) (\d{1,8})', line)[0]
        logtime = re.findall('- [-a-z]{1,6} \[(.*?)\]', line)[0]

        logtime = time.mktime(time.strptime(logtime, "%d/%b/%Y:%H:%M:%S +0800"))
        
        info = re.findall('\"(.*?)\"', line)
        if len(info) == 1:
            urlinfo = info[0]
            referer = ""
            headers = ""
        else:
            try:
                [urlinfo, referer, headers] = info
            except:
                urlinfo = ""
                referer = ""
                headers = ""
        if urlinfo:
            agreement = re.findall(' [^\s]*?$', urlinfo)[0]
            mode = re.findall('(^.*?) ', urlinfo)[0]
            url = re.findall(' (.*) [^\s]*?$', urlinfo)[0]
        else:
            agreement=mode=url = ""
        # 蜘蛛选择
        for spider_name in spiderList:
            if headers.find(spider_name) != -1:
                spider = spider_name
                #print spider
                break

        # 浏览器选择
        for browser_name in __browser_list:
            if headers.find(browser_name) != -1:
                browser = browser_name
                break
            
        # 终端选择
        for terminal_name in terminal_list:
            if headers.find(terminal_name) != -1:
                terminal = terminal_name
                break

        return [self.site, escape(ip), status, size, escape(referer[:250]), escape(headers[:250]), logtime, mode, escape(url[:250]), agreement, escape(spider), browser, terminal]
        

    # 解析错误的日志文件
    def __parseErrorLog(self, line):
        if self.log_type == "nginx":
            logtime = re.findall('^(.*?) \[', line)[0]
            
            logtime = self.__converTimeStamp(logtime)
            level = re.findall(' \[([a-z]*?)\]', line)[0]
            errorid = re.findall('\d{3,6}#\d', line)[0]
            errorinfo = re.findall("\d{3,6}#\d: (.*$)", line)[0]
            return (self.site, logtime, level, errorid, errorinfo)
        else:
            info = re.findall('\[([^\[]*?)\] ', line)
            if info:
                logtime = self.__converTimeStamp(info[0])
                level = info[1]
                errorid = info[2] if len(info)>2 and "pid" in info[2] else ""
                errorinfo = re.findall(".*\] (.*$)", line)[0]
                return (self.site, logtime, level, errorid, errorinfo)
            
    def init_mysql_conn(self):
        sqlite = db.Sql().dbfile('default')
        create_table_file = "/www/server/panel/plugin/logs/panel.sql"
        create_table_sql = public.readFile(create_table_file);
        grant_sql = "grant all on panel_logs.* to 'panel_logs'@'localhost';"
        panel_db_info = sqlite.table("databases").field("password").where("name=?", ('panel_logs',)).find()
        passwd=sqlite.table("config").field("mysql_root").find()['mysql_root']
        conn = mysql_conn('root', passwd, 'mysql')
        if not panel_db_info:
            panel_pwd = public.GetRandomString(32)
            create_user_sql = "CREATE USER 'panel_logs'@'localhost' IDENTIFIED BY '%s';" % (panel_pwd)
            sql =  create_table_sql + create_user_sql + grant_sql
            conn.execute(sql)
            sqlite.table("databases").add("name,username,password,accept",('panel_logs','panel_logs',panel_pwd,'127.0.0.1'))
            time.sleep(1)
        else:
            if not conn.query("show databases like 'panel_logs';","").find():
                conn.execute(create_table_sql+grant_sql);
            panel_pwd = panel_db_info['password']
        conn_mysql = mysql_conn('panel_logs', panel_pwd, 'panel_logs')
        return conn_mysql
    

    def __getPageInfo(self, get, count, page_sql, table):
        result='1,2,3,4,5,8'
        import page
        page = page.Page()
        info = {}
        data = {}
        info['count'] = count
        info['row'] = int(get['row']) if hasattr(get, 'row') and get['row'].isdigit() else 5
        info['uri'] = {}
        info['p'] = int(get['p']) if hasattr(get, 'p') and get['p'].isdigit() else 1
        info['return_js'] = get.tojs if hasattr(get, 'tojs') else ''
        data['table'] = table
        data['page'] = page.GetPage(info, result)
        page_sql = page_sql + " limit " + bytes(page.SHIFT) + ',' + bytes(page.ROW)

        if hasattr(get, 'value'):
            params = [get.site, get.value]
        elif hasattr(get, 'site'):
            params = [get.site]
        else:
            params = ""
        
        initTime = time.time()
        data['data'] = self._mysql.query(page_sql, params).findall()
        #print "all _ count 2 :",  time.time() - initTime 
        
        return data
    
    # 转成时间戳
    def __converTimeStamp(self, logtime):
        logtime = re.sub('\.(\d{6})', '' , logtime)
        if logtime[:4].isdigit():
            formatStyle = "%Y/%m/%d %H:%M:%S"
        else:
            formatStyle = "%a %b %d %H:%M:%S %Y"
        timestamp = time.mktime(time.strptime(logtime, formatStyle))
        return int(timestamp)

    # 返回数据处理，更改成json数据
    def __formatData(self, data, fields):
        logs_arr = []
        for line in data["data"]:
            logs = {}
            for index, value in enumerate(line):
                if "count(*)" == fields[index]:
                    fields[index] = "num"
                if "sum(num)" == fields[index]:
                    fields[index] = "num"
                if "num" == fields[index]:
                    logs[fields[index]] = int(value)
                    continue
                logs[fields[index]] = value
            logs_arr.append(logs)
        data["data"] = logs_arr
        return data
    
    
    def Statistical(self, get):
        site=get.site if hasattr(get, 'site') else None
        if not self.parseLog(specify_site=site): # 进行统计
            return public.returnMsg(True,'日志正在统计中，请稍候重试');
        return public.returnMsg(True,'日志更新成功');
    
    
    # 根据站点 统计 mode
    # 根据站点 统计错误等级 level
    # 根据站点 统计终端
    # 根据站点 统计状态码
    # 根据站点 统计spider
    # 根据站点 统计browser
    def getLogsGroupByType(self, get):
        field = get.type.replace('"','').replace("'",'')
        timelimit = ""
        data = {}
        fields = ["count(*)"]
        fields.append(field)
        if hasattr(get, 'start') and get['start'].isdigit() and hasattr(get, 'end') and get['end'].isdigit():
            timelimit = "and logtime > %s and logtime < %s" % (get['start'], get['end'])
        page_sql = "select %s from %s where site=%%s %s and %s not in ('', '-') GROUP by %s ORDER BY count(*) DESC;" % (",".join(fields), get.table, timelimit, field, field)
        data['data'] = self._mysql.query(page_sql, [get.site]).findall()
        return self.__formatData(data, fields)
    
        
    # 根据站点 统计iP访问
    # 根据站点 统计url访问
    # 根据站点 统计referer
    def getLogsGroupByTypePage0(self, get):
        field = get.type.replace('"','').replace("'",'')
        timelimit = ""
        fields = ["count(*)"]
        fields.append(field)
        
        if hasattr(get, 'start') and get['start'].isdigit() and hasattr(get, 'end') and get['end'].isdigit():
            timelimit = "and logtime > %s and logtime < %s" % (get['start'], get['end'])
        page_sql = "select %s from %s where site=%%s %s and %s not in ('', '-') GROUP by %s ORDER BY count(*) DESC" % (",".join(fields), get.table, timelimit, field, field)
        count_sql = "select count(distinct %s) from %s where site=%%s  %s and %s != '' and %s != '-';"  % (field, get.table, timelimit, field, field)
        if hasattr(get, 'site'):
            inittime = time.time()
            count = self._mysql.query(count_sql, [get.site]).find()
            count=count[0] if count else 0
            #print "统计条数 花费时间", time.time() - inittime
            inittime = time.time()
            data = self.__getPageInfo(get, count, page_sql, get.table)
            #print "查询结果 花费时间", time.time() - inittime
            return self.__formatData(data, fields)


    def getLogsGroupByTypePage(self,get):
        field = get.type.replace('"','').replace("'",'')
        timelimit = ""
        fields = ["sum(num)"]
        fields.append(field)
        
        if hasattr(get, 'start') and get['start'].isdigit() and hasattr(get, 'end') and get['end'].isdigit():
            timelimit = "and start_time > %s and start_time < %s" % (get['start'], get['end'])
        table = field+'_days'
        page_sql = "select %s from %s where site=%%s %s group by %s ORDER BY sum(num) DESC" % (",".join(fields),table,timelimit, field)
        count_sql = "select count(distinct %s) from %s where site=%%s %s" % (field, table, timelimit)
        if hasattr(get, 'site'):
            inittime = time.time()
            count = self._mysql.query(count_sql, [get.site]).find()
            count=count[0] if count else 0
            #print "统计条数 花费时间", time.time() - inittime
            inittime = time.time()
            data = self.__getPageInfo(get, count, page_sql, get.table)
            #print "查询结果 花费时间", time.time() - inittime
            return self.__formatData(data, fields) 
    

    def getPieInfo(self, get):
        timelimit = ""
        data = {}
        if hasattr(get, 'start') and get['start'].isdigit() and hasattr(get, 'end') and get['end'].isdigit():
            timelimit = "and start_time > %s and start_time < %s" % (get['start'], get['end'])
        field = "sum(s502),sum(s500),sum(s200),sum(s404), sum(s403),sum(Windows),sum(Android),sum(iPhone),sum(iPad),sum(Mac_OS),sum(linux)"
        page_sql = "select %s from times_traffic where site=%%s %s ORDER BY count(*) DESC;" % (field, timelimit)
        info= self._mysql.query(page_sql, [get.site]).find()
        data['status'] = {}
        '''
        if info[2]: data['status']['s200'] = int(info[2])
        if info[4]: data['status']['s403'] = int(info[4])
        if info[3]: data['status']['s404'] = int(info[3])
        if info[1]: data['status']['s500'] = int(info[1])
        if info[0]: data['status']['s502'] = int(info[0])
        '''
        data['status'] = {'s200':int(info[2]) if info[2] else 0,
                          's403':int(info[4]) if info[4] else 0, 
                          's404':int(info[3]) if info[3] else 0,
                          's500':int(info[1]) if info[1] else 0,
                          's502':int(info[0]) if info[0] else 0 }
        
        data['terminal'] = {'Windows':int(info[5]) if info[5] else 0,
                            'Android':int(info[6]) if info[6] else 0,
                            'iPhone':int(info[7]) if info[7] else 0,
                            'iPad':int(info[8]) if info[8] else 0,
                            'Mac_OS':int(info[9])if info[9] else 0,
                            'linux':int(info[10])if info[10] else 0 }
        return data
        

    
    # 获取所有正常日志信息
    def getNormalLog(self, get):
        timelimit = ""
        fields = ["site","ip", "url", "status", "referer", "spider", "browser", "logtime", "size", "terminal"]     
        if hasattr(get, 'start') and get['start'].isdigit() and hasattr(get, 'end') and get['end'].isdigit():
            timelimit = "and logtime > %s and logtime < %s" % (get['start'], get['end'])

        page_sql = "select %s from normallog where site=%%s %s order by logtime desc" % (",".join(fields), timelimit)
        count_sql = "select count(*) from normallog where site=%%s %s" % timelimit
    

        info = self._mysql.query(count_sql, [get.site]).find()
        count =info[0] if info else 0
        data = self.__getPageInfo(get, count, page_sql, "normallog")
        return self.__formatData(data, fields)
    
    
    # 获取所有错误日志文件信息
    def getErrorLog(self, get):
        timelimit = ""
        fields = ["errorid", "level", "errorinfo", "logtime"]
        if hasattr(get, 'start') and get['start'].isdigit() and hasattr(get, 'end') and get['end'].isdigit():
            timelimit = "and logtime > %s and logtime < %s" % (get['start'], get['end'])
        page_sql = "select %s from errorlog where site=%%s %s order by logtime desc" % (",".join(fields) ,timelimit)
        count_sql = "select count(*) from errorlog where site=%%s %s" % timelimit   
        info = self._mysql.query(count_sql, [get.site]).findall()
        count=info[0][0] if info else 0
        data = self.__getPageInfo(get, count, page_sql, "errorlog")
        return self.__formatData(data, fields)
    
    # 设置过期时间
    def setExpiredTime(self, get):
        if hasattr(get, 'site') and hasattr(get, 'expiredtime') and get['expiredtime'].isdigit():
            if self._mysql.query("select * from logs where site=%s", [get.site]).find():
                if self._mysql.query("UPDATE logs SET expiredtime = %s WHERE site = %s;", [get.expiredtime, get.site]):
                    self._mysql.commit()
                    return public.returnMsg(True,'修改成功！');
        return public.returnMsg(False,'修改失败！');
    
    # 获取站点统计信息
    def getSitesInfo(self, get):
        first = 0 if not hasattr(get, 'first') else 1
        fields = ["site", "total_size", "access_num", "post_num", "get_num", "expiredtime", "lasttime"]
        count = self._mysql.query("select count(*) from logs", "").find()[0]
        page_sql = "select %s from %s" % (",".join(fields), "logs")
        data = self.__getPageInfo(get, count, page_sql, "logs")
        if not data['data'] and first ==0:
            get.first = 1
            self.parseLog()
            return self.getSitesInfo(get)
        elif not data['data']:
            return public.returnMsg(False,'暂无数据，请稍候重试！');
        return self.__formatData(data, fields)

    # 获取每个时间区域的数据量
    def timeZoneInfo(self, get):
        dict = {}
        fields = ["start_time","access_num","s502","s500"]
        if hasattr(get, 'end') and get['end'].isdigit():
            sqlwhere = "site=%s and start_time>%s and start_time<%s"
            params = [get.site, get.start, get.end]
        elif hasattr(get, 'start') and get['start'].isdigit():
            sqlwhere = "site=%s and start_time>%s"
            params = [get.site, get.start]
        else:
            sqlwhere = "site=%s"
            params = [get.site]
        sql = "select %s from times_traffic where " % ",".join(fields) + sqlwhere
        dict['data'] = self._mysql.query(sql, params).findall()
        data = self.__formatData(dict, fields)['data']
        return data[::(300+len(data))/300]
    
    '''
     * 通过字段值 获取该值的信息
     * @param string table 表
     * @param string type 字段名
     * @param string value 字段值
    '''
    def getLogsByTypeValue(self, get):
        timelimit = ""
        type = get.type.replace('"','').replace("'",'')
        if get.table not in ["errorlog", "normallog"]:
            return public.returnMsg(True,'传参有误！'); 
        elif get.table == "normallog":
            fields = ["site", "size", "logtime", "url", "ip", "terminal", "status", "referer", "mode", "spider", "browser"]
        else:
            fields = ["site","logtime","errorid","level","errorinfo"]

        if hasattr(get, 'start') and get['start'].isdigit() and hasattr(get, 'end') and get['end'].isdigit():
            timelimit = "and logtime > %s and logtime < %s" % (get['start'], get['end'])
        
        page_sql = "select %s from %s where site=%%s and %s=%%s %s order by logtime desc" % (",".join(fields), get.table ,type, timelimit)
        count_sql = "select count(*) from %s where site=%%s and %s=%%s %s" % (get.table, type, timelimit)
        info = self._mysql.query(count_sql, [get.site, get.value]).find()
        count=info[0] if info else 0
        data = self.__getPageInfo(get, count, page_sql, get.table)

        return self.__formatData(data, fields)
    
    def isRuning(self, get):
        self.createCrond();
        if not os.path.exists("/www/server/mysql/bin/mysql"):
            return public.returnMsg(False,'请安装MySQL'); 
        if os.path.exists(self.progress_file): 
            progress = public.readFile(self.progress_file)
            if not public.ExecShell('ps -ef|grep logs_main|grep -v grep |grep -v ps')[0]:
                # 存在文件 不存在进程时  删除记录文件
                os.remove(self.progress_file)
            return public.returnMsg(False,'日志正在统计中 %s%%，请稍后重试！'% progress[:3]);
        return public.returnMsg(True,'yes');
    
    def createCrond(self):
        if public.M('crontab').where('name=?',(u'日志分析任务',)).count(): return True;
        import crontab
        data = {}
        data['name'] = '日志分析任务'
        data['type'] = 'minute-n'
        data['where1'] = '30'
        data['sBody'] = 'python /www/server/panel/plugin/logs/logs_main.py'
        data['backupTo'] = 'localhost'
        data['sType'] = 'toShell'
        data['hour'] = ''
        data['minute'] = ''
        data['week'] = ''
        data['sName'] = ''
        data['urladdress'] = ''
        data['save'] = ''
        return crontab.crontab().AddCrontab(data)

if __name__ == "__main__":
    log = logs_main()
    log.parseLog(fromInstart=True)
    