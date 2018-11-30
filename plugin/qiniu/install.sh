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
Install_Qiniu()
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
    pip install pip==9.0.3
	pip install qiniu
	echo '正在安装脚本文件...' > $install_tmp
	mkdir -p /www/server/panel/plugin/qiniu
	wget -O /www/server/panel/script/backup_qiniu.py $download_Url/install/plugin/qiniu/qiniu_main.py -T 5
	\cp -a -r /www/server/panel/script/backup_qiniu.py /www/server/panel/plugin/qiniu/qiniu_main.py
	wget -O /www/server/panel/plugin/qiniu/index.html $download_Url/install/plugin/qiniu/index.html -T 5
	
	if [ -f /usr/lib/python2.7/site-packages/qiniu/zone.py ];then
		wget -O /usr/lib/python2.7/site-packages/qiniu/zone.py $download_Url/install/plugin/qiniu/zone.py -T 5
	else
		pip install certifi==2015.04.28
	fi
	wget -O /www/server/panel/plugin/qiniu/info.json $download_Url/install/plugin/qiniu/info.json -T 5
	echo '安装完成' > $install_tmp
}

Uninstall_Qiniu()
{
	rm -rf /www/server/panel/plugin/qiniu
	rm -f /www/server/panel/script/backup_qiniu.py
	pip uninstall qiniu -y
	echo '卸载完成' > $install_tmp
}


action=$1
if [ "${1}" == 'install' ];then
	Install_Qiniu
else
	Uninstall_Qiniu
fi
