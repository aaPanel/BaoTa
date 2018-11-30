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

Install_load_leveling()
{
	mkdir -p /www/server/panel/plugin/load_leveling
	echo '正在安装脚本文件...' > $install_tmp
	wget -O /www/server/panel/plugin/load_leveling/load_leveling_main.py $download_Url/install/plugin/load_leveling/load_leveling_main.py -T 5
	wget -O /www/server/panel/plugin/load_leveling/index.html $download_Url/install/plugin/load_leveling/index.html -T 5
	wget -O /www/server/panel/plugin/load_leveling/info.json $download_Url/install/plugin/load_leveling/info.json -T 5
	wget -O /www/server/panel/plugin/load_leveling/icon.png $download_Url/install/plugin/load_leveling/icon.png -T 5
	\cp -a -r /www/server/panel/plugin/load_leveling/icon.png /www/server/panel/static/img/soft_ico/ico-load_leveling.png
	echo '安装完成' > $install_tmp
}

Uninstall_load_leveling()
{
	rm -rf /www/server/panel/plugin/load_leveling
	#rm -f /www/server/panel/vhost/nginx/leveling_*
	#/etc/init.d/nginx reload
}

action=$1
if [ "${1}" == 'install' ];then
	Install_load_leveling
else
	Uninstall_load_leveling
fi
