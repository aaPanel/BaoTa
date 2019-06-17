#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
export HOME=/root
install_tmp='/tmp/bt_install.pl'
public_file=/www/server/panel/install/public.sh
if [ ! -f $public_file ];then
	wget -O $public_file http://download.bt.cn/install/public.sh -T 5;
fi
. $public_file

#配置插件下载地址和安装目录
download_url=$NODE_URL
install_path=/www/server/panel/plugin/pgsql_manager

#安装
Install()
{
	
	echo '正在安装...'
	#==================================================================
	#打包插件目录上传的情况下
	#依赖安装开始
	#pip install psycopg2

	#依赖安装结束
	#==================================================================

	#==================================================================
	#使用命令行安装的情况下，如果使用面板导入的，请删除以下代码
	
	#创建插件目录
	mkdir -p $install_path

	#开始下载文件
	wget -O $install_path/pgsql_manager_main.py $download_url/install/plugin/pgsql_manager/pgsql_manager_main.py -T 20
	wget -O $install_path/index.html $download_url/install/plugin/pgsql_manager/index.html -T 20
	wget -O $install_path/info.json $download_url/install/plugin/pgsql_manager/info.json -T 20
	wget -O $install_path/icon.png $download_url/install/plugin/pgsql_manager/icon.png -T 20
	wget -O $install_path/pgsql_install.sh $download_url/install/plugin/pgsql_manager/pgsql_install.sh -T 20
	wget -O $install_path/pgsql.sh $download_url/install/plugin/pgsql_manager/pgsql.sh -T 20
    
	#文件下载结束
	#==================================================================
	if [ -e /www/server/pgsql/data_directory ]; then
    cat /www/server/pgsql/data_directory
    else
        mkdir -p /www/server/pgsql/
        echo "/www/server/pgsql/data" >/www/server/pgsql/data_directory
    fi

	\cp -a -r $install_path/pgsql.sh /etc/init.d/pgsql
	chmod +x /etc/init.d/pgsql
	echo '================================================'
	echo '安装完成'
}

#卸载
Uninstall()
{
	rm -rf $install_path
}

#操作判断
if [ "${1}" == 'install' ];then
	Install
elif [ "${1}" == 'uninstall' ];then
	Uninstall
else
	echo 'Error!';
fi

