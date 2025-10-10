#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "用法: $0 <类型> <秒数> <cron名称>"
    exit 1
fi

type=$1
second=$2
cronName=$3
cronFile="/www/server/cron/$cronName"

echo "当前参数: 类型=$type, 秒数=$second, cron名称=$cronName"
echo "Cron文件路径: $cronFile"

# 删除现有的特定btpython调用的整个if块
echo "尝试删除现有的btpython调用块..."
sed -i '/if \[\[ \$1 != "start" \]\]/{:a;N;/fi/!ba;/btpython \/www\/server\/panel\/script\/second_task.py [0-9]* '"$cronName"'/d}' "$cronFile"
sed_status=$?
echo "sed删除操作完成，状态码: $sed_status"

# 检查是否满足条件以添加新的调用
if [[ $type == "second-n" && -n "$second" ]]; then
    echo "在'second-n'类型条件下添加新的btpython调用..."
    # 在特定位置插入新的调用
    sed -i "/^export PATH/a \
if [[ \$1 != \"start\" ]]; then\n\
    btpython /www/server/panel/script/second_task.py $second $cronName\n\
    exit 0\n\
fi" "$cronFile"
    add_status=$?
    echo "sed添加操作完成，状态码: $add_status"
else
    echo "不需要操作，因为类型是 $type 或秒数为空"
fi

echo "脚本执行完毕。"
