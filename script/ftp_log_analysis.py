import json
import sys
import traceback

if not '/www/server/panel/class/' in sys.path:
    sys.path.insert(0, '/www/server/panel/class/')
import PluginLoader
import crontab
import public


def del_cron_task():
    name = '[勿删]FTP日志分析任务'
    id = public.M('crontab').where("name=?", (name,)).getField('id')
    args = {"id": id}
    crontab.crontab().DelCrontab(args)


def run():
    config = json.loads(public.readFile('/www/server/panel/data/analysis_config.json'))
    if not config['cron_task_status']:
        print('未开启日志定时检测')
        return False, ''
    status, data = get_analysis(config)
    if not status:
        print('获取日志分析结果失败')
        exit()
    if not data:
        print('无异常日志')
        exit()
    channel = config['cron_task']['channel']
    data = ['此ip【{}】存在【{}】'.format(k, v['type']) for k, v in data.items()]
    data = public.get_push_info('FTP日志分析', data)
    send_notification(data, channel)


def get_analysis(config):
    try:
        args = public.dict_obj()
        args.model_index = "logs"  # 模块名
        task_type = config['cron_task']['task_type']
        task_type = [i for i, j in task_type.items() if j]
        args.search = json.dumps(task_type)
        args.username = json.dumps([])
        args.day = config['cron_task']['cycle']
        data = PluginLoader.module_run("ftp", "log_analysis", args)
        if 'status' in data.keys():
            return False, ''
        return True, data
    except:
        return False, ''


def send_notification(data, channels):
    for channel in channels.split(','):
        try:
            obj = public.init_msg(channel)
            obj.send_msg(data['msg'])
            print('{}通道发送成功'.format(channel))
        except:
            print('{}通道发送失败'.format(channel))


if __name__ == '__main__':
    run()
