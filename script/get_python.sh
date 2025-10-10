#!/bin/bash

pyversion=${1}
download_Url=${2}
vpath=${3}
py_path=/www/server/pyporject_evn/versions
mkdir -p ${py_path}

install_python() {
  wget -O /tmp/Python-${pyversion}.tar.xz ${download_Url}/src/Python-${pyversion}.tar.xz
  cd /tmp/ && xz -d /tmp/Python-${pyversion}.tar.xz && tar -xvf /tmp/Python-${pyversion}.tar && cd /tmp/Python-${pyversion}
  if [ ${pyversion:2:2} -ge 10 ]; then
    openssl111check=$(openssl version | grep 1.1.1)
    if [ -z "${openssl111check}" ]; then
      Install_Openssl111
      WITH_SSL="--with-openssl=/usr/local/openssl111"
    else
      WITH_SSL=""
    fi
    cd /tmp/Python-${pyversion}
    ./configure --prefix=${py_path}/${pyversion} ${WITH_SSL} -with-openssl-rpath=auto
    make && make install
    rm -rf /tmp/Python-*
  else
    ./configure --prefix=${py_path}/${pyversion}
    make && make install
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
    cd openssl-${opensslVersion}
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

install_pip() {
  cd ${vpath}
  wget -O get-pip.py http://dg1.bt.cn/install/plugin/pythonmamager/pip/get-pip${pyversion:0:3}.py
  if [ -f ${vpath}/bin/python ]; then
    bin/python get-pip.py
  else
    bin/python3 get-pip.py
  fi
}

if [ "${vpath}" == "" ]; then
  install_python
else
  install_pip
fi
