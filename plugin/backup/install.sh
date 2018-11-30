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
pluginPath=/www/server/panel/plugin/backup


Install_Backup()
{
	mkdir -p $pluginPath
	echo '正在安装脚本文件...' > $install_tmp
	wget -O $pluginPath/backup_main.py $download_Url/install/plugin/backup/backup_main.py -T 5
	wget -O $pluginPath/index.html $download_Url/install/plugin/backup/index.html -T 5
	wget -O $pluginPath/info.json $download_Url/install/plugin/backup/info.json -T 5
	wget -O $pluginPath/icon.png $download_Url/install/plugin/backup/icon.png -T 5
	\cp -a -r /www/server/panel/plugin/backup/icon.png /www/server/panel/static/img/soft_ico/ico-backup.png
	echo '安装完成' > $install_tmp
}

Uninstall_Backup()
{
	rm -rf $pluginPath
}

if [ "${1}" == 'install' ];then
	Install_Backup
elif  [ "${1}" == 'update' ];then
	Install_Backup
elif [ "${1}" == 'uninstall' ];then
	Uninstall_Backup
fi
