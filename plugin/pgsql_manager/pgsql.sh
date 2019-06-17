#!/bin/bash
#pgsql启动停止服务脚本
data_directory=`head -1 /www/server/pgsql/data_directory`
case $1 in
start)
su - postgres -c "/www/server/pgsql/bin/postgres -D $data_directory >>/www/server/pgsql/logs/pgsql.log 2>&1 &"
;;
stop)
kill -INT `head -1 $data_directory/postmaster.pid`
;;
restart)
su - postgres -c "/www/server/pgsql/bin/pg_ctl -D $data_directory stop;/www/server/pgsql/bin/postgres -D $data_directory >>/www/server/pgsql/logs/pgsql.log 2>&1 &"
;;
reload)
su - postgres -c "/www/server/pgsql/bin/pg_ctl -D $data_directory reload"
 ;;
*)
echo "usage start|stop|reload"
exit 1
;;

esac
