#!/bin/bash
# chkconfig: 2345 55 25
# description: bt.cn Syssafe

### BEGIN INIT INFO
# Provides:          bt_syssafe
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts bt_syssafe
# Description:       starts the bt_syssafe
### END INIT INFO

panel_path=/www/server/panel/plugin/syssafe
cd $panel_path
panel_start()
{        
        isStart=`ps aux |grep syssafe_main|grep -v grep|grep -v '/www'|awk '{print $2}'`
        if [ "$isStart" == '' ];then
                echo -e "Starting Bt-Syssafe service... \c"
                nohup python syssafe_main.py > $panel_path/service.log 2>&1 &
                sleep 0.5
                isStart=`ps aux |grep syssafe_main|grep -v grep|grep -v '/www'|awk '{print $2}'`
                if [ "$isStart" == '' ];then
                        echo -e "\033[31mfailed\033[0m"
                        echo '------------------------------------------------------'
                        cat $panel_path/service.log
                        echo '------------------------------------------------------'
                        echo -e "\033[31mError: Bt-Syssafe service startup failed.\033[0m"
                        return;
                fi
                echo -e "\033[32mdone\033[0m"
        else
                echo "Starting  Bt-Syssafe service (pid $isStart) already running"
        fi
}

panel_stop()
{
		echo -e "Stopping Bt-Syssafe service... \c";
        pids=`ps aux |grep syssafe_main|grep -v grep|awk '{print $2}'`
        arr=($pids)

        for p in ${arr[@]}
        do
                kill -9 $p
        done
        echo -e "\033[32mdone\033[0m"
}

panel_status()
{
        isStart=`ps aux |grep syssafe_main|grep -v grep|grep -v '/www'|awk '{print $2}'`
        if [ "$isStart" != '' ];then
                echo -e "\033[32mBt-Syssafe service (pid $isStart) already running\033[0m"
        else
                echo -e "\033[31mBt-Syssafe service not running\033[0m"
        fi
}

case "$1" in
        'start')
                panel_start
                ;;
        'stop')
                panel_stop
                ;;
        'restart')
                panel_stop
                sleep 0.2
                panel_start
                ;;
        'status')
                panel_status
                ;;
        *)
                echo "Usage: /etc/init.d/bt_syssafe {start|stop|restart}"
        ;;
esac