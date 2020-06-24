#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
nodes=(http://dg2.bt.cn http://dg1.bt.cn http://123.129.198.197 http://103.224.251.67 http://125.88.182.172:5880 http://45.76.53.20 http://119.188.210.21:5880 http://120.206.184.160 http://113.107.111.78 http://128.1.164.196 http://183.235.223.101:3389);
tmp_file1=/dev/shm/net_test1.pl
tmp_file2=/dev/shm/net_test2.pl
if [ -f $tmp_file1 ];then
    rm -f $tmp_file1
fi
if [ -f $tmp_file2 ];then
    rm -f $tmp_file2
fi
touch $tmp_file1
touch $tmp_file2
for node in ${nodes[@]};
do
	NODE_CHECK=$(curl --connect-timeout 3 -m 3 2>/dev/null -w "%{http_code} %{time_total}" ${node}/net_test|xargs)
    RES=$(echo ${NODE_CHECK}|awk '{print $1}')
 	NODE_STATUS=$(echo ${NODE_CHECK}|awk '{print $2}')
 	TIME_TOTAL=$(echo ${NODE_CHECK}|awk '{print $3 * 1000 - 500 }'|cut -d '.' -f 1)
 	if [ "${NODE_STATUS}" == "200" ];then
        if [ $TIME_TOTAL -lt 100 ];then
            if [ "${RES}" -ge "1500" ];then
                echo "$RES $node" >> $tmp_file1
            fi
        else
            if [ "${RES}" -ge "1000" ];then
                echo "$TIME_TOTAL $node" >> $tmp_file2
            fi
        fi

        i=$(($i+1))
        if [ $TIME_TOTAL -lt 100 ];then
            if [ "${RES}" -ge "3000" ];then
            break;
            fi
        fi
 		
 	fi
done

NODE_URL=$(cat $tmp_file1|sort -r -g -t " " -k 1|head -n 1|awk '{print $2}')
if [ "$NODE_URL" = "" ];then
    NODE_URL=$(cat $tmp_file2|sort -g -t " " -k 1|head -n 1|awk '{print $2}')
    if [ "$NODE_URL" = "" ];then
	    NODE_URL='http://download.bt.cn';
    fi
fi

rm -f $tmp_file1
rm -f $tmp_file2
echo $NODE_URL
