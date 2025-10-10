#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

echo "==================================================="
echo "正在执行修复面板脚本，将会将面板升级至最新版..........."

if [ -f "/www/server/panel/script/reload_check.py" ];then
	echo "==================================================="
	echo "执行节点选择脚本，选择最优官网路线"
	btpython /www/server/panel/script/reload_check.py repair
fi

if [ -f "/www/server/panel/data/down_url.pl" ];then
	D_NODE_URL=$(cat /www/server/panel/data/down_url.pl|grep bt.cn)
fi

if [ -z "${D_NODE_URL}" ];then
	D_NODE_URL="download.bt.cn"
fi

wget --no-check-certificate -O update.sh http://${D_NODE_URL}/install/update6.sh -T 12 -t 2 
bash update.sh
sleep 3
echo "REPIAR DONE"
