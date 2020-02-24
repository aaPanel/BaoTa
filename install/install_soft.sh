#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
pyenv_bin=/www/server/panel/pyenv/bin
rep_path=${pyenv_bin}:$PATH

mtype=$1
actionType=$2
name=$3
version=$4
. /www/server/panel/install/public.sh
serverUrl=$NODE_URL/install

if [ ! -f 'lib.sh' ];then
	wget -O lib.sh $serverUrl/$mtype/lib.sh
fi

libNull=`cat lib.sh`
if [ "$libNull" == '' ];then
	wget -O lib.sh $serverUrl/$mtype/lib.sh
fi

if [ -d "$pyenv_bin" ];then
	PATH=$rep_path
fi

wget -O $name.sh $serverUrl/$mtype/${name}.sh
if [ "$actionType" == 'install' ];then
	sed -i "s#PATH=.*#PATH=$PATH#" lib.sh
	bash lib.sh
fi
sed -i "s#PATH=.*#PATH=$PATH#" ${name}.sh
bash ${name}.sh $actionType $version
