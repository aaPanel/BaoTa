#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

is_flask1=$(/www/server/panel/pyenv/bin/python3 -c "import flask;print(flask.__version__)"|grep -E '^1')
if [ "${is_flask1}" = "" ];then
    exit;
fi

/www/server/panel/pyenv/bin/pip3 install flask -U
/www/server/panel/pyenv/bin/pip3 install flask-sock
bash /www/server/panel/init.sh reload
rm -f /www/server/panel/script/upgrade_flask.sh
