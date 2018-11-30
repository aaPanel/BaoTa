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

Install_safelogin()
{
	mkdir -p /www/server/panel/plugin/safelogin
	echo '正在安装脚本文件...' > $install_tmp
	wget -O /www/server/panel/plugin/safelogin/safelogin_main.py $download_Url/install/plugin/safelogin/safelogin_main.py -T 5
	wget -O /www/server/panel/plugin/safelogin/index.html $download_Url/install/plugin/safelogin/index.html -T 5
	wget -O /www/server/panel/plugin/safelogin/info.json $download_Url/install/plugin/safelogin/info.json -T 5
	wget -O /www/server/panel/plugin/safelogin/icon.png $download_Url/install/plugin/safelogin/icon.png -T 5
	echo '安装完成' > $install_tmp
	
}

Uninstall_safelogin()
{
	chattr -i /www/server/panel/plugin/safelogin/token.pl
	rm -f /www/server/panel/data/limitip.conf
	sed -i "/ALL/d" /etc/hosts.deny
	rm -rf /www/server/panel/plugin/safelogin
}


action=$1
host=$2;
if [ "${1}" == 'install' ];then
	Install_safelogin
else
	Uninstall_safelogin
fi
