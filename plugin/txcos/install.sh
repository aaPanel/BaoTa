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

Install_tenoss()
{
	pip install cos-python-sdk-v5
	mkdir -p /www/server/panel/plugin/txcos
	echo '正在安装脚本文件...' > $install_tmp
	wget -O /www/server/panel/plugin/txcos/txcos_main.py $download_Url/install/plugin/txcos/tenoss_main.py -T 5
	wget -O /www/server/panel/plugin/txcos/index.html $download_Url/install/plugin/txcos/index.html -T 5
	wget -O /www/server/panel/plugin/txcos/info.json $download_Url/install/plugin/txcos/info.json -T 5
	wget -O /www/server/panel/plugin/txcos/icon.png $download_Url/install/plugin/txcos/icon.png -T 5
	wget -O /www/server/panel/static/img/soft_ico/ico-txcos.png $download_Url/install/plugin/txcos/icon.png -T 5
	python /www/server/panel/plugin/txcos/txcos_main.py lib
	echo '安装完成' > $install_tmp
}

Uninstall_tenoss()
{
	rm -rf /www/server/panel/plugin/txcos
	pip uninstall cos-python-sdk-v5 -y
}


action=$1
if [ "${1}" == 'install' ];then
	Install_tenoss
else
	Uninstall_tenoss
fi
