#!/bin/bash
#===============================================================================
# 宝塔面板更新预准备脚本
# 功能：在面板更新时，提前准备，避免面板更新失败
# 改进：自动扫描并执行所有前置函数，支持动态发现
# 说明：接收两个参数：1.更新的面板版本号 2.更新的版本是否为稳定版 3.执行时机(prepare, after)
#        prepare: 在下载面板文件之前就运行的内容
#        after: 在替换文件之后，运行重启之前执行的内容
# 支持：CentOS/RHEL、Ubuntu、Debian系统
#===============================================================================

UPDATE_VERSION=""  # 版本号, 形如： 11.2.3
UPDATE_VER_MAJOR=""  # 主版本号 -> 11
UPDATE_VER_MINOR=""  # 次版本号 -> 2
UPDATE_VER_MICRO=""  # 小版本号 -> 3
IS_STABLE=false  # 默认不是稳定版而是正式版本
OPPORTUNITY="prepare"

PANEL_PATH="/www/server/panel"
PANEL_UPDATING_VERSION_FILE="${PANEL_PATH}/updating_version.pl"

# 定义版本控制顺序（按时间顺序排列，新版本放后面）
# 会自动扫描所有 prepare_X_X 和 after_X_X 格式的函数
ALL_VERSIONS=("11.3" "11.5" "11.6")

# 输出成功信息, 必须输出 "BT-Panel Update Ready" 才证明预处理成功
function success() {
    local message=$1
    if [ -n "$message" ]; then
        echo "$message"
    fi
    echo "BT-Panel Update Ready"
}

# 获取当前版本号
function get_now_version() {
    if [ -f "$PANEL_UPDATING_VERSION_FILE" ]; then
        local version=$(cat "$PANEL_UPDATING_VERSION_FILE")
        echo "$version"
        return 0
    fi
    local common_file="$PANEL_PATH/class/common.py"
    if [ ! -f "$common_file" ]; then
        echo ""
        return 1
    fi
    local version_str=$(grep -E '^\s+g.version\s*=\s*.*$' "$PANEL_PATH/class/common.py" | cut -d "=" -f2 )
    local version=$(echo "$version_str" | sed -n "s/.*['\"]\(.*\)['\"].*/\1/p" )
    echo "$version"
    return 0
}

# 解析参数
function parse_arguments() {
    if [ -z "$1" ]; then
        echo "Error: 请指定接下来的更新版本号"
        exit 1
    fi
    if echo "$1" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
        :
    else
        echo "Error: 请指定正确的版本号"
        exit 1
    fi
    UPDATE_VERSION=$1
    UPDATE_VER_MAJOR=$(echo $UPDATE_VERSION | cut -d. -f1)
    UPDATE_VER_MINOR=$(echo $UPDATE_VERSION | cut -d. -f2)
    UPDATE_VER_MICRO=$(echo $UPDATE_VERSION | cut -d. -f3)
    case "$2" in
        1|True|true)   IS_STABLE=true ;;
        0|False|false) IS_STABLE=false ;;
        *)             IS_STABLE=false ;;
    esac
    case "$3" in
        prepare) OPPORTUNITY="prepare" ;;
        after)   OPPORTUNITY="after" ;;
        *)       OPPORTUNITY="prepare" ;;
    esac
}

# 版本号转数字: 11.6.0 -> 110600
function version_to_int() {
    local ver=$1
    local major=$(echo $ver | cut -d. -f1)
    local minor=$(echo $ver | cut -d. -f2)
    local micro=$(echo $ver | cut -d. -f3)
    minor=${minor:-0}
    micro=${micro:-0}
    printf "%d%02d%02d" $major $minor $micro
}

# 判断当前版本是否小于目标版本（需要执行前置操作）
function need_execute() {
    local current_ver=$1
    local target_ver=$2
    local current_int=$(version_to_int "$current_ver")
    local target_int=$(version_to_int "$target_ver")
    [ $current_int -lt $target_int ]
}

# 判断目标版本是否在升级范围内（即目标版本 >= 指定版本）
# 用于限制只执行到目标版本为止的函数
function is_in_upgrade_range() {
    local target_ver=$1  # 要检查的版本（如11.3）
    local update_ver=$2  # 升级目标版本（如11.6）
    local target_int=$(version_to_int "$target_ver")
    local update_int=$(version_to_int "$update_ver")
    [ $target_int -le $update_int ]
}

# 版本号转函数名：11.5 -> 11_5
function ver_to_func_name() {
    echo "$1" | sed 's/\./_/g'
}

# 检查函数是否存在
function function_exists() {
    declare -f "$1" > /dev/null 2>&1
}

#===============================================================================
# PREPARE 阶段函数（按版本顺序）
#===============================================================================

# 11.5 版本 prepare
function prepare_11_5() {
    echo "[prepare 11.5] 安装必要Python包"
    local pip_bin="/www/server/panel/pyenv/bin/python3 -m pip"
    $pip_bin install asn1crypto==1.5.1 cbor2==5.4.6 2>&1
    if [ $? -eq 0 ]; then
        echo "[prepare 11.5] 安装成功"
        return 0
    else
        echo "[prepare 11.5] 安装失败，请手动执行: btpip install asn1crypto==1.5.1 cbor2==5.4.6"
        return 1
    fi
}


#===============================================================================
# AFTER 阶段函数（按版本顺序）
#===============================================================================

# 11.3 版本 after
function after_11_3() {
    echo "[after 11.3] 替换bt命令"
    local init_path="${PANEL_PATH}/init.sh"
    if [ -f "$init_path" ]; then
        \cp -a "$init_path" /etc/init.d/bt
        chmod +x /etc/init.d/bt
        echo "[after 11.3] 替换成功"
        return 0
    else
        echo "Error: $init_path 文件不存在"
        return 1
    fi
}

# 11.5 版本 after
function after_11_5() {
    echo "[after 11.5] 配置btcli"
    chmod +x /www/server/panel/script/btcli.py
    ln -sf /www/server/panel/script/btcli.py /usr/bin/btcli
    echo "[after 11.5] 配置成功"
    return 0
}

#===============================================================================
# 自动执行引擎（自动扫描函数）
#===============================================================================

# PREPARE 阶段自动执行
function auto_run_prepare() {
    rm -f "$PANEL_UPDATING_VERSION_FILE"
    local now_version=$(get_now_version)
    echo "$now_version" > "$PANEL_UPDATING_VERSION_FILE"
    if [ $? -ne 0 ] || [ -z "$now_version" ]; then
        echo "Error: 获取当前版本失败"
        exit 1
    fi

    echo "PREPARE 阶段"
    echo "当前版本: $now_version -> 目标版本: $UPDATE_VERSION"

    local executed=false

    # 按顺序遍历版本列表
    for ver in "${ALL_VERSIONS[@]}"; do
        # 先判断目标版本是否在升级范围内（UPDATE_VERSION >= ver）
        if ! is_in_upgrade_range "$ver" "$UPDATE_VERSION"; then
#            echo "--- 跳过 $ver (目标版本 $UPDATE_VERSION < $ver)"
            continue
        fi

        # 再判断当前版本是否小于该版本（需要执行前置操作）
        if ! need_execute "$now_version" "$ver.0"; then
#            echo "--- 跳过 $ver (当前版本 $now_version >= $ver)"
            continue
        fi

        local func_name="prepare_$(ver_to_func_name $ver)"

        # 检查函数是否存在
        if function_exists "$func_name"; then
            echo ">>> 执行 $func_name"
            $func_name
            if [ $? -ne 0 ]; then
                echo "Error: $func_name 执行失败"
                exit 1
            fi
            echo "<<< $func_name 完成"
            executed=true
        else
            echo "--- 跳过 $ver (函数 $func_name 不存在)"
        fi
    done

    if [ "$executed" = true ]; then
        success "PREPARE 阶段完成"
    else
        success "无需 PREPARE 处理"
    fi
}

# AFTER 阶段自动执行
function auto_run_after() {
    local now_version=$(get_now_version)
    rm -f "$PANEL_UPDATING_VERSION_FILE"
    if [ $? -ne 0 ] || [ -z "$now_version" ]; then
        echo "Error: 获取当前版本失败"
        exit 1
    fi

    echo "AFTER 阶段"
    echo "当前版本: $now_version -> 目标版本: $UPDATE_VERSION"

    local executed=false

    # 按顺序遍历版本列表
    for ver in "${ALL_VERSIONS[@]}"; do
        # 先判断目标版本是否在升级范围内（UPDATE_VERSION >= ver）
        if ! is_in_upgrade_range "$ver" "$UPDATE_VERSION"; then
#            echo "--- 跳过 $ver (目标版本 $UPDATE_VERSION < $ver)"
            continue
        fi

        # 再判断当前版本是否小于该版本（需要执行后续操作）
        if ! need_execute "$now_version" "$ver.0"; then
#            echo "--- 跳过 $ver (当前版本 $now_version >= $ver)"
            continue
        fi

        local func_name="after_$(ver_to_func_name $ver)"

        # 检查函数是否存在
        if function_exists "$func_name"; then
            echo ">>> 执行 $func_name"
            $func_name
            if [ $? -ne 0 ]; then
                echo "Error: $func_name 执行失败"
                exit 1
            fi
            echo "<<< $func_name 完成"
            executed=true
        else
            echo "--- 跳过 $ver (函数 $func_name 不存在)"
        fi
    done

    if [ "$executed" = true ]; then
        success "AFTER 阶段完成"
    else
        success "无需 AFTER 处理"
    fi
}

# 主函数
function main() {
    if [ "$OPPORTUNITY" = "prepare" ]; then
        auto_run_prepare
    elif [ "$OPPORTUNITY" = "after" ]; then
        auto_run_after
    fi
}

# 主函数入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    parse_arguments $@
    main
fi