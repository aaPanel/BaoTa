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
pluginPath=/www/server/panel/plugin/tamper_proof

Install_tamper_proof()
{
	mkdir -p $pluginPath
	mkdir -p $pluginPath/sites
	echo '正在安装脚本文件...' > $install_tmp
	wget -O $pluginPath/tamper_proof_main.py $download_Url/install/plugin/tamper_proof/tamper_proof_main.py -T 5
	wget -O $pluginPath/tamper_proof_init.py $download_Url/install/plugin/tamper_proof/tamper_proof_init.py -T 5
	wget -O $pluginPath/tamper_proof_service.py $download_Url/install/plugin/tamper_proof/tamper_proof_service.py -T 5
	wget -O $pluginPath/index.html $download_Url/install/plugin/tamper_proof/index.html -T 5
	wget -O $pluginPath/config.json $download_Url/install/plugin/tamper_proof/config.json -T 5
	wget -O $pluginPath/icon.png $download_Url/install/plugin/tamper_proof/icon.png -T 5

	siteJson=$pluginPath/sites.json
	if [ ! -f $siteJson ];then
		wget -O $siteJson $download_Url/install/plugin/tamper_proof/sites.json -T 5
	fi
	initSh=/etc/init.d/bt_tamper_proof
	wget -O $initSh $download_Url/install/plugin/tamper_proof/init.sh -T 5
	chmod +x $initSh
	if [ -f "/usr/bin/apt-get" ];then
		sudo update-rc.d bt_tamper_proof defaults
	else
		chkconfig --add bt_tamper_proof
		chkconfig --level 2345 bt_tamper_proof on

	$initSh stop
	$initSh start
	chmod -R 600 $pluginPath

	echo '安装完成' > $install_tmp
}

Uninstall_tamper_proof()
{
	initSh=/etc/init.d/bt_tamper_proof
	initSh stop
	chkconfig --del bt_tamper_proof
	rm -rf $pluginPath
	rm -f $initSh
}


action=$1
if [ "${1}" == 'install' ];then
	Install_tamper_proof
else
	Uninstall_tamper_proof
fi
