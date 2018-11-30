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
mongodb_version=3.6.2
mongodb_path=/www/server/mongodb

Install_mongodb()
{
	if [ ! -d /www/server/panel/plugin/mongodb ];then
		wget -O mongodb-linux-x86_64-$mongodb_version.tgz $download_Url/src/mongodb-linux-x86_64-$mongodb_version.tgz -T 5
		tar zxvf mongodb-linux-x86_64-$mongodb_version.tgz
		mkdir -p $mongodb_path/data
		mkdir -p $mongodb_path/log
		\cp -a -r mongodb-linux-x86_64-$mongodb_version/bin $mongodb_path/
		
		groupadd mongo
		useradd -s /sbin/nologin -M -g mongo mongo
		
		chown -R mongo:mongo $mongodb_path
		chmod +x $mongodb_path/bin
		ln -sf $mongodb_path/bin/* /usr/bin/
		
		wget -O /etc/init.d/mongodb $download_Url/install/plugin/mongodb/mongodb.init -T 5
		wget -O $mongodb_path/config.conf $download_Url/install/plugin/mongodb/config.conf -T 5
		chmod +x /etc/init.d/mongodb
		chkconfig --add mongodb
		chkconfig --level 2345 mongodb on
	fi
	
	mkdir -p /www/server/panel/plugin/mongodb
	echo '正在安装脚本文件...' > $install_tmp
	wget -O /www/server/panel/plugin/mongodb/mongodb_main.py $download_Url/install/plugin/mongodb/mongodb_main.py -T 5
	wget -O /www/server/panel/plugin/mongodb/index.html $download_Url/install/plugin/mongodb/index.html -T 5
	wget -O /www/server/panel/plugin/mongodb/info.json $download_Url/install/plugin/mongodb/info.json -T 5
	wget -O /www/server/panel/plugin/mongodb/icon.png $download_Url/install/plugin/mongodb/icon.png -T 5
	wget -O /www/server/panel/plugin/mongodb/panel.sql $download_Url/install/plugin/mongodb/panel.sql -T 5
	echo '安装完成' > $install_tmp
}

Uninstall_mongodb()
{
	/etc/init.d/mongodb stop
	chkconfig --del mongodb
	rm -f /etc/init.d/mongodb
	rm -f /usr/bin/mongo*
	rm -f /usr/bin/bsondump /usr/bin/install_compass
	rm -rf $mongodb_path/bin
	rm -rf $mongodb_path/log
	rm -rf /www/server/panel/plugin/mongodb
}

action=$1
if [ "${1}" == 'install' ];then
	Install_mongodb
else
	Uninstall_mongodb
fi
