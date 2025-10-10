#!/bin/bash

# 定义要测试的pip源
sources=("https://pypi.tuna.tsinghua.edu.cn/simple" "https://pypi.douban.com/simple" "https://mirrors.aliyun.com/pypi/simple" "https://pypi.org/simple")

# 初始化最快的源和最短的时间
fastest_source=""
shortest_time=4000

# 测试每一个源
for source in ${sources[@]}; do
  # 使用curl命令测试源的速度，并设置超时时间为1秒
  start_time=$(date +%s%N)
  curl -I -o /dev/null -s -w %{time_total} -m 1 $source
  end_time=$(date +%s%N)
  elapsed_time=`expr $end_time - $start_time`
  elapsed_time=`expr $elapsed_time/1000000`

  # 如果这个源的速度比之前的最快速度还要快，那么就更新最快的源和最短的时间
  if (( $elapsed_time < $shortest_time )); then
    fastest_source=$source
    shortest_time=$elapsed_time
  fi
done

# 设置最快的源为当前使用的pip源
btpip config set global.index-url $fastest_source
btpip config set global.trusted-host $(echo $fastest_source | awk -F/ '{print $3}')
btpip config set install.trusted-host $(echo $fastest_source | awk -F/ '{print $3}')

# 打印出最快的源
echo "The fastest pip source is $fastest_source"
