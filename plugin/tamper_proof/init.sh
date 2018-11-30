#!/bin/bash
# chkconfig: 2345 55 25
# description: bt.cn tamper proof

### BEGIN INIT INFO
# Provides:          bt_tamper_proof
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts bt_tamper_proof
# Description:       starts the bt_tamper_proof
### END INIT INFO

panel_path=/www/server/panel/plugin/tamper_proof
cd $panel_path
panel_start()
{        
        isStart=`ps aux |grep tamper_proof_service|grep -v grep|awk '{print $2}'`
        if [ "$isStart" == '' ];then
                echo -e "Starting Bt-Tamper proof service... \c"
                nohup python tamper_proof_service.py > $panel_path/service.log 2>&1 &
                sleep 0.5
                isStart=`ps aux |grep tamper_proof_service|grep -v grep|awk '{print $2}'`
                if [ "$isStart" == '' ];then
                        echo -e "\033[31mfailed\033[0m"
                        echo '------------------------------------------------------'
                        cat $panel_path/service.log
                        echo '------------------------------------------------------'
                        echo -e "\033[31mError: Bt-Tamper proof service startup failed.\033[0m"
                        return;
                fi
                echo -e "\033[32mdone\033[0m"
        else
                echo "Starting  Bt-Tamper proof service (pid $isStart) already running"
        fi
}

panel_stop()
{
		echo -e "Stopping Bt-Tamper proof service... \c";
        pids=`ps aux |grep tamper_proof_service|grep -v grep|awk '{print $2}'`
        arr=($pids)

        for p in ${arr[@]}
        do
                kill -9 $p
        done
        echo -e "\033[32mdone\033[0m"
}

panel_status()
{
        isStart=`ps aux |grep tamper_proof_service|grep -v grep|awk '{print $2}'`
        if [ "$isStart" != '' ];then
                echo -e "\033[32mBt-Tamper proof service (pid $isStart) already running\033[0m"
        else
                echo -e "\033[31mBt-Tamper proof service not running\033[0m"
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
                echo "Usage: /etc/init.d/bt_tamper_proof {start|stop|restart}"
        ;;
esac