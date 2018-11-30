#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
public_file=/www/server/panel/install/public.sh
if [ ! -f $public_file ];then
	wget -O $public_file http://download.bt.cn/install/public.sh -T 5;
fi
. $public_file

download_Url=$NODE_URL

Install_logs()
{
	mkdir -p /www/server/panel/plugin/logs
	echo '正在安装脚本文件...' > $install_tmp
	wget -O /www/server/panel/plugin/logs/logs_main.py $download_Url/install/plugin/logs/logs_main.py -T 5
	wget -O /www/server/panel/plugin/logs/index.html $download_Url/install/plugin/logs/index.html -T 5
	wget -O /www/server/panel/plugin/logs/info.json $download_Url/install/plugin/logs/info.json -T 5
	wget -O /www/server/panel/plugin/logs/icon.png $download_Url/install/plugin/logs/icon.png -T 5
	wget -O /www/server/panel/plugin/logs/panel.sql $download_Url/install/plugin/logs/panel.sql -T 5
	nohup python /www/server/panel/plugin/logs/logs_main.py > /dev/null &
	echo '安装完成' > $install_tmp
}

Uninstall_logs()
{
	rm -rf /www/server/panel/plugin/logs
}


action=$1
if [ "${1}" == 'install' ];then
	Install_logs
else
	Uninstall_logs
fi
