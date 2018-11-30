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

Install_docker()
{
	Install_Docker_ce
	mkdir -p /www/server/panel/plugin/docker
	echo '正在安装脚本文件...' > $install_tmp
	wget -O /www/server/panel/plugin/docker/docker_main.py $download_Url/install/plugin/docker/docker_main.py -T 5
	wget -O /www/server/panel/plugin/docker/index.html $download_Url/install/plugin/docker/index.html -T 5
	wget -O /www/server/panel/plugin/docker/info.json $download_Url/install/plugin/docker/info.json -T 5
	wget -O /www/server/panel/plugin/docker/icon.png $download_Url/install/plugin/docker/icon.png -T 5
	wget -O /www/server/panel/plugin/docker/login-docker.html $download_Url/install/plugin/docker/login-docker.html -T 5
	wget -O /www/server/panel/plugin/docker/userdocker.html $download_Url/install/plugin/docker/userdocker.html -T 5
	echo '安装完成' > $install_tmp
}

Install_Docker_ce()
{
	#install docker-ce
	yum remove docker docker-common docker-selinux docker-engine -y
	yum install -y yum-utils device-mapper-persistent-data lvm2 -y
	yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
	yum-config-manager --enable docker-ce-edge
	yum install docker-ce -y
	yum-config-manager --disable docker-ce-edge
	
	#move docker data to /www/server/docker
	echo 'move docker data to /www/server/docker ...';
	if [ -f /usr/bin/systemctl ];then
		systemctl stop docker
	else
		service docker stop
	fi
	if [ ! -d /www/server/docker ];then
		mv -f /var/lib/docker /www/server/docker
	else
		rm -rf /var/lib/docker
	fi
	
	ln -sf /www/server/docker /var/lib/docker
	
	#systemctl or service
	if [ -f /usr/bin/systemctl ];then
		systemctl stop getty@tty1.service
		systemctl mask getty@tty1.service
		systemctl enable docker
		systemctl start docker
	else
		chkconfig --add docker
		chkconfig --level 2345 docker on
		service docker start
	fi
	
	#install python-docker
	pip install docker

	#pull image of bt-panel
	imageVersion='5.6.0'
	docker pull registry.cn-hangzhou.aliyuncs.com/bt-panel/panel:$imageVersion
	docker tag `docker images|grep bt-panel|awk '{print $3}'` bt-panel:$imageVersion
}

Uninstall_docker()
{
	rm -rf /www/server/panel/plugin/docker
	if [ -f /usr/bin/systemctl ];then
		systemctl disable docker
		systemctl stop docker
	else
		service docker stop
		chkconfig --level 2345 docker off
		chkconfig --del docker
	fi
	pip uninstall docker -y
}


action=$1
if [ "${1}" == 'install' ];then
	Install_docker
else
	Uninstall_docker
fi