#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

#配置插件下载地址和安装目录
download_url=http://wy73.51dns.cn/dnsext
install_path=/www/server/panel/plugin/dnsext

#安装
Install()
{
    
    echo '正在安装...'
    #==================================================================
    #打包插件目录上传的情况下
    #依赖安装开始


    #依赖安装结束
    #==================================================================

    #==================================================================
    #使用命令行安装的情况下，如果使用面板导入的，请删除以下代码
    
    #创建插件目录
    mkdir -p $install_path

    # #开始下载文件
    # wget -O $install_path/dnsext_main.py  $download_url/dnsext_main.py
    # wget -O $install_path/index.html $download_url/index.html
    # wget -O $install_path/info.json $download_url/info.json
    # wget -O $install_path/icon.png $download_url/icon.png
    # wget -O $install_path/install.sh $download_url/install.sh
    #文件下载结束
    #==================================================================
    echo '================================================'
    echo '安装完成'
}

#卸载
Uninstall()
{
    rm -rf $install_path
}

#操作判断
if [ "${1}" == 'install' ];then
    Install
elif [ "${1}" == 'uninstall' ];then
    Uninstall
else
    echo 'Error!';
fi
