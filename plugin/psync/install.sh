#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

public_file=/www/server/panel/install/public.sh
if [ ! -f $public_file ];then
	wget -O $public_file http://download.bt.cn/install/public.sh -T 5;
fi
. $public_file

download_Url=$NODE_URL

current=`date "+%Y-%m-%d %H:%M:%S"`  
timeStamp=`date -d "$current" +%s`   
currentTimeStamp=$((timeStamp*1000+`date "+%N"`/1000000)) 
if [ -f /usr/bin/yum ];then
	yum install -y rsync
elif [ -f /usr/bin/apt ]; then
	apt-get install rsync -y
fi
Install_psync()
{
	pip install tldextract
	mkdir -p /www/server/panel/plugin/psync/backup
	echo '正在安装脚本文件...' > $install_tmp
	wget -O /www/server/panel/plugin/psync/psync_main.py $download_Url/install/lib/plugin/psync/psync_main.py -T 5
	wget -O /www/server/panel/plugin/psync/index.html $download_Url/install/lib/plugin/psync/index.html -T 5
	wget -O /www/server/panel/plugin/psync/info.json $download_Url/install/lib/plugin/psync/info.json -T 5
	wget -O /www/server/panel/plugin/psync/icon.png $download_Url/install/lib/plugin/psync/icon.png -T 5
	wget -O /www/server/panel/plugin/psync/ico-success.png $download_Url/install/lib/plugin/psync/ico-success.png -T 5
	wget -O /www/server/panel/plugin/psync/password $download_Url/install/lib/plugin/psync/password -T 5
	wget -O /www/server/panel/plugin/psync/liang.db $download_Url/install/lib/plugin/psync/liang.db -T 5
	wget -O /www/server/panel/plugin/psync/rsynd $download_Url/install/lib/plugin/psync/rsync -T 5
	wget -O /www/server/panel/plugin/psync/rsyncd.conf $download_Url/install/lib/plugin/psync/rsyncd.conf -T 5
	chmod 600 /www/server/panel/plugin/psync/liang.db
	chmod 600 /www/server/panel/plugin/psync/password
	if [ -f /etc/init.d/rsynd ];then
		mv /www/server/panel/plugin/psync/rsync  /etc/init.d/rsynd
		chmod +x /etc/init.d/rsynd 
	fi 
if [ ! -d /www/server/panel/plugin/rsync/secrets/ ];then
	mv /www/server/panel/plugin/psync/rsyncd.conf  /etc/rsyncd.conf 
else

unalias cp
if [!  -f /etc/rsyncd_bak.conf ];then
	cp -p /etc/rsyncd.conf /etc/rsyncd_bak.conf
fi 


cat >>/etc/rsyncd.conf<<EOF
[9fc81642102bf60d]
comment = 
read only = false
auth users = liang
path = /www/wwwroot
ignore errors
secrets file = /www/server/panel/plugin/psync/liang.db
EOF
fi
	\cp -a -r /www/server/panel/plugin/psync/ico-success.png /www/server/panel/static/img/ico-success.png
	\cp -a -r /www/server/panel/plugin/psync/icon.png /www/server/panel/static/img/soft_ico/ico-psync.png
	
	isReload=`cat /etc/init.d/bt|grep panel_reload`
	if [ "$isReload" = '' ];then
		mv -f /etc/init.d/bt /tmp/bt_backup
		wget -O /etc/init.d/bt $download_Url/install/bt.init -T 20
		chmod +x /etc/init.d/bt
	fi
	
	isReload=`cat /etc/init.d/bt|grep panel_reload`
	if [ "$isReload" = '' ];then
		mv -f /tmp/bt_backup /etc/init.d/bt
		chmod +x /etc/init.d/bt
	fi
	
	if [ ! -f '/www/server/panel/class/panelPlugin.py' ];then
		return;
	fi
	
	isPlugin=`cat /www/server/panel/class/panelPlugin.py|grep LIB_TEMPLATE`
	if [ "$isPlugin" = '' ];then
		return;
	fi
	
	if [ ! -f '/www/server/panel/main.py' ];then
		return;
	fi
	
	isMain=`cat /www/server/panel/main.py|grep panelDownloadApi`
	if [ "$isMain" = '' ];then
		return;
	fi
	
	isMain=`cat /www/server/panel/main.py|grep 'Transfer-Encoding'`
	if [ "$isMain" != '' ];then
		return;
	fi
	
	if [ ! -f '/www/server/panel/class/public.py' ];then
		return;
	fi
	
	isPublic=`cat /www/server/panel/class/public.py|grep checkToken`
	if [ "$isPublic" = '' ];then
		return;
	fi
	
	echo '安装完成' > $install_tmp
	
	sleep 1 && /etc/init.d/bt reload &
	/etc/init.d/rsynd stop
	/etc/init.d/rsynd start  
}

Uninstall_psync()
{
	rm -rf /www/server/panel/plugin/psync
	mv -f  /etc/rsyncd_bak.conf /etc/rsyncd.conf
	/etc/init.d/rsynd stop
	/etc/init.d/rsynd start  
}


action=$1
if [ "${1}" == 'install' ];then
	Install_psync
else
	Uninstall_psync
fi
