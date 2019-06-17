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
echo 'download url...'
echo $download_Url
pluginPath=/www/server/panel/plugin/mail_sys
pluginStaticPath=/www/server/panel/plugin/mail_sys/static

Install()
{
	mkdir -p $pluginPath
	mkdir -p $pluginStaticPath
	echo '正在安装脚本文件...' > $install_tmp
	wget -O $pluginPath/mail_sys_main.py $download_Url/install/plugin/mail_sys/mail_sys_main.py -T 5
	wget -O $pluginPath/receive_mail.py $download_Url/install/plugin/mail_sys/receive_mail.py -T 5
	wget -O $pluginPath/send_mail.py $download_Url/install/plugin/mail_sys/send_mail.py -T 5
	wget -O $pluginPath/index.html $download_Url/install/plugin/mail_sys/index.html -T 5
	wget -O $pluginPath/info.json $download_Url/install/plugin/mail_sys/info.json -T 5
	wget -O $pluginPath/icon.png $download_Url/install/plugin/mail_sys/icon.png -T 5
	wget -O $pluginPath/install.sh $download_Url/install/plugin/mail_sys/install.sh -T 5
	wget -O $pluginStaticPath/api.zip $download_Url/install/plugin/mail_sys/api.zip -T 5
	wget -O /www/server/panel/BTPanel/static/ckeditor.zip $download_Url/install/plugin/mail_sys/ckeditor.zip -T 5
	if [ ! -d "/www/server/panel/BTPanel/static/ckeditor" ]; then
	    unzip /www/server/panel/BTPanel/static/ckeditor.zip -d /www/server/panel/BTPanel/static
	fi

	rpm -Uhv $download_Url/install/plugin/mail_sys/gf-release-latest.gf.el7.noarch.rpm

	pip install dnspython==1.16.0
	echo '安装完成' > $install_tmp
}

#卸载
Uninstall()
{
	yum remove postfix3 -y
	rm -rf /etc/postfix
	rm -rf /etc/postfix.origin

	yum remove dovecot -y
	rm -rf /etc/dovecot
	rm -rf /etc/dovecot.origin

	userdel vmail
	unalias cp
	cp -a /www/vmail /www/vmail.bak
	rm -rf /www/vmail

    firewall-cmd --remove-port=25/tcp --remove-port=110/tcp --remove-port=143/tcp --permanent
    firewall-cmd --remove-port=465/tcp --remove-port=995/tcp --remove-port=993/tcp --remove-port=587/tcp --permanent
    firewall-cmd --reload

    rm -rf $pluginPath
}

#操作判断
if [ "${1}" == 'install' ];then
	Install
elif [ "${1}" == 'uninstall' ];then
	Uninstall
else
	echo 'Error!';
fi
