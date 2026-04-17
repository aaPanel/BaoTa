

#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
LANG=en_US.UTF-8

setup_path=/www
version=$(curl -Ss --connect-timeout 5 -m 2 http://www.bt.cn/api/panel/get_version)
if [ "$version" = '' ]; then
    version='8.0.1'
fi
armCheck=$(uname -m | grep arm)
if [ "${armCheck}" ]; then
    version='7.7.0'
fi

if [ "$1" ]; then
    version=$1
fi
downloadUrl="http://192.168.1.19"
echo "===================================="
echo "正在打包git-$1分支面板文件"
echo "===================================="
LINUX_PANEL=$(curl "http://192.168.1.19/git.php?v=$1")

wget -O /tmp/panel.zip ${downloadUrl}/${LINUX_PANEL} -T 10

unzip -o /tmp/panel.zip -d $setup_path/server/ >/dev/null
rm -f /tmp/panel.zip
echo '3' >/www/server/panel/data/db/update

rm -f /www/server/panel/*.pyc
rm -f /www/server/panel/class/*.pyc

chattr -i /etc/init.d/bt
chmod +x /etc/init.d/bt
echo "====================================="
rm -f /dev/shm/bt_sql_tips.pl
kill $(ps aux | grep -E "task.pyc|main.py" | grep -v grep | awk '{print $2}')
/etc/init.d/bt start
echo 'True' >/www/server/panel/data/restart.pl
pkill -9 gunicorn &
echo "已成功升级到${LINUX_PANEL}"
echo "========================================================================="
echo "可用下面命令在外网进行升级！"
echo "wget -O git_ol.sh http://downooad-test.bt.cn/git_ol.sh;bash git_ol.sh ${LINUX_PANEL}"
