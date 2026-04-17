#!/bin/bash
#===============================================================================
# 宝塔面板更新预准备脚本
# 功能：在面板更新时，提前准备，避免面板更新失败
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
    local common_file="$PANEL_PATH/class/common.py"
    if [ ! -f "$common_file" ]; then
        echo ""  # 文件不存在时返回空字符串
        return 1
    fi
    # 形如：g.version = '11.2.0'
    local version_str=$(grep -E '^\s+g.version\s*=\s*.*$' "$PANEL_PATH/class/common.py" | cut -d "=" -f2 )
    # 形如：'11.2.0'
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
        1|True|true)   # 稳定版
            IS_STABLE=true
            ;;
        0|False|false)    # 非稳定版
            IS_STABLE=false
            ;;
        *)
            IS_STABLE=false
            ;;
    esac
    case "$3" in
        prepare)
            OPPORTUNITY="prepare"
            ;;
        after)
            OPPORTUNITY="after"
            ;;
        *)
            OPPORTUNITY="prepare"
            ;;
    esac
}

# 默认处理，什么都不做
function nothing_do() {
    local version=$1
    # 输出成功信息
    success "已完成[BT-Panel-$version]处理"
}

function replace_bt_command() {
    local init_path="${PANEL_PATH}/init.sh"
    if [ -f "$init_path" ]; then
        \cp -a "$init_path" /etc/init.d/bt
        chmod +x /etc/init.d/bt
    else
        echo "Error: $init_path 文件不存在"
        exit 1
    fi
}

function prepare_main() {
    echo "开始处理预更新..."
    local now_version=$(get_now_version)
    if [ $? -eq 0 ]; then
        echo "当前版本：$now_version, 目标版本：$UPDATE_VERSION"
    else
        echo "获取当前版本失败"
        exit 1
    fi

    case "$UPDATE_VER_MAJOR.$UPDATE_VER_MINOR.$UPDATE_VER_MICRO" in
    11.3.*)
        nothing_do $UPDATE_VERSION
        ;;
    11.5.*)
        install_package_for_11_5
        success "已完成[BT-Panel-$UPDATE_VERSION]处理"
        ;;
    11.6.*)
        install_package_for_11_5
        success "已完成[BT-Panel-$UPDATE_VERSION]处理"
        ;;
    * )
        nothing_do $UPDATE_VERSION
        ;;
    esac
}

function install_package_for_11_5() {
    pip_bin="/www/server/panel/pyenv/bin/python3 -m pip"
    $pip_bin install asn1crypto==1.5.1 cbor2==5.4.6
    if [ $? -eq 0 ]; then
        echo "安装成功"
    else
        echo "必要库安装失败 ！！！"
        echo "请尝试使用以下命令手动安装 btpip install asn1crypto==1.5.1 cbor2==5.4.6"
        exit 1
    fi
}

function install_after_11_5() {
    chmod +x  /www/server/panel/script/btcli.py
    ln -sf /www/server/panel/script/btcli.py /usr/bin/btcli
}

function after_main() {
    echo "启动预检测..."
    case "$UPDATE_VER_MAJOR.$UPDATE_VER_MINOR.$UPDATE_VER_MICRO" in
    11.3.*)
        replace_bt_command
        success "已完成[BT-Panel-$UPDATE_VERSION]启动检查处理"
        ;;
    11.5.*)
        install_after_11_5
        success "已完成[BT-Panel-$UPDATE_VERSION]启动检查处理"
        ;;
    11.6.*)
        install_after_11_5
        success "已完成[BT-Panel-$UPDATE_VERSION]启动检查处理"
        ;;
    *)
        nothing_do $UPDATE_VERSION
        ;;
    esac
}

# 主函数
function main() {
    if [ "$OPPORTUNITY" = "prepare" ]; then
        prepare_main
    elif [ "$OPPORTUNITY" = "after" ]; then
        after_main
    fi
}

# 主函数入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    parse_arguments $@
    main
fi