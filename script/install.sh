#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
echo "
+----------------------------------------------------------------------
| Bt-WebPanel 3.0 FOR CentOS beta
+----------------------------------------------------------------------
| Copyright (c) 2015-2017 BT-SOFT(http://www.bt.cn) All rights reserved.
+----------------------------------------------------------------------
| Python2.6/2.7 successful the http://SERVER_IP:8888 is WebPanel
+----------------------------------------------------------------------
"

download_Url='http://download.bt.cn'
setup_patn=/www

while [ "$go" != 'y' ] && [ "$go" != 'n' ]
do
	read -p "Now do you want to install Bt-Panel to the $setup_patn directory?(y/n): " go;
done

if [ "$go" == 'n' ];then
	exit;
fi

yum -y install ntp
\cp -a -r /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
echo 'Synchronizing system time..'
ntpdate 0.asia.pool.ntp.org
hwclock -w

startTime=`date +%s`

rm -f /var/run/yum.pid
paces="wget python-devel python-imaging zip unzip openssl openssl-devel gcc libxml2 libxml2-dev libxslt* zlib zlib-devel libjpeg-devel libpng-devel libwebp libwebp-devel freetype freetype-devel lsof pcre pcre-devel vixie-cron crontabs"
yum -y install $paces

if [ ! -f '/usr/bin/mysql_config' ];then
	yum install mysql-devel -y
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

if [ ! -f "/usr/lib64/python${pVersion}/site-packages/Pillow-3.2.0-py${pVersion}-linux-x86_64.egg" ] && [ ! -f "/usr/lib/python${pVersion}/site-packages/Pillow-3.2.0-py${pVersion}-linux-x86_64.egg" ];then
	wget $download_Url/install/src/Pillow-3.2.0.zip -T 10
	unzip Pillow-3.2.0.zip
	rm -f Pillow-3.2.0.zip
	cd Pillow-3.2.0
	python setup.py install
	cd ..
	rm -rf Pillow-3.2.0
fi

if [ ! -d "/usr/lib/python${pVersion}/site-packages/psutil-5.1.3-py${pVersion}-linux-x86_64.egg" ] && [ ! -d "/usr/lib64/python${pVersion}/site-packages/psutil-5.1.3-py${pVersion}-linux-x86_64.egg" ];then
	wget $download_Url/install/src/psutil-5.1.3.tar.gz -T 10
	tar xvf psutil-5.1.3.tar.gz
	rm -f psutil-5.1.3.tar.gz
	cd psutil-5.1.3
	python setup.py install
	cd ..
	rm -rf psutil-5.1.3
fi

if [ ! -f "/usr/lib64/python${pVersion}/site-packages/MySQL_python-1.2.5-py${pVersion}-linux-x86_64.egg" ] && [ ! -f "/usr/lib/python${pVersion}/site-packages/MySQL_python-1.2.5-py${pVersion}-linux-x86_64.egg" ];then
	wget $download_Url/install/src/MySQL-python-1.2.5.zip -T 10
	unzip MySQL-python-1.2.5.zip
	rm -f MySQL-python-1.2.5.zip
	cd MySQL-python-1.2.5
	python setup.py install
	cd ..
	rm -rf MySQL-python-1.2.5
fi

if [ ! -f "/usr/lib/python${pVersion}/site-packages/chardet-2.3.0-py${pVersion}.egg" ];then
	wget $download_Url/install/src/chardet-2.3.0.tar.gz -T 10
	tar xvf chardet-2.3.0.tar.gz
	rm -f chardet-2.3.0.tar.gz
	cd chardet-2.3.0
	python setup.py install
	cd ..
	rm -rf chardet-2.3.0
fi
if [ ! -f "/usr/lib/python${pVersion}/site-packages/web.py-0.38-py${pVersion}.egg-info" ];then
	wget $download_Url/install/src/web.py-0.38.tar.gz -T 10
	tar xvf web.py-0.38.tar.gz
	rm -f web.py-0.38.tar.gz
	cd web.py-0.38
	python setup.py install
	cd ..
	rm -rf web.py-0.38
fi


mkdir -p $setup_patn/server/panel/logs
wget https://dl.eff.org/certbot-auto --no-check-certificate -O $setup_patn/server/panel/certbot-auto
chmod +x $setup_patn/server/panel/certbot-auto
isCron=`cat /var/spool/cron/root|grep certbot.log`
if [ "${isCron}" == "" ];then
	echo "30 2 * * * $setup_patn/server/panel/certbot-auto renew >> $setup_patn/server/panel/logs/certbot.log" >>  /var/spool/cron/root
	chown 600 /var/spool/cron/root
fi

if [ -f '/etc/init.d/bt' ];then
	service bt stop
fi

mkdir -p /www/server
mkdir -p /www/wwwroot
mkdir -p /www/wwwlogs
mkdir -p /www/backup/database
mkdir -p /www/backup/site


wget -O panel.zip $download_Url/install/src/panel.zip -T 10
wget -O /etc/init.d/bt $download_Url/install/src/bt.init -T 10
if [ -f "$setup_patn/server/panel/data/default.db" ];then
	if [ -d "/$setup_patn/server/panel/old_data" ];then
		rm -rf /$setup_patn/server/panel/old_data
	fi
	mv $setup_patn/server/panel/data /$setup_patn/server/panel/old_data
fi

unzip -o panel.zip -d $setup_patn/server/ > /dev/null

if [ -d "$setup_patn/server/panel/old_data" ];then
	if [ -d "/$setup_patn/server/panel/data" ];then
		rm -rf /$setup_patn/server/panel/data
	fi
	mv /$setup_patn/server/panel/old_data $setup_patn/server/panel/data
fi


rm -f panel.zip

rm -f $setup_patn/server/panel/class/*.pyc
rm -f $setup_patn/server/panel/*.pyc
python -m compileall $setup_patn/server/panel
rm -f $setup_patn/server/panel/class/*.py
rm -f $setup_patn/server/panel/*.py

chmod +x /etc/init.d/bt
chkconfig --add bt
chkconfig --level 2345 bt on
echo '8888' > $setup_patn/server/panel/data/port.pl
chmod -R 600 $setup_patn/server/panel
chmod +x $setup_patn/server/panel/certbot-auto
chmod -R +x $setup_patn/server/panel/script
service bt start
password=`cat /dev/urandom | head -n 16 | md5sum | head -c 8`
cd $setup_patn/server/panel/
python tools.pyc panel $password
cd ~
echo "$password" > $setup_patn/server/panel/default.pl
chmod 600 $setup_patn/server/panel/default.pl

if [ -f "/etc/init.d/iptables" ];then
	iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 20 -j ACCEPT
	iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 21 -j ACCEPT
	iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT
	iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 80 -j ACCEPT
	iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 8888 -j ACCEPT
	iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 30000:40000 -j ACCEPT
	service iptables save

	iptables_status=`service iptables status | grep 'not running'`
	if [ "${iptables_status}" == '' ];then
		service iptables restart
	fi
fi

if [ "${isVersion}" == '' ];then
	if [ ! -f "/etc/init.d/iptables" ];then
		yum install firewalld -y
		systemctl enable firewalld
		systemctl start firewalld
		firewall-cmd --permanent --zone=public --add-port=20/tcp
		firewall-cmd --permanent --zone=public --add-port=21/tcp
		firewall-cmd --permanent --zone=public --add-port=22/tcp
		firewall-cmd --permanent --zone=public --add-port=80/tcp
		firewall-cmd --permanent --zone=public --add-port=8888/tcp
		firewall-cmd --permanent --zone=public --add-port=30000-40000/tcp
		firewall-cmd --reload
	fi
fi

yum -y install epel-release
country=`curl -sS --connect-timeout 10 -m 60 http://ip.vpser.net/country`
if [ "${country}" = "CN" ]; then
    mkdir ~/.pip
    cat > ~/.pip/pip.conf <<EOF
[global]
index-url = https://pypi.doubanio.com/simple/

[install]
trusted-host=pypi.doubanio.com
EOF
    fi
nohup $setup_patn/server/panel/certbot-auto -n > /tmp/certbot-auto.log 2>&1 &

address=""
n=0
while [ "$address" == '' ]
do
	address=`curl -s http://city.ip138.com/ip2city.asp|grep -Eo '([0-9]+\.){3}[0-9]+'`
	let n++
	sleep 0.1
	if [ $n -gt 5 ];then
		address="SERVER_IP"
	fi
done

curl http://www.bt.cn/Api/SetupCount?type=Linux

echo "====================================="
echo -e "\033[32mThe install successful!\033[0m"
echo -e "====================================="
echo -e "Bt-Panel: http://$address:8888"
echo -e "username: admin"
echo -e "password: $password"
echo -e "====================================="
endTime=`date +%s`
((outTime=($endTime-$startTime)/60))
echo -e "Time consuming:\033[32m $outTime \033[0mMinute!"
rm -f install.sh
