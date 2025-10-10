import os,sys,time
panel_path = '/www/server/panel'
os.chdir(panel_path)
sys.path.append('class')
sys.path.insert(0, panel_path)
import public


# 检查是否有其他进程在运行
pidfile = '/tmp/panel_daily.pid'
if os.path.exists(pidfile):
    pid = public.readFile(pidfile)
    proc_stat_file = '/proc/{}/stat'.format(pid)
    if os.path.exists(proc_stat_file):
        public.print_log('daily.py is running')
        sys.exit()

# 写入PID文件
public.writeFile(pidfile, str(os.getpid()))

from pluginAuth import Plugin
plugin_obj = Plugin(False)
plugin_list = plugin_obj.get_plugin_list()
if plugin_list["ltd"] < 0 and plugin_list["pro"] < 0:
    sys.exit(0)

from panelDaily import panelDaily
pd = panelDaily()
pd.check_databases()

# 日报数据收集
start_daily_file = os.path.join(panel_path, 'data/start_daily.pl')
if os.path.exists(start_daily_file):
    try:
        t_now = time.localtime()
        yesterday = time.localtime(time.mktime((
            t_now.tm_year, t_now.tm_mon, t_now.tm_mday - 1,
            0, 0, 0, 0, 0, 0
        )))
        yes_time_key = pd.get_time_key(yesterday)
        store_app_usage_file = os.path.join(panel_path, 'data/store_app_usage.pl')
        con = public.ReadFile(store_app_usage_file)
        # self.write_log(str(con))
        store = False
        if con:
            if con != str(yes_time_key):
                store = True
        else:
            store = True

        if store:
            date_str = str(yes_time_key)
            pd.store_app_usage(yes_time_key)
            pd.check_server()
            daily_data = pd.get_daily_data_local(date_str)
            if "status" in daily_data.keys():
                if daily_data["status"]:
                    score = daily_data["score"]
                    if public.M("system").dbfile("system").table("daily").where("time_key=?", (yes_time_key,)).count() == 0:
                        public.M("system").dbfile("system").table("daily").add("time_key,evaluate,addtime", (yes_time_key, score, time.time()))
                    public.WriteFile(store_app_usage_file, str(yes_time_key), "w")
    except Exception as e:
        public.print_log("存储应用空间信息错误:" + str(e))

# 删除PID文件
if os.path.exists(pidfile):
    os.remove(pidfile)