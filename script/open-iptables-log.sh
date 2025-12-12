#!/bin/bash

# 判断防火墙类型
if [ -x /sbin/ufw ]; then
    FIREWALL_TYPE="ufw"
elif [ -x /usr/sbin/firewalld ]; then
    FIREWALL_TYPE="firewalld"
else
    echo "不支持的防火墙类型"
    exit 1
fi

# 通用日志配置函数
configure_logging() {
    # 配置rsyslog
    sudo tee /etc/rsyslog.d/ip-daily-log.conf <<EOF
:msg, contains, "DAILY-IP: " -/var/log/IP-DAILY-LOG.log
& stop
EOF

# IP-DAILY-LOG 配置（轻量日志）
sudo tee /etc/logrotate.d/ip-daily-log <<EOF
/var/log/IP-DAILY-LOG.log {
    daily
    rotate 3            # 仅保留3天历史
    missingok
    nocompress          # 无需压缩
    notifempty
    sharedscripts
    postrotate
        systemctl reload rsyslog >/dev/null 2>&1
    endscript
}
EOF


##########################防火墙全量日志##############################
    sudo tee /etc/rsyslog.d/firewall-access-log.conf <<EOF
:msg, contains, "FIREWALL-ACCESS: " -/var/log/FIREWALL-ACCESS-LOG.log
& stop
EOF

sudo tee /etc/logrotate.d/firewall-access-log <<EOF
/var/log/FIREWALL-ACCESS-LOG.log {
    daily
    rotate 30           # 保留30天历史
    missingok
    compress            # 启用gzip压缩
    delaycompress       # 延迟压缩前一个日志
    notifempty
    sharedscripts
    postrotate
        systemctl reload rsyslog >/dev/null 2>&1
    endscript
}
EOF
##########################防火墙全量日志##############################

    # 重启服务
    sudo systemctl restart rsyslog
}

case $FIREWALL_TYPE in
    "ufw")
        echo "检测到UFW防火墙，配置iptables规则..."
        sudo iptables -N IP-DAILY-LOG
        sudo iptables -I INPUT 1 -m conntrack --ctstate NEW -j LOG --log-prefix "FIREWALL-ACCESS: " --log-level 4
        sudo iptables -I INPUT 2 -j IP-DAILY-LOG
        sudo iptables -A IP-DAILY-LOG -m recent --name DAILY_IPS --rcheck --seconds 86400 -j RETURN
        sudo iptables -A IP-DAILY-LOG -m recent --name DAILY_IPS --set -j LOG --log-prefix "DAILY-IP: " --log-level 4
        sudo iptables -A IP-DAILY-LOG -j RETURN

        configure_logging
        ;;
    "firewalld")
        echo "检测到Firewalld，配置direct规则..."

      sudo firewall-cmd --permanent --direct --add-chain ipv4 filter IP-DAILY-LOG;
      sudo firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 1 -m conntrack --ctstate NEW -j LOG --log-prefix 'FIREWALL-ACCESS: ' --log-level 4;
      sudo firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 2 -j IP-DAILY-LOG;
      sudo firewall-cmd --permanent --direct --add-rule ipv4 filter IP-DAILY-LOG 0 -m recent --name DAILY_IPS --rcheck --seconds 86400 -j RETURN;
      sudo firewall-cmd --permanent --direct --add-rule ipv4 filter IP-DAILY-LOG 1 -m recent --name DAILY_IPS --set -j LOG --log-prefix 'DAILY-IP: ' --log-level 4;
      sudo firewall-cmd --permanent --direct --add-rule ipv4 filter IP-DAILY-LOG 2 -j RETURN;
        
        # 重载配置
        sudo firewall-cmd --reload
        configure_logging
        ;;
esac