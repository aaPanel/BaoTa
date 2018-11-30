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

Install_deployment()
{
	mkdir -p /www/server/panel/plugin/deployment
	mkdir -p /www/server/panel/plugin/deployment/package
	echo '正在安装脚本文件...' > $install_tmp
	wget -O /www/server/panel/plugin/deployment/deployment_main.py $download_Url/install/plugin/deployment/deployment_main.py -T 5
	wget -O /www/server/panel/plugin/deployment/index.html $download_Url/install/plugin/deployment/index.html -T 5
	wget -O /www/server/panel/plugin/deployment/info.json $download_Url/install/plugin/deployment/info.json -T 5
	wget -O /www/server/panel/plugin/deployment/list.json $download_Url/install/plugin/deployment/list.json -T 5
	wget -O /www/server/panel/plugin/deployment/type.json $download_Url/install/plugin/deployment/type.json -T 5
	wget -O /www/server/panel/plugin/deployment/icon.png $download_Url/install/plugin/deployment/icon.png -T 5
	wget -O /www/server/panel/static/img/soft_ico/ico-deployment.png $download_Url/install/plugin/deployment/icon.png -T 5
	echo '安装完成' > $install_tmp
}

Uninstall_deployment()
{
	rm -rf /www/server/panel/plugin/deployment
}


action=$1
if [ "${1}" == 'install' ];then
	Install_deployment
else
	Uninstall_deployment
fi
