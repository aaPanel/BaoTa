#!/bin/bash
#===============================================================================
# 宝塔面板Python 3.13环境升级脚本 - 简化版本
# 功能：将宝塔面板Python环境从3.7升级到3.13（仅Python环境升级）
# 支持：CentOS/RHEL、Ubuntu、Debian系统
# 先在临时目录安装，确认无误后再替换原环境
#===============================================================================

PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
LANG=en_US.UTF-8

# 安装路线枚举
ROUTE_SYSTEM_SPECIFIC=1  # 系统特定预编译包
ROUTE_GENERIC=2          # 通用预编译包
ROUTE_COMPILE=3          # 源码编译

# 全局变量定义
PANEL_PATH="/www/server/panel"
PYTHON_PYENV="$PANEL_PATH/pyenv"
PYTHON_PYENV_NEW="$PANEL_PATH/pyenv313"  # 新的临时安装目录
PYTHON_VERSION="3.13.7"
DOWNLOAD_URL="https://download.bt.cn"
FORCE_COMPILE=false  # 是否强制使用源码编译
PIP_REQUIREMENTS_FILE="pip313.txt"  # 更新为pip313.txt
USE_SOFTLINK=false  # 是否使用软链接方式替换环境
PREPARE_ONLY=false
INSTALL_ROUTE=$ROUTE_COMPILE  # 默认安装路线
TAR_PYENV_FLAG=false
HAS_OLD_PANEL=true
ONLY_REPLACE=false

# 颜色定义
RED='\033[1;31;40m'
GREEN='\033[1;32;40m'
YELLOW='\033[1;33;40m'
BLUE='\033[1;34;40m'
NC='\033[0m' # No Color

#===============================================================================
# 工具函数
#===============================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_separator() {
    echo '============================================================='
}

Red_Error(){
    echo '=================================================';
    printf '\033[1;31;40m%b\033[0m\n' "$@";
    GetSysInfo
    exit 1;
}

GetSysInfo(){
    if [ -s "/etc/redhat-release" ];then
        SYS_VERSION=$(cat /etc/redhat-release)
    elif [ -s "/etc/issue" ]; then
        SYS_VERSION=$(cat /etc/issue)
    fi
    SYS_INFO=$(uname -a)
    SYS_BIT=$(getconf LONG_BIT)
    MEM_TOTAL=$(free -m|grep Mem|awk '{print $2}')
    CPU_INFO=$(getconf _NPROCESSORS_ONLN)

    echo -e ${SYS_VERSION}
    echo -e Bit:${SYS_BIT} Mem:${MEM_TOTAL}M Core:${CPU_INFO}
    echo -e ${SYS_INFO}
    echo -e "请截图以上报错信息发帖至论坛www.bt.cn/bbs求助"
}

show_usage() {
    echo "宝塔面板Python 3.13环境升级脚本使用说明："
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项："
    echo "  -c, --compile        强制使用源码编译，跳过预编译包安装"
    echo "  -s, --softlink       使用软链接方式替换环境（默认为直接替换）"
    echo "  -p, --prepare        仅准备环境，不进行升级"
    echo "  --replace            仅替换环境，需要有准备好的环境"
    echo "  --tar                安装成功后，打包当前Python环境，与'-p'冲突"
    eche "  --disable-color      禁用颜色输出"
    echo "  -h, --help           显示此帮助信息"
    echo ""
    echo "示例："
    echo "  $0                   升级Python环境到3.13（优先使用预编译包，直接替换环境）"
    echo "  $0 -c                强制使用源码编译Python 3.13"
    echo "  $0 -s                使用软链接方式替换环境"
    echo ""
    echo "注意：此脚本仅升级Python环境，不更新面板版本"
    echo "      如需兼容Python 3.13，请手动更新面板到11.1版本"
}

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -c|--compile)
                FORCE_COMPILE=true
                shift
                ;;
            -s|--softlink)
                USE_SOFTLINK=true
                shift
                ;;
            -p|--prepare)
                PREPARE_ONLY=true
                shift
                ;;
            --tar)
                TAR_PYENV_FLAG=true
                shift
                ;;
            --replace)
                ONLY_REPLACE=true
                shift
                ;;
            --disable-color)
                NC=""
                RED=""
                GREEN=""
                YELLOW=""
                BLUE=""
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

#===============================================================================
# 系统检查函数
#===============================================================================

check_root_permission() {
    if [ $(whoami) != "root" ]; then
        Red_Error "请使用root权限执行升级脚本！"
    fi
    log_info "Root权限检查通过"
}

check_system_architecture() {
    local is64bit=$(getconf LONG_BIT)
    if [ "${is64bit}" != '64' ]; then
        Red_Error "抱歉, 当前版本不支持32位系统, 请使用64位系统!"
    fi
    log_info "系统架构检查通过：${is64bit}位"
}

check_bt_panel() {
    if [ ! -d "/www/server/panel" ]; then
        log_error "未检测到宝塔面板，请先安装宝塔面板"
        mkdir -p /www/server/panel
        HAS_OLD_PANEL=false
    fi

    if [ ! -d "$PYTHON_PYENV" ]; then
        log_error "未找到现有Python环境目录：$PYTHON_PYENV"
        mkdir -p "$PYTHON_PYENV"
        HAS_OLD_PANEL=false
    fi
    if [ ! -f "/www/server/panel/init.sh" ] || [ ! -d "/www/server/panel/data" ]; then
        HAS_OLD_PANEL=false
    fi
    if [ "$HAS_OLD_PANEL" = true ]; then
        log_info "宝塔面板检查通过"
    fi
}

check_download_tool() {
    if [ ! -f "/usr/bin/curl" ]; then
        if [ "${PM}" = "yum" ]; then
            yum install curl -y
        elif [ "${PM}" = "apt-get" ]; then
            apt-get install curl -y
        fi
    fi
    if [ ! -f "/usr/bin/wget" ]; then
        if [ "${PM}" = "yum" ]; then
            yum install wget -y
        elif [ "${PM}" = "apt-get" ]; then
            apt-get install wget -y
        fi
    fi
    if  [ -f "/usr/bin/curl" ] && [ -f "/usr/bin/wget" ] ; then
        log_info "下载工具检查通过"
        return 0
    else
        Red_Error "请安装curl，wget工具"
    fi
}

# 获取最优下载节点
get_node_url(){
	if [ -f "/www/node.pl" ];then
      DOWNLOAD_URL=$(cat /www/node.pl)
      log_info "Download node: $DOWNLOAD_URL"
      return 0
	fi

	log_info "Selected download node..."
	nodes=(https://dg2.bt.cn https://download.bt.cn https://ctcc1-node.bt.cn https://cmcc1-node.bt.cn https://ctcc2-node.bt.cn https://hk1-node.bt.cn https://na1-node.bt.cn https://jp1-node.bt.cn https://cf1-node.aapanel.com https://download.bt.cn);

  CN_CHECK=$(curl -sS --connect-timeout 10 -m 10 https://api.bt.cn/api/isCN)
  if [ "${CN_CHECK}" == "True" ];then
      nodes=(https://dg2.bt.cn https://download.bt.cn https://ctcc1-node.bt.cn https://cmcc1-node.bt.cn https://ctcc2-node.bt.cn https://hk1-node.bt.cn);
  else
      PING6_CHECK=$(ping6 -c 2 -W 2 download.bt.cn &> /dev/null && echo "yes" || echo "no")
      if [ "${PING6_CHECK}" == "yes" ];then
          nodes=(https://dg2.bt.cn https://download.bt.cn https://cf1-node.aapanel.com);
      else
          nodes=(https://cf1-node.aapanel.com https://download.bt.cn https://na1-node.bt.cn https://jp1-node.bt.cn https://dg2.bt.cn);
      fi
  fi

	tmp_file1=/dev/shm/net_test1.pl
	tmp_file2=/dev/shm/net_test2.pl
	[ -f "${tmp_file1}" ] && rm -f ${tmp_file1}
	[ -f "${tmp_file2}" ] && rm -f ${tmp_file2}
	touch $tmp_file1
	touch $tmp_file2
	for node in ${nodes[@]};
	do
      if [ "${node}" == "https://cf1-node.aapanel.com" ];then
          NODE_CHECK=$(curl --connect-timeout 3 -m 3 2>/dev/null -w "%{http_code} %{time_total}" ${node}/1net_test|xargs)
      else
          NODE_CHECK=$(curl --connect-timeout 3 -m 3 2>/dev/null -w "%{http_code} %{time_total}" ${node}/net_test|xargs)
      fi

      RES=$(echo ${NODE_CHECK}|awk '{print $1}')
      NODE_STATUS=$(echo ${NODE_CHECK}|awk '{print $2}')
      TIME_TOTAL=$(echo ${NODE_CHECK}|awk '{print $3 * 1000 - 500 }'|cut -d '.' -f 1)
      if [ "${NODE_STATUS}" == "200" ];then
          if [ $TIME_TOTAL -lt 300 ];then
              if [ $RES -ge 1500 ];then
                  echo "$RES $node" >> $tmp_file1
              fi
          else
              if [ $RES -ge 1500 ];then
                  echo "$TIME_TOTAL $node" >> $tmp_file2
              fi
          fi

          i=$(($i+1))
          if [ $TIME_TOTAL -lt 300 ];then
              if [ $RES -ge 2390 ];then
                  break;
              fi
          fi
      fi
	done

	local node_url=$(cat $tmp_file1|sort -r -g -t " " -k 1|head -n 1|awk '{print $2}')
	if [ -z "$node_url" ];then
      node_url=$(cat $tmp_file2|sort -g -t " " -k 1|head -n 1|awk '{print $2}')
      if [ -z "$node_url" ];then
          node_url='https://download.bt.cn';
      fi
	fi
	rm -f $tmp_file1
	rm -f $tmp_file2
	DOWNLOAD_URL=$node_url
	log_info "Download node: $DOWNLOAD_URL";
}

setup_loongarch64_symlink() {
    # 检查gcc是否存在
    if [ ! -f "/usr/bin/loongarch64-linux-gnu-gcc" ] && [ -f "/usr/bin/gcc" ]; then
        # 创建软链接
        ln -s /usr/bin/gcc /usr/bin/loongarch64-linux-gnu-gcc
        log_info "已为LoongArch64架构创建gcc软链接"
    fi
    if [ ! -f "/usr/bin/loongarch64-linux-gnu-g++" ] && [ -f "/usr/bin/g++" ]; then
        # 创建软链接
        ln -s /usr/bin/g++ /usr/bin/loongarch64-linux-gnu-g++
        log_info "已为LoongArch64架构创建g++软链接"
    fi
}

# 检测系统版本并确定预编译包名称
Get_Versions() {
    redhat_version_file="/etc/redhat-release"
    deb_version_file="/etc/issue"
    precompiled_package=""
    generic_precompiled_package=""

    # 检测CPU架构
    local arch_suffix=""
    local cpu_arch=$(uname -m)
    
    case "$cpu_arch" in
        x86_64)
            arch_suffix="-x86_64"
            generic_precompiled_package="cpython-3.13.7-x86_64-unknown-linux-gnu.tar.gz"
            log_info "检测到x86_64架构"
            ;;
        aarch64|arm64)
            arch_suffix="-arm64"
            generic_precompiled_package="cpython-3.13.7-aarch64-unknown-linux-gnu.tar.gz"
            log_info "检测到ARM64架构"
            ;;
        loongarch64)
            arch_suffix="-loongarch64"
            generic_precompiled_package="cpython-3.13.7-loongarch64-unknown-linux-gnu.tar.gz"
            setup_loongarch64_symlink
            log_info "检测到LoongArch64架构"
            ;;
        *)
            arch_suffix=""
            generic_precompiled_package=""
            ;;
    esac

    if [ -z "$arch_suffix" ]; then
        log_error "未识别的CPU架构: $cpu_arch"
    fi

    if [ -n "$generic_precompiled_package" ]; then
        log_info "匹配的基础编译包: $generic_precompiled_package"
    fi

    # 优先使用/etc/os-release检测系统版本
    if [ -f "/etc/os-release" ]; then
        . /etc/os-release
        OS_V=${VERSION_ID%%.*}
        
        # 根据ID和版本号确定预编译包名称
        case "$ID" in
            # Red Hat系列企业Linux (统一为el格式)
            centos)
                case "$OS_V" in
                    7) precompiled_package="pyenv313-el7${arch_suffix}.tar.gz" ;;
                    8) precompiled_package="pyenv313-el8${arch_suffix}.tar.gz" ;;
                    9) precompiled_package="pyenv313-el9${arch_suffix}.tar.gz" ;;
                    10) precompiled_package="pyenv313-el10${arch_suffix}.tar.gz" ;;
                esac
                ;;
            rhel)
                case "$OS_V" in
                    7) precompiled_package="pyenv313-el7${arch_suffix}.tar.gz" ;;
                    8) precompiled_package="pyenv313-el8${arch_suffix}.tar.gz" ;;
                    9) precompiled_package="pyenv313-el9${arch_suffix}.tar.gz" ;;
                    10) precompiled_package="pyenv313-el10${arch_suffix}.tar.gz" ;;
                esac
                ;;
            rocky)
                case "$OS_V" in
                    8) precompiled_package="pyenv313-el8${arch_suffix}.tar.gz" ;;
                    9) precompiled_package="pyenv313-el9${arch_suffix}.tar.gz" ;;
                    10) precompiled_package="pyenv313-el10${arch_suffix}.tar.gz" ;;
                esac
                ;;
            almalinux)
                case "$OS_V" in
                    8) precompiled_package="pyenv313-el8${arch_suffix}.tar.gz" ;;
                    9) precompiled_package="pyenv313-el9${arch_suffix}.tar.gz" ;;
                    10) precompiled_package="pyenv313-el10${arch_suffix}.tar.gz" ;;
                esac
                ;;
            centos-stream)
                case "$OS_V" in
                    8) precompiled_package="pyenv313-el8${arch_suffix}.tar.gz" ;;
                    9) precompiled_package="pyenv313-el9${arch_suffix}.tar.gz" ;;
                    10) precompiled_package="pyenv313-el10${arch_suffix}.tar.gz" ;;
                esac
                ;;
            opencloudos)
                case "$OS_V" in
                    8) precompiled_package="pyenv313-opencloudos8${arch_suffix}.tar.gz" ;;
                    9) precompiled_package="pyenv313-opencloudos9${arch_suffix}.tar.gz" ;;
                esac
                ;;
            anolis)
                case "$OS_V" in
                    8) precompiled_package="pyenv313-anolis8${arch_suffix}.tar.gz" ;;
                    9) precompiled_package="pyenv313-anolis9${arch_suffix}.tar.gz" ;;
                esac
                ;;
            tencentos)
                case "$OS_V" in
                    3) precompiled_package="pyenv313-tencentos3${arch_suffix}.tar.gz" ;;
                    4) precompiled_package="pyenv313-tencentos4${arch_suffix}.tar.gz" ;;
                esac
                ;;
            alinux|alibaba)
                case "$OS_V" in
                    2) precompiled_package="pyenv313-alibabacloud2${arch_suffix}.tar.gz" ;;
                    3) precompiled_package="pyenv313-alibabacloud3${arch_suffix}.tar.gz" ;;
                    4) precompiled_package="pyenv313-alibabacloud4${arch_suffix}.tar.gz" ;;
                esac
                ;;
            openeuler)
                case "$OS_V" in
                    9) precompiled_package="pyenv313-openeuler9${arch_suffix}.tar.gz" ;;
                esac
                ;;
                
            # Debian系列
            ubuntu)
                case "$OS_V" in
                    18) precompiled_package="pyenv313-ubuntu18${arch_suffix}.tar.gz" ;;
                    20) precompiled_package="pyenv313-ubuntu20${arch_suffix}.tar.gz" ;;
                    22) precompiled_package="pyenv313-ubuntu22${arch_suffix}.tar.gz" ;;
                    24) precompiled_package="pyenv313-ubuntu24${arch_suffix}.tar.gz" ;;
                esac
                ;;
            debian)
                case "$OS_V" in
                    10) precompiled_package="pyenv313-debian10${arch_suffix}.tar.gz" ;;
                    11) precompiled_package="pyenv313-debian11${arch_suffix}.tar.gz" ;;
                    12) precompiled_package="pyenv313-debian12${arch_suffix}.tar.gz" ;;
                    13) precompiled_package="pyenv313-debian13${arch_suffix}.tar.gz" ;;
                esac
                ;;
                
            # 其他特殊系统
            kylin)
                if [[ "$VERSION" == *"V10"* ]]; then
                    precompiled_package="pyenv313-kylinv10${arch_suffix}.tar.gz"
                fi
                ;;
        esac
    fi

    # 如果通过/etc/os-release没有找到匹配项，则尝试通过传统方式检测
    if [ -z "$precompiled_package" ]; then
        if [ -f $redhat_version_file ]; then
            local release_content=$(cat $redhat_version_file)
            
            # 检查红帽系列系统 (统一为el格式)
            if echo "$release_content" | grep -q "CentOS.*7"; then
                precompiled_package="pyenv313-el7${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "CentOS.*8"; then
                precompiled_package="pyenv313-el8${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "CentOS.*9"; then
                precompiled_package="pyenv313-el9${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "CentOS Stream.*8"; then
                precompiled_package="pyenv313-el8${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "CentOS Stream.*9"; then
                precompiled_package="pyenv313-el9${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "CentOS Stream.*10"; then
                precompiled_package="pyenv313-el10${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "Red Hat Enterprise Linux.*7"; then
                precompiled_package="pyenv313-el7${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "Red Hat Enterprise Linux.*8"; then
                precompiled_package="pyenv313-el8${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "Red Hat Enterprise Linux.*9"; then
                precompiled_package="pyenv313-el9${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "Rocky.*8"; then
                precompiled_package="pyenv313-el8${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "Rocky.*9"; then
                precompiled_package="pyenv313-el9${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "Rocky.*10"; then
                precompiled_package="pyenv313-el10${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "AlmaLinux.*8"; then
                precompiled_package="pyenv313-el8${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "AlmaLinux.*9"; then
                precompiled_package="pyenv313-el9${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "AlmaLinux.*10"; then
                precompiled_package="pyenv313-el10${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "Anolis.*8"; then
                precompiled_package="pyenv313-anolis8${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "Anolis.*9"; then
                precompiled_package="pyenv313-anolis9${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "OpenCloudOS.*8"; then
                precompiled_package="pyenv313-opencloudos8${arch_suffix}.tar.gz"
#            elif echo "$release_content" | grep -q "OpenCloudOS.*9"; then
#                precompiled_package="pyenv313-opencloudos9${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "TencentOS.*3"; then
                precompiled_package="pyenv313-tencentos3${arch_suffix}.tar.gz"
#            elif echo "$release_content" | grep -q "TencentOS.*4"; then
#                precompiled_package="pyenv313-tencentos4${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "openEuler.*9"; then
                precompiled_package="pyenv313-openeuler9${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "EulerOS.*9"; then
                precompiled_package="pyenv313-openeuler9${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "Alibaba Cloud.*2"; then
                precompiled_package="pyenv313-alibabacloud2${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "Alibaba Cloud.*3"; then
                precompiled_package="pyenv313-alibabacloud3${arch_suffix}.tar.gz"
            elif echo "$release_content" | grep -q "Alibaba Cloud.*4"; then
                precompiled_package="pyenv313-alibabacloud4${arch_suffix}.tar.gz"
            fi
        elif [ -f $deb_version_file ]; then
            local issue_content=$(cat $deb_version_file)
            
            # 检查Debian/Ubuntu系列系统
            if echo "$issue_content" | grep -q "Ubuntu.*18"; then
                precompiled_package="pyenv313-ubuntu18${arch_suffix}.tar.gz"
            elif echo "$issue_content" | grep -q "Ubuntu.*20"; then
                precompiled_package="pyenv313-ubuntu20${arch_suffix}.tar.gz"
            elif echo "$issue_content" | grep -q "Ubuntu.*22"; then
                precompiled_package="pyenv313-ubuntu22${arch_suffix}.tar.gz"
            elif echo "$issue_content" | grep -q "Ubuntu.*24"; then
                precompiled_package="pyenv313-ubuntu24${arch_suffix}.tar.gz"
            elif echo "$issue_content" | grep -q "Debian.*10"; then
                precompiled_package="pyenv313-debian10${arch_suffix}.tar.gz"
            elif echo "$issue_content" | grep -q "Debian.*11"; then
                precompiled_package="pyenv313-debian11${arch_suffix}.tar.gz"
            elif echo "$issue_content" | grep -q "Debian.*12"; then
                precompiled_package="pyenv313-debian12${arch_suffix}.tar.gz"
            elif echo "$issue_content" | grep -q "Debian .*13"; then
                precompiled_package="pyenv313-debian13${arch_suffix}.tar.gz"
            elif echo "$issue_content" | grep -q "Kylin.*V10"; then
                precompiled_package="pyenv313-kylinv10${arch_suffix}.tar.gz"
            fi
        fi
    fi

    if [ -n "$precompiled_package" ]; then
        log_info "匹配的预编译包: $precompiled_package"
    else
        log_warn "未找到匹配的预编译包"
    fi
}

install_system_dependencies() {
    log_info "安装系统依赖包..."

    if command -v yum >/dev/null 2>&1; then
        # 仅安装Python编译必需的依赖包，移除非必要包
        yum install -y xz-devel
        yum install -y gcc gcc-c++ make openssl-devel zlib-devel bzip2-devel libffi-devel readline-devel sqlite-devel wget curl unzip
    elif command -v apt-get >/dev/null 2>&1; then
        apt update
        # 仅安装Python编译必需的依赖包，移除非必要包
        apt-get install -y liblzma-dev libncurses5-dev
        apt install -y build-essential libssl-dev zlib1g-dev libreadline-dev libsqlite3-dev libffi-dev libbz2-dev  wget curl unzip
    else
        log_warn "未识别的包管理器，请手动安装编译依赖包"
        return 1
    fi

    if [ $? -eq 0 ]; then
        log_info "系统依赖包安装完成"
    else
        Red_Error "系统依赖包安装失败"
    fi

    Get_Versions
}

#===============================================================================
# 版本检查和条件编译函数
#===============================================================================

# 版本比较函数（通用）
version_compare() {
    local ver1="$1"
    local ver2="$2"

    # 将版本号转换为可比较的数字
    local ver1_num=$(echo "$ver1" | awk -F. '{printf "%03d%03d%03d", $1, $2, $3}')
    local ver2_num=$(echo "$ver2" | awk -F. '{printf "%03d%03d%03d", $1, $2, $3}')

    [ "$ver1_num" -ge "$ver2_num" ]
}

# 检查系统类型并执行相应的版本检查
check_dev_packages() {
    local need_compile_openssl=false
    local need_compile_sqlite=false

    log_info "检查系统开发库版本..."

    # 通过包管理器检查系统类型
    if command -v rpm >/dev/null 2>&1; then
        # Red Hat系列系统（使用rpm）
        log_info "检测到Red Hat系列系统，使用rpm检查包版本"

        # 检查openssl-devel包
        if rpm -q openssl-devel >/dev/null 2>&1; then
            local openssl_version=$(rpm -q --queryformat '%{VERSION}' openssl-devel 2>/dev/null)
            log_info "检测到openssl-devel版本: $openssl_version"

            # 检查版本是否满足要求（>= 1.1.1）
            if ! version_compare "$openssl_version" "1.1.1"; then
                log_warn "openssl-devel版本 $openssl_version < 1.1.1，需要编译静态OpenSSL"
                need_compile_openssl=true
            else
                log_info "openssl-devel版本 $openssl_version >= 1.1.1，满足要求"
            fi
        else
            log_warn "未安装openssl-devel包，需要编译静态OpenSSL"
            need_compile_openssl=true
        fi

        # 检查sqlite-devel包
        if rpm -q sqlite-devel >/dev/null 2>&1; then
            local sqlite_version=$(rpm -q --queryformat '%{VERSION}' sqlite-devel 2>/dev/null)
            log_info "检测到sqlite-devel版本: $sqlite_version"

            # 检查版本是否满足要求（>= 3.15.2）
            if ! version_compare "$sqlite_version" "3.15.2"; then
                log_warn "sqlite-devel版本 $sqlite_version < 3.15.2，需要编译静态SQLite3"
                need_compile_sqlite=true
            else
                log_info "sqlite-devel版本 $sqlite_version >= 3.15.2，满足要求"
            fi
        else
            log_warn "未安装sqlite-devel包，需要编译静态SQLite3"
            need_compile_sqlite=true
        fi

    elif command -v dpkg >/dev/null 2>&1; then
        # Debian系列系统（使用dpkg）
        log_info "检测到Debian系列系统，使用dpkg检查包版本"

        # 检查libssl-dev包
        if dpkg -l libssl-dev 2>/dev/null | grep -q "^ii"; then
            local openssl_version=$(dpkg -l libssl-dev 2>/dev/null | grep "^ii" | awk '{print $3}' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
            if [ -n "$openssl_version" ]; then
                log_info "检测到libssl-dev版本: $openssl_version"

                # 检查版本是否满足要求（>= 1.1.1）
                if ! version_compare "$openssl_version" "1.1.1"; then
                    log_warn "libssl-dev版本 $openssl_version < 1.1.1，需要编译静态OpenSSL"
                    need_compile_openssl=true
                else
                    log_info "libssl-dev版本 $openssl_version >= 1.1.1，满足要求"
                fi
            else
                log_warn "无法获取libssl-dev版本信息，需要编译静态OpenSSL"
                need_compile_openssl=true
            fi
        else
            log_warn "未安装libssl-dev包，需要编译静态OpenSSL"
            need_compile_openssl=true
        fi

        # 检查libsqlite3-dev包
        if dpkg -l libsqlite3-dev 2>/dev/null | grep -q "^ii"; then
            local sqlite_version=$(dpkg -l libsqlite3-dev 2>/dev/null | grep "^ii" | awk '{print $3}' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
            if [ -n "$sqlite_version" ]; then
                log_info "检测到libsqlite3-dev版本: $sqlite_version"

                # 检查版本是否满足要求（>= 3.15.2）
                if ! version_compare "$sqlite_version" "3.15.2"; then
                    log_warn "libsqlite3-dev版本 $sqlite_version < 3.15.2，需要编译静态SQLite3"
                    need_compile_sqlite=true
                else
                    log_info "libsqlite3-dev版本 $sqlite_version >= 3.15.2，满足要求"
                fi
            else
                log_warn "无法获取libsqlite3-dev版本信息，需要编译静态SQLite3"
                need_compile_sqlite=true
            fi
        else
            log_warn "未安装libsqlite3-dev包，需要编译静态SQLite3"
            need_compile_sqlite=true
        fi

    else
        # 未知系统，默认编译静态库
        log_warn "未识别的包管理器，默认编译静态OpenSSL和SQLite3"
        need_compile_openssl=true
        need_compile_sqlite=true
    fi

    # 返回检查结果
    if [ "$need_compile_openssl" = true ] && [ "$need_compile_sqlite" = true ]; then
        return 3  # 都需要编译
    elif [ "$need_compile_openssl" = true ]; then
        return 1  # 只需要编译OpenSSL
    elif [ "$need_compile_sqlite" = true ]; then
        return 2  # 只需要编译SQLite
    else
        return 0  # 都不需要编译
    fi
}

# 编译OpenSSL 1.1.1w
Install_Openssl111() {
    log_info "编译OpenSSL 1.1.1w..."

    local opensslVersion="1.1.1w"

    cd /tmp
    if ! wget "${DOWNLOAD_URL}/src/openssl-${opensslVersion}.tar.gz" -T 30; then
        Red_Error "下载OpenSSL源码失败"
    fi

    tar -zxf "openssl-${opensslVersion}.tar.gz"
    rm -f "openssl-${opensslVersion}.tar.gz"
    cd "openssl-${opensslVersion}" || Red_Error "进入OpenSSL目录失败"

    log_info "配置OpenSSL编译环境..."
    ./config --prefix="$PYTHON_PYENV_NEW/openssl111w-static" enable-md2 enable-rc5 sctp zlib no-shared

    log_info "编译OpenSSL（可能需要较长时间）..."
    make -j$(nproc)

    log_info "安装OpenSSL..."
    make install

    cd ..
    rm -rf "openssl-${opensslVersion}"

    if [ -d "$PYTHON_PYENV_NEW/openssl111w-static" ]; then
        log_info "OpenSSL 1.1.1w编译安装成功"
    else
        Red_Error "OpenSSL编译安装失败"
    fi
}

# 编译SQLite3 3.50.4
Install_Sqlite3() {
    log_info "编译SQLite3 3.50.4..."

    cd /tmp
    if ! wget "${DOWNLOAD_URL}/src/sqlite-src-3500400.zip" -T 30; then
        Red_Error "下载SQLite源码失败"
    fi

    unzip -q "sqlite-src-3500400.zip"
    rm -f "sqlite-src-3500400.zip"
    cd "sqlite-src-3500400"

    log_info "配置SQLite编译环境..."
    ./configure \
        --prefix="$PYTHON_PYENV_NEW/sqlite3-static" \
        --disable-shared \
        --enable-static \
        CFLAGS="-fPIC -DSQLITE_ENABLE_TRACE_V2 -DSQLITE_ENABLE_LOAD_EXTENSION -DSQLITE_VERSION_NUMBER=3500400 -DSQLITE_VERSION='\"3.50.4\"'" \
        LDFLAGS="-lm -lz"

    log_info "编译SQLite3..."
    make -j$(nproc) && make install

    cd /tmp
    rm -rf "sqlite-src-3500400"

    if [ -d "$PYTHON_PYENV_NEW/sqlite3-static" ]; then
        log_info "SQLite3 3.50.4编译安装成功"
    else
        Red_Error "SQLite3编译安装失败"
    fi
}

# 尝试安装预编译的Python 3.13环境
install_precompiled_python() {
    if [ "$FORCE_COMPILE" == "true" ]; then
        log_info "强制使用源码编译，跳过预编译包安装"
        INSTALL_ROUTE=$ROUTE_COMPILE
        return 1
    fi

    # 安装路线1: 系统特定预编译包（最快）
    if [ -n "$precompiled_package" ]; then
        log_info "尝试安装系统特定预编译Python环境: $precompiled_package"
        if install_system_specific_precompiled_python; then
            log_info "成功：使用系统特定预编译包安装完成"
            INSTALL_ROUTE=$ROUTE_SYSTEM_SPECIFIC
            return 0
        else
            log_warn "失败：系统特定预编译包安装失败"
        fi
    fi
    
    # 安装路线2: 通用预编译包（中等速度）
    if [ -n "$generic_precompiled_package" ]; then
        log_info "尝试安装通用预编译Python环境: $generic_precompiled_package"
        if install_generic_precompiled_python; then
            log_info "成功：使用通用预编译包安装完成"
            INSTALL_ROUTE=$ROUTE_GENERIC
            return 0
        else
            log_warn "失败：通用预编译包安装失败"
        fi
    fi
    
    # 安装路线3: 源码编译（最慢，保底手段）
    log_info "所有预编译包都不可用，将使用源码编译"
    INSTALL_ROUTE=$ROUTE_COMPILE
    return 1
}

# 安装系统特定预编译Python环境
install_system_specific_precompiled_python() {
    local pyenv_file="/tmp/$precompiled_package"
    local download_url="${DOWNLOAD_URL}/install/pyenv/$precompiled_package"

    if ! wget -O "$pyenv_file" "$download_url" -T 30; then
        log_warn "下载系统特定预编译包失败"
        rm -f "$pyenv_file"
        return 1
    fi

    local file_size=$(du -b "$pyenv_file" 2>/dev/null | awk '{print $1}')
    if [ "$file_size" -lt 10000000 ]; then
        log_warn "下载的预编译包文件过小，可能损坏"
        rm -f "$pyenv_file"
        return 1
    fi

    if extract_and_install_precompiled_python "$pyenv_file"; then
        return 0
    else
        return 1
    fi
}

# 安装通用预编译Python环境
install_generic_precompiled_python() {
    local pyenv_file="/tmp/$generic_precompiled_package"
    
    # 检查本地是否存在通用预编译包
    if [ ! -f "$pyenv_file" ]; then
        # 本地不存在则从下载节点下载
        log_info "本地未找到通用预编译包，从下载节点获取..."
        local download_url="${DOWNLOAD_URL}/install/pyenv/$generic_precompiled_package"
        
        if ! wget -O "$pyenv_file" "$download_url" -T 30; then
            log_warn "下载通用预编译包失败"
            rm -f "$pyenv_file"
            return 1
        fi
    else
        log_info "使用本地通用预编译包: $pyenv_file"
    fi

    local file_size=$(du -b "$pyenv_file" 2>/dev/null | awk '{print $1}')
    if [ "$file_size" -lt 10000000 ]; then
        log_warn "预编译包文件过小，可能损坏"
        rm -f "$pyenv_file"
        return 1
    fi

    if extract_and_install_precompiled_python "$pyenv_file"; then
        return 0
    else
        return 1
    fi
}

# 解压并安装预编译Python环境
extract_and_install_precompiled_python() {
    local pyenv_file=$1
    
    log_info "解压预编译Python环境到临时目录..."
    rm -rf "$PYTHON_PYENV_NEW"
    mkdir -p "$(dirname "$PYTHON_PYENV_NEW")"

    # 创建解压临时目录，避免与现有pyenv目录冲突
    local extract_temp_dir="$(dirname "$PYTHON_PYENV_NEW")/extract_temp"
    rm -rf "$extract_temp_dir"
    mkdir -p "$extract_temp_dir"

    if ! tar -zxf "$pyenv_file" -C "$extract_temp_dir" >/dev/null 2>&1; then
        log_warn "解压预编译包失败"
        rm -rf "$extract_temp_dir"
        rm -f "$pyenv_file"
        rm -rf "$PYTHON_PYENV_NEW"
        return 1
    fi

    # 将解压出的pyenv目录移动到目标位置
    if [ -d "$extract_temp_dir/pyenv" ]; then
        mv "$extract_temp_dir/pyenv" "$PYTHON_PYENV_NEW"
        rm -rf "$extract_temp_dir"
    else 
        if [ -d "$extract_temp_dir/python" ]; then
            mv "$extract_temp_dir/python" "$PYTHON_PYENV_NEW"
            rm -rf "$extract_temp_dir"
            setup_python_environment
        else
            log_error "预编译包格式错误，未找到pyenv或python目录"
            rm -rf "$extract_temp_dir"
            rm -f "$pyenv_file"
            rm -rf "$PYTHON_PYENV_NEW"
            return 1
        fi
    fi

    rm -f "$pyenv_file"

    if [ ! -f "$PYTHON_PYENV_NEW/bin/python3.13" ]; then
        log_warn "预编译Python环境安装验证失败"
        rm -rf "$PYTHON_PYENV_NEW"
        return 1
    fi

    chmod -R 700 "$PYTHON_PYENV_NEW/bin"

    if "$PYTHON_PYENV_NEW/bin/python3.13" --version >/dev/null 2>&1; then
        log_info "预编译Python 3.13环境安装成功"
        return 0
    else
        log_warn "预编译Python环境验证失败"
        rm -rf "$PYTHON_PYENV_NEW"
        return 1
    fi
}

# 修改Python脚本的shebang行以提高可移植性
modify_python_shebang() {
    log_info "修改Python脚本的shebang行以提高可移植性..."
    
    # 遍历bin目录下的所有文件
    for file in "$PYTHON_PYENV_NEW/bin"/*; do
        # 检查是否为文件且大小小于10KB
        if [ -f "$file" ] && [ $(du -b "$file" 2>/dev/null | awk '{print $1}') -lt 10240 ]; then
            # 检查文件是否包含Python shebang
            if head -n 1 "$file" | grep -q "^#!.*python"; then
                log_info "修改脚本: $(basename "$file")"
                
                # 保存原有文件权限
                local file_permissions=$(stat -c "%a" "$file" 2>/dev/null || echo "755")
                
                # 先读取第一行后的内容
                local rest_content=$(tail -n +2 "$file")
                
                # 创建新的shebang内容
                echo '#!/bin/sh' > "$file.tmp"
                echo "'''exec' \"\$(dirname -- \"\$(realpath -- \"\$0\")\")/python3.13\" \"\$0\" \"\$@\"" >> "$file.tmp"
                echo "' '''" >> "$file.tmp"
                
                # 添加原有内容
                echo "$rest_content" >> "$file.tmp"
                
                # 恢复原有文件权限
                chmod "$file_permissions" "$file.tmp"
                
                # 替换原文件
                mv "$file.tmp" "$file"
            fi
        fi
    done
    
    log_info "Python脚本的shebang行修改完成"
}

# 源码编译Python 3.13
compile_python_313() {
    log_info "开始源码编译Python $PYTHON_VERSION 到临时目录..."

    local python_src="/tmp/python-${PYTHON_VERSION}.tar.xz"
    local python_src_path="/tmp/Python-${PYTHON_VERSION}"
    local download_url="https://mirrors.aliyun.com/python-release/source/Python-${PYTHON_VERSION}.tar.xz"

    # 创建临时安装目录
    rm -rf "$PYTHON_PYENV_NEW"
    mkdir -p "$PYTHON_PYENV_NEW"

    # 检查是否需要编译静态库
    log_info "检查系统库版本并决定编译策略..."
    check_dev_packages
    local check_result=$?

    # 根据检查结果编译所需的静态库
    if [ $check_result -eq 1 ] || [ $check_result -eq 3 ]; then
        log_info "编译OpenSSL 1.1.1w..."
        Install_Openssl111
    fi

    if [ $check_result -eq 2 ] || [ $check_result -eq 3 ]; then
        log_info "编译SQLite3 3.50.4..."
        Install_Sqlite3
    fi

    if [ $check_result -eq 0 ]; then
        log_info "系统OpenSSL和SQLite版本满足要求，跳过静态库编译"
    fi

    # 下载源码
    log_info "下载Python源码..."
    cd /tmp
    if ! wget -O "$python_src" "$download_url" -T 30; then
        Red_Error "下载Python源码失败: $download_url"
    fi

    local file_size=$(du -b "$python_src" 2>/dev/null | awk '{print $1}')
    if [ "$file_size" -lt 1000000 ]; then
        rm -f "$python_src"
        Red_Error "下载的Python源码包文件损坏或过小"
    fi

    # 解压源码
    log_info "解压Python源码..."
    if ! tar -xJf "$python_src"; then
        Red_Error "解压Python源码失败"
    fi

    rm -f "$python_src"
    cd "$python_src_path"

    # 根据版本检查结果配置编译参数
    log_info "配置Python编译环境..."

    if [ $check_result -eq 0 ]; then
        # 系统OpenSSL和SQLite版本都满足要求
        log_info "使用系统OpenSSL和SQLite库"
        ./configure --prefix="$PYTHON_PYENV_NEW"
    elif [ $check_result -eq 1 ]; then
        # 只需要编译OpenSSL
        log_info "使用静态OpenSSL和系统SQLite"
        CFLAGS="-I$PYTHON_PYENV_NEW/openssl111w-static/include -I/usr/include" \
        LDFLAGS="-L$PYTHON_PYENV_NEW/openssl111w-static/lib -lssl -lcrypto -lz -lm" \
        ./configure \
            --prefix="$PYTHON_PYENV_NEW" \
            --with-openssl="$PYTHON_PYENV_NEW/openssl111w-static"
    elif [ $check_result -eq 2 ]; then
        # 只需要编译SQLite
        log_info "使用系统OpenSSL和静态SQLite"
        CFLAGS="-I/usr/include" \
        LDFLAGS="-L$PYTHON_PYENV_NEW/sqlite3-static/lib -lsqlite3 -lz -lm" \
        CPPFLAGS="-I$PYTHON_PYENV_NEW/sqlite3-static/include -DSQLITE_VERSION=\"3.50.4\" -DSQLITE_VERSION_NUMBER=3500400" \
        ./configure \
            --prefix="$PYTHON_PYENV_NEW" \
            --enable-loadable-sqlite-extensions
    else
        # 需要编译OpenSSL和SQLite
        log_info "使用静态OpenSSL和SQLite"
        CFLAGS="-I$PYTHON_PYENV_NEW/openssl111w-static/include -I/usr/include" \
        LDFLAGS="-L$PYTHON_PYENV_NEW/sqlite3-static/lib -L$PYTHON_PYENV_NEW/openssl111w-static/lib -lsqlite3 -lssl -lcrypto -lz -lm" \
        CPPFLAGS="-I$PYTHON_PYENV_NEW/sqlite3-static/include -DSQLITE_VERSION=\"3.50.4\" -DSQLITE_VERSION_NUMBER=3500400" \
        ./configure \
            --prefix="$PYTHON_PYENV_NEW" \
            --with-openssl="$PYTHON_PYENV_NEW/openssl111w-static" \
            --enable-loadable-sqlite-extensions
    fi

    if [ $? -ne 0 ]; then
        cd /tmp && rm -rf "$python_src_path"
        Red_Error "Python配置失败"
    fi

    local cpu_count=$(getconf _NPROCESSORS_ONLN)
    log_info "开始编译Python（使用 $cpu_count 个CPU核心，可能需要较长时间）..."

    if ! make -j"$cpu_count"; then
        cd /tmp && rm -rf "$python_src_path"
        Red_Error "Python编译失败"
    fi

    log_info "安装Python到临时目录..."
    if ! make install; then
        cd /tmp && rm -rf "$python_src_path"
        Red_Error "Python安装失败"
    fi

    cd /tmp && rm -rf "$python_src_path"

    if [ ! -f "$PYTHON_PYENV_NEW/bin/python3.13" ]; then
        Red_Error "Python 3.13安装验证失败"
    fi

    log_info "Python 3.13源码编译安装成功"
}

# 设置Python环境
setup_python_environment() {
    log_info "设置Python 3.13环境..."

    cd "$PYTHON_PYENV_NEW/bin"
    ln -sf python3.13 python3.7
    ln -sf python3.13 python3
    ln -sf python3.13 python
    ln -sf pip3 pip

    cd "$PYTHON_PYENV_NEW/lib"
    ln -sf python3.13 python3.7
    chmod -R 700 "$PYTHON_PYENV_NEW/bin"
    log_info "Python环境设置完成"
}

# 安装Python包
install_python_packages() {
    set_pip_source

    log_info "安装Python 3.13所需包..."

    cd "$PYTHON_PYENV_NEW"

    # 初始化pip 安装包
    bin/python3.13 -m ensurepip
    bin/python3.13 -m pip install --upgrade pip
    bin/pip install -U setuptools
    # 本地的pip313.txt文件存在时，免去下载动作
    if [ -f "/www/server/panel/script/$PIP_REQUIREMENTS_FILE" ]; then
        log_info "使用本地Python包列表: /www/server/panel/script/$PIP_REQUIREMENTS_FILE"
        # 复制本地文件到安装目录
        cp "/www/server/panel/script/$PIP_REQUIREMENTS_FILE" .
    else
        log_info "下载Python包列表..."
        local download_url="${DOWNLOAD_URL}/install/pyenv/pip313.txt"
        if ! wget -O "$PIP_REQUIREMENTS_FILE" "$download_url" -T 30; then
            Red_Error "Python包列表下载失败: $download_url"
        fi
    fi

    if [ $(uname -m) == "loongarch64" ]; then
        bin/pip3 install cryptography cffi -i https://pypi.loongnix.cn/loongson/pypi/+simple/ --only-binary=cryptography
        bin/pip install -r "$PIP_REQUIREMENTS_FILE"
        bin/pip install psycopg2-binary==2.9.10  # 如果没有pgsql开发包，可能会报错，故单独处理
        bin/pip install psutil gevent flask
        log_info "Python包安装结束"
        return
    fi

    if bin/pip install -r "$PIP_REQUIREMENTS_FILE"; then
        bin/pip install psycopg2-binary==2.9.10  # 如果没有pgsql开发包，可能会报错，故单独处理
        log_info "Python包安装完成"
    else
        log_warn "部分Python包安装失败，但不影响基本功能"
    fi
}

# 验证Python环境
verify_python_environment() {
    log_info "验证Python 3.13环境..."

    local python_bin="$PYTHON_PYENV_NEW/bin/python3.13"

    # 检查Python版本
    local python_version=$("$python_bin" --version 2>&1)
    log_info "Python版本: $python_version"

    # 检查SSL支持
    if "$python_bin" -c "import ssl; print('SSL支持正常')" 2>/dev/null; then
        log_info "SSL支持检查通过"
    else
        Red_Error "SSL支持检查失败"
    fi

    # 检查SQLite支持
    if "$python_bin" -c "import sqlite3; print('SQLite支持正常')" 2>/dev/null; then
        log_info "SQLite支持检查通过"
    else
        Red_Error "SQLite支持检查失败"
    fi

    # 检查关键包
    local packages=("psutil" "gevent" "flask")
    for package in "${packages[@]}"; do
        if "$python_bin" -c "import $package" 2>/dev/null; then
            log_info "包 $package 检查通过"
        else
            log_warn "包 $package 检查失败"
        fi
    done

    log_info "Python环境验证完成"
}

# 替换Python环境
replace_python_environment() {
    log_info "备份原有Python环境并替换为新环境..."

    # 停止宝塔服务
    log_info "停止宝塔服务..."
    if [ "${HAS_OLD_PANEL}" == "true" ]; then
        /etc/init.d/bt stop
    fi

    # 1. 记录现有环境状态
    local original_type=""  # directory, symlink, or none
    local original_target=""  # 如果是软链接，记录目标路径
    
    if [ -L "$PYTHON_PYENV" ]; then
        original_type="symlink"
        original_target=$(readlink "$PYTHON_PYENV")
        log_info "检测到现有环境为软链接，目标: $original_target"
    elif [ -d "$PYTHON_PYENV" ]; then
        original_type="directory"
        log_info "检测到现有环境为目录"
    else
        original_type="none"
        log_info "未检测到现有环境"
    fi

    # 2. 备份现有环境
    local backup_time=$(date '+%Y%m%d_%H%M%S')
    local backup_path="${PYTHON_PYENV}_backup_${backup_time}"
    
    if [ "$original_type" = "symlink" ]; then
        # 如果原环境是软链接，只需记录信息，无需备份目标目录（避免耗时）
        log_info "软链接环境无需备份目标目录"
        # 创建一个标识文件记录原始链接信息
        mkdir -p "$backup_path"
        echo "$original_target" > "$backup_path/symlink_target"
    elif [ "$original_type" = "directory" ]; then
        # 如果原环境是目录，重命名为备份
        log_info "重命名目录为备份: $backup_path"
        if ! mv "$PYTHON_PYENV" "$backup_path"; then
            /etc/init.d/bt start
            Red_Error "备份原有环境失败"
        fi
    else
        # 如果没有原环境，创建备份目录以备恢复时使用
        log_info "创建备份目录: $backup_path"
        mkdir -p "$backup_path"
    fi
    
    log_info "备份完成: $backup_path"

    # 3. 生成恢复函数
    restore_original_environment() {
        log_warn "正在执行环境恢复..."

        # 停止服务
        /etc/init.d/bt stop

        # 删除当前环境
        rm -rf "$PYTHON_PYENV"

        # 根据原始类型恢复环境
        if [ "$original_type" = "symlink" ]; then
            # 恢复软链接（从备份目录读取原始目标）
            if [ -f "$backup_path/symlink_target" ]; then
                local target=$(cat "$backup_path/symlink_target")
                log_info "恢复软链接: $PYTHON_PYENV -> $target"
                ln -sf "$target" "$PYTHON_PYENV"
            fi
        elif [ "$original_type" = "directory" ]; then
            # 恢复目录
            log_info "恢复目录环境"
            if [ -d "$backup_path" ]; then
                mv "$backup_path" "$PYTHON_PYENV"
            fi
        else
            # 原来没有环境，清理备份
            log_info "清理备份目录"
            rm -rf "$backup_path"
        fi

        # 重启服务
        /etc/init.d/bt start
        log_info "环境恢复完成"
    }

    # 4. 替换环境
    if [ "$USE_SOFTLINK" = true ]; then
        # 使用软链接方式替换环境
        log_info "使用软链接方式替换Python环境..."

        # 删除原环境（如果存在）
        if [ "$original_type" != "none" ]; then
            rm -rf "$PYTHON_PYENV"
        fi

        # 创建软链接
        log_info "创建软链接 $PYTHON_PYENV -> $PYTHON_PYENV_NEW"
        if ln -sf "$PYTHON_PYENV_NEW" "$PYTHON_PYENV"; then
            log_info "Python环境软链接创建成功"
        else
            log_error "Python环境软链接创建失败"
            restore_original_environment
            Red_Error "Python环境替换失败"
        fi
    else
        # 直接替换环境（默认方式）
        log_info "直接替换Python环境..."

        # 删除原环境（如果存在）
        if [ "$original_type" != "none" ]; then
            rm -rf "$PYTHON_PYENV"
        fi

        # 移动新环境到正式位置
        log_info "将新Python环境移动到正式位置..."
        if mv "$PYTHON_PYENV_NEW" "$PYTHON_PYENV"; then
            log_info "Python环境替换成功"
        else
            log_error "Python环境替换失败"
            restore_original_environment
            Red_Error "Python环境替换失败"
        fi
    fi

    # 重新启动宝塔服务
    log_info "重新启动宝塔服务..."
    /etc/init.d/bt start
    # 尝试重启fail2ban服务
    if [ -d "$PANEL_PATH/plugin/fail2ban" ]; then
        log_info "尝试重启fail2ban服务..."
         nohup systemctl restart fail2ban &
    fi
    
    # 使用专门的函数检查服务状态
    if check_bt_service_status; then
        log_info "Python环境替换完成！"
    else
        log_warn "宝塔服务启动失败"
        restore_original_environment
        
        # 再次检查服务状态
        if check_bt_service_status; then
            log_info "已恢复原有环境并成功启动服务"
        else
            log_warn "恢复环境后服务仍然启动失败，请手动检查"
        fi
    fi
}

# 获取面板进程PID
get_panel_pids() {
    isStart=$(ps aux|grep -E '(runserver|BT-Panel)'|grep -v grep|awk '{print $2}'|xargs)
    pids=$isStart
}

# 获取任务进程PID
get_task_pids() {
    isStart=$(ps aux|grep -E '(task.py|BT-Task)'|grep -v grep|awk '{print $2}'|xargs)
    pids=$isStart
}

# 检查宝塔服务是否正常运行
check_bt_service_status() {
    if [ "${HAS_OLD_PANEL}" == "false" ]; then
        log_info "没有面板文件，跳过检查。"
        return 0
    fi

    log_info "检查宝塔服务运行状态..."
    
    # 检查面板进程是否启动成功
    get_panel_pids
    local panel_pids=$pids
    # 检查任务进程是否启动成功
    get_task_pids
    local task_pids=$pids
    
    # 等待一段时间让进程完全启动
    sleep 2
    
    # 再次检查进程状态
    get_panel_pids
    local new_panel_pids=$pids
    get_task_pids
    local new_task_pids=$pids
    
    # 验证进程是否正常运行
    if [ -n "$new_panel_pids" ] && [ -n "$new_task_pids" ]; then
        log_info "宝塔服务启动成功"
        log_info "面板进程PID: $new_panel_pids"
        log_info "任务进程PID: $new_task_pids"
        return 0
    else
        log_warn "宝塔服务启动可能存在问题"
        if [ -z "$new_panel_pids" ]; then
            log_warn "面板进程未正常启动"
        fi
        if [ -z "$new_task_pids" ]; then
            log_warn "任务进程未正常启动"
        fi
        return 1
    fi
}

#===============================================================================
# 打包
#===============================================================================
tar_pyenv(){
    log_info "打包当前Python环境..."
    if [ -z "$precompiled_package" ]; then
        log_info "未识别的Python环境，不进行打包..."
        return 0
    fi
    /etc/init.d/bt stop
    sleep 2
    cd "${PANEL_PATH}"
    tar -zcvf "$precompiled_package" \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        pyenv > /dev/null 2>&1
    if [ $? -eq 0 ]; then \
      log_info "Python环境打包完成：$precompiled_package"
    else
      log_error "Python环境打包失败"
      return 1
    fi
    /etc/init.d/bt start
}

#===============================================================================
# pip 源设置
#===============================================================================
# pip源列表
pip_nodes=(
    https://mirrors.tencent.com/pypi/simple
    https://mirrors.aliyun.com/pypi/simple
    https://pypi.tuna.tsinghua.edu.cn/simple
    https://pypi.mirrors.ustc.edu.cn/simple
    https://pypi.org/simple
)

# 全局变量定义
FASTEST_PIP_SOURCE=""  # 保存最快的pip源

# 检测pip源速度
get_fastest_pip_source() {
    log_info "正在检测可用的pip源速度..."

    local fastest_url=""
    local shortest_time=5000
    local current_time

    # 检查是否为腾讯云服务器
    check_tencent_cloud_optimization

    # 遍历所有节点检测速度
    for node in "${pip_nodes[@]}"; do
        if test_pip_source_speed "$node"; then
            calculate_response_time "$node"
            local response_time=$current_time

            log_info "$node 响应时间: ${response_time}ms"

            if [ $response_time -lt $shortest_time ]; then
                shortest_time=$response_time
                fastest_url=$node
            fi

            # 如果响应时间小于50ms，认为已经足够快，直接返回
            if [ $shortest_time -lt 50 ]; then
                break
            fi
        else
            log_warn "$node 连接失败或超时"
        fi
    done

    finalize_fastest_source "$fastest_url" "$shortest_time"
}

# 检查腾讯云优化
check_tencent_cloud_optimization() {
    if [ -f "/etc/hostname" ]; then
        local tencent_cloud=$(cat /etc/hostname | grep -E VM-[0-9]+-[0-9]+)
        if [ "${tencent_cloud}" ]; then
            log_info "检测到腾讯云服务器，优先使用腾讯云镜像源"
            pip_nodes=(https://mirrors.tencent.com/pypi/simple https://mirrors.aliyun.com/pypi/simple https://pypi.tuna.tsinghua.edu.cn/simple https://pypi.mirrors.ustc.edu.cn/simple https://pypi.org/simple)
        fi
    fi
}

# 测试pip源速度
test_pip_source_speed() {
    local node=$1
    # 使用HEAD请求测试连接速度，超时设置为3秒
    if curl -sS --connect-timeout 3 -m 10 -I "$node/" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 计算响应时间
calculate_response_time() {
    local node=$1
    local start=$(date +%s.%N)
    curl -sS --connect-timeout 3 -m 10 -I "$node/" > /dev/null 2>&1
    local end=$(date +%s.%N)

    # 计算毫秒级响应时间
    local start_s=$(echo $start | cut -d '.' -f 1)
    local start_ns=$(echo $start | cut -d '.' -f 2)
    local end_s=$(echo $end | cut -d '.' -f 1)
    local end_ns=$(echo $end | cut -d '.' -f 2)
    current_time=$(( (10#$end_s-10#$start_s)*1000000 + (10#$end_ns/1000 - 10#$start_ns/1000) ))
    current_time=$((current_time/1000))
}

# 确定最快的源
finalize_fastest_source() {
    local fastest_url=$1
    local shortest_time=$2

    if [ -z "$fastest_url" ] || [ $shortest_time = 5000 ]; then
        log_error "未找到可用的pip源"
        FASTEST_PIP_SOURCE="False"
        return 1
    else
        log_info "最快pip源: $fastest_url (${shortest_time}ms)"
        FASTEST_PIP_SOURCE="$fastest_url"
        return 0
    fi
}

# 获取信任主机
get_trusted_host() {
    local url=$1
    if [[ "$url" == *"aliyun"* ]]; then
        echo "mirrors.aliyun.com"
    elif [[ "$url" == *"tencent"* ]]; then
        echo "mirrors.tencent.com"
    elif [[ "$url" == *"tsinghua"* ]]; then
        echo "pypi.tuna.tsinghua.edu.cn"
    elif [[ "$url" == *"pypi.org"* ]]; then
        echo "pypi.org"
    else
        # 提取域名
        echo "$url" | awk -F/ '{print $3}'
    fi
}

# 设置pip源
set_pip_source() {
    # 调用函数检测最快pip源
    get_fastest_pip_source

    # 直接使用全局变量获取最快pip源
    local pip_url="$FASTEST_PIP_SOURCE"

    # 根据检测结果执行相应操作
    if is_valid_pip_source "$pip_url"; then
        configure_pip_source "$pip_url"
    else
        handle_invalid_pip_source
    fi
}

# 检查pip源是否有效
is_valid_pip_source() {
    local pip_url=$1
    if [ "$pip_url" = "False" ]; then
        return 1
    else
        return 0
    fi
}

# 配置pip源
configure_pip_source() {
    local pip_url=$1
    local trusted_host=$(get_trusted_host "$pip_url")

    # 创建pip配置目录
    create_pip_config_directory

    # 写入配置文件
    write_pip_config "$pip_url" "$trusted_host"

    log_info "pip源已设置成功！"
    log_info "源地址: $pip_url"
    log_info "信任主机: $trusted_host"
    log_info "配置文件: ~/.pip/pip.conf"

    return 0
}

# 处理无效的pip源
handle_invalid_pip_source() {
    log_warn "无法检测到可用pip源，将移除现有配置"
    remove_pip_config
    return 1
}

# 创建pip配置目录
create_pip_config_directory() {
    if [ ! -d ~/.pip ]; then
        mkdir -p ~/.pip
    fi
}

# 写入pip配置文件
write_pip_config() {
    local pip_url=$1
    local trusted_host=$2

    cat > ~/.pip/pip.conf << EOF
[global]
index-url = $pip_url

[install]
trusted-host = $trusted_host
EOF
}

# 移除pip源配置
remove_pip_config() {
    if [ -f "~/.pip/pip.conf" ]; then
        rm -f ~/.pip/pip.conf
        log_info "已移除pip源配置文件"
    else
        log_info "未找到pip源配置文件"
    fi
}

#===============================================================================
# 插件第三方库更新相关
#===============================================================================

# 插件包配置数组
# key 为插件包名称，value 为该插件包所依赖的第三方库名称
# 特殊情况， 如果 key为 插件包_args, 则value是插件包所依赖的第三方库的扩展安装参数
declare -A PLUGIN_PACKAGES
PLUGIN_PACKAGES=(
    ["alidns"]="alibabacloud_alidns20150109 alibabacloud_tea_openapi alibabacloud_tea_util alibabacloud_sts20150401 alibabacloud_ecs20140526"
    ["alioss"]="oss2"
    ["aliyun"]="alibabacloud_swas_open20200601 alibabacloud_tea_openapi alibabacloud_tea_util aliyun-python-sdk-sts aliyun-python-sdk-core"
    ["aws_s3"]="boto3"
    ["bos"]="bce-python-sdk"
    ["bt_webhorse"]="pyahocorasick"
    ["cosfs"]="cos-python-sdk-v5"
    ["dnspod"]="tencentcloud-sdk-python"
    ["dogecloud"]="boto3"
    ["frp"]="toml"
    ["gcloud_storage"]="ndg-httpsclient google-cloud-storage"
    ["gdrive"]="google-api-python-client google-auth-httplib2 google-auth-oauthlib httplib2"
    ["gpustat"]="pynvml"
    ["jdcloud"]="'boto3<=1.35.0' 'botocore>=1.27.0'"
    ["linuxsys"]="distro"
    ["mail_sys"]="python-dateutil"
    ["minio"]="minio"
    ["monitor"]="reportlab==4.4.3 matplotlib==3.10.6"
    ["monitor_args"]="--only-binary=contourpy,numpy"
    ["msonedrive"]="requests-oauthlib==1.3.0"
    ["obs"]="esdk-obs-python==3.25.8"
    ["ossfs"]="boto3 esdk-obs-python==3.25.8 ks3sdk oss2 bce-python-sdk"
    ["qiniu"]="qiniu==7.4.1"
    ["supervisor"]="supervisor==4.2.4"
    ["supervisor_args"]="-I"
    ["sysdisk"]="blkinfo"
    ["tencentcloud"]=""
    ["tencent"]="tencentcloud-sdk-python"
    ["tianyiyun"]="boto3"
    ["total"]="pdfkit user-agents==2.2.0"
    ["txcdn"]="tencentcloud-sdk-python"
    ["txcos"]="cos-python-sdk-v5"
    ["txeo"]="tencentcloud-sdk-python"
    ["webdav"]="webdav4"
)

# 安装插件包
install_plugin_packages() {
    # 检查pip路径
    local python_path=$1
    local pip_path="$python_path/bin/pip3"
    if [ ! -f "$pip_path" ]; then
        log_error "pip路径错误"
        return 1
    fi

    # 定义插件列表
    plugins=("alidns" "alioss" "aliyun" "aws_s3" "bos" "bt_webhorse" "cosfs" "dnspod"
             "dogecloud" "frp" "gcloud_storage" "gdrive" "gpustat" "jdcloud" "linuxsys"
             "mail_sys" "minio" "monitor" "msonedrive" "obs" "ossfs" "qiniu" "supervisor"
             "sysdisk" "tencentcloud" "tencent" "tianyiyun" "total" "txcdn" "txcos" "txeo" "webdav")

    # 遍历插件
    for plugin in "${plugins[@]}"; do
        plugin_path="$PANEL_PATH/plugin/$plugin"

        # 检查插件目录是否存在
        if [ ! -d "$plugin_path" ]; then
            continue
        fi

        echo "处理插件: $plugin"

        # 获取插件对应的包列表
        packages_key="${plugin}"
        packages="${PLUGIN_PACKAGES[$packages_key]}"

        # 如果没有包定义，跳过
        if [ -z "$packages" ]; then
            continue
        fi

        # 检查是否有特殊参数
        args_key="${plugin}_args"
        args="${PLUGIN_PACKAGES[$args_key]}"

        # 在一条pip命令中处理多个包
        cmd="$pip_path install $packages"
        if [ -n "$args" ]; then
            cmd="$cmd $args"
        fi
        echo "执行命令: $cmd"
        if ! eval $cmd; then
            log_warn "插件[${plugin}]的库安装异常: $package"
        eles
            log_info "插件[${plugin}]的库安装成功: $package"
        fi
    done

    # fail2ban 需要特殊处理
    local fail2ban_path="$PANEL_PATH/plugin/fail2ban"
    if [ -d "$fail2ban_path" ]; then
        log_info "处理插件: fail2ban"
        if command -v apt-get >/dev/null 2>&1; then
            apt-get install libsystemd-dev pkg-config -y
        elif command -v yum >/dev/null 2>&1; then
            yum install systemd-devel pkgconfig -y
        fi
        ${pip_path} install systemd-python

        cp ${fail2ban_path}/fail2ban.tar.gz /tmp/fail2ban.tar.gz
        cd /tmp
        tar -vxf fail2ban.tar.gz
        cd /tmp/fail2ban || return 1
        rm -f /tmp/fail2ban.tar.gz
        ${python_path}/bin/python3 setup.py install
    fi
}


#===============================================================================
# 主函数
#===============================================================================

main() {
    print_separator
    log_info "宝塔面板Python 3.13环境升级脚本开始执行..."
    log_info "编译模式：$([ "$FORCE_COMPILE" == "true" ] && echo "强制使用源码编译" || echo "优先使用预编译包")"
    log_info "环境替换模式：$([ "$USE_SOFTLINK" == "true" ] && echo "软链接方式" || echo "直接替换方式（默认）")"
    print_separator

    # 1. 系统检查
    log_info "步骤1: 系统环境检查"
    check_root_permission
    check_system_architecture
    check_bt_panel
    check_download_tool

    if [ "$ONLY_REPLACE" == "true" ]; then
        log_info "步骤2: 检查已有环境"
        if "$PYTHON_PYENV_NEW/bin/python3.13" --version >/dev/null 2>&1; then
            verify_python_environment
            log_info "Python 3.13环境检查成功"
        else
            Red_Error "Python 3.13环境验证失败"
        fi

        log_info "步骤3: 替换Python环境"
        replace_python_environment

        print_separator
        log_info "宝塔面板Python 3.13环境升级完成！"
        log_info "Python路径: $PYTHON_PYENV/bin/python3.13"
        log_info "虚拟环境: $PYTHON_PYENV"
        log_info "请访问宝塔面板确认升级成功"
        print_separator
        exit 0
    fi

    # 2. 获取下载节点
    log_info "步骤2: 获取下载节点"
    get_node_url

    # 3. 环境准备
    log_info "步骤3: 环境准备"
    install_system_dependencies

    # 4. 安装Python 3.13环境
    log_info "步骤4: Python 3.13环境安装"
    local install_success=0
    
    # 根据安装路线执行相应操作
    if install_precompiled_python; then
        log_info "使用预编译Python环境安装成功"
        install_success=1
    else
        # 源码编译
        log_info "$([ "$FORCE_COMPILE" == "true" ] && echo "按用户要求强制使用源码编译..." || echo "预编译安装失败，开始源码编译...")"
        compile_python_313
        setup_python_environment
        install_success=1
    fi

    if "$PYTHON_PYENV_NEW/bin/python3.13" --version >/dev/null 2>&1; then
        log_info "Python 3.13环境复测成功"
    else
        rm -rf "$PYTHON_PYENV_NEW"
        Red_Error "Python 3.13环境安装验证失败"
    fi

    # 5. 安装Python包（根据安装路线决定是否需要执行）
    case $INSTALL_ROUTE in
        $ROUTE_SYSTEM_SPECIFIC)
            log_info "步骤5: 系统特定预编译包已包含依赖，跳过依赖安装"
            ;;
        $ROUTE_GENERIC|$ROUTE_COMPILE)
            log_info "步骤5: 安装Python依赖包"
            install_python_packages
            modify_python_shebang
            ;;
    esac

    # 6. 安装插件包
    log_info "步骤6: 安装插件包"
    install_plugin_packages "$PYTHON_PYENV_NEW"
    modify_python_shebang

    # 7. 验证环境
    log_info "步骤7: 验证Python环境"
    verify_python_environment

    if [ "$PREPARE_ONLY" == "true" ]; then
        print_separator
        log_info "仅准备环境，跳过环境替换步骤"
        log_info "最新环境存在于: ${PYTHON_PYENV_NEW}"
        return 0
    fi

    # 8. 替换环境
    log_info "步骤8: 替换Python环境"
    replace_python_environment

    print_separator
    log_info "宝塔面板Python 3.13环境升级完成！"
    log_info "Python路径: $PYTHON_PYENV/bin/python3.13"
    log_info "虚拟环境: $PYTHON_PYENV"
    log_info "备份位置: ${PYTHON_PYENV}_backup_* (如果存在)"
    log_info "请访问宝塔面板确认升级成功"
    print_separator
    if [ "$TAR_PYENV_FLAG" == "true" ]; then
        tar_pyenv
    fi
}

# 脚本入口点
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    parse_arguments "$@"
    main
fi