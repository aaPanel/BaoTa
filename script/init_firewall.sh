#!/bin/bash
create_chain() {
    # 创建iptables链
    # params：表名 链名
    local table=$1
    local chain=$2
    if ! iptables -t "$table" -n -L "$chain" > /dev/null 2>&1; then
        iptables -t "$table" -N "$chain"
        echo "Created chain $chain in table $table"
    else
        echo "Chain $chain already exists in table $table"
    fi
}

insert_input_output_rules() {
    # 在指定的表的链中插入子链
    # params："表名:目标链名:需要插入的链"
    local rules=("$@")
    for rule in "${rules[@]}"; do
        IFS=':' read -r table chain target <<< "$rule"
        if ! iptables -t "$table" -C "$chain" -j "$target" > /dev/null 2>&1; then
            iptables -t "$table" -A "$chain" -j "$target"
            echo "Inserted $target to $chain in table $table"
        else
            echo "$target already in $chain in table $table"
        fi
    done
}

add_jump_rules() {
    # 在指定的表的链中添加跳转规则
    # params：表名 目标链名 需要跳转的链
    local table=$1
    local target_chain=$2
    shift 2
    local chains=("$@")
    for chain in "${chains[@]}"; do
        if ! iptables -t "$table" -C "$target_chain" -j "$chain" > /dev/null 2>&1; then
            iptables -t "$table" -A "$target_chain" -j "$chain"
            echo "Added $chain to $target_chain in table $table"
        else
            echo "$chain already in $target_chain in table $table"
        fi
    done
}

create_ipset() {
    local ipset_name=$1
    if ! ipset list "$ipset_name" > /dev/null 2>&1; then
        ipset create "$ipset_name" hash:net maxelem 100000 timeout 0
        echo "Created ipset $ipset_name"
    else
        echo "ipset $ipset_name already exists"
    fi
}

add_ipset_rules() {
    local rules=("$@")
    for rule in "${rules[@]}"; do
        IFS=':' read -r chain action direction ipset_name <<< "$rule"
        if ! iptables -C "$chain" -m set --match-set "$ipset_name" "$direction" -j "$action" > /dev/null 2>&1; then
            iptables -I "$chain" 1 -m set --match-set "$ipset_name" "$direction" -j "$action"
            echo "Added $action rule for $ipset_name ($direction) in $chain"
        else
            echo "$action rule for $ipset_name ($direction) already in $chain"
        fi
    done
}

# 函数：创建systemd服务
create_systemd_service() {
    local exec_path="/www/server/panel/pyenv/bin/python3 /www/server/panel/script/BT-FirewallServices.py"
    local service_file="/etc/systemd/system/BT-FirewallServices.service"
    if [ ! -f "$service_file" ]; then
        /www/server/panel/pyenv/bin/python3 -c "import os,sys; os.chdir('/www/server/panel/'); sys.path.insert(0, 'class/'); sys.path.insert(0, '/www/server/panel/'); import public; public.stop_syssafe();"
        cat << EOF > "$service_file"
[Unit]
Description=Firewall and System Event Listener Service
After=network.target

[Service]
ExecStart=$exec_path start
ExecReload=$exec_path reload
ExecStop=$exec_path stop
User=root
Type=simple

[Install]
WantedBy=multi-user.target
EOF
        systemctl daemon-reload
        systemctl enable BT-FirewallServices.service
        ${exec_path} save
        systemctl start BT-FirewallServices.service
        echo "Systemd service created and started"
        /www/server/panel/pyenv/bin/python3 -c "import os,sys; os.chdir('/www/server/panel/'); sys.path.insert(0, 'class/'); sys.path.insert(0, '/www/server/panel/'); import public; public.start_syssafe();"
    else
        echo "Systemd service already exists"
    fi
}

main() {
    # 所有需要创建接管的子链
  local chains=(
        "filter:IN_BT"
        "filter:IN_BT_log"
        "filter:IN_BT_user_ip"
        "filter:IN_BT_ip"
        "filter:IN_BT_user_port"
        "filter:OUT_BT"
        "filter:OUT_BT_user_ip"
        "filter:OUT_BT_user_port"
        "filter:IN_BT_Country"
        "nat:FORWARD_BT"
    )
    for chain in "${chains[@]}"; do
        IFS=':' read -r table chain_name <<< "$chain"
        create_chain "$table" "$chain_name"
    done

    # 插入接管的子链
    local rules=(
        "filter:INPUT:IN_BT"
        "filter:IN_BT:IN_BT_log"
        "filter:IN_BT:IN_BT_user_ip"
        "filter:IN_BT:IN_BT_ip"
        "filter:IN_BT:IN_BT_user_port"
        "filter:IN_BT_ip:IN_BT_Country"
        "filter:OUTPUT:OUT_BT"
        "filter:OUT_BT:OUT_BT_user_ip"
        "filter:OUT_BT:OUT_BT_user_port"
        "nat:PREROUTING:FORWARD_BT"
    )
    insert_input_output_rules "${rules[@]}"

    # ipset集合
    local ipsets=(
        "in_bt_user_accept_ipset"
        "in_bt_user_drop_ipset"
        "out_bt_user_accept_ipset"
        "out_bt_user_drop_ipset"
    )
    for ipset_name in "${ipsets[@]}"; do
        create_ipset "$ipset_name"
    done

    local ipset_rules=(
        "IN_BT_user_ip:ACCEPT:src:in_bt_user_accept_ipset"
        "IN_BT_user_ip:DROP:src:in_bt_user_drop_ipset"
        "OUT_BT_user_ip:ACCEPT:dst:out_bt_user_accept_ipset"
        "OUT_BT_user_ip:DROP:dst:out_bt_user_drop_ipset"
    )
    add_ipset_rules "${ipset_rules[@]}"
    create_systemd_service
    systemctl reload BT-FirewallServices
    echo "防火墙初始化完毕..."
}

if [ $# -eq 1 ]; then
    if [ "$1" = "clean" ]; then
        iptables -F IN_BT
        iptables -F OUT_BT
    fi
else
  main
fi