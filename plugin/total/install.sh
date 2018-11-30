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
pluginPath=/www/server/panel/plugin/total


Install_total()
{
	Install_cjson
	Install_socket
	Install_mod_lua
	mkdir -p $pluginPath
	echo '正在安装脚本文件...' > $install_tmp
	mkdir -p /www/server/total
	wget -O $pluginPath/total_main.py $download_Url/install/plugin/total/total_main.py -T 5
	wget -O $pluginPath/index.html $download_Url/install/plugin/total/index.html -T 5
	wget -O $pluginPath/info.json $download_Url/install/plugin/total/info.json -T 5
	wget -O $pluginPath/icon.png $download_Url/install/plugin/total/icon.png -T 5
	
	if [ ! -f /www/server/panel/static/js/china.js ];then
		wget -O /www/server/panel/static/js/china.js $download_Url/install/plugin/total/china.js -T 5
	fi
	wget -O /www/server/panel/vhost/apache/total.conf $download_Url/install/plugin/total/total_httpd.conf -T 5
	wget -O /www/server/panel/vhost/nginx/total.conf $download_Url/install/plugin/total/total_nginx.conf -T 5
	\cp -a -r /www/server/panel/plugin/total/icon.png /www/server/panel/static/img/soft_ico/ico-total.png
	wget -O $pluginPath/total.zip $download_Url/install/plugin/total/total.zip -T 5
	unzip -o $pluginPath/total.zip -d /www/server/total/ > /dev/null
	rm -f $pluginPath/total.zip
	total_path=/www/server/total
	if [ ! -f $total_path/config.json ];then
		wget -O $total_path/config.json $download_Url/install/plugin/total/config.json -T 5
	fi
	
	python -m compileall $pluginPath/total_init.py
	chown -R www:www  $total_path
	chmod -R 755 $total_path
	chmod +x $total_path/httpd_log.lua
	chmod +x $total_path/nginx_log.lua
	chmod +x $total_path/memcached.lua
	chmod +x $total_path/CRC32.lua
	
	cd /www/server/panel
	python $pluginPath/total_main.py
	if [ -f $pluginPath/total_init.pyc ];then
		rm -f $pluginPath/total_init.py
	fi
	
	waf=/www/server/panel/vhost/apache/btwaf.conf
	if [ ! -f $waf ];then
		echo "LoadModule lua_module modules/mod_lua.so" > $waf
	fi
	
	if [ -f /etc/init.d/httpd ];then
		/etc/init.d/httpd reload
	else
		/etc/init.d/nginx reload
	fi
	
	echo '安装完成' > $install_tmp
}

Install_cjson()
{
	if [ -f /usr/bin/yum ];then
		isInstall=`rpm -qa |grep lua-devel`
		if [ "$isInstall" == "" ];then
			yum install lua lua-devel -y
		fi
	else
		isInstall=`dpkg -l|grep liblua5.1-0-dev`
		if [ "$isInstall" == "" ];then
			apt-get install lua5.1 lua5.1-dev -y
		fi
	fi
	
	if [ ! -f /usr/local/lib/lua/5.1/cjson.so ];then
		wget -O lua-cjson-2.1.0.tar.gz $download_Url/install/src/lua-cjson-2.1.0.tar.gz -T 20
		tar xvf lua-cjson-2.1.0.tar.gz
		rm -f lua-cjson-2.1.0.tar.gz
		cd lua-cjson-2.1.0
		make clean
		make
		make install
		cd ..
		rm -rf lua-cjson-2.1.0
		ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib64/lua/5.1/cjson.so
		ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib/lua/5.1/cjson.so
	else
		if [ -d "/usr/lib64/lua/5.1" ];then
			ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib64/lua/5.1/cjson.so
		fi
		
		if [ -d "/usr/lib/lua/5.1" ];then
			ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib/lua/5.1/cjson.so
		fi
	fi
}

Install_socket()
{
	if [ ! -f /usr/local/lib/lua/5.1/socket/core.so ];then
		wget -O luasocket-master.zip $download_Url/install/src/luasocket-master.zip -T 20
		unzip luasocket-master.zip
		rm -f luasocket-master.zip
		cd luasocket-master
		make
		make install
		cd ..
		rm -rf luasocket-master
	fi
	
	if [ ! -d /usr/share/lua/5.1/socket ]; then
		if [ -d /usr/lib64/lua/5.1 ];then
			rm -rf /usr/lib64/lua/5.1/socket /usr/lib64/lua/5.1/mime
			ln -sf /usr/local/lib/lua/5.1/socket /usr/lib64/lua/5.1/socket
			ln -sf /usr/local/lib/lua/5.1/mime /usr/lib64/lua/5.1/mime
		else
			rm -rf /usr/lib/lua/5.1/socket /usr/lib/lua/5.1/mime
			ln -sf /usr/local/lib/lua/5.1/socket /usr/lib/lua/5.1/socket
			ln -sf /usr/local/lib/lua/5.1/mime /usr/lib/lua/5.1/mime
		fi
		rm -rf /usr/share/lua/5.1/mime.lua /usr/share/lua/5.1/socket.lua /usr/share/lua/5.1/socket
		ln -sf /usr/local/share/lua/5.1/mime.lua /usr/share/lua/5.1/mime.lua
		ln -sf /usr/local/share/lua/5.1/socket.lua /usr/share/lua/5.1/socket.lua
		ln -sf /usr/local/share/lua/5.1/socket /usr/share/lua/5.1/socket
	fi
}

Install_mod_lua()
{
	if [ ! -f /etc/init.d/httpd ];then
		return 0;
	fi
	
	if [ -f /www/server/apache/modules/mod_lua.so ];then
		return 0;
	fi
	cd /www/server/apache
	if [ ! -d /www/server/apache/src ];then
		wget -O httpd-2.4.33.tar.gz $download_Url/src/httpd-2.4.33.tar.gz -T 20
		tar xvf httpd-2.4.33.tar.gz
		rm -f httpd-2.4.33.tar.gz
		mv httpd-2.4.33 src
		cd /www/server/apache/src/srclib
		wget -O apr-1.6.3.tar.gz $download_Url/src/apr-1.6.3.tar.gz
		wget -O apr-util-1.6.1.tar.gz $download_Url/src/apr-util-1.6.1.tar.gz
		tar zxf apr-1.6.3.tar.gz
		tar zxf apr-util-1.6.1.tar.gz
		mv apr-1.6.3 apr
		mv apr-util-1.6.1 apr-util
	fi
	cd /www/server/apache/src
	./configure --prefix=/www/server/apache --enable-lua
	cd modules/lua
	make
	make install
	
	if [ ! -f /www/server/apache/modules/mod_lua.so ];then
		echo 'mod_lua安装失败!';
		exit 0;
	fi
}

Uninstall_total()
{
	rm -rf /www/server/total
	rm -f /www/server/panel/vhost/apache/total.conf
	rm -f /www/server/panel/vhost/nginx/total.conf
	rm -rf $pluginPath
	
	if [ -f /etc/init.d/httpd ];then
		/etc/init.d/httpd reload
	else
		/etc/init.d/nginx reload
	fi
}

if [ "${1}" == 'install' ];then
	Install_total
elif  [ "${1}" == 'update' ];then
	Install_total
elif [ "${1}" == 'uninstall' ];then
	Uninstall_total
fi
