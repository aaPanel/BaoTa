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

Install_btyw()
{
	mkdir -p /www/server/panel/plugin/btyw
	echo '正在安装脚本文件...' > $install_tmp
	wget -O /www/server/panel/plugin/btyw/btyw_main.py $download_Url/install/plugin/btyw/btyw_main.py -T 5
	wget -O /www/server/panel/plugin/btyw/index.html $download_Url/install/plugin/btyw/index.html -T 5
	wget -O /www/server/panel/plugin/btyw/info.json $download_Url/install/plugin/btyw/info.json -T 5
	wget -O /www/server/panel/plugin/btyw/icon.png $download_Url/install/plugin/btyw/icon.png -T 5
	wget -O /www/server/panel/static/img/soft_ico/ico-btyw.png $download_Url/install/plugin/btyw/icon.png -T 5
	wget -O /www/server/panel/static/images/ico-hot.png $download_Url/install/plugin/btyw/ico-hot.png -T 5
	
	echo '安装完成' > $install_tmp
}

Uninstall_btyw()
{
	rm -rf /www/server/panel/plugin/btyw
	pip uninstall btyw -y
}


action=$1
if [ "${1}" == 'install' ];then
	Install_btyw
else
	Uninstall_btyw
fi
