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
Install_score()
{
	echo '正在安装脚本文件...' > $install_tmp
	mkdir -p /www/server/panel/plugin/score
	wget -O /www/server/panel/plugin/score/score_main.py $download_Url/install/plugin/score/score_main.py -T 5
	sleep 0.1;
	wget -O /www/server/panel/plugin/score/index.html $download_Url/install/plugin/score/index.html -T 5
	sleep 0.1;
	wget -O /www/server/panel/plugin/score/testcpu.c $download_Url/install/plugin/score/testcpu.c -T 5
	gcc /www/server/panel/plugin/score/testcpu.c -o /www/server/panel/plugin/score/testcpu -lpthread
	if [ ! -f '/www/server/panel/plugin/score/testcpu' ];then
		sleep 0.1
		gcc /www/server/panel/plugin/score/testcpu.c -o /www/server/panel/plugin/score/testcpu -lpthread
	fi
	
	
	if [ ! -f '/www/server/panel/static/img/soft_ico/ico-score.png' ];then
		wget -O /www/server/panel/static/img/soft_ico/ico-score.png $download_Url/install/plugin/score/img/ico-score.png
	fi
	
	wget -O /www/server/panel/plugin/score/info.json $download_Url/install/plugin/score/info.json -T 5
	echo '安装完成' > $install_tmp
}

Uninstall_score()
{
	rm -rf /www/server/panel/plugin/score
	echo '卸载完成' > $install_tmp
}


action=$1
if [ "${1}" == 'install' ];then
	Install_score
else
	Uninstall_score
fi
