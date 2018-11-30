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
pluginPath=/www/server/panel/plugin/syssafe

Install_syssafe()
{
	mkdir -p $pluginPath
	mkdir -p $pluginPath/sites
	echo '正在安装脚本文件...' > $install_tmp
	wget -O $pluginPath/syssafe_main.py $download_Url/install/plugin/syssafe/syssafe_main.py -T 5
	wget -O $pluginPath/index.html $download_Url/install/plugin/syssafe/index.html -T 5
	if [ ! -f $pluginPath/config.json ];then
		wget -O $pluginPath/config.json $download_Url/install/plugin/syssafe/config.json -T 5
	fi
	wget -O $pluginPath/icon.png $download_Url/install/plugin/syssafe/icon.png -T 5

	initSh=/etc/init.d/bt_syssafe
	wget -O $initSh $download_Url/install/plugin/syssafe/init.sh -T 5
	chmod +x $initSh
	if [ -f "/usr/bin/apt-get" ];then
		sudo update-rc.d bt_syssafe defaults
	else
		chkconfig --add bt_syssafe
		chkconfig --level 2345 bt_syssafe on

	$initSh stop
	$initSh start
	chmod -R 600 $pluginPath

	echo '安装完成' > $install_tmp
}

Uninstall_syssafe()
{
	initSh=/etc/init.d/bt_syssafe
	$initSh stop
	chkconfig --del bt_syssafe
	rm -rf $pluginPath
	rm -f $initSh
}


action=$1
if [ "${1}" == 'install' ];then
	Install_syssafe
else
	Uninstall_syssafe
fi
