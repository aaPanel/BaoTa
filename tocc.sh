#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
LANG=en_US.UTF-8

cd /www/server/panel
rm -f class/plugin2.so class/plugin3.so
python code_v.py
python36 code_v.py
python3.4 code_v.py