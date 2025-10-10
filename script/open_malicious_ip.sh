#!/bin/bash

configure_logging() {
    sudo tee /etc/rsyslog.d/ip-daily-log.conf <<EOF
:msg, contains, "DAILY-IP: " -/var/log/IP-DAILY-LOG.log
& stop
EOF

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
    sudo systemctl restart rsyslog
}


sudo iptables -C IN_BT_log -j IN_BT_log_DAILY > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "规则 'iptables -I IN_BT_log -j IN_BT_log_DAILY' 已经存在 Exiting..."
    exit 0
else
    echo "添加规则..."
    sudo iptables -N IN_BT_log_DAILY
    sudo iptables -I IN_BT_log -j IN_BT_log_DAILY
    sudo iptables -A IN_BT_log_DAILY -m recent --name DAILY_IPS --rcheck --seconds 86400 -j RETURN
    sudo iptables -A IN_BT_log_DAILY -m recent --name DAILY_IPS --set -j LOG --log-prefix "DAILY-IP: " --log-level 4

    ipset create in_bt_malicious_ipset hash:ip maxelem 1000000 timeout 0;
    iptables -A IN_BT_ip -m set --match-set in_bt_malicious_ipset src -j DROP
    systemctl reload BT-FirewallServices
    configure_logging
    echo "规则添加完成..."
fi