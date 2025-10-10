#!/usr/bin/python
# coding: utf-8
# -----------------------------
# 定时检测并管理服务状态
# -----------------------------


import subprocess
import time
import datetime
import os,sys, time, re
os.chdir('/www/server/panel')
sys.path.insert(0,'./')
sys.path.insert(1,'class/')
sys.path.insert(2,'BTPanel/')
sys.path.insert(3,'/www/server/panel/plugin/mail_sys')
import public

class ServiceMonitor:
    def __init__(self, services=['dovecot', 'postfix', 'rspamd']):
        self.services = services

    def check_service_status(self, service_name: str) -> bool:
        """
        检查指定服务的状态
        :param service_name: 服务名称
        :return: True 如果服务正在运行，False 否则
        """

        try:
            result = subprocess.run(['systemctl', 'is-active', service_name], capture_output=True, text=True)
            print(f"0000 checking {service_name} result:{result}")

            return result.returncode == 0
        except Exception as e:
            print(f"Error checking {service_name} status: {e}")
            return False

    def restart_service(self, service_name: str):
        """
        重启指定的服务
        :param service_name: 服务名称
        """
        try:
            print(f"Restarting {service_name}...")
            subprocess.run(['systemctl', 'restart', service_name], check=True)
            print(f"Successfully restarted {service_name}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to restart {service_name}: {e}")

    def run_monitor(self):
        """
        开始监控服务状态
        """

        # import public.PluginLoader as plugin_loader
        # bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        # SendMailBulk = bulk.SendMailBulk
        alarm = False
        args = public.dict_obj()
        args.keyword = 'mail_server_status'
        from mailModel import bulkModel
        SendMailBulk = bulkModel.main
        try:
            send_task = SendMailBulk().get_alarm_send(args)
        except:
            public.print_log(public.get_error_info())
            send_task = False
        if send_task and send_task.get('status', False):
            alarm = True


        for service in self.services:
            if not self.check_service_status(service):
                # 告警
                if alarm:
                    # body = f"Your Mail Service [{service}] is down.  \n\n"
                    body = [f">Send content:Your Mail Service [{service}] is down, Restarting..."]
                    # 推送告警信息
                    args1 = public.dict_obj()
                    args1.keyword = 'mail_server_status'
                    args1.body = body
                    # self.send_mail_data(args1)

                    try:
                        SendMailBulk().send_mail_data(args1)
                    except:
                        public.print_log(public.get_error_info())

                self.restart_service(service)
                print(f"{service} 未运行，已重启")
            else:
                print(f"{service} 正常运行")


if __name__ == '__main__':
    monitor = ServiceMonitor()
    monitor.run_monitor()
