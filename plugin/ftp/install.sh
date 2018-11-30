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
Install_Ftp()
{	
	echo '正在安装脚本文件...' > $install_tmp
	wget -O /www/server/panel/script/backup_ftp.py $download_Url/install/plugin/ftp/ftp_main.py -T 5
	\cp -a -r /www/server/panel/script/backup_ftp.py /www/server/panel/plugin/ftp/ftp_main.py
	wget -O /www/server/panel/plugin/ftp/index.html $download_Url/install/plugin/ftp/index.html -T 5
	wget -O /www/server/panel/plugin/ftp/info.json $download_Url/install/plugin/ftp/info.json -T 5
	echo '安装完成' > $install_tmp
}

Uninstall_Ftp()
{
	rm -f /www/server/panel/script/backup_ftp.py
	rm -rf /www/server/panel/plugin/ftp
	echo '卸载完成' > $install_tmp
}


action=$1
if [ "${1}" == 'install' ];then
	Install_Ftp
else
	Uninstall_Ftp
fi
