#!/bin/bash
pyversion=${1}
py_path=/www/server/pyporject_evn/versions
py_cache=/www/server/pyporject_evn/versions/cached
cpuCore=$(cat /proc/cpuinfo |grep "physical id"|sort |uniq|wc -l)

mkdir -p ${py_path}
download_Url='https://download.bt.cn'

install_python() {
  \cp ${py_cache}/Python-${pyversion}.tar.xz /tmp/Python-${pyversion}.tar.xz
  cd /tmp/ && xz -d /tmp/Python-${pyversion}.tar.xz && tar -xvf /tmp/Python-${pyversion}.tar
  cd /tmp/Python-${pyversion} || exit
  if [ ${pyversion:0:1} -ge 2 ]; then
    openssl111check=$(openssl version | grep 1.1.1)
    if [ -z "${openssl111check}" ]; then
      Install_Openssl111
      WITH_SSL="--with-openssl=/usr/local/openssl111"
    else
      WITH_SSL=""
    fi
    cd /tmp/Python-${pyversion} || exit
    ./configure --prefix=${py_path}/${pyversion} ${WITH_SSL} -with-openssl-rpath=auto
    make -j${cpuCore}
    make install
    rm -rf /tmp/Python-*
  else
    ./configure --prefix=${py_path}/${pyversion}
    make -j${cpuCore}
    make install
    rm -rf /tmp/Python-*
  fi
}

Install_Openssl111() {
  opensslCheck=$(/usr/local/openssl111/bin/openssl version | grep 1.1.1)
  if [ -z "${opensslCheck}" ]; then
    opensslVersion="1.1.1o"
    cd /tmp/
    wget ${download_Url}/src/openssl-${opensslVersion}.tar.gz
    tar -zxf openssl-${opensslVersion}.tar.gz
    rm -f openssl-${opensslVersion}.tar.gz
    cd openssl-${opensslVersion} || exit
    ./config --prefix=/usr/local/openssl111 zlib-dynamic
    make -j${cpuCore}
    make install
    echo "/usr/local/openssl111/lib" >>/etc/ld.so.conf.d/openssl111.conf
    ldconfig
    ldconfig /lib64
    cd ..
    rm -rf openssl-${opensslVersion}
  fi
}

install_python
