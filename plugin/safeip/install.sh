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
Install_safeip()
{
	echo '正在安装脚本文件...' > $install_tmp
	mkdir -p /www/server/panel/plugin/safeip
	wget -O /www/server/panel/plugin/safeip/safeip_main.py $download_Url/install/plugin/safeip/safeip_main.py -T 5
	sleep 0.1;
	wget -O /www/server/panel/plugin/safeip/index.html $download_Url/install/plugin/safeip/index.html -T 5
	
	
	if [ ! -f '/www/server/panel/static/img/soft_ico/ico-safeip.png' ];then
		wget -O /www/server/panel/static/img/soft_ico/ico-safeip.png $download_Url/install/plugin/safeip/img/icon.png
	fi
	
	wget -O /www/server/panel/plugin/safeip/info.json $download_Url/install/plugin/safeip/info.json -T 5
	echo '安装完成' > $install_tmp
}

Uninstall_safeip()
{
	rm -rf /www/server/panel/plugin/safeip
	echo '卸载完成' > $install_tmp
}


action=$1
if [ "${1}" == 'install' ];then
	Install_safeip
else
	Uninstall_safeip
fi
