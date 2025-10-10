import json
import sys, os
import time
import traceback

os.chdir('/www/server/panel')
sys.path.insert(0, "class/")
sys.path.insert(0, '/www/server/panel')
import crontab
import public

from mod.base.push_mod import push_by_task_keyword
from mod.base.push_mod.web_log_push import WEBLogTask


def run(path) -> list:
    from log_analysis import log_analysis
    log_analysis = log_analysis()
    get = public.dict_obj()
    get.action = 'log_analysis'
    get.path = path
    res = log_analysis.log_analysis(get)
    if res['status'] is False:
        return [res["msg"]]
    get.action = 'speed_log'
    start_time = time.time()
    while True:
        time.sleep(1)
        data = log_analysis.speed_log(get)
        if int(data['msg']) == 100 or data['status'] == False:
            break
        if time.time() - start_time > 100:
            break

    get.action = 'get_result'
    res = log_analysis.get_result(get)
    data = res['data'][0]
    msg_list = []
    if data['is_status']:
        all_num = data['php'] + data['san'] + data['sql'] + data['xss']
        if all_num > 0:
            msg_list.append('【异常】，共发现{}条异常日志。'.format(all_num))
            if data['php'] > 0:
                msg_list.append('PHP攻击{}条。'.format(data['php']))
            if data['san'] > 0:
                msg_list.append('恶意扫描{}条。'.format(data['san']))
            if data['sql'] > 0:
                msg_list.append('SQL注入攻击{}条。'.format(data['sql']))
            if data['xss'] > 0:
                msg_list.append('XSS攻击{}条。'.format(data['xss']))
        else:
            msg_list.append('【安全】，未发现异常日志。')
    return msg_list


def send_notification(title, msg, channels):
    data = public.get_push_info(title, msg)
    for channel in channels.split(','):
        try:
            obj = public.init_msg(channel)
            obj.send_msg(data['msg'])
            print('{}通道发送成功'.format(channel))
        except:
            print('{}通道发送失败'.format(channel))


if __name__ == '__main__':
    resource = []
    cron_task_path = '/www/server/panel/data/cron_task_analysis.json'
    if not os.path.exists(cron_task_path) or len(json.loads(public.ReadFile(cron_task_path))) <= 1:
        cron_name = '[勿删]web日志定期检测服务'
        p = crontab.crontab()
        id = public.M('crontab').where("name=?", (cron_name,)).getField('id')
        args = {"id": id}
        p.DelCrontab(args)
        exit()
    data = json.loads(public.ReadFile(cron_task_path))
    web_log_map = WEBLogTask.all_web_log_scan()
    for path, config in data.items():
        if path == 'channel':
            continue
        try:
            msg_list = run(path)
        except:
            msg_list = []
            traceback.print_exc()
            continue
        try:
            name = os.path.basename(path).rsplit(".", 1)[0]
        except:
            name = path
        if msg_list:
            print('网站【{}】日志检测：{}'.format(name, ','.join(msg_list)))
        else:
            print('网站【{}】日志检测：检测中报错了。'.format(name))
        if path in web_log_map and msg_list:
            msg_list.insert(0, '网站【{}】日志检测：'.format(web_log_map[path]))
            push_by_task_keyword('web_log_scan', "web_log_scan_{}".format(path), push_data={"msg_list": msg_list})
    # if resource:
    #     send_notification('网站日志检测', resource, channel)
    # print('网站日志检测：\n{}'.format('  \n'.join(resource)))
