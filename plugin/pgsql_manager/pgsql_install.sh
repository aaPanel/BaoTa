#!/bin/bash
#pgsql安装脚本
install_dir=/www/server/pgsql
pgsql_version=$1
down_url=$2
#进入软件的制定安装目录
echo "进入目录/usr/local，下载pgsql文件"
cd /usr/local
#判断是否有postgre版本的安装包
if [ -d postgresql* ]
then
        rm -rf /usr/local/postgresql*
        echo "安装包删除成功"
fi

#开始下载pgsql版本10.5并解压
if [ ! -d /usr/local/src ]
then
        mkdir /usr/local/src
fi

cd /usr/local/src
wget $down_url
if [ $? == 0 ]
then
tar -zxf $pgsql_version -C /usr/local/
fi

echo "pgsql文件解压成功"
#判断用户是否存在
user=postgres
group=postgres

#create group if not exists
egrep "^$group" /etc/group >& /dev/null
if [ $? -ne 0 ]
then
    groupadd $group
fi

#create user if not exists
egrep "^$user" /etc/passwd >& /dev/null
if [ $? -ne 0 ]
then
    useradd -g $group $user
fi

echo "重命名postgresql并且进入安装目录"
mv /usr/local/post* /usr/local/pgsql
cd /usr/local/pgsql
#-------------------------------安装pgsql------------------------------------
echo "安装一些库文件"
yum install -y zlib zlib-devel >& /del/null
echo "开始执行configure步骤"
./configure --prefix=$install_dir --without-readline
if [ $? == 0 ]
then
        echo "configure配置通过，开始进行make编译"
        make
        if [ $? == 0 ]
        then
                echo "make编译通过，开始进行make install安装步骤"
                make install
                if [ $? != 0 ];then
                        echo "make install安装失败"
                fi
                echo "安装成功"
        else
                echo "make编译失败，检查错误。"
        fi
else
        echo "configure检查配置失败，请查看错误进行安装库文件"
fi
echo "开始进行pgsql的配置"
echo "给pgsql创建data目录"
mkdir -p ${install_dir}/data
mkdir -p ${install_dir}/logs
echo "修改用户组"
chown -R postgres:postgres ${install_dir}
chmod -R 700   ${install_dir}/data

echo "/www/server/pgsql/data" >/www/server/pgsql/data_directory
echo "添加环境变量,进入postgres用户的家目录"
cd /home/postgres
if [ -f .bash_profile ] ;then
        /bin/cp .bash_profile .bash_profile.bak
        echo "export PGHOME=${install_dir}" >> .bash_profile
        echo "export PGDATA=${install_dir}/data" >> .bash_profile
        echo "export PATH=${install_dir}/bin:\$PATH " >> .bash_profile
        echo "MANPATH=$PGHOME/share/man:$MANPATH" >> .bash_profile
        echo "LD_LIBRARY_PATH=$PGHOME/lib:$LD_LIBRARY_PATH" >> .bash_profile
fi
alias pg_start='pg_ctl -D $PGDATA -l ${install_dir}/logs/pgsql.log start'
alias ps_stop='pg_ctl -D $PGDATA -l ${install_dir}logs/pgsql.log stop'
echo "切换至postgres用户来初始化数据库"
su - postgres -c "${install_dir}/bin/initdb -D ${install_dir}/data"

echo "启用慢查询SQL语句跟踪"
cat >> ${install_dir}/data/postgresql.conf <<EOF
logging_collector = on
log_destination = 'stderr'
log_directory = '${install_dir}/logs'
log_filename = 'postgresql-%Y-%m-%d.log'
log_statement = all
log_min_duration_statement = 5000
EOF

su - postgres -c "${install_dir}/bin/postgres -D ${install_dir}/data >>${install_dir}/logs/pgsql.log 2>&1 &"
echo "---------------------------------------------------------------------------------------"
echo "---------------------------------------------------------------------------------------"
echo "----------------------------SUCCESS INSTALLATION OF POSTGRESQL-------------------------"


