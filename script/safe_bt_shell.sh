function bt() {
  tool_en=false
  if [[ "$1" == "switch_tool_en" ]]; then
    shift
    tool_en=true
  fi
  if [ $# -eq 0 ]; then
    if [[ "$tool_en" == true ]]; then
      echo "" | btpython /www/server/panel/tools_en.py cli; printf '\033[1A\033[2K\033[1A\033[2K'
      read -p "Please enter command number:" u_input
    else
      echo "" | /etc/init.d/bt; printf '\033[1A\033[2K\033[1A\033[2K'
      read -p "请输入命令编号：" u_input
    fi
    if ! [[ "$u_input" =~ ^[0-9]+$ ]]; then
        u_input=0
    fi
    case "$u_input" in
      99)
        bt switch_tool_en
        ;;
      1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|28|29|30|31|32|33|34|35|36)
        if [[ "$tool_en" == true ]]; then
          bt switch_tool_en "$u_input"
        else
          bt "$u_input"
        fi
        ;;
      *)
        echo "==============================================="
        if [[ "$tool_en" == true ]]; then
          echo "Cancelled!"
        else
          echo "已取消!"
        fi
        ;;
    esac
  else
    case $1 in
    2|stop)
      if [[ "$tool_en" == true ]]; then
        echo "Do not stop the panel service directly in the panel terminal. To stop, please go to [Settings] > [Panel Settings] > [Shutdown Panel]"
      else
        echo "请勿在面板终端直接停止面板服务，如需停止请前往【设置】>【面板设置】>【关闭面板】"
      fi
      ;;
    1|start|restart|reload|3|4|10)
      if [[ "$tool_en" == true ]]; then
        echo "Do not restart the panel service in the panel terminal. To restart, please go to [Home] > [Restart]"
      else
        echo "请勿在面板终端重启面板服务，如需重启请前往【首页】>【重启】"
      fi
      ;;
    26)
      if [[ "$tool_en" == true ]]; then
        echo "Disabling panel SSL will restart the panel service. Please operate at [Settings] > [Security Settings] > [Panel SSL]"
      else
        echo "关闭面板 SSL 将会重启面板服务，请在【设置】>【安全设置】>【面板 SSL】处操作"
      fi
      ;;
    29)
      if [[ "$tool_en" == true ]]; then
        echo "Disabling access device verification will restart the panel service. Please operate at [Settings] > [Security Settings] > [Access Device Verification]"
      else
        echo "关闭访问设备验证将会重启面板服务，请在【设置】>【安全设置】>【访问设备验证】处操作"
      fi
      ;;
    8)
      if [[ "$tool_en" == true ]]; then
        echo "Changing the panel port number will restart the service. Please operate at [Settings] > [Common Settings] > [Panel Port]"
      else
        echo "修改面板端口号将重启服务，请在【设置】>【常用设置】>【面板端口】处操作"
      fi
      ;;
    9)
      if [[ "$tool_en" == true ]]; then
        echo "Clearing panel cache cannot be executed in the panel terminal. You can delete [/www/server/panel/data/session] and restart the panel"
      else
        echo "清除面板缓存无法在面板终端执行，您可以删除【/www/server/panel/data/session】并重启面板"
      fi
      ;;
    12)
      if [[ "$tool_en" == true ]]; then
        echo "Canceling domain binding restriction will restart the panel service. Please operate at [Settings] > [Common Settings] > [Domain Binding]"
      else
        echo "取消域名绑定限制将会重启面板服务，请在【设置】>【常用设置】>【域名绑定】处操作"
      fi
      ;;
    13)
      if [[ "$tool_en" == true ]]; then
        echo "Canceling IP access restriction will restart the panel service. Please operate at [Settings] > [Security Settings] > [Authorized IP]"
      else
        echo "取消 IP 访问限制将会重启面板服务，请在【设置】>【安全设置】>【授权 IP】处操作"
      fi
      ;;
    16)
      if [[ "$tool_en" == true ]]; then
        echo "Repairing the panel cannot be done in the panel terminal. Please operate at [Home] > [Repair]"
      else
        echo "修复面板无法在面板终端进行，请在【首页】>【修复】处操作"
      fi
      ;;
    23)
      if [[ "$tool_en" == true ]]; then
        echo "Disabling BasicAuth authentication will restart the panel service. Please operate at [Settings] > [Security Settings] > [BasicAuth Authentication]"
      else
        echo "关闭 BasicAuth 认证将重启面板服务，请在【设置】>【安全设置】>【BasicAuth 认证】处操作"
      fi
      ;;
    34)
      if [[ "$tool_en" == true ]]; then
        echo "Updating the panel cannot be done in the panel terminal. Please operate at [Home] > [Update]"
      else
        echo "更新面板无法在面板终端进行，请在【首页】>【更新】处操作"
      fi
      ;;
    99)
      bt switch_tool_en
      ;;
    * )
      if [[ "$tool_en" == true ]]; then
        btpython /www/server/panel/tools_en.py cli $@
      else
        /etc/init.d/bt $@
      fi
    esac
  fi
}
export -f bt
