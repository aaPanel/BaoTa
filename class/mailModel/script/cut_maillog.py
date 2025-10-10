#!/usr/bin/python
# coding: utf-8
# -----------------------------
# 定时更新当天日志
# -----------------------------

from datetime import datetime, timedelta
import os,sys, time, re
os.chdir('/www/server/panel')
sys.path.insert(0,'./')
sys.path.insert(1,'class/')
sys.path.insert(2,'BTPanel/')


import public
try:
    from dateutil.parser import parse
except:
    public.ExecShell("btpip install python-dateutil==2.9.0.post0")
    from dateutil.parser import parse

class Cut:
    def __init__(self):

        self.back_log_path = '/www/server/panel/data/mail/back_log'
        self.maillog_path = '/var/log/maillog'
        if "ubuntu" in public.get_linux_distribution().lower():
            self.maillog_path = '/var/log/mail.log'
    def M2(self, table_name):
        import db
        sql = db.Sql()
        sql._Sql__DB_FILE = '/www/vmail/postfixmaillog.db'
        sql._Sql__encrypt_keys = []

        return sql.table(table_name)

    # 日志时间转换
    def parse_log_time(self, line):
        try:
            # First try ISO format
            if line[:4].isdigit():
                return int(parse(line[:31]).timestamp())

            # Then try standard format
            current_year = datetime.now().year
            timestamp_str = f"{line[:15]} {current_year}"
            return int(datetime.strptime(timestamp_str, '%b %d %H:%M:%S %Y').timestamp())
        except:
            return int(datetime.now().timestamp())
    # 当天日志放入单独文件
    def get_today_log(self):

        # 日期格式 Nov 19 兼容 如果日期是1~9时  数字前自动多加一个空格
        today_ = datetime.now()
        today = today_.strftime('%b ') + (str(today_.day).rjust(2) if today_.day < 10 else str(today_.day))
        today0 = datetime.now().strftime('%b %-d')

        # 日期格式 2024-11-20
        full_date = today_.strftime('%Y-%m-%d')

        # 取出当天的日志
        cmd = f"grep -E '({full_date}|{today})' {self.maillog_path} > /tmp/cut_maillog_today.log"
        if today0 != today:
            cmd = f"grep -E '({full_date}|{today}|{today0})' {self.maillog_path} > /tmp/cut_maillog_today.log"
        _, err = public.ExecShell(cmd)
        return

    def align_to_hour(self, timestamp):
        # 获取当前小时，分钟，秒数
        local_time = time.localtime(timestamp)
        return int(time.mktime((local_time.tm_year, local_time.tm_mon, local_time.tm_mday,
                                local_time.tm_hour, 0, 0, 0, 0, -1)))

    # 读取切分出来的日志文件 提取数据写入表
    def get_data_info(self):
        time0 = time.time()
        # data_info = {}
        current_time = datetime.now()
        start_of_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)

        # 生成当天每个整点的时间戳列表
        hour_timestamps = [int((start_of_day + timedelta(hours=i)).timestamp()) for i in range(24)]

        # 改读取当天日志
        today = datetime.now().strftime('%Y-%m-%d')
        # day_log = f"{self.back_log_path}/{today}_mail.log"
        day_log = '/tmp/cut_maillog_today.log'
        if not os.path.exists(day_log):
            return
        log_data = public.readFile(day_log)

        # 获取插入最新数据的时间  例如 3:02  那么从 3:00  开始匹配
        with self.M2("mail_errlog") as obj2:
            lasttime = obj2.order('created desc').getField('created')
        print("Last sync time : {}".format(lasttime))
        # 数据为空时
        if not lasttime:
            lasttime = int(time.time())

        last_time = self.align_to_hour(lasttime)

        try:
            # 判断是否处理过  处理过的小时跳过
            unsubmat = []
            for timestamp in hour_timestamps:
                if timestamp < last_time:
                    # public.print_log("skip--{}".format(timestamp))
                    continue
                else:
                    unsubmat.append(timestamp)

            for i in unsubmat:
                # 当前小时以后的不获取
                current_time = int(time.time())
                if current_time < i:
                    continue
                print("Time period being synchronized : {}".format(i))
                self.get_hour_errinfo(i, log_data)

        except:
            # print(public.get_error_info())
            public.print_log(public.get_error_info())

        time1 = time.time()
        print("get_data_info elapsed time:{} ".format(time1 - time0))

    def get_hour_errinfo(self, timestamp, log_data):
        # 分小时处理日志

        # time0 = time.time()

        start = int(timestamp)
        end = int(timestamp) + 3599

        seen_recipients = set()

        insert_data = []

        # 预编译
        status_pattern = re.compile(r'status=([^ ]+)')
        recipient_pattern = re.compile(r'to=<([^>]+)>')
        delay_pattern = re.compile(r'delay=(\d+(\.\d+)?)')
        delays_pattern = re.compile(r'delays=([\d./*]+)')
        dsn_pattern = re.compile(r'dsn=([\d.]+)')
        relay_pattern = re.compile(r'relay=(.*?)(?=,| )')
        err_info_pattern = re.compile(r'\((.*?)\)')

        for line in log_data.splitlines():

            try:
                log_time = self.parse_log_time(line)
                if end >= log_time >= start:
                    status_match = status_pattern.search(line)
                    recipient_match = recipient_pattern.search(line)
                    if status_match and recipient_match:
                        status = status_match.group(1)
                        if status == 'sent':
                            continue
                        if 'postmaster@' in recipient_match.group(1):
                            continue

                        recipient = recipient_match.group(1)
                        name, domain = recipient.split('@')

                        err_one = {
                            'recipient': recipient,
                            "domain": domain,
                            'status': status,
                            'delay': delay_pattern.search(line).group(1) if delay_pattern.search(line) else '',
                            'delays': delays_pattern.search(line).group(1) if delays_pattern.search(line) else '',
                            'dsn': dsn_pattern.search(line).group(1) if dsn_pattern.search(line) else '',
                            'relay': relay_pattern.search(line).group(1) if relay_pattern.search(line) else '',
                            'err_info': err_info_pattern.search(line).group(1) if err_info_pattern.search(line) else '',
                            'created': log_time
                        }

                        if recipient not in seen_recipients:
                            seen_recipients.add(recipient)
                            insert_data.append(err_one)

                            # with self.M2("mail_errlog") as obj2:
                            #     aa = obj2.insert(err_one)
                            #     # print("更新数据表--{} --{}".format(log_time, aa))


            except Exception as e:
                print(public.get_error_info())
                public.print_log(public.get_error_info())

            if len(insert_data) >= 5000:
                with public.S("mail_errlog","/www/vmail/postfixmaillog.db") as obj2:
                    aa = obj2.insert_all(insert_data, option='IGNORE')
                    # public.print_log("更新数据表--{}".format(aa))
                    insert_data = []


        if len(insert_data)>0:
            with public.S("mail_errlog", "/www/vmail/postfixmaillog.db") as obj2:
                aa = obj2.insert_all(insert_data, option='IGNORE')
                # public.print_log("更新数据表--{}".format(aa))


        # time2 = time.time()
        # public.print_log("匹配后 耗时:{} ".format(time2 - time1))




if __name__ == '__main__':
    cut = Cut()
    # cut.day_log_cut()

    # 筛选出当天日志
    cut.get_today_log()
    cut.get_data_info()
    # public.print_log("ok")
    print("ok")
