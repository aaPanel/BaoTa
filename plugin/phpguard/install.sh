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

Install_phpguard()
{
	mkdir -p /www/server/panel/plugin/phpguard
	wget -O /www/server/panel/plugin/phpguard/info.json $download_Url/install/plugin/phpguard/info.json -T 5
	echo 'True' > /www/server/panel/data/502Task.pl
}

Uninstall_phpguard()
{
	rm -rf /www/server/panel/plugin/phpguard
	rm -f /www/server/panel/data/502Task.pl
}


action=$1
if [ "${1}" == 'install' ];then
	Install_phpguard
else
	Uninstall_phpguard
fi
