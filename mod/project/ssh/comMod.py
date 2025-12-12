import json
import os
import sys
import time
from datetime import datetime

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

os.chdir("/www/server/panel")
import public
# from mod.project.ssh.base import SSHbase
from mod.project.ssh.journalctlMod import JournalctlManage
from mod.project.ssh.secureMod import SecureManage


class main(JournalctlManage, SecureManage):

    def __init__(self):
        super(main,self).__init__()

    def get_ssh_list(self, get):
        """
        @name 获取日志列表
        @param data:{"p":1,"limit":20,"search":"","select":"ALL"}
        @return list
        """
        page = int(get.p) if hasattr(get, 'p') else 1
        limit = int(get.limit) if hasattr(get, 'limit') else 20
        query = get.get("search", "").strip().lower()
        history = get.get("historyType", "").strip().lower()

        # 读取IP封禁规则
        ip_rules_file = "data/ssh_deny_ip_rules.json"
        try:
            ip_rules = json.loads(public.readFile(ip_rules_file))
        except Exception:
            ip_rules = []

        login_type = self.login_all_flag
        get.select = get.get("select", "ALL")
        if get.select == "Failed":
            login_type = self.login_failed_flag
        elif get.select == "Accepted":
            login_type = self.login_access_flag

        if history == "all":
            self.ssh_log_path += "*"
        count,login_list = self.get_secure_logs(login_type=login_type,pagesize=limit, page=page, query=query)

        for log in login_list:
            if log["address"] in ip_rules:
                log["deny_status"] = 1
        data = self.return_area(login_list, 'address')
        # count = self.get_secure_log_count(login_type, query)
        result = public.get_page(count=count,p=page,rows=limit)
        result["data"] = data

        return result

    def get_ssh_intrusion(self, get):
        """
        @name 登陆详情统计  周期 昨天/今天  类型 成功/失败
        @return {"error": 0, "success": 0, "today_error": 0, "today_success": 0}
        """
        stats = {
            'error': 0,
            'success': 0,
            'today_error': 0,
            'today_success': 0,
            'yesterday_error': 0,
            'yesterday_success': 0,
            'sevenday_error': 0,
            'sevenday_success': 0
        }
        try:
            from datetime import datetime, timedelta
            
            # 获取并更新日志数据
            today = datetime.now()
            yesterday = today - timedelta(days=1)
            
            osv = public.get_os_version().lower()
            #个别系统使用标准时间格式
            date_v1 = ["debian", "opencloudos"]
            is_iso_date = any(d in osv for d in date_v1)
            if is_iso_date:
                # Debian/OpenCloudOS 日志为标准时间
                today_str = today.strftime("%Y-%m-%d")
                yesterday_str = yesterday.strftime("%Y-%m-%d")
            else:
                #centos ubuntu 等日志为月份日期
                today_str = today.strftime("%b %d").replace(" 0", "  ")
                yesterday_str = yesterday.strftime("%b %d").replace(" 0", "  ")
                
            stats['today_error'] = self.get_secure_log_count(self.login_failed_flag, today_str)
            stats['today_success'] = self.get_secure_log_count(self.login_access_flag, today_str)
            stats['yesterday_success'] = self.get_secure_log_count(self.login_access_flag, yesterday_str)
            stats['yesterday_error'] = self.get_secure_log_count(self.login_failed_flag, yesterday_str)
            stats['sevenday_error'] = self.get_secure_log_count(self.login_failed_flag, "")
            stats['sevenday_success'] = self.get_secure_log_count(self.login_access_flag, "")
            
            self.ssh_log_path += "*"
            stats['error'] = self.get_secure_log_count(self.login_failed_flag)
            stats['success'] = self.get_secure_log_count(self.login_access_flag)
        except Exception as e:
            import traceback
            public.print_log(f"获取SSH登录信息失败: {traceback.format_exc()}")
        return stats

    def clean_ssh_list(self, get):
        """
        @name 清空SSH登录记录 只保留最近一周的数据（从周日开始为一周）
        @return: {"status": True, "msg": "清空成功"}
        """

        public.ExecShell("rm -rf /var/log/secure-*;rm -rf /var/log/auth.log.*".format())

        return public.returnMsg(True, '清理成功')

    def index_ssh_info(self, get):
        """
        获取今天和昨天的SSH登录统计
        @return: list [今天登录次数, 昨天登录次数]
        """
        from datetime import datetime, timedelta

        today_count = 0
        yesterday_count = 0

        try:
            # 获取并更新日志数据
            today = datetime.now()
            yesterday = today - timedelta(days=1)

            osv = public.get_os_version().lower()
            #个别系统使用标准时间格式
            date_v1 = ["debian", "opencloudos"]
            is_iso_date = any(d in osv for d in date_v1)
            if is_iso_date:
                # Debian/OpenCloudOS 日志为标准时间
                today_str = today.strftime("%Y-%m-%d")
                yesterday_str = yesterday.strftime("%Y-%m-%d")
            else:
                #centos ubuntu 等日志为月份日期
                today_str = today.strftime("%b %d").replace(" 0", "  ")
                yesterday_str = yesterday.strftime("%b %d").replace(" 0", "  ")

            today_count = self.get_secure_log_count(self.login_all_flag, today_str)
            yesterday_count = self.get_secure_log_count(self.login_all_flag, yesterday_str)
        except Exception as e:
            import traceback
            public.print_log(f"统计SSH登录信息失败: {traceback.format_exc()}")

        return [today_count, yesterday_count]

    def add_cron_job(self,get):
        """
        将 SSH爆破的脚本 添加到定时任务中
        """
        cron_hour = get.get("cron_hour", 1)
        fail_count = get.get("fail_count", 10)
        ban_hour = get.get("ban_hour", 10)
        # public.print_log(f"{cron_hour},{fail_count},{ban_hour}")
        cron_exist = public.M('crontab').where("name='BT-SSH爆破IP封禁[安全-SSH管理-登录日志中添加]'", ()).get()
        if  len(cron_exist) > 0:
            return public.returnMsg(False, '定时任务已存在! 任务详细可在面板计划任务中查看~')


        from time import localtime
        run_minute = localtime().tm_min + 1
        if run_minute == 60: run_minute = 0

        get.name = "BT-SSH爆破IP封禁[安全-SSH管理-登录日志中添加]"
        get.type = "hour-n"
        get.hour = cron_hour
        get.minute = run_minute
        get.where1 = cron_hour
        get.where_hour = cron_hour
        get.week = "1"
        get.timeType = "sday"
        get.timeSet = "1"
        get.sType = "toShell"
        get.sBody = "{path}/pyenv/bin/python3 -u {path}/script/ssh_ban_login_failed.py {cron_hour} {fail_count} {ban_second}".format(
            path = public.get_panel_path(),
            cron_hour = cron_hour,
            fail_count = fail_count,
            ban_second = ban_hour * 3600
        )
        get.sName = ""
        get.backupTo = ""
        get.save = ""
        get.urladdress = ""
        get.save_local = "0"
        get.notice = "0"
        get.notice_channel = ""
        get.datab_name = ""
        get.tables_name = ""
        get.keyword = ""
        get.flock = "1"
        get.stop_site = "0"
        get.version = ""
        get.user = "root"
        from crontab import crontab

        res = crontab().AddCrontab(get)
        if res["status"] == True:
            return public.returnMsg(True,"添加成功，任务将在每{}小时的{}分运行。".format(cron_hour,run_minute))
        public.set_module_logs('SSH', 'add_cron_job', 1)
        return res

    def remove_cron_job(self,get):
        """
        将 SSH爆破的脚本 在定时任务中移除
        """
        cron_exist = public.M('crontab').where("name='BT-SSH爆破IP封禁[安全-SSH管理-登录日志中添加]'", ()).get()
        if len(cron_exist) > 0:
            for crontask in cron_exist:
                get.id = crontask["id"]
                from crontab import crontab

            return crontab().DelCrontab(get)
        else:
            return public.returnMsg(False, '移除失败,定时任务不存在!')

    def run_ban_login_failed_ip(self,get):
        hour = get.get("hour", 1)
        fail_count = get.get("fail_count", 10)
        ban_hour = get.get("ban_hour", 10)

        exec_shell = "{path}/pyenv/bin/python3 -u {path}/script/ssh_ban_login_failed.py {hour} {fail_count} {ban_second}".format(
            path=public.get_panel_path(),
            hour=hour,
            fail_count=fail_count,
            ban_second=ban_hour * 3600
        )
        import panelTask
        task_obj = panelTask.bt_task()
        task_id = task_obj.create_task('SSH封禁爆破IP程序', 0, exec_shell)
        public.set_module_logs('SSH', 'run_ban_login_failed_ip', 1)
        return {'status': True, 'msg': '任务已创建.', 'task_id': task_id}