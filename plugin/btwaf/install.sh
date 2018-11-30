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
pluginPath=/www/server/panel/plugin/btwaf


Install_btwaf()
{
	Install_cjson
	mkdir -p $pluginPath
	echo '正在安装脚本文件...' > $install_tmp
	wget -O $pluginPath/btwaf_main.py $download_Url/install/plugin/btwaf/btwaf_main.py -T 5
	wget -O $pluginPath/index.html $download_Url/install/plugin/btwaf/index.html -T 5
	wget -O $pluginPath/info.json $download_Url/install/plugin/btwaf/info.json -T 5
	wget -O $pluginPath/icon.png $download_Url/install/plugin/btwaf/icon.png -T 5
	wget -O /www/server/panel/vhost/nginx/btwaf.conf $download_Url/install/plugin/btwaf/btwaf.conf -T 5
	\cp -a -r /www/server/panel/plugin/btwaf/icon.png /www/server/panel/static/img/soft_ico/ico-btwaf.png
	wget -O $pluginPath/btwaf.zip $download_Url/install/plugin/btwaf/btwaf.zip -T 5
	unzip -o $pluginPath/btwaf.zip -d /tmp/ > /dev/null
	rm -f $pluginPath/btwaf.zip
	btwaf_path=/www/server/btwaf
	mkdir -p $btwaf_path/html
	
	if [ ! -f $btwaf_path/html/get.html ];then
		\cp -a -r /tmp/btwaf/html/get.html $btwaf_path/html/get.html
		\cp -a -r /tmp/btwaf/html/get.html $btwaf_path/html/post.html
		\cp -a -r /tmp/btwaf/html/get.html $btwaf_path/html/cookie.html
		\cp -a -r /tmp/btwaf/html/get.html $btwaf_path/html/user_agent.html
		\cp -a -r /tmp/btwaf/html/get.html $btwaf_path/html/other.html
	fi
	
	mkdir -p $btwaf_path/rule
	if [ ! -f $btwaf_path/rule/url.json ];then
		\cp -a -r /tmp/btwaf/rule/url.json $btwaf_path/rule/url.json
		\cp -a -r /tmp/btwaf/rule/args.json $btwaf_path/rule/args.json
		\cp -a -r /tmp/btwaf/rule/post.json $btwaf_path/rule/post.json
		\cp -a -r /tmp/btwaf/rule/cn.json $btwaf_path/rule/cn.json
		\cp -a -r /tmp/btwaf/rule/cookie.json $btwaf_path/rule/cookie.json
		\cp -a -r /tmp/btwaf/rule/head_white.json $btwaf_path/rule/head_white.json
		\cp -a -r /tmp/btwaf/rule/ip_black.json $btwaf_path/rule/ip_black.json
		\cp -a -r /tmp/btwaf/rule/ip_white.json $btwaf_path/rule/ip_white.json
		\cp -a -r /tmp/btwaf/rule/scan_black.json $btwaf_path/rule/scan_black.json
		\cp -a -r /tmp/btwaf/rule/url_black.json $btwaf_path/rule/url_black.json
		\cp -a -r /tmp/btwaf/rule/url_white.json $btwaf_path/rule/url_white.json
		\cp -a -r /tmp/btwaf/rule/user_agent.json $btwaf_path/rule/user_agent.json
	fi
	
	if [ ! -f $btwaf_path/site.json ];then
		\cp -a -r /tmp/btwaf/site.json $btwaf_path/site.json
	fi
	
	if [ ! -f $btwaf_path/config.json ];then
		\cp -a -r /tmp/btwaf/config.json $btwaf_path/config.json
	fi
	
	if [ ! -f $btwaf_path/total.json ];then
		\cp -a -r /tmp/btwaf/total.json $btwaf_path/total.json
	fi
	
	if [ ! -f $btwaf_path/drop_ip.log ];then
		\cp -a -r /tmp/btwaf/drop_ip.log $btwaf_path/drop_ip.log
	fi
	\cp -a -r /tmp/btwaf/init.lua $btwaf_path/init.lua
	\cp -a -r /tmp/btwaf/waf.lua $btwaf_path/waf.lua
	chmod +x $btwaf_path/waf.lua
	chmod +x $btwaf_path/init.lua
	
	mkdir -p /www/wwwlogs/btwaf
	chmod 777 /www/wwwlogs/btwaf
	chmod -R 755 /www/server/btwaf
	chmod -R 666 /www/server/btwaf/rule
	chmod -R 666 /www/server/btwaf/total.json
	chmod -R 666 /www/server/btwaf/drop_ip.log
	echo '' > /www/server/nginx/conf/luawaf.conf
	rm -rf /tmp/btwaf
	python $pluginPath/btwaf_main.py
	/etc/init.d/nginx reload
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

Uninstall_btwaf()
{
	rm -rf /www/server/panel/static/btwaf
	if [ ! -d /www/server/panel/plugin/btwaf_httpd ];then
		rm -rf /www/server/btwaf
	fi
	rm -f /www/server/panel/vhost/nginx/btwaf.conf
	rm -rf $pluginPath
	cat > /www/server/nginx/conf/luawaf.conf<<EOF
lua_shared_dict limit 10m;
lua_package_path "/www/server/nginx/waf/?.lua";
init_by_lua_file  /www/server/nginx/waf/init.lua;
access_by_lua_file /www/server/nginx/waf/waf.lua;
EOF

}

if [ "${1}" == 'install' ];then
	Install_btwaf
elif  [ "${1}" == 'update' ];then
	Install_btwaf
elif [ "${1}" == 'uninstall' ];then
	Uninstall_btwaf
fi
