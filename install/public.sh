#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
pyenv_bin=/www/server/panel/pyenv/bin
rep_path=${pyenv_bin}:$PATH
if [ -d "$pyenv_bin" ];then
	PATH=$rep_path
fi
export PATH
export LANG=en_US.UTF-8
export LANGUAGE=en_US:en

NODE_FILE_CHECK=$(cat /www/server/panel/data/node.json |grep 125.88.182.172)
if [ "${NODE_FILE_CHECK}" ];then
	rm -f /www/server/panel/data/node.json
fi

if [ -f "/www/server/panel/install/d_node.pl" ];then
	LOCAL_DATE=$(date +%Y-%m-%d)
	FILE_DATE=$(stat /www/server/panel/install/d_node.pl|grep Change|awk '{print $2}')
	if [ "${LOCAL_DATE}" != "${FILE_DATE}" ];then
		rm -f /www/server/panel/install/d_node.pl
	else
		test_url=$(cat /www/server/panel/install/d_node.pl)
		HTTP_CHECK=$(curl --connect-timeout 3 -m 3 2>/dev/null -w "%{http_code} %{time_total}" ${test_url}/net_test|xargs|awk '{print $2}')
		if [ "${HTTP_CHECK}" == "200" ];then
			NODE_URL=$test_url
		fi
	fi
fi

get_node_url(){
	nodes=(https://dg2.bt.cn https://download.bt.cn https://ctcc1-node.bt.cn https://cmcc1-node.bt.cn https://ctcc2-node.bt.cn https://hk1-node.bt.cn https://na1-node.bt.cn https://jp1-node.bt.cn https://cf1-node.aapanel.com);

	if [ -f "/www/server/panel/data/domestic_ip.pl" ];then
		nodes=(https://dg2.bt.cn https://download.bt.cn https://ctcc1-node.bt.cn https://cmcc1-node.bt.cn https://ctcc2-node.bt.cn https://hk1-node.bt.cn);
	fi

	if [ -f "/www/server/panel/data/foreign_ip.pl" ];then
		nodes=(https://cf1-node.aapanel.com https://dg2.bt.cn https://na1-node.bt.cn  https://jp1-node.bt.cn https://download.bt.cn https://ctcc1-node.bt.cn  https://ctcc2-node.bt.cn https://hk1-node.bt.cn);
	fi

	if [ "$1" ];then
		nodes=($(echo ${nodes[*]}|sed "s#${1}##"))
	fi

	tmp_file1=/dev/shm/net_test1.pl
	tmp_file2=/dev/shm/net_test2.pl
	[ -f "${tmp_file1}" ] && rm -f ${tmp_file1}
	[ -f "${tmp_file2}" ] && rm -f ${tmp_file2}
	touch $tmp_file1
	touch $tmp_file2
	for node in ${nodes[@]};
	do
		if [ "${node}" == "https://cf1-node.aapanel.com" ];then
			NODE_CHECK=$(curl --connect-timeout 3 -m 3 2>/dev/null -w "%{http_code} %{time_total}" ${node}/1net_test|xargs)
		else
			NODE_CHECK=$(curl --connect-timeout 3 -m 3 2>/dev/null -w "%{http_code} %{time_total}" ${node}/net_test|xargs)
		fi
		RES=$(echo ${NODE_CHECK}|awk '{print $1}')
		NODE_STATUS=$(echo ${NODE_CHECK}|awk '{print $2}')
		TIME_TOTAL=$(echo ${NODE_CHECK}|awk '{print $3 * 1000 - 500 }'|cut -d '.' -f 1)
		if [ "${NODE_STATUS}" == "200" ];then
			if [ $TIME_TOTAL -lt 300 ];then
				if [ $RES -ge 1500 ];then
					echo "$RES $node" >> $tmp_file1
				fi
			else
				if [ $RES -ge 1500 ];then
					echo "$TIME_TOTAL $node" >> $tmp_file2
				fi
			fi

			i=$(($i+1))
			if [ $TIME_TOTAL -lt 300 ];then
				if [ $RES -ge 2390 ];then
					break;
				fi
			fi	
		fi
	done

	NODE_URL=$(cat $tmp_file1|sort -r -g -t " " -k 1|head -n 1|awk '{print $2}')
	if [ -z "$NODE_URL" ];then
		NODE_URL=$(cat $tmp_file2|sort -g -t " " -k 1|head -n 1|awk '{print $2}')
		if [ -z "$NODE_URL" ];then
			NODE_URL='https://download.bt.cn';
		fi
	fi
	rm -f $tmp_file1
	rm -f $tmp_file2
}

GetCpuStat(){
	time1=$(cat /proc/stat |grep 'cpu ')
	sleep 1
	time2=$(cat /proc/stat |grep 'cpu ')
	cpuTime1=$(echo ${time1}|awk '{print $2+$3+$4+$5+$6+$7+$8}')
	cpuTime2=$(echo ${time2}|awk '{print $2+$3+$4+$5+$6+$7+$8}')
	runTime=$((${cpuTime2}-${cpuTime1}))
	idelTime1=$(echo ${time1}|awk '{print $5}')
	idelTime2=$(echo ${time2}|awk '{print $5}')
	idelTime=$((${idelTime2}-${idelTime1}))
	useTime=$(((${runTime}-${idelTime})*3))
	[ ${useTime} -gt ${runTime} ] && cpuBusy="true"
	if [ "${cpuBusy}" == "true" ]; then
		cpuCore=$((${cpuInfo}/2))
	else
		cpuCore=$((${cpuInfo}-1))
	fi
}
GetPackManager(){
	if [ -f "/usr/bin/yum" ] && [ -f "/etc/yum.conf" ]; then
		PM="yum"
	elif [ -f "/usr/bin/apt-get" ] && [ -f "/usr/bin/dpkg" ]; then
		PM="apt-get"		
	fi
}

bt_check(){
	p_path=/www/server/panel/class/panelPlugin.py
	if [ -f $p_path ];then
		is_ext=$(cat $p_path|grep btwaf)
		if [ "$is_ext" != "" ];then
			send_check
		fi
	fi
	
	p_path=/www/server/panel/BTPanel/templates/default/index.html
	if [ -f $p_path ];then
		is_ext=$(cat $p_path|grep fbi)
		if [ "$is_ext" != "" ];then
			send_check
		fi
	fi
}

send_check(){
	chattr -i /etc/init.d/bt
	chmod +x /etc/init.d/bt
	p_path2=/www/server/panel/class/common.py
	p_version=$(cat $p_path2|grep "version = "|awk '{print $3}'|tr -cd [0-9.])
	curl -sS --connect-timeout 3 -m 60 https://www.bt.cn/api/panel/notpro?version=$p_version
	NODE_URL=""
	exit 0;
}
GetSysInfo(){
	if [ "${PM}" = "yum" ]; then
		SYS_VERSION=$(cat /etc/redhat-release)
	elif [ "${PM}" = "apt-get" ]; then
		SYS_VERSION=$(cat /etc/issue)
	fi
	SYS_INFO=$(uname -msr)
	SYS_BIT=$(getconf LONG_BIT)
	MEM_TOTAL=$(free -m|grep Mem|awk '{print $2}')
	CPU_INFO=$(getconf _NPROCESSORS_ONLN)
	GCC_VER=$(gcc -v 2>&1|grep "gcc version"|awk '{print $3}')
	CMAKE_VER=$(cmake --version|grep version|awk '{print $3}')

	echo -e ${SYS_VERSION}
	echo -e Bit:${SYS_BIT} Mem:${MEM_TOTAL}M Core:${CPU_INFO} gcc:${GCC_VER} cmake:${CMAKE_VER}
	echo -e ${SYS_INFO}
}
cpuInfo=$(getconf _NPROCESSORS_ONLN)
if [ "${cpuInfo}" -ge "4" ];then
	GetCpuStat
else
	cpuCore="1"
fi
GetPackManager

if [ -d "/www/server/phpmyadmin/pma" ];then
	rm -rf /www/server/phpmyadmin/pma
	EN_CHECK=$(cat /www/server/panel/config/config.json |grep English)
	if [ "${EN_CHECK}" ];then
		curl https://download.bt.cn/install/update6_en.sh|bash
	else
		curl https://download.bt.cn/install/update6.sh|bash
	fi
	echo > /www/server/panel/data/restart.pl
fi

if [ ! $NODE_URL ];then
	EN_CHECK=$(cat /www/server/panel/config/config.json |grep English)
	if [ -z "${EN_CHECK}" ];then
		echo '正在选择下载节点...';
	else
		echo "selecting download node...";
	fi
	get_node_url
	bt_check
fi


