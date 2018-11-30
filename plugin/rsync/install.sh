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
pluginPath=/www/server/panel/plugin/rsync
centos=1
if [ ! -f /usr/bin/yum ];then
	centos=0
fi

Install_rsync()
{
	check_fs
	check_package
	
	wget -O /etc/init.d/rsynd $download_Url/install/plugin/rsync/rsynd.init -T 5
	chmod +x /etc/init.d/rsynd
	if [ $centos == 1 ];then
		chkconfig --add rsynd
		chkconfig --level 2345 rsynd on
	else
		update-rc.d rsynd defaults
	fi
	
	wget -O /etc/init.d/lsyncd $download_Url/install/plugin/rsync/lsyncd.init -T 5
	chmod +x /etc/init.d/lsyncd
	if [ $centos == 1 ];then
		chkconfig --add lsyncd
		chkconfig --level 2345 lsyncd on
	else
		update-rc.d lsyncd defaults
	fi
	
	mkdir -p $pluginPath
	echo '正在安装脚本文件...' > $install_tmp
	wget -O $pluginPath/rsync_main.py $download_Url/install/plugin/rsync/rsync_main.py -T 5
	wget -O $pluginPath/index.html $download_Url/install/plugin/rsync/index.html -T 5
	wget -O $pluginPath/info.json $download_Url/install/plugin/rsync/info.json -T 5
	wget -O $pluginPath/icon.png $download_Url/install/plugin/rsync/icon.png -T 5
	if [ ! -f $pluginPath/config.json ];then
		wget -O $pluginPath/config.json $download_Url/install/plugin/rsync/config.json -T 5
	fi
	
	echo '安装完成' > $install_tmp
	python $pluginPath/rsync_main.py new
}

check_package()
{
	if [ $centos == 1 ];then
		isInstall=`rpm -qa |grep lua-devel`
		if [ "$isInstall" == "" ];then
			yum install lua lua-devel asciidoc cmake -y
		fi
	else
		isInstall=`dpkg -l|grep liblua5.1-0-dev`
		if [ "$isInstall" == "" ];then
			apt-get install lua5.1 lua5.1-dev cmake -y
		fi
	fi
	
	if [ -f /usr/local/lib/lua/5.1/cjson.so ];then
		if [ -d "/usr/lib64/lua/5.1" ];then
			ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib64/lua/5.1/cjson.so
		fi
		
		if [ -d "/usr/lib/lua/5.1" ];then
			ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib/lua/5.1/cjson.so
		fi
	fi
	rconf=`cat /etc/rsyncd.conf|grep 'rsyncd.pid'`
	if [ "$rconf" == "" ];then
		cat > /etc/rsyncd.conf <<EOF
uid = root
use chroot = no
dont compress = *.gz *.tgz *.zip *.z *.Z *.rpm *.deb *.bz2 *.mp4 *.avi *.swf *.rar
hosts allow = 
max connections = 200
gid = root
timeout = 600
lock file = /var/run/rsync.lock
pid file = /var/run/rsyncd.pid
log file = /var/log/rsyncd.log
port = 873
EOF
	fi
	
	rsync_version=`/usr/bin/rsync --version|grep version|awk '{print $3}'`
	if [ "$rsync_version" != "3.1.2" ] &&  [ "$rsync_version" != "3.1.3" ];then
		wget -O rsync-3.1.3.tar.gz $download_Url/install/src/rsync-3.1.3.tar.gz -T 20
		tar xvf rsync-3.1.3.tar.gz
		cd rsync-3.1.3
		./configure --prefix=/usr
		make
		make install
		cd ..
		rm -rf rsync-3.1.3*
		rsync_version=`/usr/bin/rsync --version|grep version|awk '{print $3}'`
		if [ "$rsync_version" != "3.1.3" ];then
			rm -f /usr/bin/rsync
			ln -sf /usr/local/bin/rsync /usr/bin/rsync
		fi
	fi
	
	lsyncd_version=`lsyncd --version |grep Version|awk '{print $2}'`
	if [ "$lsyncd_version" != "2.2.2" ];then
		wget -O lsyncd-release-2.2.2.zip $download_Url/install/src/lsyncd-release-2.2.2.zip -T 20
		unzip lsyncd-release-2.2.2.zip
		cd lsyncd-release-2.2.2
		cmake -DCMAKE_INSTALL_PREFIX=/usr
		make
		make install
		cd ..
		rm -rf lsyncd-release-2.2.2*
		if [ ! -f /etc/lsyncd.conf ];then
			echo > /etc/lsyncd.conf
		fi
	fi
}


check_fs()
{
	is_max_user_instances=`cat /etc/sysctl.conf|grep max_user_instances`
	if [ "$is_max_user_instances" == "" ];then
		echo "fs.max_user_instances = 1024" >> /etc/sysctl.conf
		echo "1024" > /proc/sys/fs/inotify/max_user_instances
	fi
	
	is_max_user_watches=`cat /etc/sysctl.conf|grep max_user_watches`
	if [ "$is_max_user_watches" == "" ];then
		echo "fs.max_user_watches = 819200" >> /etc/sysctl.conf
		echo "819200" > /proc/sys/fs/inotify/max_user_watches
	fi
}

Uninstall_rsync()
{
	/etc/init.d/rsynd stop
	if [ $centos == 1 ];then
		chkconfig --del rsynd
	else
		update-rc.d -f rsynd remove
	fi
	rm -f /etc/init.d/rsynd
	
	if [ -f /etc/init.d/rsync_inotify ];then
		/etc/init.d/rsync_inotify stopall
		chkconfig --del rsync_inotify
		rm -f /etc/init.d/rsync_inotify
	fi
	
	if [ -f /etc/init.d/lsyncd ];then
		/etc/init.d/lsyncd stop
		if [ $centos == 1 ];then
			chkconfig --level 2345 lsyncd off
			chkconfig --del rsynd
		else
			update-rc.d -f rsynd remove
		fi
	else
		systemctl disable lsyncd
		systemctl stop lsyncd
	fi
	
	rm -f /etc/lsyncd.conf
	rm -f /etc/rsyncd.conf
	rm -rf $pluginPath
}

if [ "${1}" == 'install' ];then
	Install_rsync
elif [ "${1}" == 'uninstall' ];then
	Uninstall_rsync
fi

