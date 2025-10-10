#!/usr/bin/python
# coding: utf-8
# -----------------------------
# 宝塔docker容器日志切割脚本
# -----------------------------
import sys
import os
import time
import datetime

os.chdir("/www/server/panel")
sys.path.append('class/')
import public
import subprocess


class DkLogSpilt:
    task_list = []

    def __init__(self):
        if not public.M('sqlite_master').db('docker_log_split').where('type=? AND name=?', ('table', 'docker_log_split')).count():
            self.task_list = []
        else:
            self.task_list = public.M('docker_log_split').select()
            for i in self.task_list:
                # 使用 Docker 命令检查容器是否存在
                result = subprocess.run(['docker', 'inspect', i['pid']], capture_output=True, text=True)
                if result.returncode != 0:
                    public.M('docker_log_split').where('id=?', (i['id'],)).delete()


    def run(self):
        if not self.task_list:
            print('无docker日志切割任务')
        for task in self.task_list:
            try:
                if task['split_type'] == 'day':
                    self.day_split(task)
                elif task['split_type'] == 'size':
                    self.size_split(task)
            except:
                print('{}切割日志失败!'.format(task['name']))

    def day_split(self, task):
        now_time = int(time.time())
        exec_time = int(self.get_timestamp_of_hour_minute(task['split_hour'], task['split_minute']))
        if now_time <= exec_time <= now_time + 300:
            print("{}容器开始日志切割".format(task['name']))
            split_path = '/var/lib/docker/containers/history_logs/{}/'.format(task['pid'])
            if not os.path.exists(split_path):
                os.makedirs(split_path)
            os.rename(task['log_path'], split_path + task['pid'] + "-json.log" + '_' + str(int(time.time())))
            public.writeFile(task['log_path'], '')
            print("{}日志已切割到:{}".format(task['name'],split_path + task['pid'] + "-json.log" + '_' + str(int(time.time()))))
            self.check_save(task)
        else:
            print('{}容器日志未到切割时间'.format(task['name']))


    def size_split(self, task):
        if not os.path.exists(task['log_path']):
            print('日志文件不存在')
            return
        if os.path.getsize(task['log_path']) >= task['split_size']:
            print("{}容器开始日志切割".format(task['name']))
            split_path = '/var/lib/docker/containers/history_logs/{}/'.format(task['pid'])
            if not os.path.exists(split_path):
                os.makedirs(split_path)
            os.rename(task['log_path'], split_path + task['pid'] + "-json.log" + '_' + str(int(time.time())))
            public.writeFile(task['log_path'], '')
            print("{}日志已切割到:{}".format(task['name'],split_path + task['pid'] + "-json.log" + '_' + str(int(time.time()))))
            self.check_save(task)
        else:
            print('{}容器日志未到切割大小'.format(task['name']))

    def check_save(self, task):
        split_path = '/var/lib/docker/containers/history_logs/{}/'.format(task['pid'])
        file_count = len(os.listdir(split_path))
        if file_count > task['save']:
            file_list = os.listdir(split_path)
            file_list.sort()
            for i in range(file_count - task['save']):
                os.remove(split_path + file_list[i])
                print('删除日志文件:{}'.format(split_path + file_list[i]))
        print('已保留最新{}份日志'.format(task['save']))

    def get_timestamp_of_hour_minute(self, hour, minute):
        """获取当天指定时刻的时间戳。
        Args:
          hour: 小时。
          minute: 分钟。
        Returns:
          时间戳。
        """
        current_time = datetime.datetime.now()
        timestamp = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return int(timestamp.timestamp())


if __name__ == '__main__':
    dk = DkLogSpilt()
    dk.run()
