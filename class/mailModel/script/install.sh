#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

pluginPath=/www/server/panel/plugin/mail_sys
pluginStaticPath=/www/server/panel/plugin/mail_sys/static

Get_Public() {
    public_file=/www/server/panel/install/public.sh
    publicFileMd5=$(md5sum ${public_file} 2>/dev/null | awk '{print $1}')
    md5check="8e49712d1fd332801443f8b6fd7f9208"
    if [ "${publicFileMd5}" != "${md5check}" ]; then
        wget -O Tpublic.sh https://download.bt.cn/install/public.sh -T 20
        publicFileMd5=$(md5sum Tpublic.sh 2>/dev/null | awk '{print $1}')
        if [ "${publicFileMd5}" == "${md5check}" ]; then
            \cp -rpa Tpublic.sh $public_file
        fi
        rm -f Tpublic.sh
    fi

    . "${public_file}"

    download_Url=$NODE_URL
}

cpu_arch=$(arch)
if [[ $cpu_arch != "x86_64" ]]; then
    echo 'Does not support non-x86 system installation'
    exit 0
fi
. /etc/os-release

#if [ -f "/usr/bin/apt-get" ]; then
#    systemver='ubuntu'
#elif [ -f "/etc/redhat-release" ]; then
#    systemver7=$(cat /etc/redhat-release | sed -r 's/.* ([0-9]+)\..*/\1/')
#    systemver8=$(cat /etc/redhat-release | sed -r 's/.* ([0-9]+)\..*/\1/' | grep -o '8')
#    postfixver=$(postconf mail_version | sed -r 's/.* ([0-9\.]+)$/\1/')
#elif [ $NAME == "OpenCloudOS" ]; then
#    systemver='opencloudos'
#else
#    echo 'Unsupported system version'
#    exit 0
#fi

check_linux() {
    . /etc/os-release
    if [ $NAME == "OpenCloudOS" ] || [ $ID == "amzn" ]; then
        systemver='opencloudos'
    elif [ $ID == "centos" ]; then
        systemver7=$(cat /etc/redhat-release | sed -r 's/.* ([0-9]+)\..*/\1/')
        systemver8=$(cat /etc/redhat-release | sed -r 's/.* ([0-9]+)\..*/\1/' | grep -o '8')
        postfixver=$(postconf mail_version | sed -r 's/.* ([0-9\.]+)$/\1/')
        systemver='centos'
    elif [ $ID == "almalinux" ]; then
        systemver='almalinux'
    elif [ $ID == "ubuntu" ] || [ $ID == "debian" ]; then
        systemver='ubuntu'
    elif [ $ID == "alinux" ] || [ $ID == "rocky" ]; then
        systemver='alinux'
    else
        echo 'Unsupported system version'
        exit 0
    fi
}
Install_almalinux(){
    if [[ $cpu_arch != "x86_64" ]]; then
        echo 'Does not support non-x86 system installation'
        exit 0
    fi
    yum install epel-release -y
    # 卸载系统自带的postfix
    if [[ $cpu_arch = "x86_64" && $postfixver != "3.4.7" ]]; then
        yum remove postfix -y
        rm -rf /etc/postfix
    fi
    # 安装postfix和postfix-sqlite

    yum install postfix -y
    yum install postfix-sqlite -y
    if [[ ! -f "/usr/sbin/postfix" ]]; then
        echo "postfix3-3.8.3-1.gf.el7.x86_64.rpm安装失败，请联系堡塔官方人员"
        exit 1
    fi
    # 安装dovecot和dovecot-sieve
    yum install dovecot-pigeonhole -y
    if [[ ! -f "/usr/sbin/dovecot" ]]; then
        yum install dovecot -y
    fi
    # 安装rspamd
    install_rspamd
    yum install cyrus-sasl-plain -y
}


Install_opencloudos() {
    if [[ $cpu_arch != "x86_64" ]]; then
        echo 'Does not support non-x86 system installation'
        exit 0
    fi
    yum install epel-release -y
    # 卸载系统自带的postfix
    if [[ $cpu_arch = "x86_64" && $postfixver != "3.4.7" ]]; then
        yum remove postfix -y
        rm -rf /etc/postfix
    fi
    # 安装postfix和postfix-sqlite

    yum install postfix -y
    yum install postfix-sqlite -y
    if [[ ! -f "/usr/sbin/postfix" ]]; then
        echo "postfix3-3.8.3-1.gf.el7.x86_64.rpm安装失败，请联系堡塔官方人员"
        exit 1
    fi
    # 安装dovecot和dovecot-sieve
    yum install dovecot-pigeonhole -y
    if [[ ! -f "/usr/sbin/dovecot" ]]; then
        yum install dovecot -y
    fi
    # 安装rspamd
    install_rspamd


    if ps -ef|grep rspamd|grep -v grep; then
        echo "Rspamd is running."
    else
        compile_rspamd
    fi

    yum install cyrus-sasl-plain -y
}

Install_centos7() {
    if [[ $cpu_arch != "x86_64" ]]; then
        echo 'Does not support non-x86 system installation'
        exit 0
    fi

    yum install epel-release -y
    # 卸载系统自带的postfix
    if [[ $cpu_arch = "x86_64" && $postfixver != "3.4.7" ]]; then
        yum remove postfix -y
        rm -rf /etc/postfix
    fi
    # 安装postfix和postfix-sqlite
    mkdir $pluginPath/rpm
    wget -O $pluginPath/rpm/postfix3-3.8.3-1.gf.el7.x86_64.rpm $download_Url/install/plugin/mail_sys/rpm/postfix3-3.8.3-1.gf.el7.x86_64.rpm -T 5
    wget -O $pluginPath/rpm/postfix3-sqlite-3.8.3-1.gf.el7.x86_64.rpm $download_Url/install/plugin/mail_sys/rpm/postfix3-sqlite-3.8.3-1.gf.el7.x86_64.rpm -T 5
    yum localinstall $pluginPath/rpm/postfix3-3.8.3-1.gf.el7.x86_64.rpm -y
    yum localinstall $pluginPath/rpm/postfix3-sqlite-3.8.3-1.gf.el7.x86_64.rpm -y
    if [[ ! -f "/usr/sbin/postfix" ]]; then
        echo "postfix3-3.8.3-1.gf.el7.x86_64.rpm安装失败，请联系堡塔官方人员"
        exit 1
    fi
    # 安装dovecot和dovecot-sieve
    yum install dovecot-pigeonhole -y
    if [[ ! -f "/usr/sbin/dovecot" ]]; then
        yum install dovecot -y
    fi
    #安装rspamd
    if [ $ping_url != "200" ]; then
        install_rspamd
    else
        install_rspamd
    fi
    yum install cyrus-sasl-plain -y
    # 安装pflogsumm 日志分析工具
    yum install postfix-pflogsumm  -y
}

install_rspamd() {
    # 优先尝试系统源安装并启动
    local installed_ok=0
    if command -v apt-get >/dev/null 2>&1; then
        apt-get update
        if apt-get install -y rspamd; then
            systemctl enable rspamd || true
            systemctl restart rspamd || true
            if systemctl is-active --quiet rspamd && [ -x /usr/bin/rspamd ]; then
                installed_ok=1
            fi
        fi
    else
        if command -v dnf >/dev/null 2>&1; then
            if dnf install -y rspamd; then
                systemctl enable rspamd || true
                systemctl restart rspamd || true
                if systemctl is-active --quiet rspamd && [ -x /usr/bin/rspamd ]; then
                    installed_ok=1
                fi
            fi
        else
            if yum install -y rspamd; then
                systemctl enable rspamd || true
                systemctl restart rspamd || true
                if systemctl is-active --quiet rspamd && [ -x /usr/bin/rspamd ]; then
                    installed_ok=1
                fi
            fi
        fi
    fi

    # 如果系统源安装不可用，则使用官方源安装
    if [ "$installed_ok" != "1" ]; then
        if [[ $systemver7 = "7" ]]; then
            wget -O /etc/yum.repos.d/rspamd.repo https://rspamd.com/rpm-stable/centos-7/rspamd.repo
            rpm --import https://rspamd.com/rpm-stable/gpg.key
            yum makecache -y
            yum install rspamd -y
        elif [ $systemver8 = "8" ] || [ $systemver = "centos" ]; then
            wget -O /etc/yum.repos.d/rspamd.repo https://rspamd.com/rpm-stable/centos-8/rspamd.repo
            rpm --import https://rspamd.com/rpm-stable/gpg.key
            yum makecache -y
            yum install rspamd -y
        elif [ $systemver = "opencloudos" ] || [ $systemver = "alinux" ]; then
            source /etc/os-release
            export EL_VERSION=`echo -n $PLATFORM_ID | sed "s/.*el//"`
            curl https://rspamd.com/rpm-stable/centos-${EL_VERSION}/rspamd.repo > /etc/yum.repos.d/rspamd.repo
            yum install rspamd -y
        elif [ $systemver = "almalinux" ]; then
            source /etc/os-release
            export EL_VERSION=`echo -n $PLATFORM_ID | sed "s/.*el//"`
            curl https://rspamd.com/rpm-stable/centos-${EL_VERSION}/rspamd.repo > /etc/yum.repos.d/rspamd.repo
            yum install rspamd -y
        else
            apt-get install -y lsb-release wget gpg  # for install
            CODENAME=`lsb_release -c -s`
            mkdir -p /etc/apt/keyrings
            wget -O- https://rspamd.com/apt-stable/gpg.key | gpg --dearmor |  tee /etc/apt/keyrings/rspamd.gpg > /dev/null
            echo "deb [signed-by=/etc/apt/keyrings/rspamd.gpg] http://rspamd.com/apt-stable/ $CODENAME main" |  tee /etc/apt/sources.list.d/rspamd.list
            echo "deb-src [signed-by=/etc/apt/keyrings/rspamd.gpg] http://rspamd.com/apt-stable/ $CODENAME main"  |  tee -a /etc/apt/sources.list.d/rspamd.list
            apt-get update
            apt-get --no-install-recommends install rspamd -y
        fi
        systemctl enable rspamd || true
        systemctl restart rspamd || true
        if ! systemctl is-active --quiet rspamd || [ ! -x /usr/bin/rspamd ]; then
            if command -v apt-get >/dev/null 2>&1; then
                echo "官方源安装失败，请检查网络或源配置"
                exit 1
            else
                echo "官方源安装失败，尝试RPM安装..."
                Install_rspamd_rpm
                systemctl enable rspamd || true
                systemctl restart rspamd || true
                if ! systemctl is-active --quiet rspamd || [ ! -x /usr/bin/rspamd ]; then
                    echo "rspamd安装失败，请检查网络或源配置"
                    exit 1
                fi
            fi
        fi
    fi

    # 补充前端资源
    wget -O /usr/share/rspamd/www/rspamd.zip $download_Url/install/plugin/mail_sys/rspamd.zip -T 5
    cd /usr/share/rspamd/www
    unzip -o rspamd.zip
}

Install_rspamd_rpm() {
    if [[ $systemver7 = "7" ]]; then
        wget $download_Url/src/rspamd-3.4-1.x86_64.rpm
        rpm -ivh rspamd-3.4-1.x86_64.rpm
        rm -f rspamd-3.4-1.x86_64.rpm
    elif [[ $systemver8 = "8" ]] || [[ $systemver = "centos" ]]; then
        wget $download_Url/src/rspamd-3.4-1.x86_64.rpm
        rpm -ivh rspamd-3.4-1.x86_64.rpm --nodeps
        rm -f rspamd-3.4-1.x86_64.rpm
    elif [ $systemver = "opencloudos" ] || [ $systemver = "alinux" ]; then
        wget $download_Url/src/rspamd-3.4-1.x86_64.rpm
        rpm -ivh rspamd-3.4-1.x86_64.rpm --nodeps
        rm -f rspamd-3.4-1.x86_64.rpm
    elif [ $systemver = "almalinux" ]; then
        wget $download_Url/src/rspamd-3.4-1.x86_64.rpm
        yum install rspamd-3.4-1.x86_64.rpm
        rm -f rspamd-3.4-1.x86_64.rpm
    else
        apt-get install -y lsb-release wget gpg  # for install
        CODENAME=`lsb_release -c -s`
        mkdir -p /etc/apt/keyrings
        wget -O- https://rspamd.com/apt-stable/gpg.key | gpg --dearmor |  tee /etc/apt/keyrings/rspamd.gpg > /dev/null
        echo "deb [signed-by=/etc/apt/keyrings/rspamd.gpg] http://rspamd.com/apt-stable/ $CODENAME main" |  tee /etc/apt/sources.list.d/rspamd.list
        echo "deb-src [signed-by=/etc/apt/keyrings/rspamd.gpg] http://rspamd.com/apt-stable/ $CODENAME main"  |  tee -a /etc/apt/sources.list.d/rspamd.list
        apt-get update
        apt-get --no-install-recommends install rspamd -y
    fi
    wget -O /usr/share/rspamd/www/rspamd.zip $download_Url/install/plugin/mail_sys/rspamd.zip -T 5
    cd /usr/share/rspamd/www
    unzip -o rspamd.zip
}

compile_rspamd() {
    if [[ $systemver = "opencloudos" ]]; then
        dnf install -y git cmake gcc make gcc-c++ ragel lua lua-devel openssl-devel zlib-devel pcre2-devel glib2-devel libevent-devel libicu-devel sqlite-devel json-c-devel hiredis-devel libcurl-devel libarchive libarchive-devel luajit-devel libsodium-devel
    else
        echo "Unsupported system version"
        exit 0
    fi

    wget -O $pluginPath/rspamd-rspamd-3.8.zip $download_Url/install/plugin/mail_sys/rspamd-rspamd-3.8.zip
    unzip $pluginPath/rspamd-rspamd-3.8.zip -d $pluginPath
    cd $pluginPath/rspamd-rspamd-3.8
    mkdir build
    cd build
    cmake ..  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr
    make
    make install
    mv ../rspamd.service /lib/systemd/system/rspamd.service
    mkdir -p /etc/rspamd
    cp -r /usr/etc/rspamd/ /etc/rspamd/

    useradd -r -M -s /sbin/nologin _rspamd
    mkdir -p /var/log/rspamd
    chown -R _rspamd:_rspamd /var/log/rspamd
    chmod 755 /var/log/rspamd

    systemctl daemon-reload
    systemctl enable rspamd
    systemctl start rspamd
    make clean
    rm -rf $pluginPath/rspamd-rspamd-3.8/
    compile=1

    wget -O /usr/share/rspamd/www/rspamd.zip $download_Url/install/plugin/mail_sys/rspamd.zip -T 5
    cd /usr/share/rspamd/www
    unzip -o rspamd.zip
    }

#获取rspamd网站，检查判断返回是否200
ping_url=$(curl -I -m 10 -o /dev/null -s -w %{http_code}"\n" https://rspamd.com)

Install_centos8() {
    yum install epel-release -y
    # 卸载系统自带的postfix
    if [[ $cpu_arch = "x86_64" && $postfixver != "3.4.9" ]]; then
        yum remove postfix -y
        rm -rf /etc/postfix
    fi
    # 安装postfix和postfix-sqlite
    mkdir $pluginPath/rpm
    wget -O $pluginPath/rpm/postfix3-3.4.9-1.gf.el8.x86_64.rpm $download_Url/install/plugin/mail_sys/rpm/postfix3-3.4.9-1.gf.el8.x86_64.rpm -T 5
    wget -O $pluginPath/rpm/postfix3-sqlite-3.4.9-1.gf.el8.x86_64.rpm $download_Url/install/plugin/mail_sys/rpm/postfix3-sqlite-3.4.9-1.gf.el8.x86_64.rpm -T 5
    yum install $pluginPath/rpm/postfix3-3.4.9-1.gf.el8.x86_64.rpm -y
    yum install $pluginPath/rpm/postfix3-sqlite-3.4.9-1.gf.el8.x86_64.rpm -y
    if [[ ! -f "/usr/sbin/postfix" ]]; then
        yum install postfix -y
        yum install postfix-sqlite -y
    fi
    # 安装dovecot和dovecot-sieve
    yum install dovecot-pigeonhole -y
    if [[ ! -f "/usr/sbin/dovecot" ]]; then
        yum install dovecot -y
    fi
#    Install_rspamd_rpm
    #安装rspamd
    if [ $ping_url != "200" ]; then
        Install_rspamd_rpm
    else
        install_rspamd
    fi
    yum install cyrus-sasl-plain libsodium libwins -y
    # 安装pflogsumm 日志分析工具
    yum install postfix-pflogsumm  -y
}

Install_ubuntu() {
    hostname=$(hostname)
    # 安装postfix和postfix-sqlite
    debconf-set-selections <<<"postfix postfix/mailname string ${hostname}"
    debconf-set-selections <<<"postfix postfix/main_mailer_type string 'Internet Site'"
    apt install postfix -y
    apt install postfix-sqlite -y
    apt install sqlite -y
    # 安装dovecot和dovecot-sieve
    apt install dovecot-core dovecot-pop3d dovecot-imapd dovecot-lmtpd dovecot-sqlite dovecot-sieve -y
    # 安装opendkim
    #  安装rspamd
#    Install_rspamd_rpm
    if [ $ping_url != "200" ]; then
        install_rspamd
    else
        install_rspamd
    fi
    apt install cyrus-sasl-plain libhyperscan5 -y
    # 安装pflogsumm 日志分析工具
    apt install pflogsumm -y
}

Install_redis() {
    if [ ! -f /www/server/redis/src/redis-cli ]; then
        wget -O /tmp/redis.sh $download_Url/install/0/redis.sh -T 5
        sed -i "/gen-test-certs/d" /tmp/redis.sh
        bash /tmp/redis.sh install 7.2

        [ ! -f /www/server/redis/src/redis-cli ] && echo 'Redis installation failed' && return

        # 2024/3/15 上午 10:12 如果密码为空，则默认设置redis密码
        REDIS_CONF="/www/server/redis/redis.conf"
        REDIS_PASS=$(cat ${REDIS_CONF} |grep requirepass|grep -v '#'|awk '{print $2}')
        if [ "${REDIS_PASS}" == "" ]; then
            REDIS_PASS=$(cat /dev/urandom | head -n 16 | md5sum | head -c 16)
            echo "# bt mail redis password"
            echo "requirepass ${REDIS_PASS}" >> ${REDIS_CONF}
            /etc/init.d/redis restart
        fi
    fi
}

check_mail_initialized() {
    # 定义配置文件和服务
    POSTFIX_CONF="/etc/postfix/sqlite_virtual_domains_maps.cf"
#    POSTFIX_MAIN_CF="/etc/postfix/main.cf"
    POSTFIX_MYDESTINATION=$(postconf mydestination | awk '{print $2}')
    DOVECOT_CONF="/etc/dovecot/dovecot.conf"
    DOVECOT_SERVICE="dovecot"

    # 检查 Postfix 是否已初始化
    if [ -f "$POSTFIX_CONF" ]; then
        echo "Postfix 配置文件 $POSTFIX_CONF 存在。"

        # 检查 Postfix 是否已初始化：检查 mydestination 配置项
        if [ -z "$POSTFIX_MYDESTINATION" ]; then
            echo "Postfix 尚未初始化，mydestination 配置项未设置。"
            return 1
        else
            echo "Postfix 已初始化，mydestination 配置项已设置为: $POSTFIX_MYDESTINATION"
        fi

        # 检查 Postfix 服务是否正在运行
        if systemctl is-active --quiet postfix; then
            echo "Postfix 服务正在运行。"
        else
            echo "Postfix 服务未运行，请检查 Postfix 配置并启动服务。"
            return 1
        fi
    else
        echo "Postfix 尚未安装或初始化。"
        return 1
    fi

    # 检查 Dovecot 是否已初始化
    if [ -f "$DOVECOT_CONF" ]; then
        echo "Dovecot 配置文件 $DOVECOT_CONF 存在。"

        # 检查 Dovecot 是否启用了 IMAP 协议
        if grep -q "protocols = imap" "$DOVECOT_CONF"; then
            echo "Dovecot 已初始化并启用了 IMAP 协议。"
        else
            echo "Dovecot 配置中没有启用 IMAP 协议。"
            return 1
        fi

        # 检查 Dovecot 服务是否正在运行
        if systemctl is-active --quiet "$DOVECOT_SERVICE"; then
            echo "Dovecot 服务正在运行。"
        else
            echo "Dovecot 服务未运行，请检查 Dovecot 配置并启动服务。"
            return 1
        fi
    else
        echo "Dovecot 尚未安装或初始化。"
        return 1
    fi

    # 如果所有检查通过，初始化成功
    echo "邮局系统已经初始化并正常运行。"
    exit 1
}

Install() {
    check_linux
    Get_Public
    mkdir -p $pluginPath
    mkdir -p $pluginStaticPath

    check_mail_initialized

    if [[ $systemver7 = "7" ]]; then
        Install_centos7
    elif [[ $systemver8 = "8" ]]; then
        Install_centos8
    elif [ $systemver = "centos" ]; then
        Install_centos7
    elif [[ $systemver = "opencloudos" ]]; then
        Install_opencloudos
    elif [[ $systemver = "alinux" ]]; then
        Install_centos7
    elif [[ $systemver = "almalinux" ]]; then
        Install_almalinux
    else
        Install_ubuntu
    fi

    # 安装dovecot和dovecot-sieve
    if [ ! -f /etc/dovecot/conf.d/90-sieve.conf ]; then
        if [ -f "/usr/bin/apt-get" ]; then
            apt install dovecot-sieve -y
        else
            rm -rf /etc/dovecot_back
            cp -a /etc/dovecot /etc/dovecot_back
            yum remove dovecot -y
            yum install dovecot-pigeonhole -y
            if [ ! -f /usr/sbin/dovecot ]; then
                yum install dovecot -y
            fi
            \cp -a /etc/dovecot_back/* /etc/dovecot
            chown -R vmail:dovecot /etc/dovecot
            chmod -R o-rwx /etc/dovecot

            systemctl enable dovecot
            systemctl restart dovecot
        fi
    fi

    filesize=$(ls -l /etc/dovecot/dh.pem | awk '{print $5}')
    echo $filesize

    if [ ! -f "/etc/dovecot/dh.pem" ] || [ $filesize -lt 300 ]; then
        openssl dhparam 2048 >/etc/dovecot/dh.pem
    fi

    if [ ! -d "/www/server/panel/BTPanel/static/ckeditor" ]; then
        unzip $pluginPath/ckeditor.zip -d /www/server/panel/BTPanel/static
    fi

    # 2024/3/15 上午 10:14 安装redis
    Install_redis

    # 2024/3/15 下午 3:49 运行邮局初始化
    /www/server/panel/pyenv/bin/python3.7 $pluginPath/mail_server_init.py setup_mail_sys

    # 2024/3/15 下午 10:26 处理因权限问题无法接收邮件
    if [ ! -d "/www/vmail" ]; then
        mkdir -p /www/vmail
    fi
    chmod -R 770 /www/vmail
    chown -R vmail:mail /www/vmail

    echo 'Successify'
}

#卸载
Uninstall() {
    if [[ $systemver7 = "7" ]]; then
        yum remove postfix -y
        yum remove dovecot -y
        yum remove opendkim -y
        yum remove rspamd -y
        yum remove dovecot-pigeonhole -y
    elif [ $systemver8 = "8" ] || [ $systemver = "opencloudos" ] || [ $systemver = "alinux" ]; then
        yum remove postfix -y
        yum remove dovecot -y
        yum remove opendkim -y
        yum remove rspamd -y
        yum remove dovecot-pigeonhole -y
    else
        apt remove postfix postfix-sqlite -y && rm -rf /etc/postfix
        dpkg -P postfix postfix-sqlite
        apt remove dovecot-core dovecot-imapd dovecot-lmtpd dovecot-pop3d dovecot-sqlite dovecot-sieve -y
        dpkg -P dovecot-core dovecot-imapd dovecot-lmtpd dovecot-pop3d dovecot-sqlite dovecot-sieve
        apt remove opendkim opendkim-tools -y
        dpkg -P opendkim opendkim-tools
        apt remove rspamd -y
        dpkg -P rspamd
    fi

    rm -rf /etc/postfix
    rm -rf /etc/dovecot
    rm -rf /etc/opendkim
    rm -rf /usr/share/rspamd/www/rspamd
    rm -rf $pluginPath
    echo 'Successify'
}

#检查rspamd服务是否安装，不存在则rpm包安装
check_rspamd() {
    if [ ! -f /usr/bin/rspamd ]; then
        install_rspamd
    fi
}

#check_rspamd
#操作判断
if [ "${1}" == 'install' ]; then
    Install
    echo '1' >/www/server/panel/data/reload.pl
elif [ "${1}" == 'update' ]; then
    Update
elif [ "${1}" == 'uninstall' ]; then
    Uninstall
elif [ "${1}" == 'rspamd' ]; then
    Get_Public
    check_linux
    install_rspamd
fi
