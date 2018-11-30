#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

Is_64bit=`getconf LONG_BIT`
if [ "$Is_64bit" = '32' ];then
	echo 'Error: 32 bit OS is not supported.'
	exit;
fi

if [ ! -f '/etc/redhat-release' ];then
	echo 'Error: The current OS is not supported.'
	exit;
fi

public_file=/www/server/panel/install/public.sh
if [ ! -f $public_file ];then
	wget -O $public_file http://download.bt.cn/install/public.sh -T 5;
fi
. $public_file

download_Url=$NODE_URL
Install_git()
{
	isSetup=`git version|grep ' 2\.'`
	if [ "$isSetup" != '' ];then
		
		echo $isSetup
		return
	fi
	yum install expat-devel gettext-devel openssl-devel zlib-devel asciidoc -y
	yum install  gcc perl-ExtUtils-MakeMaker
	wget -O git-master.zip $download_Url/src/git-master.zip
	unzip git-master.zip
	cd git-master/
	make configure
	./configure --prefix=/usr/local/git --with-iconv=/usr/local/libiconv
	make all
	make install
	echo "export PATH=$PATH:/usr/local/git/bin" >> /etc/bashrc
	source /etc/bashrc
	rm -f /usr/bin/git*
	ln -sf /usr/local/git/bin/* /usr/bin/
	cd ..
	rm -f git-master.zip
	rm -rf git-*
	git version
}


Install_gitlab()
{
	Install_git
	Uninstall_gitlab
	if [ -f '/opt/gitlab/embedded/service/gitlab-rails/Gemfile' ];then
		echo "The gitlab is installed."
		return;
	fi
	
	yum install openssh-server openssh-clients postfix cronie -y
	isEl7=`cat /etc/redhat-release|grep ' 7.'`
	if [ "$isEl7" != '' ];then
		systemctl enable postfix
		systemctl start postfix
		if [ ! -f gitlab-ce-8.8.5-ce.1.el7.x86_64.rpm ];then
			wget -O gitlab-ce-8.8.5-ce.1.el7.x86_64.rpm $download_Url/src/gitlab-ce-8.8.5-ce.1.el7.x86_64.rpm -T 5
		else
			wget -c $download_Url/src/gitlab-ce-8.8.5-ce.1.el7.x86_64.rpm -T 5
		fi
		rpm -ivh gitlab-ce-8.8.5-ce.1.el7.x86_64.rpm
		if [ ! -f /usr/bin/gitlab-ctl ];then
			echo 'Error: Installation failure'
			return;
		fi
		rm -f gitlab-ce-8.8.5-ce.1.el7.x86_64.rpm
		firewall-cmd --permanent --zone=public --add-port=8099/tcp > /dev/null 2>&1
		firewall-cmd --reload
	else
		chkconfig postfix on
		service postfix start
		if [ ! -f gitlab-ce-8.8.5-ce.1.el6.x86_64.rpm ];then
			wget -O gitlab-ce-8.8.5-ce.1.el6.x86_64.rpm $download_Url/src/gitlab-ce-8.8.5-ce.1.el6.x86_64.rpm -T 5
		else
			wget -c $download_Url/src/gitlab-ce-8.8.5-ce.1.el6.x86_64.rpm -T 5
		fi
		rpm -ivh gitlab-ce-8.8.5-ce.1.el6.x86_64.rpm
		if [ ! -f /usr/bin/gitlab-ctl ];then
			echo 'Error: Installation failure'
			return;
		fi
		rm -f gitlab-ce-8.8.5-ce.1.el6.x86_64.rpm
		iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 8099 -j ACCEPT
		service iptables save
		
	fi
	
	wget -O /etc/gitlab/gitlab.rb $download_Url/conf/gitlab.rb -T 5
	address=`cat /www/server/panel/data/iplist.txt`
	if [ "$address" = '' ];then
		address=`curl -sS --connect-timeout 10 -m 60 https://www.bt.cn/Api/getIpAddress`
	fi
	
	if [ -f /etc/init.d/nginx ];then
		isDownload=`cat /etc/init.d/nginx|grep 'isStart'`
		if [ "$isDownload" = '' ];then
			mv -f /etc/init.d/nginx /tmp/nginx_backup
			wget -O /etc/init.d/nginx $download_Url/init/nginx.init -T 5
			chmod +x /etc/init.d/nginx
		fi
		
		isDownload=`cat /etc/init.d/nginx|grep 'isStart'`
		if [ "$isDownload" = '' ];then
			mv -f /tmp/nginx_backup /etc/init.d/nginx
			chmod +x /etc/init.d/nginx
		fi
	fi	
	
	sed -i "s/SERVERIP/$address/" /etc/gitlab/gitlab.rb
	
	echo '正在初始化GitLab配置...'
	gitlab-ctl stop
	gitlab-ctl reconfigure
	gitlab-ctl stop
	
	wget -O gitlab-rails.zip $download_Url/src/gitlab-rails.zip -T 5
	unzip -o gitlab-rails.zip -d /opt/gitlab/embedded/service/
	rm -f gitlab-rails.zip
	gitlab-ctl start
	
	pluginPath=/www/server/panel/plugin/gitlab
	mkdir -p $pluginPath
	wget -O $pluginPath/gitlab_main.py $download_Url/install/plugin/gitlab/gitlab_main.py
	wget -O $pluginPath/icon.png $download_Url/install/plugin/gitlab/icon.png
	wget -O $pluginPath/index.html $download_Url/install/plugin/gitlab/index.html
	wget -O $pluginPath/info.json $download_Url/install/plugin/gitlab/info.json
	wget -O $pluginPath/install.sh $download_Url/install/plugin/gitlab/install.sh
	\cp -a -f $pluginPath/icon.png /www/server/panel/static/img/soft_ico/ico-gitlab.png
}


Uninstall_gitlab()
{
	if [ -f /opt/gitlab/embedded/service/gitlab-rails/Gemfile ];then
		gitlab-ctl stop
		yum remove gitlab-ce -y
		rm -rf /opt/gitlab
		rm -rf /var/opt/gitlab
		rm -rf /etc/gitlab
		rm -rf /www/server/panel/plugin/gitlab
	fi
}

action=$1
if [ "$action" = 'install' ];then
	Install_gitlab
elif [ "$action" = 'uninstall' ];then
	Uninstall_gitlab
fi
