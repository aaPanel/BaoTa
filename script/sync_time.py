import os
import sys
import time
import traceback

try:
    import requests
except:
    os.system("btpip install requests")
    import requests
try:
    import ntplib
except:
    os.system("btpip install ntplib")
    import ntplib
from datetime import datetime

try:
    import pytz
except:
    os.system("btpip install pytz")
    import pytz


def sync_server_time(server, zone):
    try:
        print("正在从{}获取时间...".format(server))
        client = ntplib.NTPClient()
        response = client.request(server, version=3)
        timestamp = response.tx_time
        tz = pytz.timezone(zone)
        time_zone = datetime.fromtimestamp(timestamp, tz)
        local_time = datetime.now()
        offset = timestamp - time.time()
        print("本地时间：", local_time)
        print("服务器时间：", time_zone)
        print("时间偏移：", offset, "秒")
        import os
        print("正在同步时间...")
        os.system('date -s "{}"'.format(time_zone))
        return True
    except Exception as e:
        print("从{}获取时间失败!".format(server))
        # print(traceback.format_exc())
        return False


server_list = ['cn.pool.ntp.org', '0.pool.ntp.org', '2.pool.ntp.org']

if __name__ == '__main__':
    area = sys.argv[1].split('/')[0]
    zone = sys.argv[1].split('/')[1]
    print("当前设置时区：{}".format(sys.argv[1]))
    if not zone:
        exit()
    os.system('rm -f /etc/localtime')
    os.system("ln -s '/usr/share/zoneinfo/" + area + "/" + zone + "' '/etc/localtime'")
    flag = 0
    for server in server_list:
        if sync_server_time(server, sys.argv[1]):
            flag = 1
            print("|-同步时间成功！")
            break
    if flag == 0:
        try:
            print("正在从{}获取时间...".format('http://www.bt.cn'))
            r = requests.get("http://www.bt.cn/api/index/get_time")
            timestamp = int(r.text)
            tz = pytz.timezone(sys.argv[1])
            time_zone = datetime.fromtimestamp(timestamp, tz)
            local_time = datetime.now()
            offset = timestamp - time.time()
            print("本地时间：", local_time)
            print("服务器时间：", time_zone)
            print("时间偏移：", offset, "秒")
            print("正在同步时间...")
            os.system(f"date -s '{time_zone}'")
            flag = 1
            print("|-同步时间成功！")
        except:
            print(traceback.format_exc())
    if flag == 0:
        print("|-同步时间出错！")
