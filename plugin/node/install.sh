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

Install_linuxsys()
{
	mkdir -p /www/server/panel/plugin/node
	wget -O /www/server/panel/data/node.json $download_Url/install/lib/node.json -T 5
	wget -O /www/server/panel/plugin/node/icon.png $download_Url/install/plugin/node/icon.png -T 5
	\cp -a -r /www/server/panel/plugin/node/icon.png /www/server/panel/static/img/soft_ico/ico-node.png
	\cp -a -r /www/server/panel/data/node.json /www/server/panel/plugin/node/node.json
	echo '安装完成' > $install_tmp
}

Uninstall_linuxsys()
{
	rm -rf /www/server/panel/plugin/node
}


action=$1
if [ "${1}" == 'install' ];then
	Install_linuxsys
else
	Uninstall_linuxsys
fi
