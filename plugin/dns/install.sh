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

Install_dns()
{
	mkdir -p /www/server/panel/plugin/dns
	echo '正在安装脚本文件...' > $install_tmp
	wget -O /www/server/panel/plugin/dns/dns_main.py $download_Url/install/plugin/dns/dns_main.py -T 5
	wget -O /www/server/panel/plugin/dns/index.html $download_Url/install/plugin/dns/index.html -T 5
	wget -O /www/server/panel/plugin/dns/info.json $download_Url/install/plugin/dns/info.json -T 5
	wget -O /www/server/panel/plugin/dns/icon.png $download_Url/install/plugin/dns/icon.png -T 5
	#wget -O /www/server/panel/static/img/tip_suu.png $download_Url/install/plugin/dns/tip_suu.png -T 5
	#wget -O /www/server/panel/static/img/label-icon.png $download_Url/install/plugin/dns/label-icon.png -T 5
	#wget -O /www/server/panel/static/img/return-icon.png $download_Url/install/plugin/dns/return-icon.png -T 5
	\cp -a -r /www/server/panel/plugin/dns/icon.png /www/server/panel/static/img/soft_ico/ico-dns.png
	nohup pip install python-whois > /dev/null 2>&1 &
	echo '安装完成' > $install_tmp
}

Uninstall_dns()
{
	rm -rf /www/server/panel/plugin/dns
}


action=$1
host=$2;
if [ "${1}" == 'install' ];then
	Install_dns
else
	Uninstall_dns
fi
