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
Install_AliOSS()
{
	echo '正在安装前置组件...' > $install_tmp
	if [ "${download_Url}" = "http://125.88.182.172:5880" ]; then
		mkdir ~/.pip
		cat > ~/.pip/pip.conf <<EOF
[global]
index-url = https://pypi.doubanio.com/simple/

[install]
trusted-host=pypi.doubanio.com
EOF
    fi
	tmp=`python -V 2>&1|awk '{print $2}'`
	pVersion=${tmp:0:3}
	
	if [ ! -f "/usr/lib/python${pVersion}/site-packages/setuptools-33.1.1-py${pVersion}.egg" ];then
		wget $download_Url/install/src/setuptools-33.1.1.zip -T 10
		unzip setuptools-33.1.1.zip
		rm -f setuptools-33.1.1.zip
		cd setuptools-33.1.1
		python setup.py install
		cd ..
		rm -rf setuptools-33.1.1
	fi
	if [ ! -f "/usr/bin/pip" ];then
		wget $download_Url/install/src/pip-9.0.1.tar.gz -T 10
		tar xvf pip-9.0.1.tar.gz
		rm -f pip-9.0.1.tar.gz
		cd pip-9.0.1
		python setup.py install
		cd ..
		rm -rf pip-9.0.1
	fi
	pip install pip==9.0.3
	pip install oss2
	echo '正在安装脚本文件...' > $install_tmp
	mkdir -p /www/server/panel/plugin/alioss
	wget -O /www/server/panel/script/backup_alioss.py $download_Url/install/plugin/alioss/alioss_main.py -T 5
	\cp -a -r /www/server/panel/script/backup_alioss.py /www/server/panel/plugin/alioss/alioss_main.py
	wget -O /www/server/panel/plugin/alioss/index.html $download_Url/install/plugin/alioss/index.html -T 5
	wget -O /www/server/panel/plugin/alioss/info.json $download_Url/install/plugin/alioss/info.json -T 5
	echo '安装完成' > $install_tmp
}

Uninstall_AliOSS()
{
	rm -rf /www/server/panel/plugin/alioss
	rm -f /www/server/panel/script/backup_alioss.py
	pip uninstall oss2 -y
	echo '卸载完成' > $install_tmp
}


action=$1
if [ "${1}" == 'install' ];then
	Install_AliOSS
else
	Uninstall_AliOSS
fi
