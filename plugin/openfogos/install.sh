#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH 

download_url=https://download.openfogos.com/linux/bt
openfogos_url=https://download.openfogos.com/linux/


install_path=/www/server/panel/plugin/openfogos

Install()
{
    chmod 700 $install_path/openfog
    $install_path/openfog --platform=PEAR_2200_X64_LINUX
    echo '================================================'
    echo '安装完成'
}

Uninstall() 
{
    docker rm -f openfog
    rm -rf $install_path
}

if [ "${1}" == 'install' ];then
        Install
elif [ "${1}" == 'uninstall' ];then
        Uninstall
else
        echo 'Error!';
fi