#!/bin/bash

# 确保输出是纯JSON，不包含其他信息
export LANG=C
export LC_ALL=C

# 定义临时文件路径
NETWORK_DATA_FILE="/tmp/system_network_data_$(id -u).json"

# 收集网络接口数据并计算速率
collect_network() {
  result="{"
  first=true
  current_time=$(date +%s)

  # 读取之前的数据（如果存在）
  prev_data=""
  prev_time=0
  if [ -f "$NETWORK_DATA_FILE" ]; then
    prev_data=$(cat "$NETWORK_DATA_FILE")
    prev_time=$(echo "$prev_data" | grep -o '"time": [0-9]*' | head -1 | awk '{print $2}')
    [ -z "$prev_time" ] && prev_time=0
  fi

  # 创建临时存储当前数据的文件
  temp_current_data="/tmp/system_network_current_$(id -u).json"
  echo "{\"time\": $current_time," > "$temp_current_data"

  # 计算时间间隔（秒）
  time_diff=1
  if [ $prev_time -ne 0 ]; then
    time_diff=$((current_time - prev_time))
    [ $time_diff -le 0 ] && time_diff=1  # 防止除以零
  fi

  # 收集所有网络接口的信息
  for iface in $(ls /sys/class/net/ | grep -v "lo"); do
    if [ "$first" = true ]; then
      first=false
      echo "\"interfaces\": {" >> "$temp_current_data"
    else
      result+=","
      echo "," >> "$temp_current_data"
    fi

    # 读取当前网络接口统计
    rx_bytes=$(cat /sys/class/net/$iface/statistics/rx_bytes 2>/dev/null || echo 0)
    tx_bytes=$(cat /sys/class/net/$iface/statistics/tx_bytes 2>/dev/null || echo 0)
    rx_packets=$(cat /sys/class/net/$iface/statistics/rx_packets 2>/dev/null || echo 0)
    tx_packets=$(cat /sys/class/net/$iface/statistics/tx_packets 2>/dev/null || echo 0)

    # 保存当前数据到临时文件
    echo "\"$iface\": {\"rx_bytes\": $rx_bytes, \"tx_bytes\": $tx_bytes, \"rx_packets\": $rx_packets, \"tx_packets\": $tx_packets}" >> "$temp_current_data"

    # 计算速率（如果有之前的数据）
    down_speed=0
    up_speed=0

    if [ -n "$prev_data" ]; then
      # 提取之前的数据
      prev_rx_bytes=$(echo "$prev_data" | grep -o "\"$iface\".*rx_bytes.*tx_bytes" | grep -o "rx_bytes\": [0-9]*" | awk '{print $2}')
      prev_tx_bytes=$(echo "$prev_data" | grep -o "\"$iface\".*tx_bytes.*rx_packets" | grep -o "tx_bytes\": [0-9]*" | awk '{print $2}')

      # 如果找到了之前的数据，计算速率
      if [ -n "$prev_rx_bytes" ] && [ -n "$prev_tx_bytes" ]; then
        # 计算差值
        rx_diff=$((rx_bytes - prev_rx_bytes))
        tx_diff=$((tx_bytes - prev_tx_bytes))

        # 确保值不是负数（可能由于系统重启计数器重置）
        [ $rx_diff -lt 0 ] && rx_diff=0
        [ $tx_diff -lt 0 ] && tx_diff=0

        # 安全地计算速率
        down_speed=$(awk "BEGIN {printf \"%.2f\", $rx_diff / $time_diff / 1024}")
        up_speed=$(awk "BEGIN {printf \"%.2f\", $tx_diff / $time_diff / 1024}")
      fi
    fi

    # 添加接口信息到结果
    result+=$(cat << EOF
"$iface": {
  "down": $down_speed,
  "up": $up_speed,
  "downTotal": $rx_bytes,
  "upTotal": $tx_bytes,
  "downPackets": $rx_packets,
  "upPackets": $tx_packets
}
EOF
)
  done

  # 完成当前数据文件
  if [ "$first" = false ]; then
    echo "}" >> "$temp_current_data"
  else
    echo "\"interfaces\": {}" >> "$temp_current_data"
  fi
  echo "}" >> "$temp_current_data"

  # 移动临时文件到持久文件位置
  mv "$temp_current_data" "$NETWORK_DATA_FILE"

  result+="}"
  echo "$result"
}

# 收集总体网络统计
collect_total_network() {
  current_time=$(date +%s)

  # 初始化计数器
  down_total=0
  up_total=0
  down_packets=0
  up_packets=0
  down_speed=0
  up_speed=0

  # 读取之前的数据（如果存在）
  prev_data=""
  prev_time=0

  if [ -f "$NETWORK_DATA_FILE" ]; then
    prev_data=$(cat "$NETWORK_DATA_FILE")
    prev_time=$(echo "$prev_data" | grep -o '"time": [0-9]*' | head -1 | awk '{print $2}')
    [ -z "$prev_time" ] && prev_time=0
  fi

  # 计算时间间隔（秒）
  time_diff=1
  if [ $prev_time -ne 0 ]; then
    time_diff=$((current_time - prev_time))
    [ $time_diff -le 0 ] && time_diff=1  # 防止除以零
  fi

  # 收集当前总流量
  for iface in $(ls /sys/class/net/ | grep -v "lo"); do
    # 读取当前网络接口统计
    rx_bytes=$(cat /sys/class/net/$iface/statistics/rx_bytes 2>/dev/null || echo 0)
    tx_bytes=$(cat /sys/class/net/$iface/statistics/tx_bytes 2>/dev/null || echo 0)
    rx_packets=$(cat /sys/class/net/$iface/statistics/rx_packets 2>/dev/null || echo 0)
    tx_packets=$(cat /sys/class/net/$iface/statistics/tx_packets 2>/dev/null || echo 0)

    # 累加当前总量
    down_total=$((down_total + rx_bytes))
    up_total=$((up_total + tx_bytes))
    down_packets=$((down_packets + rx_packets))
    up_packets=$((up_packets + tx_packets))
  done

  # 收集之前的总流量
  if [ -f "$NETWORK_DATA_FILE" ]; then
    for iface in $(ls /sys/class/net/ | grep -v "lo"); do
      # 提取之前的数据
      iface_prev_rx=$(echo "$prev_data" | grep -o "\"$iface\".*rx_bytes.*tx_bytes" | grep -o "rx_bytes\": [0-9]*" | awk '{print $2}')
      iface_prev_tx=$(echo "$prev_data" | grep -o "\"$iface\".*tx_bytes.*rx_packets" | grep -o "tx_bytes\": [0-9]*" | awk '{print $2}')

      # 累加总流量
      if [ -n "$iface_prev_rx" ]; then
        prev_down_total=$((prev_down_total + iface_prev_rx))
      fi
      if [ -n "$iface_prev_tx" ]; then
        prev_up_total=$((prev_up_total + iface_prev_tx))
      fi
    done
  fi

  # 计算总体速率
  if [ $prev_time -ne 0 ]; then
    rx_diff=$((down_total - prev_down_total))
    tx_diff=$((up_total - prev_up_total))

    # 确保值不是负数
    [ $rx_diff -lt 0 ] && rx_diff=0
    [ $tx_diff -lt 0 ] && tx_diff=0

    down_speed=$(awk "BEGIN {printf \"%.2f\", $rx_diff / $time_diff/ 1024}")
    up_speed=$(awk "BEGIN {printf \"%.2f\", $tx_diff / $time_diff/ 1024}")
  fi

  # 返回结果
  cat << EOF
{
  "down": $down_speed,
  "up": $up_speed,
  "downPackets": $down_packets,
  "upPackets": $up_packets,
  "downTotal": $down_total,
  "upTotal": $up_total
}
EOF
}

# 收集CPU信息
collect_cpu() {
  # 定义临时文件路径（使用 mktemp 提高安全性）
  CPU_DATA_FILE="/tmp/system_cpu_data_$(id -u).json"
  TEMP_CURRENT_DATA=$(mktemp "/tmp/system_cpu_current_XXXXXXX.json")

  # 初始化返回值
  local current_time
  current_time=$(date +%s)

  # 读取当前CPU统计信息
  local current_cpu_stat
  if ! current_cpu_stat=$(cat /proc/stat | grep '^cpu ' | awk '{
    user_nice_system = ($2 + $3 + $4) + 0
    idle = $5 + 0
    total = (user_nice_system + idle + ($6 + 0) + ($7 + 0) + ($8 + 0))
    printf "%d,%d,%d", user_nice_system, idle, total
  }'); then
    echo "无法读取CPU统计信息" >&2
    return 1
  fi
  local current_user_time=$(echo "$current_cpu_stat" | cut -d',' -f1)
  local current_idle_time=$(echo "$current_cpu_stat" | cut -d',' -f2)
  local current_total_time=$(echo "$current_cpu_stat" | cut -d',' -f3)

  # 收集各核心当前统计信息
  local core_stats=()
  while read -r line; do
    if [[ $line =~ ^cpu[0-9]+ ]]; then
      local core_stat=$(echo "$line" | awk '{printf "%d,%d,%d", $2+$3+$4+$6+$7+$8, $5, $2+$3+$4+$5+$6+$7+$8}')
      core_stats+=("$core_stat")
    fi
  done < /proc/stat

  # 读取之前的数据（如果存在）
  local prev_data=""
  local prev_time=0
  local prev_user_time=0
  local prev_idle_time=0
  local prev_total_time=0
  local prev_core_stats=()

  if [[ -f "$CPU_DATA_FILE" ]]; then
    if ! prev_data=$(cat "$CPU_DATA_FILE"); then
      echo "无法读取历史CPU数据" >&2
      return 1
    fi

    prev_time=$(echo "$prev_data" | grep -o '"time": [0-9]*' | head -1 | awk '{print $2}')
    prev_user_time=$(echo "$prev_data" | grep -o '"user_time": [0-9]*' | head -1 | awk '{print $2}')
    prev_idle_time=$(echo "$prev_data" | grep -o '"idle_time": [0-9]*' | head -1 | awk '{print $2}')
    prev_total_time=$(echo "$prev_data" | grep -o '"total_time": [0-9]*' | head -1 | awk '{print $2}')

    # 使用 awk 跨行匹配核心数据
    local i=0
    while true; do
      local core_data
      core_data=$(echo "$prev_data" | awk -v core="core_$i" '
        $0 ~ "\"" core "\": {" {flag=1; print; next}
        flag && /}/ {print; flag=0; exit}
        flag {print}
      ')

      if [[ -z "$core_data" ]]; then
        break
      fi

      local core_user_time=$(echo "$core_data" | grep -o '"user_time": [0-9]*' | awk '{print $2}')
      local core_idle_time=$(echo "$core_data" | grep -o '"idle_time": [0-9]*' | awk '{print $2}')
      local core_total_time=$(echo "$core_data" | grep -o '"total_time": [0-9]*' | awk '{print $2}')

      prev_core_stats+=("$core_user_time,$core_idle_time,$core_total_time")
      ((i++))
    done
  fi

  # 计算时间间隔（秒）
  local time_diff=$((current_time - prev_time))
  ((time_diff <= 0)) && time_diff=1  # 防止除以零

  # 计算总CPU使用率
  local cpu_usage=0
  if ((prev_total_time > 0)); then
    local user_diff=$((current_user_time - prev_user_time))
    local total_diff=$((current_total_time - prev_total_time))

    # 防止负值（可能由于系统重启导致计数器重置）
    ((user_diff < 0)) && user_diff=0
    ((total_diff < 0)) && total_diff=0

    if ((total_diff > 0)); then
      cpu_usage=$(awk "BEGIN {printf \"%.2f\", ($user_diff / $total_diff) * 100}")
    fi
  fi

  # 获取逻辑核心数
  local logical_cores
  logical_cores=$(nproc 2>/dev/null || getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)

  # 计算每个核心的使用率
  local cpu_cores_usage="["
  local first=true
  local i=0

  for core_stat in "${core_stats[@]}"; do
    local core_user_time=$(echo "$core_stat" | cut -d',' -f1)
    local core_idle_time=$(echo "$core_stat" | cut -d',' -f2)
    local core_total_time=$(echo "$core_stat" | cut -d',' -f3)

    local core_usage=0
    if ((i < ${#prev_core_stats[@]})); then
      local prev_core_stat=${prev_core_stats[$i]}
      local prev_core_user_time=$(echo "$prev_core_stat" | cut -d',' -f1)
      local prev_core_idle_time=$(echo "$prev_core_stat" | cut -d',' -f2)
      local prev_core_total_time=$(echo "$prev_core_stat" | cut -d',' -f3)

      local core_user_diff=$((core_user_time - prev_core_user_time))
      local core_total_diff=$((core_total_time - prev_core_total_time))

      # 防止负值
      ((core_user_diff < 0)) && core_user_diff=0
      ((core_total_diff < 0)) && core_total_diff=0

      if ((core_total_diff > 0)); then
        core_usage=$(awk "BEGIN {printf \"%.2f\", ($core_user_diff / $core_total_diff) * 100}")
      fi
    fi

    if [[ "$first" == true ]]; then
      first=false
    else
      cpu_cores_usage+=","
    fi

    cpu_cores_usage+="$core_usage"
    ((i++))
  done

  cpu_cores_usage+="]"

  # 获取CPU名称（优先使用lscpu）
  local cpu_name
  if command -v lscpu >/dev/null 2>&1; then
    cpu_name=$(lscpu | grep "Model name" | head -n 1 | cut -d':' -f2 | sed 's/^[[:space:]]*//')
  else
    cpu_name=$(grep "model name" /proc/cpuinfo | head -n 1 | cut -d':' -f2 | sed 's/^[[:space:]]*//')
  fi

  # 获取核心数（优先使用lscpu）
  local physical_cores=1
  local physical_cpus=1
  if command -v lscpu >/dev/null 2>&1; then
    physical_cores=$(lscpu | grep "Core(s) per socket" | awk '{print $4}')
    physical_cpus=$(lscpu | grep "Socket(s)" | awk '{print $2}')
  else
    # 备用方法：解析/proc/cpuinfo
    physical_cpus=$(grep "physical id" /proc/cpuinfo | sort -u | wc -l)
    physical_cores=$(grep "cpu cores" /proc/cpuinfo | head -1 | awk '{print $4}')

    # 如果无法获取核心数，计算保守估算
    if [[ -z "$physical_cores" ]]; then
      physical_cores=$(( logical_cores / physical_cpus ))
    fi
  fi

  # 确保变量有值
  [[ -z "$physical_cores" ]] && physical_cores=1
  [[ -z "$physical_cpus" ]] && physical_cpus=1

  # 保存当前CPU统计信息到临时文件用于下次比较
  {
    echo "{"
    echo "  \"time\": $current_time,"
    echo "  \"user_time\": $current_user_time,"
    echo "  \"idle_time\": $current_idle_time,"
    echo "  \"total_time\": $current_total_time,"

    # 保存每个核心的统计信息
    local i=0
    for core_stat in "${core_stats[@]}"; do
      local core_user_time=$(echo "$core_stat" | cut -d',' -f1)
      local core_idle_time=$(echo "$core_stat" | cut -d',' -f2)
      local core_total_time=$(echo "$core_stat" | cut -d',' -f3)

      echo "  \"core_$i\": {"
      echo "    \"user_time\": $core_user_time,"
      echo "    \"idle_time\": $core_idle_time,"
      echo "    \"total_time\": $core_total_time"

      if ((i < ${#core_stats[@]} - 1)); then
        echo "  },"
      else
        echo "  }"
      fi

      ((i++))
    done

    echo "}"
  } > "$TEMP_CURRENT_DATA"

  # 原子性替换文件
  if ! mv "$TEMP_CURRENT_DATA" "$CPU_DATA_FILE"; then
    echo "无法保存CPU数据到 $CPU_DATA_FILE" >&2
    rm -f "$TEMP_CURRENT_DATA"
    return 1
  fi

  # 返回格式化的结果
  echo "[$cpu_usage, $logical_cores, $cpu_cores_usage, \"$cpu_name\", $physical_cores, $physical_cpus]"
}

# 收集CPU时间
collect_cpu_times() {
  # 获取CPU时间
  cpu_line=$(cat /proc/stat | grep '^cpu ' | awk '{print $2,$3,$4,$5,$6,$7,$8,$9,$10,$11}')
  read -r user nice system idle iowait irq softirq steal guest guest_nice <<< "$cpu_line"

  # 获取进程信息
  total_processes=$(ps -e | wc -l)
  active_processes=$(ps -eo stat | grep -c "R")

  cat << EOF
{
  "user": $user,
  "nice": $nice,
  "system": $system,
  "idle": $idle,
  "iowait": $iowait,
  "irq": $irq,
  "softirq": $softirq,
  "steal": $steal,
  "guest": $guest,
  "guest_nice": $guest_nice,
  "总进程数": $total_processes,
  "活动进程数": $active_processes
}
EOF
}

# 收集磁盘信息
collect_disk() {
  df_output=$(df -TPB1 -x tmpfs -x devtmpfs | tail -n +2 | grep -vE "/boot\$" | grep -vE "docker/overlay2")

  result="["
  first=true

  while read -r filesystem type total used avail pcent mountpoint; do
    if [ "$first" = true ]; then
      first=false
    else
      result+=","
    fi

    size_bytes=$total
    size_used=$used
    size_avail=$avail

    # 格式化为人类可读大小（使用单独的awk命令处理每个值）
    size_human=$(echo "$size_bytes" | awk '{
      suffix="BKMGT"; value=$1;
      for(i=1; value>=1024 && i<length(suffix); i++) value/=1024;
      printf("%.2f%s", value, substr(suffix,i,1));
    }')

    size_used_human=$(echo "$size_used" | awk '{
      suffix="BKMGT"; value=$1;
      for(i=1; value>=1024 && i<length(suffix); i++) value/=1024;
      printf("%.2f%s", value, substr(suffix,i,1));
    }')

    size_avail_human=$(echo "$size_avail" | awk '{
      suffix="BKMGT"; value=$1;
      for(i=1; value>=1024 && i<length(suffix); i++) value/=1024;
      printf("%.2f%s", value, substr(suffix,i,1));
    }')

    # 收集inode信息
    inode_info=$(df -i | grep -E "$mountpoint\$" | awk '{print $2,$3,$4,$5}')
    read -r itotal iused iavail ipcent <<< "$inode_info"

    # 确保inode值不为空
    [ -z "$itotal" ] && itotal=0
    [ -z "$iused" ] && iused=0
    [ -z "$iavail" ] && iavail=0
    [ -z "$ipcent" ] && ipcent="0%"

    result+=$(cat << EOF
{
  "filesystem": "$filesystem",
  "types": "$type",
  "path": "$mountpoint",
  "rname": "$(basename "$mountpoint")",
  "byte_size": [$size_bytes, $size_used, $size_avail],
  "size": ["$size_human", "$size_used_human", "$size_avail_human"],
  "d_size": "$pcent",
  "inodes": [$itotal, $iused, $iavail, "$ipcent"]
}
EOF
)
  done <<< "$df_output"

  result+="]"
  echo "$result"
}

# 收集IO统计
collect_iostat() {
  result="{"
  first=true

  disks=$(ls /sys/block/ 2>/dev/null | grep -E '^(sd|hd|vd|nvme)' 2>/dev/null || echo "")

  for disk in $disks; do
    if [ -r "/sys/block/$disk/stat" ]; then
      if [ "$first" = true ]; then
        first=false
      else
        result+=","
      fi

      # 读取磁盘统计信息
      disk_stats=$(cat /sys/block/$disk/stat 2>/dev/null)
      if [ -n "$disk_stats" ]; then
        # 使用默认值以防读取失败
        read_comp=0 read_merged=0 read_sectors=0 read_ms=0 write_comp=0 write_merged=0 write_sectors=0 write_ms=0 io_in_progress=0 io_ms_weighted=0

        # 尝试读取值
        read read_comp read_merged read_sectors read_ms write_comp write_merged write_sectors write_ms io_in_progress io_ms_weighted <<< "$disk_stats"

        # 转换扇区为字节 (512字节为一个扇区)
        read_bytes=$((read_sectors * 512))
        write_bytes=$((write_sectors * 512))

        result+=$(cat << EOF
"$disk": {
  "read_count": $read_comp,
  "read_merged_count": $read_merged,
  "read_bytes": $read_bytes,
  "read_time": $read_ms,
  "write_count": $write_comp,
  "write_merged_count": $write_merged,
  "write_bytes": $write_bytes,
  "write_time": $write_ms
}
EOF
)
      fi
    fi
  done

  result+="}"
  echo "$result"
}

# 收集负载信息
collect_load() {
  load_avg=$(cat /proc/loadavg)
  read -r one five fifteen others <<< "$load_avg"

  cpu_count=$(nproc)
  max_load=$((cpu_count * 2))

  # 安全计算安全负载
  safe_load=$(awk "BEGIN {printf \"%.2f\", $max_load * 0.7}")

  cat << EOF
{
  "one": $one,
  "five": $five,
  "fifteen": $fifteen,
  "max": $max_load,
  "limit": $cpu_count,
  "safe": $safe_load
}
EOF
}

# 收集内存信息
collect_mem() {
  mem_info=$(cat /proc/meminfo)

  # 提取内存数据 (单位: KB)
  mem_total=$(awk '/^MemTotal/ {print $2; exit}' <<< "$mem_info" || echo 0)
  mem_free=$(awk '/^MemFree/ {print $2; exit}' <<< "$mem_info" || echo 0)
  mem_available=$(awk '/^MemAvailable/ {print $2; exit}' <<< "$mem_info" || echo "$mem_free")
  mem_buffers=$(awk '/^Buffers/ {print $2; exit}' <<< "$mem_info" || echo 0)
  mem_cached=$(awk '/^Cached:/ {print $2; exit}' <<< "$mem_info" || echo 0)
  mem_sreclaimable=$(awk '/^SReclaimable:/ {print $2; exit}' <<< "$mem_info" || echo 0)
  mem_buffers=$(awk '/^Buffers:/ {print $2; exit}' <<< "$mem_info" || echo 0)
  mem_shared=$(awk '/^Shmem/ {print $2; exit}' <<< "$mem_info" || echo 0)

  # 确保数值有效
  [ -z "$mem_total" ] && mem_total=0
  [ -z "$mem_free" ] && mem_free=0
  [ -z "$mem_available" ] && mem_available=0
  [ -z "$mem_buffers" ] && mem_buffers=0
  [ -z "$mem_cached" ] && mem_cached=0
  [ -z "$mem_shared" ] && mem_shared=0
  [ -z "$mem_sreclaimable" ] && mem_sreclaimable=0
  [ -z "$mem_buffers" ] && mem_buffers=0

  # 安全计算实际使用的内存
  mem_real_used=$((mem_total - mem_free - mem_buffers - mem_cached - mem_sreclaimable - mem_buffers))
  [ $mem_real_used -lt 0 ] && mem_real_used=0

  # 转换为人类可读格式（单独处理每个值）
  mem_new_total=$(awk -v bytes="$((mem_total * 1024))" 'BEGIN {
    suffix="BKMGT"; value=bytes;
    for(i=1; value>=1024 && i<length(suffix); i++) value/=1024;
    printf("%.2f%s", value, substr(suffix,i,1));
  }')

  mem_new_real_used=$(awk -v bytes="$((mem_real_used * 1024))" 'BEGIN {
    suffix="BKMGT"; value=bytes;
    for(i=1; value>=1024 && i<length(suffix); i++) value/=1024;
    printf("%.2f%s", value, substr(suffix,i,1));
  }')

  # 转为字节
  mem_total_bytes=$((mem_total * 1024))
  mem_free_bytes=$((mem_free * 1024))
  mem_available_bytes=$((mem_available * 1024))
  mem_buffers_bytes=$((mem_buffers * 1024))
  mem_cached_bytes=$((mem_cached * 1024 + mem_sreclaimable * 1024 + mem_buffers* 1024))
  mem_real_used_bytes=$((mem_real_used * 1024))
  mem_shared_bytes=$((mem_shared * 1024))

  cat << EOF
{
  "memTotal": $mem_total_bytes,
  "memFree": $mem_free_bytes,
  "memAvailable": $mem_available_bytes,
  "memBuffers": $mem_buffers_bytes,
  "memCached": $mem_cached_bytes,
  "memRealUsed": $mem_real_used_bytes,
  "memShared": $mem_shared_bytes,
  "memNewTotal": "$mem_new_total",
  "memNewRealUsed": "$mem_new_real_used"
}
EOF
}

# 收集dmidecode物理内存信息
collect_physical_memory() {
    # 检查是否有sudo权限
    if command -v sudo >/dev/null 2>&1; then
        SUDO_CMD="sudo"
    else
        SUDO_CMD=""
    fi

    # 检查dmidecode是否已安装
    if ! command -v dmidecode >/dev/null 2>&1; then
        # 尝试安装dmidecode
        if command -v apt-get >/dev/null 2>&1; then
            $SUDO_CMD apt-get update >/dev/null 2>&1 && $SUDO_CMD apt-get install -y dmidecode >/dev/null 2>&1
        elif command -v yum >/dev/null 2>&1; then
            $SUDO_CMD yum install -y dmidecode >/dev/null 2>&1
        elif command -v dnf >/dev/null 2>&1; then
            $SUDO_CMD dnf install -y dmidecode >/dev/null 2>&1
        elif command -v zypper >/dev/null 2>&1; then
            $SUDO_CMD zypper install -y dmidecode >/dev/null 2>&1
        elif command -v pacman >/dev/null 2>&1; then
            $SUDO_CMD pacman -S --noconfirm dmidecode >/dev/null 2>&1
        fi
    fi

    # 再次检查dmidecode是否可用
    if command -v dmidecode >/dev/null 2>&1; then
        # 首先尝试获取Maximum Capacity
        max_capacity=$($SUDO_CMD dmidecode -t memory 2>/dev/null | grep -i "Maximum Capacity:" | head -n1 | awk '
            {
                value = $3
                unit = $4
                # 转换为字节
                if (unit == "GB" || unit == "gb") {
                    bytes = value * 1024 * 1024 * 1024
                } else if (unit == "MB" || unit == "mb") {
                    bytes = value * 1024 * 1024
                } else if (unit == "TB" || unit == "tb") {
                    bytes = value * 1024 * 1024 * 1024 * 1024
                } else {
                    bytes = 0
                }
                printf "%.0f", bytes
            }
        ')
        
        if [ -n "$max_capacity" ] && [ "$max_capacity" -gt 0 ] 2>/dev/null; then
            echo "$max_capacity"
            return 0
        fi

        # 如果Maximum Capacity获取失败，尝试获取已安装内存大小
        total_memory=$($SUDO_CMD dmidecode -t memory 2>/dev/null | grep -i "Size:" | grep -i "[0-9]* GB\|[0-9]* MB" | awk '
            BEGIN { total = 0 }
            {
                value = $2
                unit = $3
                # 转换为字节
                if (unit == "GB" || unit == "gb") {
                    bytes = value * 1024 * 1024 * 1024
                } else if (unit == "MB" || unit == "mb") {
                    bytes = value * 1024 * 1024
                }
                total += bytes
            }
            END {
                printf "%.0f", total
            }
        ')

        if [ -n "$total_memory" ] && [ "$total_memory" -gt 0 ] 2>/dev/null; then
            echo "$total_memory"
            return 0
        fi
    fi

    # 如果任何步骤失败，返回0
    echo "0"
    return 1
}

# 主函数：收集所有信息并生成JSON
main() {
  # 收集系统信息
  os_name=$(cat /etc/os-release 2>/dev/null | grep "PRETTY_NAME" | cut -d "=" -f 2 | tr -d '"' || echo "Unknown")
  simple_system=$(awk -F= '
  /^ID=/ {id=$2}
  /^VERSION_ID=/ {gsub(/"/,"",$2); version=$2}
  END {
      gsub(/"/,"",id);
      print toupper(substr(id,1,1)) substr(id,2) " " version
  }' /etc/os-release 2>/dev/null || echo "Unknown")

  hostname=$(hostname)
  current_time=$(date "+%Y-%m-%d %H:%M:%S")
  version="1.0.0" # 自定义版本

  # 假设的站点和数据库计数 (实际需要根据具体环境采集)
  site_total=0
  database_total=0
  ftp_total=0
  installed=true

  # 收集网络总统计
  network_stats=$(collect_total_network)
  down=$(echo "$network_stats" | grep -o '"down": [0-9.]*' | cut -d ":" -f 2 | tr -d " " || echo "0.00")
  up=$(echo "$network_stats" | grep -o '"up": [0-9.]*' | cut -d ":" -f 2 | tr -d " " || echo "0.00")
  down_packets=$(echo "$network_stats" | grep -o '"downPackets": [0-9]*' | cut -d ":" -f 2 | tr -d " " || echo "0")
  up_packets=$(echo "$network_stats" | grep -o '"upPackets": [0-9]*' | cut -d ":" -f 2 | tr -d " " || echo "0")
  down_total=$(echo "$network_stats" | grep -o '"downTotal": [0-9]*' | cut -d ":" -f 2 | tr -d " " || echo "0")
  up_total=$(echo "$network_stats" | grep -o '"upTotal": [0-9]*' | cut -d ":" -f 2 | tr -d " " || echo "0")
  physical_memory=$(collect_physical_memory)

  # 生成最终JSON
  cat << EOF
{
  "cpu": $(collect_cpu),
  "cpu_times": $(collect_cpu_times),
  "disk": $(collect_disk),
  "iostat": $(collect_iostat),
  "load": $(collect_load),
  "mem": $(collect_mem),
  "network": $(collect_network),
  "system": "$os_name",
  "simple_system": "$simple_system",
  "title": "$hostname",
  "time": "$current_time",
  "version": "$version",
  "site_total": $site_total,
  "database_total": $database_total,
  "ftp_total": $ftp_total,
  "installed": $installed,
  "down": $down,
  "up": $up,
  "downPackets": $down_packets,
  "upPackets": $up_packets,
  "downTotal": $down_total,
  "upTotal": $up_total,
  "physical_memory": $physical_memory
}
EOF
}

# 执行主函数
main
