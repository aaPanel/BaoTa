#!/bin/bash

# 检测包管理器是否为yum或apt
if command -v yum >/dev/null 2>&1; then
    PACKAGE_MANAGER="yum"
    CRON_PACKAGE="cronie"
elif command -v apt-get >/dev/null 2>&1; then
    PACKAGE_MANAGER="apt"
    CRON_PACKAGE="cron"
else
    echo "不支持的包管理器。"
    exit 1
fi

# 检查是否已安装cron
if command -v crontab >/dev/null 2>&1; then
    echo "已安装Cron，正在卸载..."
    if [ "$PACKAGE_MANAGER" == "yum" ]; then
         yum remove -y "$CRON_PACKAGE"
    elif [ "$PACKAGE_MANAGER" == "apt" ]; then
         apt-get remove -y "$CRON_PACKAGE"
    fi
else
    echo "Cron未安装。"
fi

# 安装cron
echo "正在安装Cron..."
if [ "$PACKAGE_MANAGER" == "yum" ]; then
     yum install -y "$CRON_PACKAGE"
elif [ "$PACKAGE_MANAGER" == "apt" ]; then
     apt-get update &&  apt-get install -y "$CRON_PACKAGE"
fi

echo "Cron安装完毕。"

# 启动cron服务
echo "正在启动Cron服务..."
if [ "$PACKAGE_MANAGER" == "yum" ]; then
     systemctl start crond.service
     systemctl enable crond.service
elif [ "$PACKAGE_MANAGER" == "apt" ]; then
     systemctl start cron
     systemctl enable cron
fi

echo "Cron服务启动完毕。"
echo "successful"
