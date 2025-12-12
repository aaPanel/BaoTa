#!/bin/bash
# chkconfig: 2345 55 25
# description: bt Cloud Service

### BEGIN INIT INFO
# Provides:          bt
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts bt
# Description:       starts the bt
### END INIT INFO

if [ "$(id -u)" -ne 0 ]; then
    echo "===================警告======================"
    echo "检测到非root用户权限执行bt命令，可能存在异常 "
    echo "请使用此命令重新执行：sudo bt"
    echo "============================================="
fi

panel_init(){
        panel_path=/www/server/panel
        pidfile=$panel_path/logs/panel.pid
        cd $panel_path
        env_path=$panel_path/pyenv/bin/python3
        if [ -f $env_path ];then
                pythonV=$panel_path/pyenv/bin/python3
                chmod -R 700 $panel_path/pyenv/bin &> /dev/null
                is_sed_panel=$(cat $panel_path/BT-Panel|head -n 1|grep '^#!/www/server/panel/pyenv/bin/python3$')
                is_sed_task=$(cat $panel_path/BT-Task|head -n 1|grep '^#!/www/server/panel/pyenv/bin/python3$')
        else
                pythonV=/usr/bin/python
                is_sed_panel=$(cat $panel_path/BT-Panel|head -n 1|grep '^#!/usr/bin/python$')
                is_sed_task=$(cat $panel_path/BT-Task|head -n 1|grep '^#!/usr/bin/python$')
        fi
        if [ "${is_sed_panel}" = "" ];then
                sed -i "s@^#!.*@#!$pythonV@" $panel_path/BT-Panel &> /dev/null
        fi
        is_python=$(cat $panel_path/BT-Task|grep import)
        if [ "${is_python}" != "" ];then
            if [ "${is_sed_task}" = "" ];then
                    sed -i "s@^#!.*@#!$pythonV@" $panel_path/BT-Task &> /dev/null
            fi
        fi
        chmod 700 $panel_path/BT-Panel &> /dev/null
        chmod 700 $panel_path/BT-Task &> /dev/null
        log_file=$panel_path/logs/error.log
        task_log_file=$panel_path/logs/task.log
        if [ -f $panel_path/data/ssl.pl ];then
                log_file=/dev/null
        fi

        port=$(cat $panel_path/data/port.pl)
}
panel_init

get_panel_pids(){
        isStart=$(ps aux|grep -E '(runserver|BT-Panel)'|grep -v grep|awk '{print $2}'|xargs)
        pids=$isStart
        arr=$isStart
}

get_task_pids(){
        isStart=$(ps aux|grep -E '(task.py|BT-Task)'|grep -v grep|awk '{print $2}'|xargs)
        pids=$isStart
        arr=$isStart
}

panel_start()
{
        isStart=`ps aux|grep 'runserver:app'|grep -v grep|awk '{print $2}'`
        if [ "$isStart" != '' ];then
                kill -9 $isStart
        fi
        get_panel_pids

        if [ -f $panel_path/script/init_db.py ]; then
            $pythonV $panel_path/script/init_db.py init_db # 初始化面板数据库
            $pythonV $panel_path/tools.py check_db # 检查面板数据库，默认数据
        fi
        if [ "$isStart" == '' ];then
                rm -f $pidfile &> /dev/null

                echo -e "Starting Bt-Panel...\c"
                echo '\n' >> $log_file
                if [ $? -ne 0 ];then
                    $panel_path/BT-Panel > /dev/null 2>&1
                else
                    $panel_path/BT-Panel >> $log_file 2>&1
                fi
                isStart=""
                n=0
                while [[ "$isStart" == "" ]];
                do
                        echo -e ".\c"
                        sleep 0.5
                        get_panel_pids
                        let n+=1
                        if [ $n -gt 8 ];then
                                break;
                        fi
                done
                if [ "$isStart" == '' ];then
                        panel_port_check
                        echo -e "\033[31mfailed\033[0m"
                        echo '------------------------------------------------------'
                        tail -n 20 $log_file
                        echo '------------------------------------------------------'
                        echo -e "\033[31mError: BT-Panel service startup failed.\033[0m"
                fi
                echo -e "	\033[32mdone\033[0m"
        else
                echo "Starting Bt-Panel... Bt-Panel (pid $(echo $isStart)) already running"
        fi

        get_task_pids
        if [ "$isStart" == '' ];then
                echo -e "Starting Bt-Tasks... \c"
                echo '\n' >> $task_log_file
                if [ $? -ne 0 ];then
                    $panel_path/BT-Task > /dev/null 2>&1
                else
                    $panel_path/BT-Task >> $task_log_file 2>&1
                fi
                sleep 0.2
                get_task_pids
                if [ "$isStart" == '' ];then
                        echo -e "\033[31mfailed\033[0m"
                        echo '------------------------------------------------------'
                        tail -n 20 $task_log_file
                        echo '------------------------------------------------------'
                        echo -e "\033[31mError: BT-Task service startup failed.\033[0m"
                        return;
                fi
                echo -e "	\033[32mdone\033[0m"
        else
                echo "Starting Bt-Tasks... Bt-Tasks (pid $isStart) already running"
        fi

        if [[ -f ${panel_path}/data/panel_ssl_error.pl ]]; then
                port=$(cat $panel_path/data/port.pl)
                password=$(cat $panel_path/default.pl)
                if [ -f $panel_path/data/domain.conf ];then
                        address=$(cat $panel_path/data/domain.conf)
                fi
                auth_path=/login
                if [ -f $panel_path/data/admin_path.pl ];then
                        auth_path=$(cat $panel_path/data/admin_path.pl)
                fi
                if [ "$address" = "" ];then
                        address=$(curl -sS --connect-timeout 10 -m 60 https://www.bt.cn/Api/getIpAddress)
                fi
                if [ "$auth_path" == "/" ];then
                        auth_path=/login
                fi
                LOCAL_IP=$(ip addr | grep -E -o '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' | grep -E -v "^127\.|^255\.|^0\." | head -n 1)
                echo ""
                echo -e "=================================================================="
                echo -e "\033[32m您的面板SSL证书似乎出现了问题，已为您临时关闭面板HTTPS访问\033[0m"
                echo -e "\033[32m请使用如下地址访问宝塔面板，随后到面板设置中重新开启面板SSL证书即可！\033[0m"
                echo -e "=================================================================="
                echo  "外网面板地址: http://${address}:${port}${auth_path}"
                echo  "内网面板地址: http://${LOCAL_IP}:${port}${auth_path}"
                echo -e `$pythonV $panel_path/tools.py username`
                echo -e "password: $password"
                echo -e "\033[33mWarning:\033[0m"
                echo -e "\033[33mIf you cannot access the panel, \033[0m"
                echo -e "\033[33mrelease the following port (8888|888|80|443|20|21) in the security group\033[0m"
                echo -e "\033[33m注意：初始密码仅在首次登录面板前能正确获取，其它时间请通过 bt 5 命令修改密码\033[0m"
                echo -e "=================================================================="
                echo -e "=================================================================="
                echo ""
                rm -rf ${panel_path}/data/panel_ssl_error.pl
        fi
}

panel_port_check()
{
	is_process=$(lsof -n -P -i:$port -sTCP:LISTEN|grep LISTEN|grep -v grep|awk '{print $1}'|sort|uniq|xargs)
	for pn in ${is_process[@]}
        do
          if [ "$pn" = "nginx" ];then
				/etc/init.d/nginx restart
		  fi

		  if [ "$pn" = "httpd" ];then
				/etc/init.d/httpd restart
		  fi

		  if [ "$pn" = "mysqld" ];then
				/etc/init.d/mysqld restart
		  fi

		  if [ "$pn" = "superviso" ];then
				pkill -9 superviso
				sleep 0.2a
				supervisord -c /etc/supervisor/supervisord.conf
		  fi

		  if [ "$pn" = "pure-ftpd" ];then
				/etc/init.d/pure-ftpd restart
		  fi

		  if [ "$pn" = "memcached" ];then
				/etc/init.d/memcached restart
		  fi

		  if [ "$pn" = "sudo" ];then
				if [ -f /etc/init.d/redis ];then
					/etc/init.d/redis restart
				fi
		  fi

		  if [ "$pn" = "php-fpm" ];then
				php_v=(52 53 54 55 56 70 71 72 73 74);
				for pv in ${php_v[@]};
				do
					if [ -f /etc/init.d/php-fpm-${pv} ];then
						if [ -f /www/server/php/%{pv}/sbin/php-fpm ];then
							if [ -f /tmp/php-cgi-${pv}.sock ];then
								/etc/init.d/php-fpm-${pv} start
							fi
							/etc/init.d/php-fpm-${pv} restart
						fi
					fi
				done
		  fi
        done

	is_ports=$(lsof -n -P -i:$port|grep LISTEN|grep -v grep|awk '{print $2}'|xargs)
	if [ "$is_ports" != '' ];then
		kill -9 $is_ports
		sleep 1
	fi
}

panel_stop()
{
        echo -e "Stopping Bt-Tasks...\c";
        get_task_pids
        arr=($pids)
        for p in ${arr[@]}
        do
                kill -9 $p
        done
        echo -e "	\033[32mdone\033[0m"

        echo -e "Stopping Bt-Panel...\c";

        get_panel_pids
        for p in ${arr[@]}
        do
                kill -9 $p &>/dev/null
        done

        if [ -f $pidfile ];then
                rm -f $pidfile &> /dev/null
        fi
        echo -e "	\033[32mdone\033[0m"
}

panel_status()
{
        port=$(cat $panel_path/data/port.pl)
        get_panel_pids
        if [ "$isStart" != '' ];then
                echo -e "\033[32mBt-Panel (pid $(echo $isStart)) already running\033[0m"
        else
                echo -e "\033[31mBt-Panel not running\033[0m"
        fi

        get_task_pids
        if [ "$isStart" != '' ];then
                echo -e "\033[32mBt-Task (pid $isStart) already running\033[0m"
        else
                echo -e "\033[31mBt-Task not running\033[0m"
        fi
}

panel_reload()
{
	isStart=$(ps aux|grep 'runserver:app'|grep -v grep|awk '{print $2}')
        if [ "$isStart" != '' ];then
		kill -9 $isStart
		sleep 0.5
	fi
	get_panel_pids
        if [ "$isStart" != '' ];then

	    get_panel_pids
	for p in ${arr[@]}
        do
                kill -9 $p
        done
		rm -f $pidfile
		echo -e "Reload Bt-Panel.\c";
                nohup $panel_path/BT-Panel >> $log_file 2>&1 &
		isStart=""
		n=0
		while [[ "$isStart" == "" ]];
		do
			echo -e ".\c"
			sleep 0.5
			get_panel_pids
			let n+=1
			if [ $n -gt 8 ];then
				break;
			fi
		done
        if [ "$isStart" == '' ];then
                panel_port_check
                echo -e "\033[31mfailed\033[0m"
                echo '------------------------------------------------------'
                tail -n 20 $log_file
                echo '------------------------------------------------------'
                echo -e "\033[31mError: BT-Panel service startup failed.\033[0m"
                return;
        fi
        echo -e "	\033[32mdone\033[0m"
    else
        echo -e "\033[31mBt-Panel not running\033[0m"
        panel_start
    fi
}

install_used()
{
        if [ -f $panel_path/random_path.pl ];then
                random_path=$(cat /dev/urandom | head -n 16 | md5sum | head -c 6)
                echo "/${random_path}" > $panel_path/data/admin_path.pl
                random_user=$(cat /dev/urandom | head -n 16 | md5sum | head -c 8)
                re_user=$($pythonV $panel_path/tools.py reusername $random_user)
                rm -f $panel_path/random_path.pl
        fi

        if [ -f $panel_path/aliyun.pl ];then
                random_user=$(cat /dev/urandom | head -n 16 | md5sum | head -c 8)
                re_user=$($pythonV $panel_path/tools.py reusername $random_user)
                password=$(cat /dev/urandom | head -n 16 | md5sum | head -c 12)
                username=$($pythonV $panel_path/tools.py panel $password)
                echo "$password" > $panel_path/default.pl
                if [ -f "/www/server/panel/data/o.pl" ];then
                        IDC_CODE=$(cat /www/server/panel/data/o.pl)
                else
                        IDC_CODE=""
                fi
                if [ -f "/www/server/panel/script/download_ip.sh" ];then
                     echo "bash /www/server/panel/script/download_ip.sh > /dev/null 2>&1" |at now + 5 minutes
                fi
                echo "curl -sS --connect-timeout 10 -m 60 https://www.bt.cn/Api/SetupCount?type=Linux\&o=$IDC_CODE > /dev/null 2>&1" |at now + 5 minutes
                rm -f $panel_path/aliyun.pl
                chattr +i $panel_path/default.pl
        fi

        if [ -f $panel_path/php_mysql_auto.pl ];then
                bash $panel_path/script/mysql_auto.sh &> /dev/null
                bash $panel_path/script/php_auto.sh &> /dev/null
                rm -f $panel_path/php_mysql_auto.pl
        fi

        pip_file=/www/server/panel/pyenv/bin/pip3
        python_file=/www/server/panel/pyenv/bin/python3
        if [ -f $pip_file ];then
                is_rep=$(ls -l /usr/bin/btpip|grep pip3.)
                if [ "${is_rep}" != "" ];then
                        rm -f /usr/bin/btpip /usr/bin/btpython
                        ln -sf $pip_file /usr/bin/btpip
                        ln -sf $python_file /usr/bin/btpython
                fi
        fi

}



error_logs()
{
	tail -n 100 $log_file
}


case "$1" in
        'start')
                install_used
                panel_start
                ;;
        'stop')
                panel_stop
                ;;
        'restart')
                if [ -f "/www/server/panel/script/reload_check.py" ];then
                        btpython /www/server/panel/script/reload_check.py
                fi
                panel_stop
		            sleep 1
                panel_start
                ;;
        'reload')
                panel_reload
                ;;
        'status')
                panel_status
                ;;
        'logs')
        		error_logs
        		;;
        'panel')
        		$pythonV $panel_path/tools.py cli $2
        		;;
        'default')
                port=$(cat $panel_path/data/port.pl)
                password=$(cat $panel_path/default.pl)
                if [ -f $panel_path/data/domain.conf ];then
                	address=$(cat $panel_path/data/domain.conf)
                fi
                auth_path=/login
                if [ -f $panel_path/data/admin_path.pl ];then
                	auth_path=$(cat $panel_path/data/admin_path.pl)
                fi
                ipv4_address=""
                ipv6_address=""
                if [ "$address" = "" ];then
                        ipv4_address=$(curl -4 -sS --connect-timeout 4 -m 5 https://api.bt.cn/Api/getIpAddress 2>&1)
                        if [ -z "${ipv4_address}" ];then
                                ipv4_address=$(curl -4 -sS --connect-timeout 4 -m 5 https://www.bt.cn/Api/getIpAddress 2>&1)
                                if [ -z "${ipv4_address}" ];then
                                        ipv4_address=$(curl -4 -sS --connect-timeout 4 -m 5 https://www.aapanel.com/api/common/getClientIP 2>&1)
                                fi
                        fi
                        IPV4_REGEX="^([0-9]{1,3}\.){3}[0-9]{1,3}$"
                        if ! [[ $ipv4_address =~ $IPV4_REGEX ]]; then
                                ipv4_address=""
                        fi

                        ipv6_address=$(curl -6 -sS --connect-timeout 4 -m 5 https://www.bt.cn/Api/getIpAddress 2>&1)
                        IPV6_REGEX="^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"
                        if ! [[ $ipv6_address =~ $IPV6_REGEX ]]; then
                                ipv6_address=""
                        else
                                if [[ ! $ipv6_address =~ ^\[ ]]; then
                                        ipv6_address="[$ipv6_address]"
                                fi
                        fi
                fi

                pool=http
                if [ -f $panel_path/data/ssl.pl ];then
                        pool=https
                fi
                if [ "$auth_path" == "/" ];then
                        auth_path=/login
                fi
                panel_site_address=""
                if [ -f /www/server/panel/data/panel_site_address.pl ];then
			              panel_site_address=$(cat /www/server/panel/data/panel_site_address.pl)
                fi
                LOCAL_IP=$(ip addr | grep -E -o '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' | grep -E -v "^127\.|^255\.|^0\." | head -n 1)
                echo -e "=================================================================="
                echo -e "\033[32mBT-Panel default info!\033[0m"
                echo -e "=================================================================="
                if [ "$address" = "" ] && [ "$ipv4_address" = "" ] && [ "$ipv6_address" = "" ];then
                        address="服务器公网IP"
                        echo "获取外网IP失败，请使用服务器公网IP+端口访问面板"
                fi
                if [ "$ipv4_address" ];then
                        echo  "外网ipv4面板地址: $pool://${ipv4_address}:${port}${auth_path}"
                fi
                if [ "$ipv6_address" ];then
                        echo  "外网ipv6面板地址: $pool://${ipv6_address}:${port}${auth_path}"
                fi
                if [ "$address" ];then
                        echo  "外网面板地址:     $pool://${address}:${port}${auth_path}"
                fi
                echo  "内网面板地址:     $pool://${LOCAL_IP}:${port}${auth_path}"
                if [ "$panel_site_address" != "" ];then
                    echo  "面板免端口地址: ${panel_site_address}"
                fi
                echo -e `$pythonV $panel_path/tools.py username`
                echo -e "password: $password"
                echo -e "\033[33mWarning:\033[0m"
                echo -e "\033[33mIf you cannot access the panel, \033[0m"
                echo -e "\033[33mrelease the following port (8888|888|80|443|20|21) in the security group\033[0m"
                echo -e "\033[33m注意：初始密码仅在首次登录面板前能正确获取，其它时间请通过 bt 5 命令修改密码\033[0m"
                echo -e "=================================================================="
                ;;
        *)
                if [ "${LANG}" != "en_US.UTF-8" ];then
                    export LANG=en_US.UTF-8 &> /dev/null
                fi
                if [ "${LC_ALL}" != "en_US.UTF-8" ];then
                    export LC_ALL=en_US.UTF-8 &> /dev/null
                fi
                $pythonV $panel_path/tools.py cli $1
        ;;
esac

