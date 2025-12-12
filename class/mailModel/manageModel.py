import re, json, os, sys, time, socket, requests
import public

from mailModel.base import Base


class main(Base):
    # 2024/12/21 11:36 安装宝塔邮局
    def install_service(self, get):
        '''
            @name 安装宝塔邮局
        '''
        public.httpPost(public.GetConfigValue('home') + '/api/panel/plugin_total', {"pid": "403", 'p_name': "mailmod"}, 3)

        # download_url = "{}/install/plugin/mail_sys/mail_install.sh".format(public.get_url())
        # install_path = "{}/panel/install".format(public.get_setup_path())
        # install_file = install_path + "/mail_install.sh"
        # if os.path.exists(install_file): os.remove(install_file)
        # public.ExecShell("rm -f /www/server/panel/install/mail_install.sh;wget -O " + install_file + " " + download_url + " --no-check-certificate")
        # if not os.path.exists(install_file): return public.returnMsg(False, '下载安装脚本失败')
        if public.M('tasks').where('name=? and status=?', ('安装 [宝塔邮局]', '0')).count() > 0:
            return public.returnMsg(False, '安装任务已存在')
        else:
            execstr = "cd /www/server/panel/class/mailModel/script && /bin/bash install.sh install"
            public.M('tasks').add('id,name,type,status,addtime,execstr', (
            None, '安装 [宝塔邮局]', 'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), execstr))
            public.writeFile('/tmp/panelTask.pl', 'True')
            return public.returnMsg(True, '安装任务已添加到任务队列中')

    def install_status(self, get):
        '''
        @name 安装状态
        '''
        if os.path.exists("/www/server/panel/plugin/mail_sys"):
            try:
                from mailModel.mainModel import main as mail_main
                mail_main().get_service_status(None)
            except:
                return public.returnMsg(False, '')
            return public.returnMsg(True, '')
        else:
            return public.returnMsg(False, '')
