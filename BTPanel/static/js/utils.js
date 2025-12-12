var lan = {  get: function (_, e) {var t = {  diskinfo_span_1:'磁盘分区[{1}]的可用容量小于1GB，这可能会导致MySQL自动停止，面板无法访问等问题，请及时清理！',  process_kill_confirm:'结束进程名[{1}],PID[{2}]后可能会影响服务器的正常运行，继续吗？',  del: '删除[{1}]',  del_all_task: '您共选择了[{1}]个任务,删除后将无法恢复,真的要删除吗?',  del_all_task_ok: '成功删除[{1}]个任务!',  del_all_task_the: '正在删除[{1}],请稍候...',  add_all_task_ok: '成功添加[{1}]个计划任务!',  add: '正在添加[{1}],请稍候...',  confirm_del: '您真的要删除[{1}]吗？',  update_num: '一次只能选择{1}个文件上传，剩下的不作处理！',  service_confirm: '您真的要{1}{2}服务吗？',  service_the: '正在{1}{2}服务,请稍候...',  service_ok: '{1}服务已{2}',  service_err: '{1}服务{2}失败!',  recycle_bin_confirm: '您真的要删除文件[{1}]?',  recycle_bin_confirm_dir: '您真的要删除目录[{1}]?',  del_all_ftp: '您共选择了[{1}]个FTP,删除后将无法恢复,真的要删除吗?',  del_all_ftp_ok: '成功删除{1}个FTP帐户',  del_all_database:'您共选择了[{1}]个数据库,删除后将无法恢复,真的要删除吗?',  del_all_database_ok: '成功删除[{1}]个数据库!',  config_edit_ps: '此处为{1}主配置文件,若您不了解配置规则,请勿随意修改',  install_confirm: '您真的要安装{1}-{2}吗?',  del_all_site: '您共选择了[{1}]个站点,删除后将无法恢复,真的要删除吗?',  del_all_site_ok: '成功删除[{1}]个站点!',  ssl_enable: '您已启用[{1}]证书，如需关闭，请点击"关闭SSL"按钮',  lack_param: '缺少必要参数[{1}]',  del_ftp: '是否删除[{1}]该FTP账号？',};if (!t[_]) return '';msg = t[_];for (var s = 0; s < e.length; s++)  msg = msg.replace('{' + (s + 1) + '}', e[s] + '');return msg;  },  index: {memre: '内存释放',memre_ok: '释放完成',memre_ok_0: '释放中',memre_ok_1: '已释放',memre_ok_2: '状态最佳',mem_warning:  '当前可用物理内存小于64M，这可能导致MySQL自动停止，站点502等错误，请尝试释放内存！',user_warning: '当前面板用户为admin,这可能为面板安全带来风险！',cpu_core: '核心',interfacespeed: '接口速率',package_num: '报文数量',interface_net: '接口流量实时',net_up: '上行',net_down: '下行',unit: '单位',net_font: '宋体',update_go: '立即更新',update_get: '正在获取版本信息...',update_check: '检查更新',update_to: '升级到',update_the: '正在升级面板..',update_ok: '升级成功!',update_log: '版本更新',reboot_title: '安全重启服务器',reboot_warning: '注意，若您的服务器是一个容器，请取消',reboot_ps: '安全重启有利于保障文件安全，将执行以下操作：',reboot_ps_1: '1.停止Web服务',reboot_ps_2: '2.停止MySQL服务',reboot_ps_3: '3.开始重启服务器',reboot_ps_4: '4.等待服务器启动',reboot_msg_1: '正在停止Web服务',reboot_msg_2: '正在停止MySQL服务',reboot_msg_3: '开始重启服务器',reboot_msg_4: '等待服务器启动',reboot_msg_5: '服务器重启成功!',panel_reboot_title: '重启面板服务',panel_reboot_msg: '即将重启面板服务，继续吗？',panel_reboot_to: '正在重启面板服务,请稍候...',panel_reboot_ok: '面板服务重启成功!',net_dorp_ip: '屏蔽此IP',net_doup_ip_msg:  '屏蔽此IP后，对方将无法访问本服务器，你可以在【安全】中删除，继续吗？',net_doup_ip_ps: '手动屏蔽',net_doup_ip_to: '手动屏蔽',net_status_title: '网络状态',net_protocol: '协议',net_address_dst: '本地地址',net_address_src: '远程地址',net_address_status: '状态',net_process: '进程',net_process_pid: 'PID',process_check: '正在分析...',process_kill: '结束',process_kill_title: '结束此进程',process_title: '进程管理',process_pid: 'PID',process_name: '名称',process_cpu: 'CPU',process_mem: '内存',process_disk: '读/写',process_status: '状态',process_thread: '线程',process_user: '用户',process_act: '操作',kill_msg: '正在结束进程...',rep_panel_msg:  '修复面板会获取最新的面板代码程序，<br>包括BUG修复，是否继续操作？',rep_panel_title: '修复面板',rep_panel_the: '正在校验模块...',rep_panel_ok: '修复完成，请按 Ctrl+F5 刷新缓存!',  },  config: {close_panel_msg:  '关闭面板会导致您无法访问面板 ,您真的要关闭宝塔Linux面板吗？',close_panel_title: '关闭面板',config_save: '正在保存配置...',config_sync: '正在同步时间...',config_user_binding: '绑定宝塔帐号',config_user_edit: '修改绑定宝塔账号',binding: '绑定',token_get: '正在获取密钥...',user_bt: '宝塔官网账户',pass_bt: '宝塔官网密码',binding_un_msg: '您确定要解除绑定宝塔帐号码？',binding_un_title: '解除绑定',binding_un: '解绑',ssl_close_msg: '关闭SSL后,必需使用http协议访问面板,继续吗?',ssl_open_ps: '危险！此功能不懂别开启!',ssl_open_ps_1: '必须要用到且了解此功能才决定自己是否要开启!',ssl_open_ps_2: '面板SSL是自签证书，不被浏览器信任，显示不安全是正常现象',ssl_open_ps_3: '开启后导致面板不能访问，可以点击下面链接了解解决方法',ssl_open_ps_4: '我已了经解详情,并愿意承担风险',ssl_open_ps_5: '了解详情',ssl_title: '设置面板SSL',ssl_ps: '请先确认风险!',ssl_msg: '正在安装并设置SSL组件,这需要几分钟时间...',qrcode_no_list: '当前绑定列表为空,请先绑定然后重试',  },  control: {save_day_err: '保存天数不合法!',close_log: '清空记录',close_log_msg: '您真的清空所有监控记录吗？',disk_read_num: '读取次数',disk_write_num: '写入次数',disk_read_bytes: '读取字节数',disk_write_bytes: '写入字节数',  },  crontab: {task_log_title: '任务执行日志',task_empty: '当前没有计划任务',del_task: '您确定要删除该任务吗?',del_task_all_title: '批量删除任务',del_task_err: '以下任务删除失败:',add_task_empty: '任务名称不能为空!',input_hour_err: '小时值不合法!',input_minute_err: '分钟值不合法!',input_number_err: '不能有负数!',input_file_err: '请选择脚本文件!',input_script_err: '脚本代码不能为空!',input_url_err: 'URL地址不正确!',input_empty_err: '对象列表为空，无法继续!',backup_site: '备份网站',backup_database: '备份数据库',backup_log: '切割日志',backup_all_err: '以下对象添加任务失败:',day: '天',hour: '小时',minute: '分钟',sun: '日',sbody: '脚本内容',log_site: '切割网站',url_address: 'URL地址',backup_to: '备份到',disk: '服务器磁盘',save_new: '保留最新',save_num: '份',TZZ1: '周一',TZZ2: '周二',TZZ3: '周三',TZZ4: '周四',TZZ5: '周五',TZZ6: '周六',TZZ7: '周日',mem_ps:  '释放PHP、MYSQL、PURE-FTPD、APACHE、NGINX的内存占用,建议在每天半夜执行!',mem: '释放内存',  },  firewall: {empty: '已清理!',port: '端口',accept: '放行',port_ps: '说明: 支持放行端口范围，如: 3000:3500',ip: '欲屏蔽的IP地址',drop: '屏蔽',ip_ps: '说明: 支持屏蔽IP段，如: 192.168.0.0/24',ssh_port_msg:  '更改远程端口后，有安全组的需在安全组放行新的端口才能访问，您真的要更改远程端口吗？',ssh_port_title: '远程端口',ssh_off_msg: '停用SSH服务后您将无法使用终端工具连接服务器,继续吗？',ssh_on_msg: '确定启用SSH服务吗？',ping_msg:  '禁PING后不影响服务器正常使用，但无法ping通服务器，您真的要禁PING吗？',ping_un_msg: '解除禁PING状态可能会被黑客发现您的服务器，您真的要解禁吗？',ping_title: '是否禁ping',ping: '已禁Ping',ping_un: '已解除禁Ping',ping_err: '连接服务器失败',status_not: '未使用',status_net: '外网不通',status_ok: '正常',drop_ip: '屏蔽IP',accept_port: '放行端口',port_err: '端口范围不合法!',ps_err: '备注/说明 不能为空!',del_title: '删除防火墙规则',close_log: '清空日志',close_log_msg: '即将清空面板日志，继续吗？',close_the: '正在清理,请稍候...',  },  upload: {file_type_err: '不允许上传的文件类型!',file_err: '错误的文件',file_err_empty: '不能为空字节文件!',select_file: '请选择文件!',select_empty: '没有可用文件上传，重新选择文件',up_sleep: '等待上传',up_the: '已上传',up_save: '正在保存..',up_ok: '已上传成功',up_ok_1: '上传完成',up_ok_2: '已上传',up_speed: '上传进度:',up_err: ' 上传错误',ie_err: '抱歉,IE 6/7/8 不支持请更换浏览器再上传',  },  bt: {empty: '空',dir: '选择目录',path: '当前路径',comp: '计算机',filename: '文件名',etime: '修改时间',access: '权限',own: '所有者',adddir: '新建文件夹',path_ok: '选择',save_file: '正在保存,请稍候...',read_file: '正在读取文件,请稍候...',edit_title: '在线编辑',edit_ps: '提示：Ctrl+F 搜索关键字，Ctrl+S 保存，Ctrl+H 查找替换!',stop: '停止',start: '启动',restart: '重启',reload: '重载',php_status_err: '抱歉，不支持PHP5.2',php_status_title: 'PHP负载状态',php_pool: '应用池(pool)',php_manager: '进程管理方式(process manager)',dynamic: '动态',static: '静态',php_start: '启动日期(start time)',php_accepted: '请求数(accepted conn)',php_queue: '请求队列(listen queue)',php_max_queue: '最大等待队列(max listen queue)',php_len_queue: 'socket队列长度(listen queue len)',php_idle: '空闲进程数量(idle processes)',php_active: '活跃进程数量(active processes)',php_total: '总进程数量(total processes)',php_max_active: '最大活跃进程数量(max active processes)',php_max_children: '到达进程上限次数(max children reached)',php_slow: '慢请求数量(slow requests)',nginx_title: 'Nginx负载状态',nginx_active: '活动连接(Active connections)',nginx_accepts: '总连接次数(accepts)',nginx_handled: '总握手次数(handled)',nginx_requests: '总请求数(requests)',nginx_reading: '请求数(Reading)',nginx_writing: '响应数(Writing)',nginx_waiting: '驻留进程(Waiting)',nginx_worker: '工作进程(Worker)',nginx_workercpu: 'Nginx占用CPU(Workercpu)',nginx_workermen: 'Nginx占用内存(Workermen)',apache_uptime: '启动时间(Uptime)',apache_restarttime: '重启时间(RestartTime)',apache_totalaccesses: '总连接数(TotalAccesses)',apache_totalkbytes: '传送总字节(TotalkBytes)',apache_reqpersec: '每秒请求数(ReqPerSec)',apache_idleworkers: '空闲进程(IdleWorkers)',apache_busyworkers: '繁忙进程(BusyWorkers)',apache_workercpu: 'Apache使用CPU',apache_workermem: 'Apache使用内存',drop_ip_title: '屏蔽此IP',net_status_title: '网络状态',net_pool: '协议',copy_ok: '复制成功',copy_empty: '密码为空',cal_msg: '计算结果：',cal_empty: '输入计算结果，否则无法删除',cal_err: '计算错误，请重新计算',loginout: '您真的要退出面板吗?',pass_err_len: '面板密码不能少于8位!',pass_err: '面板密码不能为弱口令',pass_err_re: '两次输入的密码不一致',pass_title: '修改密码',pass_new_title: '新的密码',pass_rep: '随机密码',pass_rep_btn: '随机',pass_re: '重复',pass_re_title: '再输一次',pass_rep_ps: '请在修改前记录好您的新密码!',user_len: '用户名长度不能少于3位',user_err_re: '两次输入的用户名不一致',user_title: '修改面板用户名',user: '用户名',user_new: '新的用户名',task_list: '任务列表',task_msg: '消息列表',task_not_list: '当前没有任务!',task_scan: '正在扫描',task_install: '正在安装',task_sleep: '等待',task_downloading: '下载中',task_the: '正在处理',task_ok: '已完成',task_close: '任务已取消!',time: '耗时',s: '秒',install_title: '推荐安装套件',install_ps: '我们为您推荐以下一键套件，请按需选择或在',install_s: '软件管理',install_s1: '页面中自动选择，推荐安装LNMP',install_lnmp: 'LNMP(推荐)',install_type: '安装方式',install_rpm: '极速安装',install_rpm_title:  '即rpm/deb，安装时间极快（5-10分钟），版本与稳定性略低于编译安装，适合快速部署测试',install_src: '编译安装',install_src_title: '安装时间长（30分钟到2小时），性能最大化，适合生产环境',install_key: '一键安装',install_apache22: '您选择的是Apache2.2,PHP将会以php5_module模式运行!',install_apache24: '您选择的是Apache2.4,PHP将会以php-fpm模式运行!',insatll_s22: 'Apache2.2不支持',insatll_s24: 'Apache2.4不支持',insatll_mem: '您的内存小于{1},不建议安装MySQL-{2}',install_to: '正在添加到安装器...',install_ok: '已将安装请求添加到安装器',task_add: '已添加到队列',panel_open: '正在打开面板...',panel_add: '关联宝塔面板',panel_edit: '修改关联',panel_err_format: '面板地址格式不正确，示例：',panel_err_empty: '面板资料不能为空',panel_address: '面板地址',panel_user: '用户名',panel_pass: '密码',panel_ps: '备注',panel_ps_1: '收藏其它服务器面板资料，实现一键登录面板功能',panel_ps_2: '面板备注不可重复',panel_ps_3:  "<font style='color:red'>注意，开启广告拦截会导致无法快捷登录</font>",task_time: '时间',task_name: '名称',task_msg_title: '消息提醒',task_title: '消息盒子',task_tip_read: '标记已读',task_tip_all: '全部已读',no_data: '当前没有数据',  },  files: {recycle_bin_re: '恢复',recycle_bin_del: '永久删除',recycle_bin_on: '文件回收站',recycle_bin_on_db: '数据库回收站',recycle_bin_ps: '注意：关闭回收站，删除的文件无法恢复！',recycle_bin_close: '清空回收站',recycle_bin_type1: '全部',recycle_bin_type2: '文件夹',recycle_bin_type3: '文件',recycle_bin_type4: '图片',recycle_bin_type5: '文档',recycle_bin_type6: '数据库',recycle_bin_th1: '文件名',recycle_bin_th2: '原位置',recycle_bin_th3: '大小',recycle_bin_th4: '删除时间',recycle_bin_th5: '操作',recycle_bin_title: '回收站',recycle_bin_re_title: '恢复文件',recycle_bin_re_msg: '若您的原位置已有同名文件或目录，将被覆盖，继续吗？',recycle_bin_re_the: '正在恢复,请稍候...',recycle_bin_del_title: '删除文件',recycle_bin_del_msg: '删除操作不可逆，继续吗？',recycle_bin_del_the: '正在删除,请稍候...',recycle_bin_close_msg: '清空回收站操作会永久删除回收站中的文件，继续吗？',recycle_bin_close_the: '正在删除,请稍候...',dir_menu_webshell: '目录查杀',file_menu_webshell: '查杀',file_menu_copy: '复制',file_menu_mv: '剪切',file_menu_rename: '重命名',file_menu_auth: '权限',file_menu_zip: '压缩',file_menu_unzip: '解压',file_menu_edit: '编辑',file_menu_img: '预览',file_menu_down: '下载',file_menu_del: '删除',file_name: '文件名',file_size: '大小',file_etime: '修改时间',file_auth: '权限',file_own: '所有者',file_read: '读取',file_write: '写入',file_exec: '执行',file_public: '公共',file_group: '用户组',file_act: '操作',get_size: '共{1}个目录与{2}个文件,大小:',get: '获取',new: '新建',new_empty_file: '新建空白文件',new_dir: '新建目录',dir_name: '目录名称',return: '返回上一级',shell: '终端',paste: '粘贴',paste_all: '粘贴所有',path_root: '根目录',all: '批量',set_auth: '设置权限',up_title: '上传文件',up_add: '添加文件',up_start: '开始上传',up_coding: '文件编码',up_bin: '二进制',unzip_title: '解压文件',unzip_name: '文件名',unzip_name_title: '压缩文件名',unzip_to: '解压到',unzip_coding: '编码',unzip_the: '正在解压,请稍候...',zip_title: '压缩文件',zip_to: '压缩到',zip_the: '正在压缩,请稍候...',zip_ok: '服务器正在后台压缩文件,请稍候刷新文件列表查看进度!',zip_pass_title: '解压密码',zip_pass_msg: '不需要请留空',mv_the: '正在移动,请稍候...',copy_the: '正在复制,请稍候...',copy_ok: '已复制',mv_ok: '已剪切',shell_title: '执行SHELL (仅支持非交互命令)',shell_go: '发送',shell_ps: 'shell命令',down_title: '下载文件',down_url: 'URL地址',down_to: '下载到',down_save: '保存文件名',down_task: '正在添加到队列，请稍候..',del_file: '删除文件',del_dir: '删除目录',del_all_file: '批量删除文件',del_all_msg: '您确定要删除选中的文件/目录吗?',file_conver_msg: '即将覆盖以下文件,是否确定？',  },  ftp: {empty: '当前没有FTP数据',stop_title: '停用这个帐号',start_title: '启用这个帐号',stop: '已停用',start: '已启用',copy: '复制密码',open_path: '打开目录',edit_pass: '改密',ps: '备注信息',add_title: '添加FTP帐户',add_user: '用户名',add_user_tips: '请输入FTP用户名',add_pass: '密码',add_pass_tips: '请输入FTP密码',add_pass_rep: '随机密码',add_path: '根目录',add_path_tips: '请输入或选择FTP目录',add_path_rep: '选择文件目录',add_path_title: '帐户根目录，会自动创建同名目录',add_path_ps: 'FTP所指向的目录',add_ps: '备注',add_ps_title: '备注信息(小于255个字符)',del_all: '是否批量删除选中的FTP账号？',del_all_err: '以下FTP帐户删除失败:',stop_confirm: '您真的要停止{1}的FTP吗?',stop_title: 'FTP帐户',pass_title: '修改FTP用户密码',pass_user: '用户名',pass_new: '新密码',pass_confirm: '您确定要修改该FTP帐户密码吗?',port_title: '修改FTP端口',port_name: '端口',port_tips: '请填写端口',del_ftp_title: '删除FTP',del_ftp_all_title: '删除选中FTP',  },  database: {empty: '当前没有数据库数据',backup_empty: '无备份',backup_ok: '有备份',copy_pass: '复制密码',input: '导入',input_title: '导入数据库',admin: '管理',admin_title: '数据库管理',auth: '权限',auth_title: '设置访问权限',edit_pass: '改密',edit_pass_title: '修改数据库密码',del_title: '删除数据库',ps: '备注信息',add_title: '添加数据库',add_name: '数据库名',add_name_title: '新的数据库名称',add_pass: '密码',add_pass_title: '数据库密码',add_pass_rep: '随机密码',add_auth: '访问权限',add_auth_local: '本地服务器',add_auth_all: '所有人',add_auth_ip: '指定IP',add_auth_ip_title: '请输允许访问此数据库的IP地址',add_ps: '备注',edit_root: 'root密码',user: '用户名',edit_pass_new: '新密码',edit_pass_new_title: '新的数据库密码',edit_pass_confirm: '您确定要修改数据库密码吗?',backup_re: '恢复',backup_name: '文件名称',backup_size: '文件大小',backup_time: '备份时间',backup_title: '数据库备份详情',backup: '备份',input_confirm: '数据库将被覆盖，继续吗?',input_the: '正在导入,请稍候...',backup_the: '正在备份,请稍候...',backup_del_title: '删除备份文件',backup_del_confirm: '您真的要删除备份文件吗?',del_all_title: '批量删除数据库',del_all_err: '以下数据库删除失败:',input_title_file: '从文件导入数据库',input_local_up: '从本地上传',input_ps1: '仅支持sql、zip、sql.gz、(tar.gz|gz|tgz)',input_ps2:  'zip、tar.gz压缩包结构：test.zip或test.tar.gz压缩包内，必需包含test.sql',input_ps3:  '若文件过大，您还可以使用SFTP工具，将数据库文件上传到/www/backup/database',input_up_type: '请上传sql、zip、sql.gz、(tar.gz|gz|tgz)',auth_err: '此数据库不能修改访问权限',auth_title: '设置数据库权限',auth_name: '访问权限',sync_the: '正在同步,请稍候...',phpmyadmin_err: '请先安装phpMyAdmin',phpmyadmin: '正在打开phpMyAdmin',  },  soft: {php_main1: 'php服务',php_main2: '上传限制',php_main3: '超时限制',php_main4: '配置文件',php_main5: '安装扩展',php_main6: '禁用函数',php_main7: '性能调整',php_main8: '负载状态',php_main9: 'Session配置',php_menu_ext: '扩展配置',admin: '管理',off: '关闭',on: '开启',stop: '停止',start: '启动',status: '当前状态',restart: '重启',reload: '重载配置',mysql_mem_err:  '机器内存小于1G，不建议使用mysql5.5以上版本</li><li>如果数据库经常自动停止，请尝试使用linux工具箱增加SWAP或者升级服务器内存',concurrency_m: '自定义',concurrency: '并发',concurrency_type: '并发方案',php_fpm_model: '运行模式',php_fpm_ps1: 'PHP-FPM运行模式',php_fpm_ps2: '允许创建的最大子进程数',php_fpm_ps3: '起始进程数（服务启动后初始进程数量）',php_fpm_ps4: '最小空闲进程数（清理空闲进程后的保留数量）',php_fpm_ps5: '最大空闲进程数（当空闲进程达到此值时清理）',php_fpm_err1: 'max_spare_servers 不能大于 max_children',php_fpm_err2: 'min_spare_servers 不能大于 start_servers',php_fpm_err3: 'min_spare_servers 不能大于 max_spare_servers',php_fpm_err4: 'start_servers 不能大于 max_children',php_fpm_err5: '配置值不能小于1',phpinfo: '查看phpinfo()',get: '正在获取...',get_config: '正在获取配置文件，请稍候...',get_list: '正在获取列表...',the_save: '正在保存数据...',config_edit: '配置修改',edit_empty: '不修改请留空',php_upload_size: '上传大小限制不能小于2M',mvc_ps: 'MVC架构的程序需要开启,如typecho',the_install: '正在安装...',the_uninstall: '正在卸载...',install_the: '安装中...',sleep_install: '等待安装...',install: '安装',uninstall: '卸载',php_ext_name: '名称',php_ext_type: '类型',php_ext_ps: '说明',php_ext_status: '状态',php_ext_install_confirm: '您真的要安装{1}吗?',php_ext_uninstall_confirm: '您真的要卸载{1}吗?',add_install: '正在添加到安装器...',install_title: '软件安装',insatll_type: '安装方式',install_version: '安装版本',type_title: '选择安装方式',err_install1: '请先卸载Apache',err_install2: '请先卸载Nginx',err_install3: '请先安装php',err_install4: '请先安装MySQL',setup: '设置',apache22: '警告:当前为php-fpm模式,将不被Apache2.2支持,请重新安装此PHP版本!',apache24:  '警告:当前为php5_module模式,将不被nginx/apache2.4支持,请重新安装此PHP版本!',apache22_err:  'Apache2.2不支持多PHP版本共存,请先卸载已安装PHP版本,再安装此版本!',mysql_f: '注意: 安装新的MySQL版本,会覆盖数据库数据,请先备份数据库!',mysql_d:  '抱歉,出于安全考虑,请先到[数据库]管理备份数据库,并中删除所有数据库!',fun_ps1: '添加要被禁止的函数名,如: exec',fun_ps2: '在此处可以禁用指定函数的调用,以增强环境安全性!',fun_ps3: '强烈建议禁用如exec,system等危险函数!',fun_msg: '您输入的函数已被禁用!',nginx_status: '负载状态',nginx_version: '切换版本',waf_title: '过滤器',web_service: 'Web服务',waf_not:  '您当前Nginx版本不支持waf模块,请安装Nginx1.12,重装Nginx不会丢失您的网站配置!',waf_edit: '编辑规则',waf_up: '上传限制',waf_input1: 'URL过滤',waf_input2: 'Cookie过滤',waf_input3: 'POST过滤',waf_input4: '防CC攻击',waf_input5: '记录防御信息',waf_input6: 'CC攻击触发频率(次)',waf_input7: 'CC攻击触发周期',waf_input8: 'IP白名单',waf_input9: 'IP黑名单',waf_ip: 'IP地址',waf_up_title: '文件上传后缀黑名单',waf_up_from1: '添加禁止上传的扩展名,如: zip',waf_up_from2: '扩展名',waf_url_white: 'URL白名单',waf_index: '警告内容',waf_cloud: '从云端更新',waf_update: '正在更新规则文件,请稍候..',waf_cc_err: 'CC防御配置值超出可用值 (频率1-3000|周期1-1800)',php_version: 'php版本',save_path: '存储位置',service: '服务',safe: '安全设置',log: '日志',error_log:'错误日志',mysql_to_msg: '迁移数据库文件过程中将会停止数据库运行,继续吗?',mysql_to_msg1: '正在迁移文件,请稍候...',mysql_to: '迁移',mysql_log_close: '清空',mysql_log_bin: '二进制日志',mysql_log_err: '错误日志',mysql_log_ps1: '当前没有日志内容!',mysql_port_title:  '修改数据库端口可能会导致您的站点无法连接数据库,确定要修改吗?',select_version: '选择版本',version_to: '切换',pma_port: '访问端口',pma_port_title: 'phpmyadmin访问端口',pma_pass: '密码访问',pma_user: '授权账号',pma_pass1: '访问密码',pma_pass2: '重复密码',pma_ps: '为phpmyadmin增加一道访问安全锁',pma_pass_close: '您真的要关闭访问认证吗?',pma_pass_empty: '授权用户或密码不能为空!',menu_temp: '正在获取模板...',menu_phpsafe: 'php守护已启动，无需设置',qiniu_lise: '正在从云端获取...',qiniu_file_title: '文件列表',qiniu_th1: '名称',qiniu_th2: '类型',qiniu_th3: '大小',qiniu_th4: '更新时间',mysql_del_err:  '抱歉,为安全考虑,请先到[数据库]管理备份数据库并中删除所有数据库!',uninstall_confirm: '您真的要卸载[{1}-{2}]吗?',from_err: '表单错误!',lib_the: '正在提交配置,请稍候...',lib_config: '配置',lib_insatll_confirm: '您真的要安装[{1}]插件吗？',lib_uninsatll_confirm: '您真的要卸载[{1}]插件吗？',lib_install: '安装插件',lib_uninstall: '卸载插件',lib_install_the: '正在安装,请稍候...',lib_uninstall_the: '正在卸载,请稍候...',mysql_set_msg: '优化方案',mysql_set_select: '请选择',mysql_set_maxmem: '最大使用内存',mysql_set_key_buffer_size: '用于索引的缓冲区大小',mysql_set_query_cache_size: '查询缓存,不开启请设为0',mysql_set_tmp_table_size: '临时表缓存大小',mysql_set_innodb_buffer_pool_size: 'Innodb缓冲区大小',mysql_set_innodb_log_buffer_size: 'Innodb日志缓冲区大小',mysql_set_sort_buffer_size: '每个线程排序的缓冲大小',mysql_set_read_buffer_size: '读入缓冲区大小',mysql_set_read_rnd_buffer_size: '随机读取缓冲区大小',mysql_set_join_buffer_size: '关联表缓存大小',mysql_set_thread_stack: '每个线程的堆栈大小',mysql_set_binlog_cache_size: '二进制日志缓存大小(4096的倍数)',mysql_set_thread_cache_size: '线程池大小',mysql_set_table_open_cache: '表缓存',mysql_set_max_connections: '最大连接数',mysql_set_restart: '重启数据库',mysql_set_conn: '连接数',mysql_set_err:  "错误,内存分配过高!<p style='color:red;'>物理内存: {1}MB<br>最大使用内存: {2}MB<br>可能造成的后果: 导致数据库不稳定,甚至无法启动MySQLd服务!</p>",mysql_status_title1: '启动时间',mysql_status_title2: '总连接次数',mysql_status_title3: '发送',mysql_status_title4: '接收',mysql_status_title5: '每秒查询',mysql_status_title6: '每秒事务',mysql_status_title7: 'File',mysql_status_title8: 'Position',mysql_status_title9: '活动/峰值连接数',mysql_status_title10: '线程缓存命中率',mysql_status_title11: '索引命中率',mysql_status_title12: 'Innodb索引命中率',mysql_status_title13: '查询缓存命中率',mysql_status_title14: '创建临时表到磁盘',mysql_status_title15: '已打开的表',mysql_status_title16: '没有使用索引的量',mysql_status_title17: '没有索引的JOIN量',mysql_status_title18: '排序后的合并次数',mysql_status_title19: '锁表次数',mysql_status_ps1: '若值过大,增加max_connections',mysql_status_ps2: '若过低,增加thread_cache_size',mysql_status_ps3: '若过低,增加key_buffer_size',mysql_status_ps4: '若过低,增加innodb_buffer_pool_size',mysql_status_ps5: '若过低,增加query_cache_size',mysql_status_ps6: '若过大,尝试增加tmp_table_size',mysql_status_ps7: 'table_open_cache配置值应大于等于此值',mysql_status_ps8: '若不为0,请检查数据表的索引是否合理',mysql_status_ps9: '若不为0,请检查数据表的索引是否合理',mysql_status_ps10: '若值过大,增加sort_buffer_size',mysql_status_ps11: '若值过大,请考虑增加您的数据库性能',config_php_tips:  "默认已开启Openssl/Curl/Mysql等扩展，详情可点击<a href='javascript:;'  class='btlink return_php_info'>phpinfo</a>查看",  },  site: {running: '正在运行',running_title: '停用这个站点',running_text: '运行中',stopped: '已停止',stopped_title: '启用这个站点',backup_yes: '有备份',backup_no: '无备份',web_end_time: '永久',open_path_txt: '打开目录',set: '设置',site_del_title: '删除站点',site_no_data: '当前没有站点数据',site_null: 'null',site_bak: '备注信息',saving_txt: '正在保存...',domain_err_txt: '域名格式不正确，请重新输入!',ftp: 'FTP账号资料',ftp_tips: '只要将网站上传至以上FTP即可访问!',user: '用户',password: '密码',database_txt: '数据库账号资料',database: '数据库',database_name: '数据库名',database_set: '数据库设置',success_txt: '成功创建站点',php_ver: 'PHP版本',site_add: '添加网站',domain: '域名',port: '端口',note: '备注',note_ph: '网站备注',web_root_dir: '网站根目录',web_dir: '网站目录',root_dir: '根目录',yes: '创建',no: '不创建',ftp_set: 'FTP设置',ftp_help:  '创建站点的同时，为站点创建一个对应FTP帐户，并且FTP目录指向站点所在目录',database_help:  '创建站点的同时，为站点创建一个对应的数据库帐户，方便不同站点使用不同数据库',domain_help:  '每行填写一个域名，默认为80端口<br>泛解析添加方法 *.domain.com<br>如另加端口格式为 www.domain.com:88',domain_len_msg: '不要超出20个字符',anti_XSS_attack: '防跨站攻击',write_access_log: '写访问日志',run_dir: '运行目录',site_help_1: '部分程序需要指定二级目录作为运行目录，如ThinkPHP5，Laravel',site_help_2: '选择您的运行目录，点保存即可',default_doc_help: '默认文档，每行一个，优先级由上至下',site_stop_txt: '站点停用后将无法访问，您真的要停用这个站点吗？',site_start_txt: '即将启动站点，您真的要启用这个站点吗？',site_del_info: '是否要删除同名的FTP、数据库、根目录',all_del_info: '同时删除站点根目录',all_del_site: '批量删除站点',del_err: '以下站点删除失败',click_access: '点击访问',operate: '操作',domain_man: '域名管理',unresolved: '未解析',parsed: '已解析',this_domain_un: '该域名未解析',analytic_ip: '域名解析IP为',current_server_ip: '当前服务器IP',parsed_info: '仅供参考,使用CDN的用户请无视',domain_empty: '域名不能为空!',domain_last_cannot: '最后一个域名不能删除',domain_del_confirm: '您真的要从站点中删除这个域名吗？',webback_del_confirm: '真的要删除备份包吗?',del_bak_file: '删除备份文件',filename: '文件名称',filesize: '文件大小',backuptime: '打包时间',backup_title: '打包备份',public_set: '全局设置',local_site: '本站',setindex: '设置网站默认文档',default_doc: '新建网站默认页面',default_site: '默认站点',default_site_yes: '设置默认站点',default_site_no: '未设置默认站点',default_site_help_1:  '设置默认站点后,所有未绑定的域名和IP都被定向到默认站点',default_site_help_2: '可有效防止恶意解析',site_menu_1: '子目录绑定',site_menu_2: '网站目录',site_menu_3: '流量限制',site_menu_4: '伪静态',site_menu_5: '默认文档',site_menu_6: '配置文件',site_menu_7: 'SSL',site_menu_8: 'PHP版本',site_menu_9: 'Tomcat',site_menu_10: '301重定向',site_menu_11: '反向代理',site_menu_12: '防盗链',website_change: '站点修改',addtime: '添加时间',the_msg: '正在提交任务...',start_scan: '开始扫描',update_lib: '更新特征库',scanned: '已扫描',risk_quantity: '风险数量',danger_fun: '危险函数',danger_fun_no: '未禁用危险函数',danger: '危险',file: '文件',ssh_port: 'SSH端口',high_risk: '高危',sshd_tampering: 'sshd文件被篡改',xss_attack: '跨站攻击',site_xss_attack: '站点未开启防跨站攻击!',mod_time: '修改时间',code: '代码',behavior: '行为',risk: '风险',details: '详情',to_update: '正在更新，请稍候...',limit_net_1: '论坛/博客',limit_net_2: '图片站',limit_net_3: '下载站',limit_net_4: '商城',limit_net_5: '门户',limit_net_6: '企业站',limit_net_7: '视频站',limit_net_8: '启用流量控制',limit_net_9: '限制方案',limit_net_10: '并发限制',limit_net_11: '限制当前站点最大并发数',limit_net_12: '单IP限制',limit_net_13: '限制单个IP访问最大并发数',limit_net_14: '流量限制',limit_net_15: '限制每个请求的流量上限（单位：KB）',subdirectories: '子目录',url_rewrite_alter: '你真的要为这个子目录创建独立的伪静态规则吗？',rule_cov_tool: '规则转换工具',a_c_n: 'Apache转Nginx',save_as_template: '另存为模板',url_rw_help_1:  '请选择您的应用，若设置伪静态后，网站无法正常访问，请尝试设置回default',url_rw_help_2: '您可以对伪静态规则进行修改，修改完后保存即可',config_url: '配置伪静态规则',d_s_empty: '域名和子目录名称不能为空',s_bin_del: '您真的要删除这个子目录绑定吗？',proxy_url: '目标URL',proxy_url_info: '请填写完整URL,例：http://www.test.com',proxy_domain: '发送域名',proxy_domian_info: '发送到目标服务器的域名,例：www.test.com',proxy_cache: '开启缓存',con_rep: '内容替换',con_rep_info: '被替换的文本,可留空',to_con: '替换为,可留空',proxy_enable: '启用反向代理',proxy_help_1: '目标Url必需是可以访问的，否则将直接502',proxy_help_2:  '默认本站点所有域名访问将被传递到目标服务器，请确保目标服务器已绑定域名',proxy_help_3: '若您是被动代理，请在发送域名处填写上目标站点的域名',proxy_help_4: '若您不需要内容替换功能，请直接留空',proxy_help_5:  '可通过purge清理指定URL的缓存,示例：http://test.com/purge/test.png',access_domain: '访问域名',all_site: '整站',target_url: '目标URL',eg_url: '请填写完整URL,例：http://www.test.com',enable_301: '启用301',to301_help_1: '选择[整站]时请不要将目标URL设为同一站点下的域名.',to301_help_2: '取消301重定向后，需清空浏览器缓存才能看到生效结果.',bt_ssl: '宝塔SSL',lets_ssl: "Let's Encrypt免费证书",other: '其它',other_ssl: '其他证书',use_other_ssl: '使用其他证书',ssl_help_1:  "本站点未设置SSL，如需设置SSL，请选择切换类目申请开启SSL<br><p style='color:red;'>关闭SSL以后,请务必清除浏览器缓存再访问站点</p>",ssl_help_2: "已为您自动生成Let's Encrypt免费证书；",ssl_help_3:  '如需使用其他SSL,请切换其他证书后粘贴您的KEY以及PEM内容，然后保存即可',ssl_key: '密钥(KEY)',ssl_crt: '证书(PEM格式)',ssl_close: '关闭SSL',bt_bind_no:  '未绑定宝塔账号，请注册绑定，绑定宝塔账号(非论坛账号)可实现一键部署SSL',bt_user: '宝塔账号',login: '登录',bt_reg: '注册宝塔账号',bt_ssl_help_1: '宝塔SSL证书为亚洲诚信证书，需要实名认证才能申请使用',bt_ssl_help_2: '已有宝塔账号请登录绑定',bt_ssl_help_3:  '宝塔SSL申请的是TrustAsia DV SSL CA - G5 原价：1900元/1年，宝塔用户免费！',bt_ssl_help_4: '一年满期后免费颁发',btapply: '申请',endtime: '到期时间',status: '状态',bt_ssl_help_5: '申请之前，请确保域名已解析，如未解析会导致审核失败',bt_ssl_help_6:  '宝塔SSL申请的是免费版TrustAsia DV SSL CA - G5证书，仅支持单个域名申请',bt_ssl_help_7: '有效期1年，不支持续签，到期后需要重新申请',bt_ssl_help_8:  "Let's Encrypt免费证书，有效期3个月，支持多域名默认会自动续签",bt_ssl_help_9: '若您的站点使用了CDN或301重定向会导致续签失败',bt_ssl_help_10:  "粘贴您的*.key以及*.pem内容，然后保存即可<a href='http://www.bt.cn/bbs/thread-704-1-1.html' class='btlink' target='_blank'>[帮助]</a>",phone_input: '请输入手机号码',ssl_apply_1: '正在提交订单，请稍候..',ssl_apply_2: '正在校验域名，请稍候..',ssl_apply_3: '正在部署证书，请稍候..',ssl_apply_4: '正在更新证书，请稍候..',lets_help_1: '不用实名认证，浏览器兼容较低，申请存在一定失败率',lets_help_2: "let's Encrypt证书有效期为3个月",lets_help_3: '3个月有效期后自动续签',get_ssl_list: '正在获取证书列表，请稍候..',order_success: '订单完成',deploy: '部署',deployed: '已部署',domain_wait: '待域名确认',domain_validate: '验证域名',domain_check: '请检查域名是否解析到本服务器',update_ssl: '更新证书',get_ssl_err: '证书获取失败',get_ssl_err1: '证书获取失败，返回如下错误信息',err_type: '错误类型',ssl_close_info: '已关闭SSL,请务必清除浏览器缓存后再访问站点!',switch: '切换',switch_php_help1: '请根据您的程序需求选择版本',switch_php_help2:  '若非必要,请尽量不要使用PHP5.2,这会降低您的服务器安全性；',switch_php_help3: 'PHP7不支持mysql扩展，默认安装mysqli以及mysql-pdo',enable_nodejs: '启用Node.js?v=1764728423',nodejs_help1: '当前版本为Node.js?v=1764728423',nodejs_help2: 'Node.js可以与PHP共存,但无法与Tomcat共存；',nodejs_help3: '若您的Node.js应用中有php脚本,访问时请添加.php扩展名',a_n_n: 'apache2.2暂不支持Tomcat!',enable_tomcat: '启用Tomcat',tomcat_help1: '当前版本为Tomcat',tomcat_help2: '若您需要其它版本,请到软件商店- 所有软件 中切换；',tomcat_help3:  '部署顺序: 安装Tomcat >> 创建站点 >> 上传并配置项目 >> 启用Tomcat',tomcat_help4: '若您的tomcat应用中有php脚本,访问时请添加.php扩展名',tomcat_help5: '开启成功后,大概需要1-5分钟时间生效!',tomcat_err_msg: '您没有安装Tomcat，请先安装!',tomcat_err_msg1: '请先安装Tomcat!',web_config_help: '此处为站点主配置文件,若您不了解配置规则,请勿随意修改.',rewritename: '0.当前',template_empty: '模板名称不能为空',save_rewrite_temp: '保存为Rewrite模板',template_name: '模板名称',change_defalut_page: '修改默认页',err_404: '404错误页',empty_page: '网站不存在提示页',default_page_stop: '网站停用后的提示页',  },  public: {success: '操作成功!',error: '操作失败!',add_success: '添加成功!',del_success: '删除成功',save: '保存',edit: '修改',edit_ok: '修改成功!',edit_err: '修改失败!',know: '知道了',close: '关闭',cancel: '取消',ok: '确定',empty: '清空',submit: '提交',exec: '执行',script: '脚本',log: '日志',slow_log: '慢日志',bin_log:'二进制日志',del: '删除',add: '添加',the_get: '正在获取,请稍候...',fresh: '刷新',config: '正在设置...',config_ok: '设置成功!',the: '正在处理,请稍候...',user: '帐号',pass: '密码',read: '正在读取,请稍候...',pre: '百分比',num: '次数',byte: '字节',input_err: '表单不合法,请重新输入!',the_add: '正在添加,请稍候...',the_del: '正在删除,请稍候...',msg: '提示',list_empty: '列表为空!',all: '所有',upload: '上传',download: '下载',action: '操作',warning: '警告',return: '返回',help: '帮助',list: '列表',off: '关闭',on: '开启',  },	pro_info_detail:{		pid:'进程id',		status:'进程状态',		ppid:'父进程id',		user_name:'所属用户名',		num_threads:'所拥有的线程数',		io_read:'读取的IO数据量',		io_write:'写入的IO数据量',		socket:'连接进程数',		create_time:'进程启动时间',		name:'名称',		exe:'可执行文件路径',		start_command:'启动命令',		pro_info:'查询结果'	},	memory_info_detail:{		rss:'物理内存大小',		vms:'虚拟内存大小',		shared:'共享内存大小',		text:'代码段内存大小',		lib:'库内存大小',		data:'数据段内存大小',		dirty:'脏内存大小',		pss:'实际使用的物理内存大小',		swap:'交换内存大小',		memory_info:'查询结果'	},	soft_info_detail:{		datid:'数据库OID（Object Identifier）',datname:'数据库名称',numbackends:'已连接到此数据库的后端数量',xact_commit:'数据库提交的事务数量',xact_rollback:'数据库回滚的事务数量',blks_read:'数据库从磁盘读取的块数',blks_hit:'数据库从共享缓存中读取的块数',tup_inserted:'数据库检索的行数',tup_fetched:'数据库检索的行数含“WHERE”限制',deadlocks: '数据库由于死锁而导致的回滚数',stats_reset:'最后一次重置统计信息的时间',active_connections:'当前活跃连接数',accepts:'接收的TCP连接数',handled:'成功处理的TCP连接数',requests:'处理的HTTP请求总数',Reading:'正在读取数据的TCP连接数',Writing:'正在写入数据的TCP连接数',Waiting:'可用连接的空闲TCP连接数',		bind: '绑定的IP地址',port: '运行的端口号',maxconn: '可同时处理的最大连接数',cachesize: '使用的内存大小',curr_connections: '当前连接数',cmd_get: '执行get命令的次数',get_hits: 'get命中缓存的次数',get_misses: 'get没有命中缓存的次数',bytes_read: '读取字节数',bytes_written: '写入字节数',limit_maxbytes: '服务器可使用的最大内存大小',bytes: '当前存储数据所占用的字节数',curr_items: '当前缓存条目数量',evictions: '缓存淘汰的条目数量',hit: '命中率，即get命中率',	Aborted_clients: '服务器主动中断的数量',	Aborted_connects: '连接失败的数量',	Bytes_received: '接收到的字节数',	Bytes_sent: '发送的字节数',	Com_commit: '提交的事务数量',	Com_rollback: '回滚的事务数量',	Connections: '已经建立的连接数量',	Created_tmp_disk_tables: '创建的临时磁盘表数量',	Created_tmp_tables: '创建的临时表数量',	Innodb_buffer_pool_pages_dirty: '当前脏页数量',	Innodb_buffer_pool_read_requests: ' 从缓冲池中读取的请求数量',	Innodb_buffer_pool_reads: '从磁盘中读取的数量',	Key_read_requests: '从缓存中读取索引的请求数量',	Key_reads: '从磁盘中读取索引的数量',	Key_write_requests: '向缓存中写入索引的请求数量',	Key_writes: '向磁盘中写入索引的数量',	Max_used_connections: '最大同时连接数量',	Open_tables: '当前打开的表数量',	Opened_files: '打开的文件数量',	Opened_tables: '打开的表数量',	Qcache_hits: '查询缓存命中数量',	Qcache_inserts: '查询缓存插入数量',	Questions: '执行的查询数量',	Select_full_join: '全表关联查询数量',	Select_range_check: '范围检查查询数量',	Sort_merge_passes: '排序合并操作的次数',	Table_locks_waited:'等待表锁的次数',	Threads_cached: '缓存的线程数量',Threads_connected: '当前连接的线程数量',	Threads_created: ' 创建的线程数量',Threads_running: '正在运行的线程数量',	Uptime: '服务运行时间',	Thread_cache_hit_ratio: '线程缓存命中率',	Index_hit_ratio: '索引命中率',	Innodb_index_hit_ratio: 'Innodb索引命中率',	Query_cache_hit_ratio: '查询缓存命中率',	tcp_port: '服务器监听的TCP端口号',uptime_in_days: '服务器运行的天数',connected_clients: '当前连接到Redis服务器的客户端数量',used_memory: '服务器当前占用的内存大小',used_memory_rss: '服务器使用的常驻内存大小',used_memory_peak: '服务器最高峰时使用的内存大小',mem_fragmentation_ratio: '内存碎片率',total_connections_received: '服务器总共接受过的连接数',total_commands_processed: '服务器总共执行过的命令数',instantaneous_ops_per_sec: '服务器瞬时执行命令速率',keyspace_hits: '命中缓存的键值对数量',keyspace_misses: '未命中缓存的键值对数量',latest_fork_usec: '最近一次fork操作消耗的时间',	version: '版本号',now_connection: '最大并发数',maximum_connection: '可以建立的最大连接数',query_num: '查询操作的数量',insert_num: '插入操作的数量',update_num: '更新操作的数量',delete_num: '删除操作的数量',hit_times: '操作的执行时间',misses_hit: '操作执行的失败次数',dataSize: '数据量',storageSize: '存储空间',resident: '当前驻留的内存大小',		ChrootEveryone: '是否需要chroot才能登录FTP服务器',BrokenClientsCompatibility: '是否支持FTP服务器的broken client兼容性',MaxClientsNumber: '最大允许的FTP客户端数量',Daemonize: '是否启用daemon模式',MaxClientsPerIP: '每个IP地址最大允许的FTP客户端数量',VerboseLog: '是否输出详细的FTP日志信息',DisplayDotFiles: '是否显示FTP文件的DOT符号',AnonymousOnly: '是否只允许匿名用户登录FTP服务器',NoAnonymous:  '是否允许匿名用户登录FTP服务器',SyslogFacility: '使用FTP的系统日志记录方式',DontResolve: '是否禁用 DNS 解析',MaxIdleTime: '设置 FTP 服务器的最大空闲时间',PureDB: '纯 FTP 服务器的 PDB 文件路径',UnixAuthentication: '是否使用 Unix 认证方式',LimitRecursion: '设置 FTP 服务器的最大重试次数',AnonymousCanCreateDirs: '是否禁止匿名用户创建目录',MaxLoad: '设置FTP服务器的最大负载',PassivePortRange: 'FTP服务器的passive端口范围',AntiWarez: '启用Anti-WebDAV功能',Umask: '设置文件的权限模式',MinUID: '最小用户ID',AllowUserFXP: '是否允许使用FTPFX协议',AllowAnonymousFXP: '是否允许匿名登FTPFX协议',ProhibitDotFilesWrite: '是否禁止写入dot文件',ProhibitDotFilesRead: '是否禁止读取.dot文件',AutoRename: '用于自动重命名文件',AnonymousCantUpload: '是否禁止匿名用户上传文件',CreateHomeDir: '是否创建FTP服务器的主目录',PIDFile:  '服务器的进程ID文件的路径',MaxDiskUsage: '服务器的最大磁盘使用量',CustomerProof:  '服务器的客户端证书',TLS: '服务器的TLS协议',AllowOverwrite: '是否允许用户覆盖文件',AllowStoreRestart:'是否允许在服务器重启时自动重新加载FTP服务器',		free_memory :'当前Java应用程序可用的内存大小',total_memory:'服务器的总内存大小',max_memory: '可以使用的最大内存大小',maxThreads: '运行的最大线程数',currentThreadCount: '运行的线程数',currentThreadsBusy:  '繁忙的线程数',maxTime: '服务器可以运行的最大时间',processingTime: '服务器处理请求所需的时间',requestCount: '当前正在处理的请求数',errorCount: '当前错误的请求数',bytesReceived: '当前已经接收到的字节数',bytesSent: '当前已经发送的字节数',		RestartTime: '重启时间',UpTime: '的运行时间',TotalAccesses: '已经处理的请求数',TotalKBytes: '已经处理的字节数',ReqPerSec: '每秒处理的请求数',BusyWorkers: '线程数',IdleWorkers: '空闲的线程数',workercpu: '线程的CPU使用率',workermem: '线程的内存使用率',apache_RestartTime: '服务器的重启时间',apache_UpTime: '服务器的运行时间',apache_TotalAccesses: '服务器处理的总请求数',apache_TotalKBytes: '服务器处理的总字节数',apache_ReqPerSec: '平均每秒的请求数',apache_BusyWorkers: '正在处理请求的工作进程数',apache_IdleWorkers: '空闲工作进程数',apache_workercpu: '工作进程的 CPU 占用率',apache_workermem: '工作进程的内存占用',soft_info:'查询结果',	},};

// 旧版bt对象，兼容旧方法
var bt = {
  os: "Linux",
  site: {
    /**
     * @description 获取消息推送
     * @param {function} callback 回调函数
     */
    get_msg_configs: function (callback) {
      var loadT = bt.load("正在获取消息推送配置，请稍候...");
      bt.send(
        "get_msg_configs",
        "config/get_msg_configs",
        {},
        function (rdata) {
          loadT.close();
          if (callback) callback(rdata);
        }
      );
    },

    /**
     * @description 获取网站安全列表
     * @param {string} id 网站id
     * @param {string} name 网站名称
     * @param {function} callback 回调函数
     */
    get_site_security: function (id, name, callback) {
      bt.send(
        "GetSecurity",
        "site/GetSecurity",
        {
          id: id,
          name: name,
        },
        function (rdata) {
          if (callback) callback(rdata);
        }
      );
    },

    /**
     * @description 设置网站安全
     * @param {*} id
     * @param {*} name
     * @param {*} fix
     * @param {*} domains
     * @param {*} status
     * @param {*} return_rule
     * @param {*} http_status
     * @param {*} callback
     */
    set_site_security: function (
      id,
      name,
      fix,
      domains,
      status,
      return_rule,
      http_status,
      callback
    ) {
      var loading = bt.load(lan.site.the_msg);
      bt.send(
        "SetSecurity",
        "site/SetSecurity",
        {
          id: id,
          name: name,
          fix: fix,
          domains: domains,
          status: status,
          return_rule: return_rule,
          http_status: http_status,
        },
        function (rdata) {
          loading.close();
          if (callback) callback(rdata);
        }
      );
    },

    /**
     * @description 全屏展示日志信息 flag 是否走编辑器全屏
     * @param {*} data 时间
     * @param {*} row 配置
     * @param {*} type 类型
     * @param {*} flag 是否走编辑器全屏
     */
    fullScreenLog: function (data, row, type, flag) {
      var layerTemplate = function (options) {
        return layer.open({
          type: 1,
          area: ["100%", "100%"], // 100%全屏
          shade: 0.4,
          title: row.title || "查看【" + row.name + "】" + type + "日志",
          closeBtn: 1,
          content: options.content,
          success: function (layers) {
            $(layers).css({ top: "0", left: "0" });
            if (options.success) options.success(layers);
          },
        });
      };
      // 点击全屏
      $(".full")
        .unbind("click")
        .click(function () {
          layerTemplate({
            content: flag
              ? '<div id="editor-content" style="height: 100%;"></div>'
              : '<pre style="background:black;color:white;height:100%;margin:0">' +
                data.html() +
                "</pre>",
            success: function (layers) {
              if (flag) {
                var editor_content = {
                  el: "editor-content",
                  mode: "dockerfile",
                  content: data.html(),
                  readOnly: row.hasOwnProperty("readOnly")
                    ? row.readOnly
                    : true,
                  theme: "ace/theme/monokai",
                };
                if (row.path) editor_content["path"] = row.path;
                var aEditor = bt.aceEditor(editor_content);
                if (!row.top) {
                  // 是否滚动到最底部
                  setTimeout(function () {
                    aEditor.ACE.getSession().setScrollTop(
                      aEditor.ACE.renderer.scrollBar.scrollHeight
                    );
                  }, 50);
                }
              }
            },
          });
        });
    },
  },
  pub:{
    get_data: function (data, callback, hide) {
      if (!hide) var loading = bt.load(lan['public'].the);
      bt.send('getData', 'data/getData', data, function (rdata) {
        if (loading) loading.close();
        if (callback) callback(rdata);
      });
    },
    set_data_by_key: function (tab, key, obj) {
      var _span = $(obj);
      var _input = $("<input class='baktext' type='text' placeholder='" + lan.ftp.ps + "' />").val(_span.text());
      _span.hide().after(_input);
      _input.focus();
      _input.blur(function () {
        var item = $(this).parents('tr').data('item');
        var _txt = $(this);
        var data = {
          table: tab,
          id: item.id,
        };
        data[key] = _txt.val();
        bt.pub.set_data_ps(data, function (rdata) {
          if (rdata.status) {
            _span.text(_txt.val());
            _span.show();
            _txt.remove();
          }
        });
      });
      _input.keyup(function () {
        if (event.keyCode == 13) {
          _input.trigger('blur');
        }
      });
    },
    set_data_ps: function (data, callback) {
      bt.send('setPs', 'data/setPs', data, function (rdata) {
        if (callback) callback(rdata);
      });
    },
    
    set_server_status: function (serverName, type) {
      var sName = serverName;
      if (bt.contains(serverName, 'php-')) {
        serverName = 'php-fpm-' + serverName.replace('php-', '').replace('.', '');
      }
      if (serverName == 'pureftpd') serverName = 'pure-ftpd';
      if (serverName == 'mysql') serverName = 'mysqld';
      serverName = serverName.replace('_soft', '');
      var data = 'name=' + serverName + '&type=' + type;
      var msg = lan.bt[type];
      var typeName = '';
      switch (type) {
        case 'stop':
          typeName = '停止';
          break;
        case 'restart':
          typeName = '重启';
          break;
        case 'reload':
          typeName = '重载';
          break;
      }
      bt.confirm(
        {
          msg: lan.get('service_confirm', [msg, serverName]),
          title: typeName + serverName + '服务',
        },
        function () {
          var load = bt.load(lan.get('service_the', [msg, serverName]));
          bt.send('system', 'system/ServiceAdmin', data, function (rdata) {
            load.close();
            var f = rdata.status ? lan.get('service_ok', [serverName, msg]) : rdata.msg || lan.get('service_err', [serverName, msg]);
            if(rdata.status) {
                bt.msg({
                  msg: f,
                  icon: rdata.status,
                });
            }else {
                layer.msg(f,{icon: 2,closeBtn: 2, time: 0,shade: 0.3, shadeClose: true})
            }
  
            if (rdata.status) {
              if ($('.bt-soft-menu').length) {
                setTimeout(function () {
                  bt.send('get_soft_find', 'plugin/get_soft_find', {sName: sName}, function (res) {
                    $('.bt-soft-menu').data('data', res)
                    $('.bt-soft-menu .bgw').click()
                  })
                }, 1000);
              } else {
                setTimeout(function () {
                  window.location.reload();
                }, 1000);
              }
              if (!rdata.status) {
                bt.msg(rdata);
              }
            }
          });
        }
      );
    },
    set_ftp_logs: function (type) {
      var serverName = 'pure-ftpd日志';
      var data = 'exec_name=' + type;
      var typeName = '开启';
      switch (type) {
        case 'stop':
          typeName = '关闭';
          break;
      }
      var status = type == 'stop' ? false : true;
      layer.confirm(
        typeName + 'pure-ftpd日志管理后，' + (status ? '将记录所有FTP用户的登录、操作记录' : '将无法记录所有FTP用户的登录、操作记录') + '，是否继续操作？',
        {
          title: typeName + serverName + '管理',
          closeBtn: 2,
          icon: 3,
          cancel: function () {
            $('#isFtplog').prop('checked', !status);
          },
        },
        function () {
          var load = bt.load('正在' + typeName + 'pure-ftpd日志管理，请稍后...');
          bt.send('ftp', 'ftp/set_ftp_logs', data, function (rdata) {
            load.close();
            bt.msg(rdata);
            $('.bt-soft-menu p').eq(3).click();
          });
        },
        function () {
          $('#isFtplog').prop('checked', !status);
        }
      );
    },
    get_ftp_logs: function (callback) {
      bt.send('ftp', 'ftp/set_ftp_logs', { exec_name: 'getlog' }, function (res) {
        var _status = res.msg === 'start' ? true : false;
        if (callback) callback(_status);
      });
    },
    set_server_status_by: function (data, callback) {
      bt.send('system', 'system/ServiceAdmin', data, function (rdata) {
        if (callback) callback(rdata);
      });
    },
    get_task_count: function (callback) {
      bt.send('GetTaskCount', 'ajax/GetTaskCount', {}, function (rdata) {
        $('.task').text(rdata);
        if (callback) callback(rdata);
      });
    },
    check_install: function (callback) {
      bt.send('CheckInstalled', 'ajax/CheckInstalled', {}, function (rdata) {
        if (callback) callback(rdata);
      });
    },
    get_user_info: function (callback) {
      var loading = bt.load();
      bt.send('GetUserInfo', 'ssl/GetUserInfo', {}, function (rdata) {
        loading.close();
        if (callback) callback(rdata);
      });
    },
    show_hide_pass: function (obj) {
      var a = 'glyphicon-eye-open';
      var b = 'glyphicon-eye-close';
  
      if ($(obj).hasClass(a)) {
        $(obj).removeClass(a).addClass(b);
        $(obj).prev().text($(obj).prev().attr('data-pw'));
      } else {
        $(obj).removeClass(b).addClass(a);
        $(obj).prev().text('**********');
      }
    },
    copy_pass: function (password) {
      var clipboard = new ClipboardJS('#bt_copys');
      clipboard.on('success', function (e) {
        bt.msg({
          msg: '复制成功',
          icon: 1,
        });
      });
  
      clipboard.on('error', function (e) {
        bt.msg({
          msg: '复制失败，浏览器不兼容!',
          icon: 2,
        });
      });
      $('#bt_copys').attr('data-clipboard-text', password);
      $('#bt_copys').click();
    },
    login_btname: function (username, password, callback) {
      var loadT = bt.load(lan.config.token_get);
      bt.send(
        'GetToken',
        'ssl/GetToken',
        {
          username: username,
          password: password,
        },
        function (rdata) {
          loadT.close();
          bt.msg(rdata);
          if (rdata.status) {
            if (callback) callback(rdata);
          }
        }
      );
    },
    bind_btname: function (callback) {
      new BindAccount().bindUserView(1);
    },
    unbind_bt: function () {
      var name = $("input[name='btusername']").val();
      bt.confirm(
        {
          msg: lan.config.binding_un_msg,
          title: lan.config.binding_un_title,
        },
        function () {
          bt.send('DelToken', 'ssl/DelToken', {}, function (rdata) {
            bt.msg(rdata);
            $("input[name='btusername']").val('');
          });
        }
      );
    },
    get_menm: function (callback) {
      var loading = bt.load();
      bt.send('GetMemInfo', 'system/GetMemInfo', {}, function (rdata) {
        loading.close();
        if (callback) callback(rdata);
      });
    },
    on_edit_file: function (type, fileName, mode) {
      if (type != 0) {
        var l = $('#PathPlace input').val();
        var body = encodeURIComponent($('#textBody').val());
        var encoding = $('select[name=encoding]').val();
        var loadT = bt.load(lan.bt.save_file);
        bt.send('SaveFileBody', 'files/SaveFileBody', 'data=' + body + '&path=' + fileName + '&encoding=' + encoding, function (rdata) {
          if (type == 1) loadT.close();
          bt.msg(rdata);
        });
        return;
      }
      var loading = bt.load(lan.bt.read_file);
      ext = bt.get_file_ext(fileName);
  
      bt.send('GetFileBody', 'files/GetFileBody', 'path=' + fileName, function (rdata) {
        if (!rdata.status) {
          bt.msg({
            msg: rdata.msg,
            icon: 5,
          });
          return;
        }
        loading.close();
        var u = ['utf-8', 'GBK', 'GB2312', 'BIG5'];
        var n = '';
        var m = '';
        var o = '';
        for (var p = 0; p < u.length; p++) {
          m = rdata.encoding === u[p] ? 'selected' : '';
          n += '<option value="' + u[p] + '" ' + m + '>' + u[p] + '</option>';
        }
        var aceEditor = {},
          r = bt.open({
            type: 1,
            shift: 5,
            closeBtn: 1,
            area: ['80%', '80%'],
            shade: false,
            title: lan.bt.edit_title + '[' + fileName + ']',
            btn: [lan['public'].save, lan['public'].close],
            content:
              '\
                <form class="bt-form pd20">\
                  <div class="line">\
                    <p style="position: relative; color:red;margin-bottom:10px">' +
              lan.bt.edit_ps +
              '<select class="bt-input-text" name="encoding" style="width: 74px;position: absolute;top: 0;right: 0;height: 22px;z-index: 9999;border-radius: 0;">' +
              n +
              '</select>\
                    </p>\
                    <div class="mCustomScrollbar bt-input-text ace_config_editor_scroll" id="textBody" style="width:100%;margin:0 auto;line-height: 1.8;position: relative;top: 10px;min-height:300px;"></div>\
                  </div>\
                </form>',
            yes: function (layer, index) {
              bt.saveEditor(aceEditor);
            },
            btn2: function (layer, index) {
              r.close();
            },
            success: function (layers) {
              function resize() {
                var $layers = $(layers).find('.layui-layer-content').height();
                $('#textBody').height($layers - 80);
              }
              resize();
              $(window).on('resize', resize);
              aceEditor = bt.aceEditor({
                el: 'textBody',
                content: rdata.data,
                mode: mode,
                saveCallback: function (val) {
                  bt.send(
                    'SaveFileBody',
                    'files/SaveFileBody',
                    {
                      path: fileName,
                      encoding: $('[name="encoding"] option:selected').val(),
                      data: val,
                    },
                    function (rdata) {
                      bt.msg(rdata);
                    }
                  );
                },
              });
            },
          });
      });
    },
  },
  soft: {
    /**
     * @description 安装插件
     * @param {*} name
     * @param {*} that
     * @returns
     */
    install: function (name, that) {
      window.parent.postMessage("installPlugin::" + name, "*"); // 调用父级页面的方法
    },

    /**
     * @description 卸载插件
     * @param {string} name 插件名称
     * @param {function} callback 回调函数
     */
    get_soft_find: function (name, callback) {
      var loadT = bt.load();
      bt.send(
        "get_soft_find",
        "plugin/get_soft_find",
        {
          sName: name,
        },
        function (rdata) {
          // bt.soft.softData = rdata
          loadT.close();
          if (callback) callback(rdata);
        }
      );
    },

    /**
     * @description 获取配置路径
     * @param {string} name 插件名称
     * @returns 
     */
    get_config_path: function (name) {
      var fileName = '';
      if (bt.os == 'Linux') {
        switch (name) {
          case 'mysql':
          case 'mysqld':
            fileName = '/etc/my.cnf';
            break;
          case 'nginx':
            fileName = '/www/server/nginx/conf/nginx.conf';
            break;
          case 'pureftpd':
            fileName = '/www/server/pure-ftpd/etc/pure-ftpd.conf';
            break;
          case 'apache':
            fileName = '/www/server/apache/conf/httpd.conf';
            break;
          case 'tomcat':
            fileName = '/www/server/tomcat/conf/server.xml';
            break;
          case 'memcached':
            fileName = '/etc/init.d/memcached';
            break;
          case 'redis':
            fileName = '/www/server/redis/redis.conf';
            break;
          case 'openlitespeed':
            fileName = '/usr/local/lsws/conf/httpd_config.conf';
            break;
          default:
            fileName = '/www/server/php/' + name + '/etc/php.ini';
            break;
        }
      }
      return fileName;
    },

    /**
     * @description 设置插件配置，
     * @param {string} name 插件名称
     * @param {string} title 插件标题
     * @param {string} version 插件版本
     * @param {string} endtime 插件到期时间
     * @returns
     */
    set_lib_config: function (name, title, version, endtime) {
      // endtime 软件商店-最近使用-到期
      var list = [
        "btwaf_httpd",
        "btwaf",
        "total",
        "rsync",
        "tamper_proof",
        "syssafe",
        "task_manager",
        "security_notice",
        "tamper_core",
        "bt_security",
        "system_scan",
        "vuln_push",
        "disk_analysis",
      ];
      if (list.indexOf(name) !== -1 && parseInt(endtime) < 0) {
        // 已到期
        return bt.soft.view_expire({
          type: "plugin",
          name: name,
          endtime: endtime,
        });
      }
      bt_tools.send(
        { url: "/plugin?action=a&name=" + name },
        function (res) {
          if (res.msg && res.msg.indexOf("您无操作此插件的权限") !== -1) {
            return bt_tools.msg(res);
          }
          var loadT = bt.load(lan.soft.menu_temp);
          $.ajax({
            url: "/plugin?action=getConfigHtml",
            data: {
              name: name,
              version: version,
            },
            type: "get",
            success: function (rhtml) {
              loadT.close();
              if (rhtml.status === false) {
                if (name == "phpguard") {
                  layer.msg(lan.soft.menu_phpsafe, {
                    icon: 1,
                  });
                } else {
                  layer.msg(rhtml.msg, {
                    icon: 2,
                  });
                }
                return;
              }

              function openPulige() {
                bt.open({
                  type: 1,
                  shift: 5,
                  offset: "auto",
                  closeBtn: 2,
                  area:
                    title.indexOf("Node.js版本管理器") > -1
                      ? ["700px", "710px"]
                      : "700px",
                  title:
                    '<img style="width: 24px;margin-right: 5px;margin-left: -10px;margin-top: -3px;" src="/static/img/soft_ico/ico-' +
                    name +
                    '.png" />' +
                    title,
                  content: rhtml.replace(
                    '"javascript/text"',
                    '"text/javascript"'
                  ),
                  success: function (layers) {
                    if (rhtml.indexOf("CodeMirror") != -1) {
                      loadLink(["/static/codemirror/lib/codemirror.css"]);
                      loadScript([
                        "/static/codemirror/lib/codemirror.js?v=1764728423",
                        "/static/codemirror/addon/edit/editAll.js?v=1764728423",
                        "/static/codemirror/mode/modeAll.js?v=1764728423",
                        "/static/codemirror/addon/dialog/dialog.js?v=1764728423",
                        "/static/codemirror/addon/search/search.js?v=1764728423",
                        "/static/codemirror/addon/scroll/annotatescrollbar.js?v=1764728423",
                      ]);
                    }
                    // 弹窗高度大于窗口高度时，设置弹窗高度为窗口高度
                    var win_height = $(window).height(),
                      layer_height = $(layers).height();
                    if (layer_height >= win_height) {
                      setTimeout(function () {
                        $(layers).css({
                          top: "0px",
                        });
                      }, 100);
                    } else {
                      $(layers)
                        .find(".layui-layer-content")
                        .removeAttr("style")
                        .css({
                          "background-color": "#fff",
                        });
                      $(layers).css({
                        top: (win_height - layer_height) / 2 + "px",
                      });
                      $(layers)
                        .find(".layui-layer-close")
                        .addClass("layui-layer-close2")
                        .removeClass("layui-layer-close1");
                    }
                  },
                  cancel: function (index) {
                    layer.close(index);
                    window.parent.postMessage("closePlugin", "*");
                    return false;
                  },
                });
              }

              // rhtml = rhtml.replace(/,\s+error:\s+function(.|\n|\r)+obj.error\(ex\);\s+\}/,"");
              if (
                name == "total" ||
                name == "rsync" ||
                name == "syssafe" ||
                name == "tamper_proof"
              ) {
                if (bt.get_storage(name + "_config") == "true") {
                  openPulige();
                } else {
                  bt_tools.send(
                    {
                      url: "/plugin?action=check_plugin_settings",
                      data: {
                        soft_name: name,
                      },
                    },
                    function (res) {
                      if (res["on_config"]) {
                        openPulige();
                      } else {
                        layer.open({
                          type: 0,
                          area: "200px",
                          title: "【" + title + "】插件",
                          closeBtn: 2,
                          icon: 3,
                          btn: ["确定", "取消"],
                          content:
                            "<div>" +
                            "<span>检测到【" +
                            title +
                            "】插件存在配置文件</span>" +
                            '<div style="display: flex;margin-top: 10px">' +
                            "<span>配置文件</span>" +
                            "<div>" +
                            '<div class="indicators-label" style="margin-left: 10px;" bt-event-click="indicatorsType" data-name="pv"><input type="radio" value="1" name="1" checked><label class="check_pv" style="font-weight:normal;cursor: pointer">导入</label><input  type="radio" name="1" value="0"><label class="check_pv" style="margin-left: 10px;   margin-bottom: 0;    font-weight: normal;cursor: pointer" class="check_pv" style="font-weight:normal">不导入</label></div>' +
                            "</div>" +
                            "</div>" +
                            "</div>",
                          success: function (layers, indexs) {
                            $(".check_pv").click(function () {
                              $(this).prev().prop("checked", true);
                            });
                            $(".layui-layer-btn1").click(function () {
                              bt.set_storage(name + "_config", true);
                              openPulige();
                              layer.close(indexs);
                            });
                          },
                          yes: function (index, layero) {
                            bt.set_storage(name + "_config", true);
                            if ($('input[name="1"]:checked').val() == 1) {
                              bt_tools.send(
                                {
                                  url: "/plugin?action=load_plugin_settings",
                                  data: { soft_name: name },
                                },
                                function (res) {
                                  if (res.status) {
                                    layer.close(index);
                                    openPulige();
                                  }
                                },
                                "导入配置文件"
                              );
                            } else {
                              layer.close(index);
                              openPulige();
                            }
                          },
                          cancel: function (index) {
                            bt.set_storage(name + "_config", true);
                            layer.close(index);
                            openPulige();
                          },
                        });
                      }
                    }
                  );
                }
              } else {
                openPulige();
              }
            },
          });
        },
        { verify: false }
      );
    },

    /**
     * @description 获取插件列表
     * @param {number} p 页码
     * @param {number} type 类型
     * @param {string} search 搜索
     * @param {function} callback 回调函数
     * @param {number} row 行数
     */
    get_soft_list: function (p, type, search, callback, row) {
      if (p == undefined) p = 1;
      if (type == undefined) type = 0;
      if (search == undefined) search = "";
      var force = bt.soft_flush_cache || 0;
      if (row == undefined) row = 12;
      p = p + "";
      if (p.indexOf("not_load") == -1) {
        var loading = bt.load(lan["public"].the, 1);
      } else {
        var loading = null;
        p = p.split("not_load")[0];
      }

      bt.send(
        "get_soft_list",
        "plugin/get_soft_list",
        {
          p: p,
          type: type,
          tojs: "soft.get_list",
          force: force,
          query: search,
          row: row,
        },
        function (rdata) {
          if (loading) loading.close();
          bt.soft.softList = rdata.list.data;
          if (rdata.list.data.length % 3 !== 0) {
            $(".soft_card_page").css("justify-content", "flex-start");
          } else {
            $(".soft_card_page").css("justify-content", "space-between");
          }
          bt.set_cookie("force", 0);
          bt.set_cookie("ltd_end", rdata.ltd);
          bt.set_cookie("pro_end", rdata.pro);
          if (callback) callback(rdata);
        }
      );
      bt.soft_flush_cache = 0;
    },

    /**
     * @description 升级企业版
     */
    updata_ltd: function () {
      // 升级企业版
      window.parent.postMessage("ProductLtdBuy", "*");
    },

    /**
     * @description 产品购买
     * @param {object} options 选项
     */
    product_pay_view: function (options) {
      window.parent.postMessage(
        "ProductPayView::" + JSON.stringify(options),
        "*"
      );
    },
  },
  firewall: {
    /**
     * @description 添加端口
     * @param {string} type 类型
     * @param {string} port 端口
     * @param {string} ps 描述
     * @param {function} callback 回调函数
     * @returns
     */
    add_accept_port: function (type, port, ps, callback) {
      var action = "AddDropAddress";
      if (type == "port") {
        ports = port.split(":");
        if (port.indexOf("-") != -1) ports = port.split("-");
        for (var i = 0; i < ports.length; i++) {
          if (!bt.check_port(ports[i])) {
            layer.msg("可用端口范围：1-65535", { icon: 2 });
            // layer.msg(lan.firewall.port_err, {
            //   icon: 5
            // });
            return;
          }
        }
        action = "AddAcceptPort";
      }

      if (ps.length < 1) {
        layer.msg(lan.firewall.ps_err, {
          icon: 2,
        });
        return -1;
      }
      loading = bt.load();
      bt.send(
        action,
        "firewall/" + action,
        {
          port: port,
          type: type,
          ps: ps,
        },
        function (rdata) {
          loading.close();
          if (callback) callback(rdata);
        }
      );
    },

    /**
     * @description 删除端口
     * @param {number} id - 端口的唯一标识符。
     * @param {number} port - 要删除的端口号。
     * @param {function} callback - 删除操作完成后的回调函数。
     */
    del_accept_port: function (id, port, callback) {
      var action = "DelDropAddress";
      if (port.indexOf(".") == -1) {
        action = "DelAcceptPort";
      }
      bt.confirm(
        {
          msg: lan.get("confirm_del", [port]),
          title: lan.firewall.del_title,
        },
        function (index) {
          var loadT = bt.load(lan["public"].the_del);
          bt.send(
            action,
            "firewall/" + action,
            {
              id: id,
              port: port,
            },
            function (rdata) {
              loadT.close();
              if (callback) callback(rdata);
            }
          );
        }
      );
    },
  },
  system: {
    /**
     * @description 重启面板
     * @param {function} callback 回调函数
     */
    rep_panel: function (callback) {
      var loading = bt.load(lan.index.rep_panel_the);
      bt.send("RepPanel", "system/RepPanel", {}, function (rdata) {
        loading.close();
        if (rdata) {
          if (callback)
            callback({
              status: rdata,
              msg: lan.index.rep_panel_ok,
            });
          bt.system.reload_panel();
        }
      });
    },
  },
  database:{
    /**
     * @description 获取数据库列表
     * @param {*} page 
     * @param {*} search 
     * @param {*} callback 
     */
    get_list: function (page, search, callback) {
      if (page == undefined) page = 1;
      search = search == undefined ? '' : search;
      var order = bt.get_cookie('order') ? '&order=' + bt.get_cookie('order') : '';

      var data = 'tojs=database.get_list&table=databases&limit=15&p=' + page + '&search=' + search + order;
      bt.pub.get_data(data, function (rdata) {
        if (callback) callback(rdata);
      });
    },
  },
  /**
   * @description 发送消息推送，通知主界面刷新路径
   * @param {string} path 路径
   */
  refreshMain: function (path) {
    window.parent.postMessage("refreshMain" + (path ? "::" + path : ""), "*");
  },

  /**
   * @description 是否为整数
   * @param {*} obj
   * @returns
   */
  isInteger: function (obj) {
    //是否整数
    return (obj | 0) === obj;
  },

  /**
   * @description 验证ip信息
   * @param {string} ip ip地址
   * @returns
   */
  check_ip: function (ip) {
    var reg =
      /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/;
    return reg.test(ip);
  },

  /**
   * @description 验证ip段
   * @param {*} ips
   * @returns
   */
  check_ips: function (ips) {
    var reg = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$/;
    return reg.test(ips);
  },

  /**
   * @description 验证域名列表
   * @param {Array} domainInfo 域名信息
   * @param {boolean} isPort 是否带端口
   * @returns
   */
  check_domain_list: function (domainInfo, isPort) {
    var domainList = domainInfo.trim().replace(" ", "").split("\n");
    for (var i = 0; i < domainList.length; i++) {
      var item = domainList[i];
      if (isPort && !bt.check_domain_port(item)) {
        bt.msg({
          status: false,
          msg: "第" + (i + 1) + "行【" + item + "】域名格式错误",
        });
        return false;
      }
      if (!isPort && !bt.check_domain(item)) {
        bt.msg({
          status: false,
          msg: "第" + (i + 1) + "行【" + item + "】域名格式错误",
        });
        return false;
      }
    }
    return domainList;
  },

  /**
   * @description 验证URL
   * @param {string} url url地址
   * @returns
   */
  check_url: function (url) {
    var reg = /^((https|http|ftp|rtsp|mms)?:\/\/)[^\s]+/;
    return reg.test(url);
  },

  /**
   * @description 验证端口
   * @param {string} port 端口
   * @returns
   */
  check_port: function (port) {
    var reg =
      /^([1-9]|[1-9]\d|[1-9]\d{2}|[1-9]\d{3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])$/;
    return reg.test(port);
  },

  /**
   * @description 验证中文
   * @param {string} str 字符串
   * @returns
   */
  check_chinese: function (str) {
    var reg = /[\u4e00-\u9fa5]/;
    return reg.test(str);
  },

  /**
   * @description 验证域名格式
   * @param {string} domain 域名
   * @returns
   */
  check_domain: function (domain) {
    var reg =
      /^([\w\u4e00-\u9fa5\-\*]{1,100}\.){1,10}([\w\u4e00-\u9fa5\-]{1,24}|[\w\u4e00-\u9fa5\-]{1,24}\.[\w\u4e00-\u9fa5\-]{1,24})$/;
    return reg.test(bt.strim(domain));
  },

  /**
   * @description 验证域名带端口号
   * @param {string} domain 域名
   * @returns
   */
  check_domain_port: function (domain) {
    //验证域名带端口号
    var reg =
      /^([\w\u4e00-\u9fa5\-\*]{1,100}\.){1,10}([\w\u4e00-\u9fa5\-]{1,24}|[\w\u4e00-\u9fa5\-]{1,24}\.[\w\u4e00-\u9fa5\-]{1,24})(:([1-9]|[1-9]\d|[1-9]\d{2}|[1-9]\d{3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5]))?$/;
    return reg.test(bt.strim(domain));
  },

  /**
   * @description 验证图片
   * @param {string} fileName 文件名
   * @returns
   */
  check_img: function (fileName) {
    var exts = ["jpg", "jpeg", "png", "bmp", "gif", "tiff", "ico"];
    var check = bt.check_exts(fileName, exts);
    return check;
  },

  /**
   * @description 验证邮箱
   * @param {string} email 邮箱
   * @returns
   */
  check_email: function (email) {
    var reg = /\w[-\w.+]*@([A-Za-z0-9][-A-Za-z0-9]+\.)+[A-Za-z]{2,14}/;
    return reg.test(email);
  },

  /**
   * @description 验证手机号
   * @param {string} phone 手机号
   * @returns
   */
  check_phone: function (phone) {
    var reg = /^1(3|4|5|6|7|8|9)\d{9}$/;
    return reg.test(phone);
  },

  /**
   * @description 验证文件是否压缩包
   * @param {string} fileName 文件名
   * @returns
   */
  check_zip: function (fileName) {
    var ext = fileName.split(".");
    var extName = ext[ext.length - 1].toLowerCase();
    if (extName == "zip") return 0;
    if (extName == "rar") return 2;
    if (extName == "gz" || extName == "tgz") return 1;
    return -1;
  },

  /**
   * @description 验证是否为文本文件
   * @param {string} fileName 文件名
   * @returns
   */
  check_text: function (fileName) {
    var exts = [
      "rar",
      "zip",
      "tar.gz",
      "gz",
      "iso",
      "xsl",
      "doc",
      "xdoc",
      "jpeg",
      "jpg",
      "png",
      "gif",
      "bmp",
      "tiff",
      "exe",
      "so",
      "7z",
      "bz",
    ];
    return bt.check_exts(fileName, exts) ? false : true;
  },

  /**
   * @description 验证文件后缀
   * @param {string} fileName 文件名
   * @param {Array} exts 后缀
   * @returns
   */
  check_exts: function (fileName, exts) {
    var ext = fileName.split(".");
    if (ext.length < 2) return false;
    var extName = ext[ext.length - 1].toLowerCase();
    for (var i = 0; i < exts.length; i++) {
      if (extName == exts[i]) return true;
    }
    return false;
  },

  /**
   * @description 验证版本
   * @param {string} version 版本
   * @param {string} cloud_version 云版本
   * @returns
   */
  check_version: function (version, cloud_version) {
    var arr1 = version.split("."); //
    var arr2 = cloud_version.split(".");
    var leng = arr1.length > arr2.length ? arr1.length : arr2.length;
    while (leng - arr1.length > 0) {
      arr1.push(0);
    }
    while (leng - arr2.length > 0) {
      arr2.push(0);
    }
    for (var i = 0; i < leng; i++) {
      if (i == leng - 1) {
        if (arr1[i] != arr2[i]) return 2; //子版本匹配不上
      } else {
        if (arr1[i] != arr2[i]) return -1; //版本匹配不上
      }
    }
    return 1; //版本正常
  },

  /**
   * @description 合并url
   * @param {string} url url地址
   * @returns
   */
  url_merge: function (url) {
    var origin = window.location.origin;
    return (
      (cdn_url !== "/static" ? cdn_url : origin + cdn_url) +
      url +
      "?version=" +
      panel_version +
      "&repair=" +
      update_code
    );
  },

  /**
   * @description 替换全部内容
   * @param {string} str 字符串正则
   * @param {string} old_data 旧内容
   * @param {string} new_data 新内容
   * @returns
   */
  replace_all: function (str, old_data, new_data) {
    var reg_str = "/(" + old_data + "+)/g";
    var reg = eval(reg_str);
    return str.replace(reg, new_data);
  },

  /**
   * @description 获取文件后缀
   * @param {string} fileName 文件名
   * @returns
   */
  get_file_ext: function (fileName) {
    var text = fileName.split(".");
    var n = text.length - 1;
    text = text[n];
    return text;
  },

  /**
   * @description 获取文件路径
   * @param {string} filename 文件名
   * @returns
   */
  get_file_path: function (filename) {
    var arr = filename.split("/");
    path = filename.replace("/" + arr[arr.length - 1], "");
    return path;
  },

  /**
   * @description 获取时间戳
   * @param {number} a 时间，可为空
   * @returns
   */
  get_date: function (a) {
    var dd = new Date();
    dd.setTime(
      dd.getTime() +
        (a == undefined || isNaN(parseInt(a)) ? 0 : parseInt(a)) * 86400000
    );
    var y = dd.getFullYear();
    var m = dd.getMonth() + 1;
    var d = dd.getDate();
    return y + "-" + (m < 10 ? "0" + m : m) + "-" + (d < 10 ? "0" + d : d);
  },

  /**
   * @description 获取表单数据
   * @param {string} select 选择器
   * @returns
   */
  get_form: function (select) {
    var sarr = $(select).serializeArray();
    var iarr = {};
    for (var i = 0; i < sarr.length; i++) {
      iarr[sarr[i].name] = sarr[i].value;
    }
    return iarr;
  },

	ltrim: function (str, r) {
		var reg_str = '/(^\\' + r + '+)/g';
		var reg = eval(reg_str);
		str = str.replace(reg, '');
		return str;
	},
	rtrim: function (str, r) {
		var reg_str = '/(\\' + r + '+$)/g';
		var reg = eval(reg_str);
		str = str.replace(reg, '');
		return str;
	},
	strim: function (str) {
		var reg_str = '/ /g';
		var reg = eval(reg_str);
		str = str.replace(reg, '');
		return str;
	},
	contains: function (str, substr) {
		if (str) {
			return str.indexOf(substr) >= 0;
		}
		return false;
	},

  /**
   * @description 格式化大小
   * @param {number} bytes 字节
   * @param {boolean} is_unit 是否显示单位
   * @param {number} fixed 小数点位置
   * @param {string} end_unit 结束单位
   * @returns
   */
  format_size: function (
    bytes,
    is_unit,
    fixed,
    end_unit //字节转换，到指定单位结束 is_unit：是否显示单位  fixed：小数点位置 end_unit：结束单位
  ) {
    if (bytes == undefined) return 0;

    if (is_unit == undefined) is_unit = true;
    if (fixed == undefined) fixed = 2;
    if (end_unit == undefined) end_unit = "";

    if (typeof bytes == "string") bytes = parseInt(bytes);
    var unit = [" B", " KB", " MB", " GB", "TB"];
    var c = 1024;
    for (var i = 0; i < unit.length; i++) {
      var cUnit = unit[i];
      if (end_unit) {
        if (cUnit.trim() == end_unit.trim()) {
          var val = i == 0 ? bytes : fixed == 0 ? bytes : bytes.toFixed(fixed);
          if (is_unit) {
            return val + cUnit;
          } else {
            val = parseFloat(val);
            return val;
          }
        }
      } else {
        if (bytes < c) {
          var val = i == 0 ? bytes : fixed == 0 ? bytes : bytes.toFixed(fixed);
          if (is_unit) {
            return val + cUnit;
          } else {
            val = parseFloat(val);
            return val;
          }
        }
      }

      bytes /= c;
    }
  },

  /**
   * @description 格式化时间
   * @param {number} tm 时间戳
   * @param {string} format 格式
   * @returns
   */
  format_data: function (tm, format) {
    if (format == undefined) format = "yyyy/MM/dd hh:mm:ss";
    tm = tm.toString();
    if (tm.length > 10) {
      tm = tm.substring(0, 10);
    }
    var data = new Date(parseInt(tm) * 1000);
    var o = {
      "M+": data.getMonth() + 1, //month
      "d+": data.getDate(), //day
      "h+": data.getHours(), //hour
      "m+": data.getMinutes(), //minute
      "s+": data.getSeconds(), //second
      "q+": Math.floor((data.getMonth() + 3) / 3), //quarter
      S: data.getMilliseconds(), //millisecond
    };
    if (/(y+)/.test(format))
      format = format.replace(
        RegExp.$1,
        (data.getFullYear() + "").substr(4 - RegExp.$1.length)
      );
    for (var k in o)
      if (new RegExp("(" + k + ")").test(format))
        format = format.replace(
          RegExp.$1,
          RegExp.$1.length == 1
            ? o[k]
            : ("00" + o[k]).substr(("" + o[k]).length)
        );

    return format;
  },

  /**
   * @description 格式化路径
   * @param {string} path 路径
   * @returns
   */
  format_path: function (path) {
    var reg = /(\\)/g;
    path = path.replace(reg, "/");
    return path;
  },

  /**
   * @description 获取随机字符串
   * @param {number} len 长度
   * @returns
   */
  get_random: function (len) {
    len = len || 32;
    var $chars = "AaBbCcDdEeFfGHhiJjKkLMmNnPpRSrTsWtXwYxZyz2345678"; // 默认去掉了容易混淆的字符oOLl,9gq,Vv,Uu,I1
    var maxPos = $chars.length;
    var pwd = "";
    for (i = 0; i < len; i++) {
      pwd += $chars.charAt(Math.floor(Math.random() * maxPos));
    }
    return pwd;
  },

  /**
   * @description 刷新密码
   * @param {number} length 长度
   * @param {string} obj 节点
   */
  refresh_pwd: function (length, obj) {
    if (obj == undefined) obj = "MyPassword";
    var _input = $("#" + obj);
    if (_input.length > 0) {
      _input.val(bt.get_random(length));
    } else {
      $("." + obj).val(bt.get_random(length));
    }
  },

  /**
   * @description 生成随机数
   * @param {number} min 最小值
   * @param {number} max 最大值
   * @returns
   */
  get_random_num: function (min, max) {
    var range = max - min;
    var rand = Math.random();
    var num = min + Math.round(rand * range); //四舍五入
    return num;
  },
  /**
   *  @description  生成计算数字(加强计算，用于删除重要数据二次确认)
   * */
  get_random_code: function () {
    var flist = [20, 21, 22, 23];

    var num1 = bt.get_random_num(13, 19);
    var t1 = num1 % 10;

    var num2 = bt.get_random_num(13, 29);
    var t2 = num2 % 10;

    while ($.inArray(num2, flist) >= 0 || t1 + t2 <= 10 || t1 == t2) {
      num2 = bt.get_random_num(13, 29);
      t2 = num2 % 10;
    }
    return { num1: num1, num2: num2 };
  },
  /**
   * @description 设置本地存储，local和session
   * @param {String} type 存储类型，可以为空，默认为session类型。
   * @param {String} key 存储键名
   * @param {String} val 存储键值
   * @return 无返回值
   */
  set_storage: function (type, key, val) {
    if (type != "local" && type != "session")
      (val = key), (key = type), (type = "local");
    window[type + "Storage"].setItem(key, val);
  },

  /**
   * @description 获取本地存储，local和session
   * @param {String} type 存储类型，可以为空，默认为session类型。
   * @param {String} key 存储键名
   * @return {String} 返回存储键值
   */
  get_storage: function (type, key) {
    if (type != "local" && type != "session") (key = type), (type = "local");
    return window[type + "Storage"].getItem(key);
  },

  /**
   * @description 删除指定本地存储，local和session
   * @param {String} type 类型，可以为空，默认为session类型。
   * @param {String} key 键名
   * @return 无返回值
   */
  remove_storage: function (type, key) {
    if (type != "local" && type != "session") (key = type), (type = "local");
    window[type + "Storage"].removeItem(key);
  },

  /**
   * @description 删除指定类型的所有存储信息储，local和session
   * @param {String} type 类型，可以为空，默认为session类型。
   * @return 无返回值
   */
  clear_storage: function (type) {
    if (type != "local" && type != "session") (key = type), (type = "local");
    window[type + "Storage"].clear();
  },

  /**
   * @description 设置cookie
   * @param {String} key 键名
   * @param {String} val 键值
   * @param {Number} time 过期时间
   */
  set_cookie: function (key, val, time) {
    if (time != undefined) {
      var exp = new Date();
      exp.setTime(exp.getTime() + time);
      time = exp.toGMTString();
    } else {
      var Days = 30;
      var exp = new Date();
      exp.setTime(exp.getTime() + Days * 24 * 60 * 60 * 1000);
      time = exp.toGMTString();
    }
    var is_https = window.location.protocol == "https:";
    var samesite = ";Secure; Path=/; SameSite=None";
    document.cookie =
      "http" +
      (is_https ? "s" : "") +
      "_" +
      key +
      "=" +
      encodeURIComponent(val) +
      ";expires=" +
      time +
      (is_https ? samesite : "");
  },

  /**
   * @description 获取cookie
   * @param {String} key 键名
   * @returns
   */
  get_cookie: function (key) {
    var is_https = window.location.protocol == "https:";
    var arr,
      reg = new RegExp(
        "(^| )http" + (is_https ? "s" : "") + "_" + key + "=([^;]*)(;|$)"
      );
    if ((arr = document.cookie.match(reg))) {
      var val = "";
      if (arr.length > 2) {
        try {
          val = decodeURIComponent(arr[2]);
        } catch (error) {
          val = arr[2];
        }
      }
      return val == "undefined" ? "" : val;
    } else {
      return null;
    }
  },

  /**
   * @description 删除cookie
   * @param {String} key 键名
   */
  clear_cookie: function (key) {
    bt.set_cookie(key, "", new Date());
  },

  /**
   * @description 普通提示弹窗
   * @param {Object} config 弹窗对象 {title:标题, msg:提示内容}
   * @param {function} callback 确认回调函数
   * @param {function} callback1 取消回调函数
   */
  simple_confirm: function (config, callback, callback1) {
    layer.open({
      type: 1,
      title: config.title,
      area: "430px",
      closeBtn: 2,
      shadeClose: false,
      btn: config["btn"]
        ? config.btn
        : [lan["public"].ok, lan["public"].cancel],
      content:
        '<div class="bt-form hint_confirm pd30">\
            <div class="hint_title">\
                <i class="hint-confirm-icon"></i>\
                <div class="hint_con">' +
        config.msg +
        "</div>\
            </div>\
        </div>",
      yes: function (index, layero) {
        if (callback && typeof callback(index) === "undefined")
          layer.close(index);
      },
      btn2: function (index) {
        //取消返回回调
        if (callback1 && typeof callback1(index) === "undefined")
          layer.close(index);
      },
      cancel: function (index) {
        //取消返回回调
        if (callback1 && typeof callback1(index) === "undefined")
          layer.close(index);
      },
    });
  },

  /**
   * @description 格式化时间
   * @param {string|number} tm 时间戳
   * @param {string} format 格式，例如：yyyy/MM/dd hh:mm:ss
   * @returns  格式化后的时间
   */
  format_data: function (tm, format) {
    if (format == undefined) format = "yyyy/MM/dd hh:mm:ss";
    tm = tm.toString();
    if (tm.length > 10) {
      tm = tm.substring(0, 10);
    }
    var data = new Date(parseInt(tm) * 1000);
    var o = {
      "M+": data.getMonth() + 1, //month
      "d+": data.getDate(), //day
      "h+": data.getHours(), //hour
      "m+": data.getMinutes(), //minute
      "s+": data.getSeconds(), //second
      "q+": Math.floor((data.getMonth() + 3) / 3), //quarter
      S: data.getMilliseconds(), //millisecond
    };
    if (/(y+)/.test(format))
      format = format.replace(
        RegExp.$1,
        (data.getFullYear() + "").substr(4 - RegExp.$1.length)
      );
    for (var k in o)
      if (new RegExp("(" + k + ")").test(format))
        format = format.replace(
          RegExp.$1,
          RegExp.$1.length == 1
            ? o[k]
            : ("00" + o[k]).substr(("" + o[k]).length)
        );

    return format;
  },

  /**
   * @description 提示确认框
   * @param {string} title 标题
   * @param {string} msg 消息
   * @param {function} callback 确认回调
   */
  prompt_confirm: function (title, msg, callback) {
    layer.open({
      type: 1,
      title: title,
      area: "350px",
      closeBtn: 2,
      btn: ["确认", "取消"],
      content:
        "<div class='bt-form promptDelete pd20'>\
								<p>" +
        msg +
        "</p>\
								<div class='confirm-info-box'>\
									<input onpaste='return false;' id='prompt_input_box' type='text' value=''>\
									<div class='placeholder c9 prompt_input_tips' >如果确认操作，请手动输入‘<font style='color: red'>" +
        title +
        "</font>’</div>\
											<div style='margin-top:5px;display: none;' class='prompt_input_ps'>验证码错误，请手动输入‘<font style='color: red'>" +
        title +
        "</font>’</div></div>\
								</div>",
      success: function () {
        var black_txt_ = $("#prompt_input_box");

        $(".placeholder").click(function () {
          $(this).hide().siblings("input").focus();
        });
        black_txt_.focus(function () {
          $(".prompt_input_tips.placeholder").hide();
        });
        black_txt_.blur(function () {
          black_txt_.val() == ""
            ? $(".prompt_input_tips.placeholder").show()
            : $(".prompt_input_tips.placeholder").hide();
        });
        black_txt_.keyup(function () {
          if (black_txt_.val() == "") {
            $(".prompt_input_tips.placeholder").show();
            $(".prompt_input_ps").hide();
          } else {
            $(".prompt_input_tips.placeholder").hide();
          }
        });
      },
      yes: function (layers, index) {
        var result = bt.replace_all($("#prompt_input_box").val(), " ", "");
        if (result == title) {
          layer.close(layers);
          if (callback) callback();
        } else {
          $(".prompt_input_ps").show();
        }
      },
    });
  },
  /**
   * @description 显示弹窗
   * @param {string} title 标题
   * @param {string} msg 消息
   * @param {function} callback 确认回调
   * @param {string} error 错误消息
   * @returns
   */
  show_confirm: function (title, msg, callback, error) {
    var d = Math.round(Math.random() * 9 + 1),
      c = Math.round(Math.random() * 9 + 1),
      t = d + " + " + c,
      e = d + c;

    function submit(index, layero) {
      var a = $("#vcodeResult"),
        val = a.val().replace(/ /g, "");
      if (val == undefined || val == "") {
        layer.msg(lan.bt.cal_err);
        return;
      }
      if (val != a.data("value")) {
        layer.msg(lan.bt.cal_err);
        return;
      }
      layer.close(index);
      if (callback) callback();
    }
    layer.open({
      type: 1,
      title: title,
      area: "365px",
      closeBtn: 2,
      shadeClose: true,
      btn: [lan["public"].ok, lan["public"].cancel],
      content:
        "<div class='bt-form webDelete pd20'>\
                          <p style='font-size:13px;word-break: break-all;margin-bottom: 5px;'>" +
        msg +
        "</p>" +
        (error || "") +
        "<div class='vcode'>" +
        lan.bt.cal_msg +
        "<span class='text'>" +
        t +
        "</span>=<input type='number' id='vcodeResult' data-value='" +
        e +
        "' value=''></div>\
                      </div>",
      success: function (layero, index) {
        $("#vcodeResult")
          .focus()
          .keyup(function (a) {
            if (a.keyCode == 13) {
              submit(index, layero);
            }
          });
      },
      yes: submit,
    });
  },

  /**
   * @description 普通提示弹窗
   * @param {Object} config 弹窗对象 {title:标题, msg:提示内容}
   * @param {function} callback 确认回调函数
   * @param {function} callback1 取消回调函数
   */
  simple_confirm: function (config, callback, callback1) {
    layer.open({
      type: 1,
      title: config.title,
      area: "430px",
      closeBtn: 2,
      shadeClose: false,
      btn: config["btn"]
        ? config.btn
        : [lan["public"].ok, lan["public"].cancel],
      content:
        '<div class="bt-form hint_confirm pd30">\
					<div class="hint_title">\
						<i class="hint-confirm-icon"></i>\
						<div class="hint_con">' +
        config.msg +
        "</div>\
					</div>\
				</div>",
      yes: function (index, layero) {
        if (callback && typeof callback(index) === "undefined")
          layer.close(index);
      },
      btn2: function (index) {
        //取消返回回调
        if (callback1 && typeof callback1(index) === "undefined")
          layer.close(index);
      },
      cancel: function (index) {
        //取消返回回调
        if (callback1 && typeof callback1(index) === "undefined")
          layer.close(index);
      },
    });
  },
  /**
   * @description 计算提示弹窗
   * @param {Object} config 弹窗对象 {title: 提示标题, msg: 提示内容}
   * @param {function} callback 回调函数
   */
  compute_confirm: function (config, callback) {
    var d = Math.round(Math.random() * 9 + 1),
      c = Math.round(Math.random() * 9 + 1),
      t = d + " + " + c,
      e = d + c;

    function submit(index, layero) {
      var a = $("#vcodeResult"),
        val = a.val().replace(/ /g, "");
      if (val == undefined || val == "") {
        layer.msg(lan.bt.cal_err);
        return;
      }
      if (val != a.data("value")) {
        layer.msg(lan.bt.cal_err);
        return;
      }
      layer.close(index);
      if (callback) callback();
    }
    layer.open({
      type: 1,
      title: config.title,
      area: "430px",
      closeBtn: 2,
      shadeClose: true,
      btn: [lan["public"].ok, lan["public"].cancel],
      content:
        '<div class="bt-form hint_confirm pd30">\
						<div class="hint_title">\
							<i class="hint-confirm-icon"></i>\
							<div class="hint_con">' +
        config.msg +
        '</div>\
						</div>\
						<div class="vcode">计算验证：<span class="text">' +
        t +
        '</span>=<input type="number" id="vcodeResult" data-value="' +
        e +
        '" value=""></div>\
				</div>',
      success: function (layero, index) {
        $("#vcodeResult")
          .focus()
          .keyup(function (a) {
            if (a.keyCode == 13) {
              submit(index, layero);
            }
          });
      },
      yes: submit,
    });
  },
  /**
   * @description 输入提示弹窗
   * @param {Object} config 弹窗对象 {title: 提示标题, value: 输入值, msg: 提示内容}
   * @param {function} callback 回调函数
   */
  input_confirm: function (config, callback) {
    layer.open({
      type: 1,
      title: config.title,
      area: "430px",
      closeBtn: 2,
      shadeClose: true,
      btn: [lan["public"].ok, lan["public"].cancel],
      content:
        '<div class="bt-form hint_confirm pd30">\
						<div class="hint_title">\
							<i class="hint-confirm-icon"></i>\
							<div class="hint_con">' +
        config.msg +
        '</div>\
						</div>\
						<div class="confirm-info-box">\
							<div>请手动输入“<span class="color-org">' +
        config.value +
        '</span>”，完成验证</div>\
							<input onpaste="return false;" id="prompt_input_box" type="text" value="" autocomplete="off">\
						</div>\
				</div>',
      yes: function (layers, index) {
        var result = bt.replace_all($("#prompt_input_box").val(), " ", "");
        if (result == config.value) {
          layer.close(layers);
          if (callback) callback();
        } else {
          $("#prompt_input_box").focus();
          return layer.msg("验证失败，请重新输入", { icon: 2 });
        }
      },
    });
  },

  /**
   * @description 获取文件列表
   * @param {string} path 路径
   * @param {string} type 类型
   * @param {function} callabck 回调函数
   * @returns
   */
  get_file_list: function (path, type, callabck) {
    type = type || "dir";
    var _that = this;
    bt.send(
      "GetDir",
      "files/GetDir",
      {
        path: path,
        disk: true,
      },
      function (rdata) {
        var d = "",
          a = "";
        if (rdata.DISK != undefined) {
          for (var f = 0; f < rdata.DISK.length; f++) {
            a +=
              '<dd class="bt_open_dir" path ="' +
              rdata.DISK[f].path +
              "\"><span class='glyphicon glyphicon-hdd'></span>&nbsp;" +
              rdata.DISK[f].path +
              "</dd>";
          }
          $("#changecomlist").html(a);
        }
        for (var f = 0; f < rdata.DIR.length; f++) {
          var g = rdata.DIR[f].split(";");
          var e = g[0];
          var ps = g[10];
          if (ps != "") {
            ps = ps.split("：")[1];
            if (ps == undefined) ps = g[10].split(":")[1];
            if (ps == undefined) ps = g[10];
          }
          if (e.length > 20) {
            e = e.substring(0, 20) + "...";
          }
          if (isChineseChar(e)) {
            if (e.length > 10) {
              e = e.substring(0, 10) + "...";
            }
          }
          d +=
            "<tr><td>" +
            (type === "all" || type === "dir" || type === "multiple"
              ? '<span style="display: flex;align-items: center;"><input style="margin: 0;" type="checkbox" name="fileCheck" /></span>'
              : "") +
            '</td><td><a class=\'fileItem bt_open_dir\' class="bt_open_dir" data-path ="' +
            rdata.PATH +
            "/" +
            g[0] +
            "\" title='" +
            g[0] +
            "' data-type=\"dir\"><span class='glyphicon glyphicon-folder-open'></span><span>" +
            e +
            "</span></a></td><td style='width:100px'><span style='  width: 100px;display: inline-block;text-overflow: ellipsis;overflow: hidden;white-space: pre;vertical-align: middle;'>" +
            ps +
            "</span></td><td>" +
            bt.format_data(g[2]) +
            "</td><td>" +
            g[3] +
            " | " +
            g[4] +
            "</td></tr>";
        }

        if (rdata.FILES !== null && rdata.FILES !== "") {
          for (var f = 0; f < rdata.FILES.length; f++) {
            var g = rdata.FILES[f].split(";");
            var e = g[0];
            var ps = g[10];
            if (ps != "") {
              ps = ps.split("：")[1];
              if (ps == undefined) ps = g[10].split(":")[1];
              if (ps == undefined) ps = g[10];
            }
            if (e.length > 20) {
              e = e.substring(0, 20) + "...";
            }
            if (isChineseChar(e)) {
              if (e.length > 10) {
                e = e.substring(0, 10) + "...";
              }
            }
            d +=
              "<tr><td>" +
              (type === "all" || type === "file" || type === "multiple"
                ? '<span  style="display: flex;align-items: center;"><input style="margin: 0;" type="checkbox" name="fileCheck" /></span>'
                : "") +
              "<td><a class='fileItem bt_open_dir' class=\"bt_open_dir\" title='" +
              g[0] +
              '\' data-type="files" data-path ="' +
              rdata.PATH +
              "/" +
              g[0] +
              "\"><span class='glyphicon glyphicon-file'></span><span>" +
              e +
              "</span></a></td><td style='width:100px'><span style='  width: 100px;display: inline-block;text-overflow: ellipsis;overflow: hidden;white-space: pre;vertical-align: middle;'>" +
              ps +
              "</span></td><td>" +
              bt.format_data(g[2]) +
              "</td><td>" +
              g[3] +
              " | " +
              g[4] +
              "</td></tr>";
          }
        }

        $(".default").hide();
        $(".file-list").show();
        $("#tbody").html(d);
        if (rdata.PATH.substr(rdata.PATH.length - 1, 1) !== "/") {
          rdata.PATH += "/";
        }
        $("#PathPlace").find("span").html(rdata.PATH);
        $("#tbody tr").click(function () {
          if ($(this).find("td:eq(0) input").length > 0) {
            if ($(this).hasClass("active")) {
              $(this).removeClass("active");
              $(this).find("td:eq(0) input").prop("checked", false);
            } else {
              $(this).addClass("active");
              $(this).find("td:eq(0) input").prop("checked", true);
              if (!(type === "multiple")) {
                $(this).addClass("active").siblings().removeClass("active");
                $(this)
                  .siblings()
                  .find("td:eq(0) input")
                  .prop("checked", false);
              }
            }
          }
        });
        $("#changecomlist dd").click(function () {
          _that.get_file_list($(this).attr("path"), type);
        });
        $(".bt_open_dir").click(function () {
          var data = $(this).data();
          if (data.type === "dir") _that.get_file_list(data.path, type);
        });
        if (callabck) callabck(rdata);
      }
    );
  },

  /**
   * @description 选择文件目录或文件
   * @param id {string} 元素ID
   * @param type {string || function} 选择方式，文件或目录
   * @param success {function} 成功后的回调
   */
  select_path: function (id, type, success, default_path) {
    bt.set_cookie("SetName", "");
    if (typeof type !== "string") (success = type), (type = "dir");
    title =
      type === "all"
        ? "选择目录和文件"
        : type === "file"
        ? lan.bt.file
        : lan.bt.dir;
    if (type === "multiple") title = "选择目录和文件，支持多选";
    var loadT = bt.open({
      type: 1,
      area: "750px",
      title: title,
      closeBtn: 2,
      shift: 5,
      content:
        "<div class='changepath'>\
            <div class='path-top flex' style='justify-content: space-between;'><div>\
                <button type='button' id='btn_back' class='btn btn-default btn-sm'><span class='glyphicon glyphicon-share-alt'></span> " +
        lan["public"]["return"] +
        "</button>\
                    <div class='place' id='PathPlace'>" +
        lan.bt.path +
        "：<span></span></div>\
                </div>\
            <div>\
                    <button type='button' id='btn_refresh' class='btn btn-default btn-sm'><span class='glyphicon glyphicon-repeat'></span> 刷新</button>\
                </div>\
            </div>\
            <div class='path-con'><div class='path-con-left'><dl><dt id='changecomlist' >" +
        lan.bt.comp +
        "</dt></dl></div><div class='path-con-right'><ul class='default' id='computerDefautl'></ul><div class='file-list divtable'><table class='table table-hover' style='border:0 none'><thead><tr class='file-list-head'><th width='5%'></th><th width='38%'>" +
        lan.bt.filename +
        "</th><th>备注</th><th width='24%'>" +
        lan.bt.etime +
        "</th><th width='8%'>" +
        lan.bt.access +
        "</th></tr></thead><tbody id='tbody' class='list-list'></tbody></table></div></div></div></div><div class='getfile-btn' style='margin-top:0'><button type='button' class='btn btn-default btn-sm pull-left' onclick='CreateFolder()'>" +
        lan.bt.adddir +
        "</button><button type='button' class='btn btn-danger btn-sm mr5' onclick=\"layer.close(getCookie('ChangePath'))\">" +
        lan["public"].close +
        "</button> <button type='button' id='bt_select' class='btn btn-success btn-sm' >" +
        lan.bt.path_ok +
        "</button></div>",
      success: function () {
        $("#btn_refresh").click(function () {
          var path = $("#PathPlace").find("span").text();
          path = bt.rtrim(bt.format_path(path), "/");
          var load = bt.load("正在刷新目录，请稍后...");
          bt.get_file_list(path, type, function () {
            load.close();
          });
        });
        $("#btn_back").on("click", function () {
          var path = $("#PathPlace").find("span").text();
          path = bt.rtrim(bt.format_path(path), "/");
          var back_path = bt.get_file_path(path);
          bt.get_file_list(back_path, type);
        });
        //选择
        $("#bt_select").on("click", function () {
          var path = [],
            trList = $("#tbody tr.active"),
            _type = "dir";
          if (!trList.length && type == "file") {
            layer.msg("请选择文件继续操作！", { icon: 0 });
            return false;
          }
          trList.each(function () {
            var $this = this;
            var $data = $(this).find(".fileItem").data();
            _type = $data.type;
            path.push(bt.rtrim($data.path, "/"));
          });
          if (path.length === 0) {
            path = [$("#PathPlace").find("span").text()];
          }
          $("#" + id)
            .val(path[0])
            .change();
          $("." + id)
            .val(path[0])
            .change();
          if (typeof success === "function") success(path[0], path, _type);
          loadT.close();
        });
        var element = $("#" + id),
          paths = element.val(),
          defaultPath = $("#defaultPath");
        if (defaultPath.length > 0 && element.parents(".tab-body").length > 0) {
          paths = defaultPath.text();
        }
        if (default_path) {
          paths = default_path;
        }
        bt.get_file_list(paths, type);
      },
    });
    bt.set_cookie("ChangePath", loadT.form);
  },

  /**
   * @description 判断是否为整数
   * @param {Number} obj
   * @returns
   */
  isInteger: function (obj) {
    return (obj | 0) === obj;
  },

  /**
   * @description 判断是否为数字
   * @param {object} param 参数 
   * @returns 
   */
  win_format_param: function (param) {
		if (typeof data == 'object') {
			var data = '';
			for (var key in param) {
				data += key + '=' + param[key] + '&';
			}
			if (data.length > 0) data = data.substr(0, data.length - 1);
			return data;
		}
		return param;
	},

  /**
   * @description 消息提示
   * @param {object} config 消息配置 {code:状态码, msg:消息内容, msg_error:错误消息, msg_solve:解决方案, icon:图标, status:状态, time:时间, title:标题, closeBtn:关闭按钮, shadeClose:点击遮罩关闭}
   * @returns
   */
  msg: function (config) {
    var btns = [];
    if (config.code === -1) {
      config.closeBtn = 1;
      config.time = 0;
    }
    var btnObj = {
      title: config.title ? config.title : false,
      shadeClose: config.shadeClose ? config.shadeClose : true,
      closeBtn: config.closeBtn ? config.closeBtn : 0,
      scrollbar: true,
      shade: 0.3,
    };
    if (!config.hasOwnProperty("time")) config.time = 2000;
    if (typeof config.msg == "string" && bt.contains(config.msg, "ERROR"))
      config.time = 0;

    if (config.hasOwnProperty("icon")) {
      if (typeof config.icon == "boolean") config.icon = config.icon ? 1 : 2;
    } else if (config.hasOwnProperty("status")) {
      config.icon = config.status ? 1 : 2;
      if (!config.status) {
        btnObj.time = 0;
      }
    }
    if (config.icon) btnObj.icon = config.icon;
    btnObj.time = config.time;
    var msg = "";
    if (config.msg) msg += config.msg;
    if (config.msg_error) msg += config.msg_error;
    if (config.msg_solve) msg += config.msg_solve;
    layer.msg(msg, btnObj);
  },

  /**
   * @description 确认框
   * @param {object} config 配置 {title:标题, msg:消息, time:时间, shadeClose:点击遮罩关闭, closeBtn:关闭按钮, skin:样式, cancel:取消回调}
   * @param {function} callback 确认回调
   * @param {function} callback1 取消回调
   */
  confirm: function (config, callback, callback1) {
    var btnObj = {
      title: config.title ? config.title : false,
      time: config.time ? config.time : 0,
      shadeClose: config.shadeClose !== undefined ? config.shadeClose : true,
      closeBtn: config.closeBtn ? config.closeBtn : 2,
      scrollbar: true,
      shade: 0.3,
      icon: 3,
      skin: config.skin ? config.skin : "",
      cancel: config.cancel ? config.cancel : function () {},
    };
    layer.confirm(
      config.msg,
      btnObj,
      function (index) {
        if (callback) callback(index);
      },
      function (index) {
        if (callback1) callback1(index);
      }
    );
  },

  /**
   * @description loading加载
   * @param {String} msg 加载提示
   * @returns
   */
  load: function (msg) {
    if (!msg) msg = lan["public"].the;
    var loadT = layer.msg(msg, {
      icon: 16,
      time: 0,
      shade: [0.3, "#000"],
    });
    var load = {
      form: loadT,
      close: function () {
        layer.close(load.form);
      },
    };
    return load;
  },

  /**
   * @description 打开弹窗
   * @param {object} config 弹窗配置 {type:弹窗类型, title:标题, area:宽高, content:内容, btn:按钮, success:成功回调, end:关闭回调, cancel:取消回调}
   * @returns
   */
  open: function (config) {
    config.closeBtn = 2;
    var loadT = layer.open(config);
    var load = {
      form: loadT,
      close: function () {
        layer.close(load.form);
      },
    };
    return load;
  },

  /**
   * @description 关闭所有弹窗
   */
  closeAll: function () {
    layer.closeAll();
  },

  /**
   * @description 发送请求
   * @param {String} response 请求方法
   * @param {String} module 模块 ，例如：files/GetDir
   * @param {Object} data 数据
   * @param {function} callback 回调函数
   * @param {Object} param 参数
   */
  send: function (response, module, data, callback, param) {
    // if (sType == undefined) sType = 1;
    module = module.replace("panel_data", "data");
    var sType = 1;
    var str = bt.get_random(16);
    console.time(str);
    if (!response) alert(lan.get("lack_param", ["response"]));
    modelTmp = module.split("/");
    if (modelTmp.length < 2)
      alert(lan.get("lack_param", ["s_module", "action"]));
    if (bt.os == "Linux" && sType === 0) {
      socket.on(response, function (rdata) {
        socket.removeAllListeners(response);
        var rRet = rdata.data;
        if (rRet.status === -1) {
          bt.to_login();
          return;
        }
        console.timeEnd(str);
        if (callback) callback(rRet);
      });
      if (!data) data = {};
      data = bt.linux_format_param(data);
      data["s_response"] = response;
      data["s_module"] = modelTmp[0];
      data["action"] = modelTmp[1];
      socket.emit("panel", data);
    } else {
      data = bt.win_format_param(data);
      var url = "/" + modelTmp[0] + "?action=" + modelTmp[1];
      $.post(url, data, function (rdata) {
        //会话失效时自动跳转到登录页面
        if (typeof rdata == "string") {
          if (
            (rdata.indexOf("/static/favicon.ico") != -1 &&
              rdata.indexOf("/static/img/qrCode.png") != -1) ||
            rdata.indexOf("<!DOCTYPE html>") === 0
          ) {
            window.location.href = "/login";
            return;
          }
          // 请求结果为字符串并且开头有traceback 弹报错窗口
          if (rdata.startsWith("Traceback")) {
            error_find = 0;
            gl_error_body = "<!--<!--" + rdata;
            var pro = parseInt(bt.get_cookie("pro_end") || -1);
            var ltd = parseInt(bt.get_cookie("ltd_end") || -1);
            isBuy = pro == 0 || ltd > 0 ? true : false;
            showErrorMessage();
            return;
          }
        }

        if (
          param &&
          param.hasOwnProperty("verify") &&
          param["verify"] === true
        ) {
          // 请求结果为对象
          if (
            typeof rdata === "object" &&
            rdata.status === false &&
            (rdata.hasOwnProperty("msg") || rdata.hasOwnProperty("error_msg"))
          ) {
            bt_tools.msg({
              status: rdata.status,
              msg: !rdata.hasOwnProperty("msg") ? rdata.error_msg : rdata.msg,
            });
            return false;
          }
        }

        if (callback) callback(rdata);
      }).error(function (e, f) {
        if (callback) callback("error");
      });
    }
  },

  /**
   * @description ACE编辑配置文件
   * @param {Object} obj 编辑配置
   * @returns
   */
  aceEditor: function (obj) {
    var aEditor = {
      ACE: ace.edit(obj.el, {
        theme: obj.theme || "ace/theme/chrome", //主题
        mode: "ace/mode/" + (obj.mode || "nginx"), // 语言类型
        wrap: true,
        showInvisibles: false,
        showPrintMargin: false,
        showFoldWidgets: false,
        useSoftTabs: true,
        tabSize: 2,
        readOnly: obj.readOnly || false,
      }),
      path: obj.path,
      content: "",
      saveCallback: obj.saveCallback,
    };
    $("#" + obj.el).css("fontSize", "12px");
    aEditor.ACE.commands.addCommand({
      name: "保存文件",
      bindKey: {
        win: "Ctrl-S",
        mac: "Command-S",
      },
      exec: function (editor) {
        bt.saveEditor(aEditor, aEditor.saveCallback);
      },
      readOnly: false, // 如果不需要使用只读模式，这里设置false
    });
    if (obj.path !== undefined) {
      var loadT = layer.msg(lan.soft.get_config, {
        icon: 16,
        time: 0,
        shade: [0.3, "#000"],
      });
      bt.send(
        "GetFileBody",
        "files/GetFileBody",
        {
          path: obj.path,
        },
        function (res) {
          layer.close(loadT);
          if (!res.status) {
            bt.msg(res);
            return false;
          }
          aEditor.ACE.setValue(res.data); //设置配置文件内容
          aEditor.ACE.moveCursorTo(0, 0); //设置文件光标位置
          aEditor.ACE.resize();
        }
      );
    } else if (obj.content != undefined) {
      aEditor.ACE.setValue(obj.content);
      aEditor.ACE.moveCursorTo(0, 0); //设置文件光标位置
      aEditor.ACE.resize();
    }
    return aEditor;
  },

  /**
   * @description 保存编辑器文件
   * @param {Object} ace 编辑器
   * @param {String} encode 编码
   */
  saveEditor: function (_aceEditor, encode) {
    if (!_aceEditor.saveCallback) {
      if (!encode) encode = "utf-8";
      var loadT = bt.load(lan.soft.the_save);
      bt.send(
        "SaveFileBody",
        "files/SaveFileBody",
        {
          data: _aceEditor.ACE.getValue(),
          path: _aceEditor.path,
          encoding: encode,
        },
        function (rdata) {
          loadT.close();
          bt.msg(rdata);
        }
      );
    } else {
      _aceEditor.saveCallback(_aceEditor.ACE.getValue());
    }
  },

  /**
   * @description 打开反馈弹窗
   * @param {Object} param 反馈配置 {title:标题, placeholder:提示, recover:恢复, key:键, proType:产品类型}
   */
	openFeedback: function (param) {
		var openFeed = bt_tools.open({
			area:['570px','380px'],
			btn:false,
			content:'<div id="feedback">\
			<div class="nps_survey_banner">\
			<span class="Ftitle"> <i></i> <span style="vertical-align:4px;">'+param.title+'</span> </span>\
		</div>\
		<div style="padding: 25px 0 0 40px">\
			<div class="flex flex-col items-center">\
				<div id="feedForm"></div>\
			</div>\
		</div>\
		</div>',
			success:function(that){
				//打开弹窗后执行的事件
				that.find('.layui-layer-title').remove()
				bt_tools.form({
					el:'#feedForm',
					form:[
						{
							group: {
								type: 'textarea',
								name: 'feed',
								style: {
									'width': '500px',
									'min-width': '500px',
									'min-height': '130px',
									'line-height': '22px',
									'padding-top': '10px',
									'resize': 'none'
								},
								tips: { //使用hover的方式显示提示
									text: param.placeholder,
									style: { top: '126px', left: '50px' },
								},
							}
						},
						{
							group:{
								name: 'tips',
								type: 'other',
								boxcontent:'<div style="color:#20a53a;margin-left:30px;">'+param.recover+'</div>'
							}
						},
						{
							group: {
								type: 'button',
								size: '',
								name: 'submitForm',
								class:'feedBtn',
								style:'margin:6px auto 0;padding:6px 40px;',
								title: '提交',
								event: function (formData, element, that) {
									// 触发submit
									if(formData.feed == '') {
										return bt.msg({status:false,msg:'请填写反馈内容'})
									}
									var config = {}
									config[param.key] = formData.feed
									bt_tools.send({url:'config?action=write_nps_new',data:{questions:JSON.stringify(config),software_name:1,rate:0,product_type:param.proType}},function(ress){
										if(ress.status){
											openFeed.close()
											layer.open({
												title: false,
												btn: false,
												shadeClose: true,
												shade:0.1,
												closeBtn: 0,
												skin:'qa_thank_dialog',
												area: '230px',
												content: '<div class="qa_thank_box" style="background-color:#F1F9F3;text-align: center;padding: 20px 0;"><img src="/static/img/feedback/QA_like.png" style="width: 55px;"><p style="margin-top: 15px;">感谢您的参与!</p></div>',
												success: function (layero,index) {
													$(layero).find('.layui-layer-content').css({'padding': '0','border-radius': '5px'})
													$(layero).css({'border-radius': '5px','min-width': '230px'})

													setTimeout(function(){layer.close(index)},3000)
												}
											})
										}
									},'提交反馈')

								}
							}
						}
					]
				})
			},
			yes:function(){
				//点击确定时,如果btn:false,当前事件将无法使用
			},
			cancel: function () {
				//点击右上角关闭时,如果btn:false,当前事件将无法使用
			}
		})
	},


  /**
   * @description 切换多选框
   */
  check_select: function () {
    setTimeout(function () {
      var num = $('input[type="checkbox"].check:checked').length;
      if (num == 1) {
        $('button[batch="true"]').hide();
        $('button[batch="false"]').show();
      } else if (num > 1) {
        $('button[batch="true"]').show();
        $('button[batch="false"]').show();
      } else {
        $('button[batch="true"]').hide();
        $('button[batch="false"]').hide();
      }
    }, 5);
  },

  /**
   * @description 渲染帮助信息
   * @param {Array} arr 帮助信息数组
   * @returns
   */
  render_help: function (arr) {
    var html = '<ul class="help-info-text c7">';
    for (var i = 0; i < arr.length; i++) {
      html += "<li>" + arr[i] + "</li>";
    }
    html += "</ul>";
    return html;
  },

  /**
   * @description 渲染备注
   * @param {Object} item 备注配置
   * @returns
   */
  render_ps: function (item) {
    var html = "<p class='p1'>" + item.title + "</p>";
    for (var i = 0; i < item.list.length; i++) {
      html +=
        "<p><span>" +
        item.list[i].title +
        "：</span><strong>" +
        item.list[i].val +
        "</strong></p>";
    }
    html +=
      '<p style="margin-bottom: 19px; margin-top: 11px; color: #666"></p>';
    return html;
  },

  /**
   * @description 渲染表格
   * @param {String} obj 表格ID
   * @param {Object} arr 表格数据
   * @param {Boolean} append 是否追加
   */
  render_table: function (obj, arr, append) {
    //渲染表单表格
    var html = "";
    for (var key in arr) {
      if (arr.hasOwnProperty(key)) {
        html += "<tr><th>" + key + "</th>";
        if (typeof arr[key] != "object") {
          html += "<td>" + arr[key] + "</td>";
        } else {
          for (var i = 0; i < arr[key].length; i++) {
            html += "<td>" + arr[key][i] + "</td>";
          }
        }
        html += "</tr>";
      }
    }
    if (append) {
      $("#" + obj).append(html);
    } else {
      $("#" + obj).html(html);
    }
  },

  /**
   * @description 固定表格
   * @param {String} name 表格ID
   */
  fixed_table: function (name) {
    $("#" + name)
      .parent()
      .bind("scroll", function () {
        var scrollTop = this.scrollTop;
        $(this)
          .find("thead")
          .css({
            transform: "translateY(" + scrollTop + "px)",
            position: "relative",
            "z-index": "1",
          });
      });
  },

  /**
   * @description 渲染Tab
   * @param {Object} obj 配置对象
   * @param {Array} arr Tab数组
   */
  render_tab: function (obj, arr) {
    var _obj = $("#" + obj).addClass("tab-nav");
    for (var i = 0; i < arr.length; i++) {
      var item = arr[i];
      var _tab = $(
        "<span " + (item.on ? 'class="on"' : "") + ">" + item.title + "</span>"
      );
      if (item.callback) {
        _tab.data("callback", item.callback);
        _tab.click(function () {
          $("#" + obj)
            .find("span")
            .removeClass("on");
          $(this).addClass("on");
          var _contents = $("#" + obj).next(".tab-con");
          _contents.html("");
          $(this).data("callback")(_contents);
        });
      }
      _obj.append(_tab);
    }
  },

  /**
   * @description 渲染表单
   * @param {Object} item 表单配置
   * @param {String} bs 样式
   * @param {String} form 表单ID
   * @returns
   */
  render_form_line: function (item, bs, form) {
    var clicks = [],
      _html = "",
      _hide = "",
      is_title_css = " ml0";
    if (!bs) bs = "";
    if (item.title) {
      _html += '<span class="tname">' + item.title + "</span>";
      is_title_css = "";
    }
    _html += "<div class='info-r " + item["class"] + " " + is_title_css + "'>";

    var _name = item.name;
    var _placeholder = item.placeholder;
    if (item.items && item.type != "select") {
      for (var x = 0; x < item.items.length; x++) {
        var _obj = item.items[x];
        if (!_name && !_obj.name) {
          alert("缺少必要参数name");
          return;
        }
        if (_obj.hide) continue;
        if (_obj.name) _name = _obj.name;
        if (_obj.placeholder) _placeholder = _obj.placeholder;
        if (_obj.title)
          _html +=
            '<div class="inlineBlock mr5"><span class="mr5">' +
            _obj.title +
            "</span>  ";
        switch (_obj.type) {
          case "select":
            var _width = _obj.width ? _obj.width : "100px";
            _html +=
              "<select " +
              (_obj.disabled ? "disabled" : "") +
              ' class="bt-input-text mr5 ' +
              _name +
              bs +
              '" name="' +
              _name +
              '" style="width:' +
              _width +
              '">';
            for (var j = 0; j < _obj.items.length; j++) {
              _html +=
                "<option " +
                (_obj.value == _obj.items[j].value ? "selected" : "") +
                ' value="' +
                _obj.items[j].value +
                '">' +
                _obj.items[j].title +
                "</option>";
            }
            _html += "</select>";
            break;
          case "textarea":
            var _width = _obj.width ? _obj.width : "330px";
            var _height = _obj.height ? _obj.height : "100px";
            _html +=
              '<textarea class="bt-input-text mr20 ' +
              _name +
              bs +
              '" name="' +
              _name +
              '" style="width:' +
              _width +
              ";height:" +
              _height +
              ';line-height:22px">' +
              (_obj.value ? _obj.value : "") +
              "</textarea>";
            if (_placeholder)
              _html +=
                '<div class="placeholder c9" style="top: 15px; left: 15px; display: block;">' +
                _placeholder +
                "</div>";
            break;
          case "button":
            var _width = _obj.width ? _obj.width : "330px";
            _html +=
              '<button type="button" name=\'' +
              _name +
              "' class=\"btn btn-" +
              (_obj["color"] ? _obj["color"] : "success") +
              " btn-sm mr5 ml5 " +
              _name +
              bs +
              " " +
              (_obj["class"] ? _obj["class"] : "") +
              '">' +
              _obj.text +
              "</button>";
            break;
          case "radio":
            var _v = _obj.value === true ? "checked" : "";
            _html +=
              '<input type="radio" class="' +
              _name +
              '" id="' +
              _name +
              '" name="' +
              _name +
              '"  ' +
              _v +
              '><label class="mr20" for="' +
              _name +
              '" style="font-weight:normal">' +
              _obj.text +
              "</label>";
            break;
          case "checkbox":
            var _v = _obj.value === true ? "checked" : "";
            _html +=
              '<input type="checkbox" class="' +
              _name +
              '" id="' +
              _name +
              '" name="' +
              _name +
              '"  ' +
              _v +
              '><label class="mr20" for="' +
              _name +
              '" style="font-weight:normal">' +
              _obj.text +
              "</label>";
            break;
          case "number":
            var _width = _obj.width ? _obj.width : "330px";
            _html +=
              "<input name='" +
              _name +
              "' " +
              (_obj.disabled ? "disabled" : "") +
              " class='bt-input-text mr5 " +
              _name +
              bs +
              "' " +
              (_placeholder ? ' placeholder="' + _placeholder + '"' : "") +
              " type='number' style='width:" +
              _width +
              "' value='" +
              (_obj.value ? _obj.value : "0") +
              "' />";
            _html += _obj.unit ? _obj.unit : "";
            break;
          case "password":
            var _width = _obj.width ? _obj.width : "330px";
            _html +=
              "<input name='" +
              _name +
              "' " +
              (_obj.disabled ? "disabled" : "") +
              " class='bt-input-text mr5 " +
              _name +
              bs +
              "' " +
              (_placeholder ? ' placeholder="' + _placeholder + '"' : "") +
              " type='password' style='width:" +
              _width +
              "' value='" +
              (_obj.value ? _obj.value : "") +
              "' />";
            break;
          case "div":
            var _width = _obj.width ? _obj.width : "330px";
            var _height = _obj.height ? _obj.height : "100px";
            _html +=
              '<div class="bt-input-text ace_config_editor_scroll mr20 ' +
              _name +
              bs +
              '" name="' +
              _name +
              '" style="width:' +
              _width +
              ";height:" +
              _height +
              ';line-height:22px">' +
              (_obj.value ? _obj.value : "") +
              "</div>";
            if (_placeholder)
              _html +=
                '<div class="placeholder c9" style="top: 15px; left: 15px; display: block;">' +
                _placeholder +
                "</div>";
            break;
          case "switch":
            _html +=
              '<div style="display: inline-block;vertical-align: middle;">\
															<input type="checkbox" id="' +
              _name +
              '" ' +
              (_obj.value == true ? "checked" : "") +
              ' class="btswitch btswitch-ios">\
															<label class="btswitch-btn" for="' +
              _name +
              '" style="margin-top:5px;"></label>\
													</div>';
            break;
          case "other":
            _html += _obj.boxcontent;
            break;
          default:
            var _width = _obj.width ? _obj.width : "330px";

            _html +=
              "<input name='" +
              _name +
              "' " +
              (_obj.disabled ? "disabled" : "") +
              " class='bt-input-text mr5 " +
              _name +
              bs +
              "' " +
              (_placeholder ? ' placeholder="' + _placeholder + '"' : "") +
              " type='text' style='width:" +
              _width +
              "' value='" +
              (_obj.value ? _obj.value : "") +
              "' />";
            break;
        }
        if (_obj.title) _html += "</div>";
        if (_obj.callback != undefined)
          clicks.push({
            bind: _name + bs,
            callback: _obj.callback,
          });

        if (_obj.event) {
          _html +=
            '<span data-id="' +
            _name +
            bs +
            '" class="glyphicon cursor mr5 ' +
            _obj.event.css +
            " icon_" +
            _name +
            bs +
            '" ></span>';
          if (_obj.event.callback)
            clicks.push({
              bind: "icon_" + _name + bs,
              callback: _obj.event.callback,
            });
        }
        if (_obj.ps) _html += " <span class='c9 mt10'>" + _obj.ps + "</span>";
        if (_obj.ps_help)
          _html +=
            "<span class='bt-ico-ask " +
            _obj.name +
            "_help' tip='" +
            _obj.ps_help +
            "'>?</span>";
      }
      if (item.ps) _html += " <span class='c9 mt10'>" + item.ps + "</span>";
    } else {
      switch (item.type) {
        case "select":
          var _width = item.width ? item.width : "100px";
          _html +=
            "<select " +
            (item.disabled ? "disabled" : "") +
            ' class="bt-input-text mr5 ' +
            _name +
            bs +
            '" name="' +
            _name +
            '" style="width:' +
            _width +
            '">';
          for (var j = 0; j < item.items.length; j++) {
            _html +=
              "<option " +
              (item.value == item.items[j].value ? "selected" : "") +
              ' value="' +
              item.items[j].value +
              '">' +
              item.items[j].title +
              "</option>";
          }
          _html += "</select>";
          break;
        case "button":
          var _width = item.width ? item.width : "330px";
          _html +=
            '<button type="button" name=\'' +
            _name +
            "' class=\"btn btn-success btn-sm mr5 ml5 " +
            _name +
            bs +
            '">' +
            item.text +
            "</button>";
          break;
        case "number":
          var _width = item.width ? item.width : "330px";
          _html +=
            "<input name='" +
            item.name +
            "' " +
            (item.disabled ? "disabled" : "") +
            " class='bt-input-text mr5 " +
            _name +
            bs +
            "' " +
            (_placeholder ? ' placeholder="' + _placeholder + '"' : "") +
            " type='number' style='width:" +
            _width +
            "' value='" +
            (item.value ? item.value : "0") +
            "' />";
          break;
        case "checkbox":
          var _v = item.value === true ? "checked" : "";
          _html +=
            '<input type="checkbox" class="' +
            _name +
            '" id="' +
            _name +
            '" name="' +
            _name +
            '"  ' +
            _v +
            '><label class="mr20" for="' +
            _name +
            '" style="font-weight:normal">' +
            item.text +
            "</label>";
          break;
        case "password":
          var _width = item.width ? item.width : "330px";
          _html +=
            "<input name='" +
            _name +
            "' " +
            (item.disabled ? "disabled" : "") +
            " class='bt-input-text mr5 " +
            _name +
            bs +
            "' " +
            (_placeholder ? ' placeholder="' + _placeholder + '"' : "") +
            " type='password' style='width:" +
            _width +
            "' value='" +
            (item.value ? item.value : "") +
            "' />";
          break;
        case "textarea":
          var _width = item.width ? item.width : "330px";
          var _height = item.height ? item.height : "100px";
          _html +=
            '<textarea class="bt-input-text mr20 ' +
            _name +
            bs +
            '"  ' +
            (item.disabled ? "disabled" : "") +
            '  name="' +
            _name +
            '" style="width:' +
            _width +
            ";height:" +
            _height +
            ';line-height:22px">' +
            (item.value ? item.value : "") +
            "</textarea>";
          if (_placeholder)
            _html +=
              '<div class="placeholder c9" style="top: 15px; left: 15px; display: block;">' +
              _placeholder +
              "</div>";
          break;
        case "other":
          _html += item.boxcontent;
          break;
        default:
          var _width = item.width ? item.width : "330px";
          _html +=
            "<input name='" +
            item.name +
            "' " +
            (item.disabled ? "disabled" : "") +
            " class='bt-input-text mr5 " +
            _name +
            bs +
            "' " +
            (_placeholder ? ' placeholder="' + _placeholder + '"' : "") +
            " type='text' style='width:" +
            _width +
            "' value='" +
            (item.value ? item.value : "") +
            "' />";
          break;
      }
      if (item.callback)
        clicks.push({
          bind: _name + bs,
          callback: item.callback,
        });
      if (item.ps) _html += " <span class='c9 mt10 mr5'>" + item.ps + "</span>";
    }
    _html += "</div>";
    if (!item["class"]) item["class"] = "";
    if (item.hide) _hide = 'style="display:none;"';
    _html =
      '<div class="line ' +
      item["class"] +
      '" ' +
      _hide +
      ">" +
      _html +
      "</div>";

    if (form) {
      form.append(_html);
      bt.render_clicks(clicks);
    }
    return {
      html: _html,
      clicks: clicks,
      data: item,
    };
  },

  /**
   * @description 渲染表单
   * @param {Object} data 表单数据
   * @param {Function} callback 回调
   * @returns
   */
  render_form: function (data, callback) {
    if (data) {
      var bs = "_" + bt.get_random(6);
      var _form = $(
        "<div data-id='form" +
          bs +
          "' class='bt-form bt-form pd20 pb70 " +
          (data["class"] ? data["class"] : "") +
          "'></div>"
      );
      var _lines = data.list;
      var clicks = [];
      for (var i = 0; i < _lines.length; i++) {
        var _obj = _lines[i];
        if (_obj.hasOwnProperty("html")) {
          _form.append(_obj.html);
        } else {
          var rRet = bt.render_form_line(_obj, bs);
          for (var s = 0; s < rRet.clicks.length; s++)
            clicks.push(rRet.clicks[s]);
          _form.append(rRet.html);
        }
      }

      var _btn_html = "";
      for (var i = 0; i < data.btns.length; i++) {
        var item = data.btns[i];
        var css = item.css ? item.css : "btn-danger";
        _btn_html +=
          "<button type='button' class='btn btn-sm " +
          css +
          " " +
          item.name +
          bs +
          "' >" +
          item.title +
          "</button>";
        clicks.push({
          bind: item.name + bs,
          callback: item.callback,
        });
      }
      _form.append("<div class='bt-form-submit-btn'>" + _btn_html + "</div>");
      var loadOpen = bt.open({
        type: 1,
        skin: data.skin,
        area: data.area,
        title: data.title,
        closeBtn: 2,
        content: _form.prop("outerHTML"),
        end: data.end ? data.end : false,
        success: function () {
          $(":focus").blur();
          if (data.yes) data.yes();
        },
      });
      setTimeout(function () {
        bt.render_clicks(clicks, loadOpen, callback);
      }, 100);
    }
    return bs;
  },

  /**
   * @description 渲染点击事件
   * @param {Array} clicks 点击事件
   * @param {Object} loadOpen 打开弹窗
   * @param {Function} callback 回调
   */
  render_clicks: function (clicks, loadOpen, callback) {
    for (var i = 0; i < clicks.length; i++) {
      var obj = clicks[i];

      var btn = $("." + obj.bind);
      btn.data("item", obj);
      btn.data("load", loadOpen);
      btn.data("callback", callback);

      switch (btn.prop("tagName")) {
        case "SPAN":
          btn.click(function () {
            var _obj = $(this).data("item");
            _obj.callback($(this).attr("data-id"));
          });
          break;
        case "SELECT":
          btn.change(function () {
            var _obj = $(this).data("item");
            _obj.callback($(this));
          });
          break;
        case "TEXTAREA":
        case "INPUT":
        case "BUTTON":
          if (
            btn.prop("tagName") == "BUTTON" ||
            btn.attr("type") == "checkbox"
          ) {
            btn.click(function () {
              var _obj = $(this).data("item");
              var load = $(this).data("load");
              var _callback = $(this).data("callback");
              var parent =
                $(this).parents(".bt-form").length === 0
                  ? $(this).parents(".bt-w-con")
                  : $(this).parents(".bt-form");

              if (_obj.callback) {
                var data = {};
                parent.find("*").each(function (index, _this) {
                  var _name = $(_this).attr("name");

                  if (_name) {
                    if (
                      $(_this).attr("type") == "checkbox" ||
                      $(_this).attr("type") == "radio"
                    ) {
                      data[_name] = $(_this).prop("checked");
                    } else {
                      data[_name] = $(_this).val();
                    }
                  }
                });
                _obj.callback(data, load, function (rdata) {
                  if (_callback) _callback(rdata);
                });
              } else {
                load.close();
              }
            });
          } else {
            if (btn.attr("type") == "radio") {
              btn.click(function () {
                var _obj = $(this).data("item");
                _obj.callback($(this));
              });
            } else {
              btn.on("input", function () {
                var _obj = $(this).data("item");
                _obj.callback($(this));
              });
            }
          }
          break;
      }
    }
  },

  /**
   * @description 渲染表格
   * @param {Object} obj 表格配置
   * @returns
   */
  render: function (obj) {
    if (obj.columns) {
      var checks = {};
      $(obj.table).html("");
      var thead = "<thead><tr>";
      for (var h = 0; h < obj.columns.length; h++) {
        var item = obj.columns[h];
        if (item) {
          thead += "<th";
          if (item.width) thead += ' width="' + item.width + '" ';
          if (item.align || item.sort) {
            thead += ' style="';
            if (item.align) thead += "text-align:" + item.align + ";";
            if (item.sort) thead += item.sort ? "cursor: pointer;" : "";
            thead += '"';
          }
          if (item.type == "checkbox") {
            thead +=
              '><input  class="check"  onclick="bt.check_select();" type="checkbox">';
          } else {
            thead += ">" + item.title;
          }
          if (item.sort) {
            checks[item.field] = item.sort;
            thead +=
              ' <span data-id="' +
              item.field +
              '" class="glyphicon glyphicon-triangle-top" style="margin-left:5px;color:#bbb"></span>';
          }
          if (item.help)
            thead +=
              '<a href="' +
              item.help +
              '" class="bt-ico-ask" target="_blank" title="点击查看说明">?</a>';

          thead += "</th>";
        }
      }
      thead += "</tr></thead>";
      var _tab = $(obj.table).append(thead);
      if (obj.data.length > 0) {
        for (var i = 0; i < obj.data.length; i++) {
          var val = obj.data[i];
          var tr = $("<tr></tr>");
          for (var h = 0; h < obj.columns.length; h++) {
            var item = obj.columns[h];
            if (item) {
              var _val = val[item.field];
              if (typeof _val == "string") _val = _val.replace(/\\/g, "");
              if (item.hasOwnProperty("templet")) _val = item.templet(val);
              if (item.type == "checkbox")
                _val =
                  "<input value=" +
                  val[item.field] +
                  '  class="check" onclick="bt.check_select();" type="checkbox">';
              var td = "<td ";
              if (item.align) {
                td += 'style="';
                if (item.align) td += "text-align:" + item.align;
                td += '"';
              }
              if (item.index) td += 'data-index="' + i + '" ';
              td += ">";
              var fixed = false;
              if (typeof item.fixed != "undefined" && item.fixed) {
                if (typeof item.class != "undefined") {
                  if (item.class.indexOf("fixed") === -1)
                    item.class += " fixed";
                } else {
                  item.class = "fixed";
                }
                fixed = true;
              }
              tr.append(
                td +
                  (fixed
                    ? '<span style="width:' +
                      (item.width - 16) +
                      'px" title="' +
                      _val +
                      '" class="' +
                      item["class"] +
                      '">' +
                      _val +
                      "</span>"
                    : _val) +
                  "</td>"
              );
              tr.data("item", val);
              _tab.append(tr);
            }
          }
        }
      } else {
        _tab.append(
          "<tr><td colspan='" +
            obj.columns.length +
            "'>" +
            lan.bt.no_data +
            "</td></tr>"
        );
        if ($(obj.table).attr("id") == "softList") {
          _tab
            .find("td")
            .css("text-align", "center")
            .html(
              "<a class=\"btlink\" onclick=\"bt.openFeedback({title:'宝塔面板需求反馈收集',placeholder:'<span>如果您在使用过程中遇到任何问题或功能不完善，请将您的问题或需求详细描述给我们，</span><br>我们将尽力为您解决或完善。',recover:'我们特别重视您的需求反馈，我们会定期每周进行需求评审。希望能更好的帮到您',key:993,proType:16})\">未查询到搜索内容,提交需求反馈</a>"
            );
          $(".soft-search").after(
            "<a class=\"btlink npsFeedBack ml20\" style=\"line-height: 30px\" onclick=\"bt.openFeedback({title:'宝塔面板需求反馈收集',placeholder:'<span>如果您在使用过程中遇到任何问题或功能不完善，请将您的问题或需求详细描述给我们，</span><br>我们将尽力为您解决或完善。',recover:'我们特别重视您的需求反馈，我们会定期每周进行需求评审。希望能更好的帮到您',key:993,proType:16})\">未查询到搜索内容,提交需求反馈</a>"
          );
        }
      }
      $(obj.table)
        .find(".check")
        .click(function () {
          var checked = $(this).prop("checked");
          if ($(this).parent().prop("tagName") == "TH") {
            $(".check").prop("checked", checked ? "checked" : "");
          }
        });
      var asc = "glyphicon-triangle-top";
      var desc = "glyphicon-triangle-bottom";

      var orderby = bt.get_cookie("order");
      if (orderby != undefined) {
        var arrys = orderby.split(" ");
        if (arrys.length == 2) {
          if (arrys[1] == "asc") {
            $(obj.table)
              .find('th span[data-id="' + arrys[0] + '"]')
              .removeClass(desc)
              .addClass(asc);
          } else {
            $(obj.table)
              .find('th span[data-id="' + arrys[0] + '"]')
              .removeClass(asc)
              .addClass(desc);
          }
        }
      }

      $(obj.table)
        .find("th")
        .data("checks", checks)
        .click(function () {
          var _th = $(this);
          var _checks = _th.data("checks");
          var _span = _th.find("span");
          if (_span.length > 0) {
            var or = _span.attr("data-id");
            if (_span.hasClass(asc)) {
              bt.set_cookie("order", or + " desc");
              $(obj.table)
                .find('th span[data-id="' + or + '"]')
                .removeClass(asc)
                .addClass(desc);
              _checks[or]();
            } else if (_span.hasClass(desc)) {
              bt.set_cookie("order", or + " asc");
              $(obj.table)
                .find('th span[data-id="' + arrys[0] + '"]')
                .removeClass(desc)
                .addClass(asc);
              _checks[or]();
            }
          }
        });
    }
    return _tab;
  },

  /**
   * @description 在线客服
   * @param {string} help 帮助信息
   */
  onlineService: function (help) {
    layer.open({
      type: 1,
      area: ["200px", "250px"],
      title: false,
      closeBtn: 2,
      shift: 0,
      content:
        '<div class="service_consult">\
						<div class="service_consult_title" style="background: rgba(32, 165, 58, 0.1);"><a href="https://www.bt.cn/new/wechat_customer" target="_blank" class="btlink"><span style="border-bottom: 1px solid;">点击咨询客服</span><div class="icon-r" style="width: 15px;height: 18px;margin-top: 1px;margin-left: 5px;vertical-align: middle;"></div></a></div>\
						<div class="contact_consult" style="margin: 10px auto 8px auto;">\
							<div id="contact_consult_qcode">\
								<img src="/static/images/customer-qrcode.png" alt="" style="border: none;" />\
							</div>\
						</div>\
						<div class="wechat-title">\
						<img class="icon" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABkAAAAZCAYAAADE6YVjAAAAAXNSR0IArs4c6QAAATlJREFUSEvtVrFOw0AMfed8AxJsZWGAgQHBXP4DCQa+Ioou7g18BRIg9T/KDGJggIGFbiDxDXGQowSBuGvrFISEmtF+7/nis312RVEMiWgIoMT375aIjpj5KeJrTMy8JSJjAPsRzEhErl1Zlhd1XZ8kRKZEdMjM0xlBBiIyATCIYZxzl857X6uTiHaY+TElZrUz87aIPCjvI0gIwVmF5uG7H1gFmZepxv85XTdqCCEcLMQ0gLz3jbbTOm/rPdkLBt0v0E77xysq2it9T2nhuTzPN4ho10KyYEXkXvvkBcC6hWjEvmqQMwCnANZa8p1RJAbfa41vAM7/0cUzczOiZ43zvunrtPVOntuO3+wrluJ12qspvFBm/+bR+u03nhPrkKZk2ZVINUZO964sy44Ta9FSK5GuQ1VVXb0DLf+sHQ9tLL0AAAAASUVORK5CYII=">\
						<span class="scan-title" style="font-size: 16px;">扫一扫</span></div>\
				</div>',
      success: function (layers) {
        $(layers).css("border-radius", "4px");
        var html = "";
        if (Array.isArray(help)) {
          for (var i = 0; i < help.length; i++) {
            html += help[i];
          }
          $("#helpList").parent(html);
        }
      },
    });
  },
  	// json格式化
	formatJsonForNotes:function(json, options) {
		var reg = null,
			formatted = '',
			pad = 0,
			PADDING = '  '; // （缩进）可以使用'\t'或不同数量的空格
		// 可选设置
		options = options || {};
		// 在 '{' or '[' follows ':'位置移除新行
		options.newlineAfterColonIfBeforeBraceOrBracket = (options.newlineAfterColonIfBeforeBraceOrBracket === true) ? true : false;
		// 在冒号后面加空格
		options.spaceAfterColon = (options.spaceAfterColon === false) ? false : true;
		// 开始格式化...
		if (typeof json !== 'string') {
			// 确保为JSON字符串
			json = JSON.stringify(json);
		} else {
			//已经是一个字符串，所以解析和重新字符串化以删除额外的空白
			json = JSON.parse(json);
			json = JSON.stringify(json);
		}
		// 在花括号前后添加换行
		reg = /([\{\}])/g;
		json = json.replace(reg, '\r\n$1\r\n');
		// 在方括号前后添加新行
		reg = /([\[\]])/g;
		json = json.replace(reg, '\r\n$1\r\n');
		// 在逗号后添加新行
		reg = /(\,)/g;
		json = json.replace(reg, '$1\r\n');
		// 删除多个换行
		reg = /(\r\n\r\n)/g;
		json = json.replace(reg, '\r\n');
		// 删除逗号前的换行
		reg = /\r\n\,/g;
		json = json.replace(reg, ',');
		// 可选格式...
		if (!options.newlineAfterColonIfBeforeBraceOrBracket) {
			reg = /\:\r\n\{/g;
			json = json.replace(reg, ':{');
			reg = /\:\r\n\[/g;
			json = json.replace(reg, ':[');
		}
		if (options.spaceAfterColon) {
			reg = /\:/g;
			json = json.replace(reg, ': ');
		}
		$.each(json.split('\r\n'), function(index, node) {
			var i = 0,
				indent = 0,
				padding = '';
			if (node.match(/\{$/) || node.match(/\[$/)) {
				indent = 1;
			} else if (node.match(/\}/) || node.match(/\]/)) {
				if (pad !== 0) {
					pad -= 1;
				}
			} else {
				indent = 0;
			}
			for (i = 0; i < pad; i++) {
				padding += PADDING;
			}
			formatted += padding + node + '\r\n';
			pad += indent;
		});
		return formatted;
	},
};
// 旧版的tools库，兼容旧方法

var bt_tools = {
  commandConnectionPool: {}, //ws连接池
  /**
   * @description 表格渲染
   * @param {object} config  配置对象 参考说明
   * @return {object} table 表格对象
   */
  table: function (config) {
    var that = this,
      table = $(config.el),
      tableData = table.data("table");
    if (tableData && table.find("table").length > 0) {
      if (config.url !== undefined) {
        tableData.$refresh_table_list(true);
      } else if (config.data !== undefined) {
        tableData.$reader_content(config.data);
      }
      return tableData;
    }

    function ReaderTable(config) {
      this.config = config;
      this.$load();
    }

    ReaderTable.prototype = {
      style_list: [], // 样式列表
      event_list: {}, // 事件列表,已绑定事件
      checkbox_list: [], // 元素选中列表
      batch_active: {},
      event_rows_model: {}, // 事件行内元素模型，行内元素点击都会将数据临时存放
      data: [],
      cache_set_column: [], //缓存设置显示隐藏的列数据
      cache_set_all: {}, //所有缓存设置显示隐藏的列数据
      page: "",
      column: [],
      batch_thread: [],
      random: bt.get_random(5),
      init: false, // 是否初始化渲染
      checked: false, // 是否激活，用来判断是否失去焦点
      /**
       * @description 加载数据
       * @return void
       */
      $load: function () {
        var _that = this;
        if (this.config.init) this.config.init(this);
        $(this.config.el).addClass("bt_table");
        if (this.config.minWidth)
          this.style_list.push({
            className: this.config.el + " table",
            css: "min-width:" + this.config.minWidth,
          });
        if (this.config.tootls) {
          this.$reader_tootls(this.config.tootls);
        } else {
          if ($(_that.config.el + ".divtable").length === 0)
            $(_that.config.el).append(
              '<div class="divtable mtb10" style="max-height:' +
                (this.config.height || "auto") +
                '"></div>'
            );
        }
        this.$reader_content();
        if (_that.config.url !== undefined) {
          this.$refresh_table_list(_that.config.load || false);
        } else if (this.config.data !== undefined) {
          this.$reader_content(this.config.data);
        } else {
          alert("缺少data或url参数");
        }
        if (this.config.methods) {
          //挂载实例方法
          $.extend(this, this.config.methods);
        }
        if (this.config.height)
          bt_tools.$fixed_table_thead(this.config.el + " .divtable");
      },

      /**
       * @description 刷新表格数据
       * @param {boolean} load
       * @param {function} callback 回调函数
       * @return void
       */
      $refresh_table_list: function (load, callback) {
        var _that = this;
        this.$http(load, function (data) {
          if (callback) callback(data);
          _that.$reader_content(
            data.data,
            typeof data.total != "undefined" ? parseInt(data.total) : data.page
          );
        });
      },

      /**
       * @description 渲染内容
       * @param {object} data 渲染的数据
       * @param {number} page 数据分页/总数
       * @return void
       */
      $reader_content: function (data, page) {
        var _that = this,
          d;
        var thead = "",
          tbody = "",
          i = 0,
          column = this.config.column,
          event_list = {},
          checkbox = $(_that.config.el + " .checkbox_" + _that.random);
        data = data || [];
        this.data = data;
        if (_that.config.setting_btn) {
          var time = setInterval(function () {
            if (bt.config != undefined) {
              pub_content(bt.config);
              clearInterval(time);
            }
          }, 1);
        } else {
          old_pub_content();
        }
        function old_pub_content() {
          if (checkbox.length) {
            checkbox.removeClass("active selected");
            _that.checkbox_list = [];
            _that.$set_batch_view();
          }
          do {
            var rows = _that.data[i],
              completion = 0;
            if (_that.data.length > 0) tbody += "<tr>";
            for (var j = 0; j < column.length; j++) {
              var item = column[j];
              if ($.isEmptyObject(item)) {
                completion++;
                continue;
              }
              if (i === 0 && !_that.init) {
                if (!_that.init)
                  _that.style_list.push(
                    _that.$dynamic_merge_style(item, j - completion)
                  );
                var sortName = "sort_" + _that.random + "",
                  checkboxName = "checkbox_" + _that.random,
                  sortValue = item.sortValue || "desc";
                thead +=
                  "<th><span " +
                  (item.sort
                    ? 'class="not-select ' +
                      sortName +
                      (item.sortValue ? " sort-active" : "") +
                      ' cursor-pointer"'
                    : "") +
                  ' data-index="' +
                  j +
                  '" ' +
                  (item.sort ? 'data-sort="' + sortValue + '"' : "") +
                  ">" +
                  (item.type == "checkbox"
                    ? '<label><i class="cust—checkbox cursor-pointer ' +
                      checkboxName +
                      '" data-checkbox="all"></i><input type="checkbox" class="cust—checkbox-input"></label>'
                    : "<span>" + item.title + "</span>") +
                  (item.sort
                    ? '<span class="glyphicon glyphicon-triangle-' +
                      (sortValue == "desc" ? "bottom" : "top") +
                      ' ml5"></span>'
                    : "") +
                  "</span></th>";
                if (i === 0) {
                  if (!event_list[sortName] && item.sort)
                    event_list[sortName] = {
                      event: _that.config.sortEvent,
                      eventType: "click",
                      type: "sort",
                    };
                  if (!event_list[checkboxName])
                    event_list[checkboxName] = {
                      event: item.checked,
                      eventType: "click",
                      type: "checkbox",
                    };
                }
              }
              if (rows !== undefined) {
                var template = "",
                  className = "event_" + item.fid + "_" + _that.random;
                if (item.template) {
                  template = _that.$custom_template_render(item, rows, j);
                }
                if (
                  typeof template === "undefined" ||
                  typeof item.template === "undefined"
                ) {
                  template = _that.$reader_column_type(item, rows);
                  event_list = $.extend(event_list, template[1]);
                  template = template[0];
                }
                var fixed = false;
                if (typeof item.fixed != "undefined" && item.fixed) {
                  if (typeof item.class != "undefined") {
                    if (item.class.indexOf("fixed") === -1)
                      item.class += " fixed";
                  } else {
                    item.class = "fixed";
                  }
                  fixed = true;
                }
                tbody +=
                  "<td><span " +
                  (fixed
                    ? 'style="width:' +
                      (item.width - 16) +
                      'px" title="' +
                      template +
                      '"'
                    : " ") +
                  (item["class"] ? 'class="' + item["class"] + '"' : "") +
                  " " +
                  (item.tips ? 'title="' + item.tips + '"' : "") +
                  ">" +
                  template +
                  "</span></td>";
                if (i === 0) {
                  if (!event_list[className] && item.event)
                    event_list[className] = {
                      event: item.event,
                      eventType: "click",
                      type: "rows",
                    };
                }
              }
            }
            if (_that.data.length > 0) tbody += "</tr>";
            if (_that.data.length == 0)
              tbody +=
                '<tr class="no-tr"><td colspan="' +
                column.length +
                '" style="text-align:center;">' +
                (_that.config["default"] || "数据为空") +
                "</td></tr>";
            i++;
          } while (i < _that.data.length);
          if (!_that.init) _that.$style_bind(_that.style_list);
          _that.$event_bind(event_list);
          if (!_that.init) {
            $(_that.config.el + " .divtable").append(
              '<table class="table table-hover"><thead style="position: relative;z-index: 1;">' +
                thead +
                "</thead><tbody>" +
                tbody +
                "</tbody></table></div></div>"
            );
          } else {
            $(_that.config.el + " .divtable tbody").html(tbody);
            if (_that.config.page) {
              $(_that.config.el + " .page").replaceWith(
                _that.$reader_page(_that.config.page, page)
              );
            }
          }

          _that.init = true;
          if (_that.config.success) _that.config.success(this);
        }
        function pub_content(rdata_header) {
          /*** 渲染设置显示隐藏列按钮 ***/
          var setting_btn = _that.config.setting_btn;
          if (setting_btn) {
            var cache_name = _that.config.el + "_" + _that.random,
              setting_ul_html = "";
            _that.cache_set_column = [];
            var flag = false,
              flag_num = 0;
            for (var j = 0; j < column.length; j++) {
              if (column[j]["type"] == "checkbox") continue;
              if (!column[j]["width"]) flag = true;
              _that.cache_set_column.push({
                title: column[j]["real_title"]
                  ? column[j]["real_title"]
                  : column[j]["title"],
                value: column[j].hasOwnProperty("display")
                  ? column[j]["display"]
                  : true,
                idx: j,
                disabled: column[j].hasOwnProperty("isDisabled")
                  ? column[j]["isDisabled"]
                  : false,
                pay: column[j].hasOwnProperty("pay") ? column[j]["pay"] : false,
              });
            }
            // if(!flag) {
            //     column[1]['width'] = 'auto'
            // }
            if (_that.config.hasOwnProperty("setting_list")) {
              for (var j = 0; j < _that.config.setting_list.length; j++) {
                _that.cache_set_column.unshift(_that.config.setting_list[j]);
              }
            }
            _that.cache_set_all = !$.isEmptyObject(rdata_header.table_header)
              ? rdata_header.table_header
              : _that.cache_set_all; // 获取所有缓存数据
            var cache_data = $.isEmptyObject(rdata_header.table_header)
              ? []
              : JSON.parse(_that.cache_set_all[_that.config.headerId] || "[]");
            try {
              var _flag =
                _that.cache_set_all[_that.config.headerId] &&
                cache_data.filter(function (item, index) {
                  if (!_that.cache_set_column[index]) return false;
                  return item.title === _that.cache_set_column[index].title;
                }).length === _that.cache_set_column.length;
              _that.cache_set_column = _flag
                ? JSON.parse(_that.cache_set_all[_that.config.headerId])
                : _that.cache_set_column; // 有缓存时用缓存数据
            } catch (error) {
              console.log(error);
            }

            // 渲染显示隐藏列按钮下拉列表
            for (var j = 0; j < _that.cache_set_column.length; j++) {
              var obj = _that.cache_set_column[j],
                title = $(obj.title).text().replace(/\?/g, "");
              if (obj.value) flag_num++;
              var text = "";
              if (title == "流量" || (obj.title == "流量" && obj.disabled))
                text = "不支持openlitespeed";
              setting_ul_html +=
                '<li title="' +
                text +
                '" class="setting_ul_li' +
                (obj.value ? " active" : "") +
                (obj.disabled ? " disabled" : "") +
                '">\
              <i></i>\
                <span class="ml10">' +
                (title ? title : obj.title) +
                "</span>" +
                (title || obj.pay
                  ? '<span class="glyphicon icon-vipLtd" style="margin-left: 6px;position: relative;top: -2px;"></span>'
                  : "") +
                "</li>";
              if (obj.idx) column[obj.idx]["display"] = obj.value; // 重置显示状态
            }

            // var allColumns = column.length;
            // var displayedColumns = _that.cache_set_column.filter(function(col) {
            // 	return col.value;
            // }).length;

            // if (displayedColumns === allColumns) { // 当界面显示列与表格的所有列长度相等时(都显示)
            // 	var allColumnsHaveWidth = column.every(function(col) {
            // 		return col.width && col.width != 'auto';
            // 	});
            //
            // 	if (allColumnsHaveWidth) {
            // 	    // 所有列都有宽度时，不进行操作
            // 	} else {
            // 		var secondColumn = column[1];
            // 			var columnWithoutWidth = column.find(function(col, index) {
            // 				return index > 1 && !col.width;
            // 			});
            //
            // 			if (columnWithoutWidth) { // 首列为复选框列，且含有除第二列的某一列无宽度或auto时，则设定第二列宽度为auto
            // 				secondColumn.width = 'auto';
            // 			} else {
            // 				var websiteNameColumn = column.find(function(col) {
            // 					return col.title === '网站名';
            // 				});
            //
            // 				if (websiteNameColumn) { // 首列为复选框列，只有第二列无宽度或auto时，设定第二列宽度为100px，若该列为网站名，则设定为210px
            // 					websiteNameColumn.width = 200;
            // 				} else {
            // 					secondColumn.width = 100;
            // 				}
            // 			}
            // 	}
            // } else { // 当界面显示列与表格所有列长度不等时(未全部展示)
            // 	var displayedColumnsHaveWidth = column.every(function(col) {
            // 		return col.display && col.width && col.width != 'auto';
            // 	});
            // 	if (displayedColumnsHaveWidth) { // 显示的所有列都有宽度时，若首列为复选框，则设定第二列的列宽度为auto
            // 		var firstColumn = column[0];
            // 		if (firstColumn.type === 'checkbox') {
            // 			var secondColumn = column[1];
            // 			secondColumn.width = 'auto';
            // 			var websiteNameColumn = column.find(function(col) {
            // 				return col.title === '网站名';
            // 			});
            // 			if (websiteNameColumn) {
            // 				var otherColumnsWidth = column.reduce(function(acc, col) {
            // 					if (col.title !== '网站名' && col.display) {
            // 						return acc + parseInt(col.width) || 0;
            // 					}
            // 					return acc;
            // 				}, 0);
            //
            // 				var tableWidth = $(_that.config.el).width();
            // 				if (tableWidth - otherColumnsWidth > 200 ) {
            // 					websiteNameColumn.width = 'auto';
            // 				}else{
            // 				    websiteNameColumn.width = 200;
            // 				}
            // 			}
            // 		}
            // 	}else{
            // 	    // 固定网站名宽度
            // 	    var websiteNameColumn = column.find(function(col) {
            // 				return col.title === '网站名';
            // 			});
            // 			if (websiteNameColumn) {
            // 				var otherColumnsWidth = column.reduce(function(acc, col) {
            // 					if (col.title !== '网站名' && col.display) {
            // 						return acc + parseInt(col.width) || 0;
            // 					}
            // 					return acc;
            // 				}, 0);
            //
            // 				var tableWidth = $(_that.config.el).width();
            // 				if (tableWidth - otherColumnsWidth > 200 ) {
            // 					websiteNameColumn.width = 'auto';
            // 				}else{
            // 				    websiteNameColumn.width = 200;
            // 				}
            // 			}
            // 	}
            // }

            //渲染显示隐藏列按钮
            if (!$(_that.config.el + " .set_list_fid_dropdown").length) {
              $(_that.config.el + " .tootls_top .pull-right").append(
                '<div class="set_list_fid_dropdown"><div class="setting_btn"><i class="glyphicon glyphicon-cog icon-setting"></i></div>\
                <ul class="setting_ul">' +
                  setting_ul_html +
                  "</ul></div>"
              );
            }
            //显示隐藏列鼠标移入事件
            var set_interval = null;
            $(_that.config.el + " .setting_btn").hover(
              function () {
                $(this).next().show();
              },
              function (e) {
                var _this = $(this),
                  mouseY = 0,
                  mouseX = 0;
                //获取鼠标位置
                $(document).mousemove(function (e) {
                  mouseY = e.pageY;
                  mouseX = e.pageX;
                });
                set_interval = setInterval(function () {
                  if (_this.next().css("display") == "block") {
                    var bW = _this.width(),
                      bH = _this.height(),
                      bT = _this.offset().top,
                      bL = _this.offset().left,
                      uW = _this.next().width(),
                      uH = _this.next().height(),
                      uT = _this.next().offset().top,
                      uL = _this.next().offset().left;
                    var is_b =
                        mouseX > bL &&
                        mouseX < bL + bW &&
                        mouseY > bT &&
                        mouseY < bT + bH,
                      is_u =
                        mouseX > uL &&
                        mouseX < uL + uW &&
                        mouseY > uT &&
                        mouseY < uT + uH;
                    //判断是否还在区域内
                    if (!is_b && !is_u) _this.next().hide();
                  } else {
                    clearInterval(set_interval);
                  }
                }, 200);
              }
            );

            //显示隐藏列点击事件
            $(_that.config.el + " .setting_ul .setting_ul_li")
              .unbind("click")
              .click(function (e) {
                if ($(this).hasClass("disabled")) return false;
                if ($(this).hasClass("active")) $(this).removeClass("active");
                else $(this).addClass("active");
                var index = $(this).index();
                _that.cache_set_column[index].value =
                  !_that.cache_set_column[index].value; //重置显示状态
                _that.cache_set_all[_that.config.headerId] =
                  _that.cache_set_column;
                bt.send(
                  "set_table_header",
                  "config/set_table_header",
                  {
                    table_name: _that.config.headerId,
                    table_data: JSON.stringify(_that.cache_set_column),
                  },
                  function (res) {
                    bt.send(
                      "get_table_header",
                      "config/get_table_header",
                      {},
                      function (rdata_header) {
                        // 获取所有表自定义列数据
                        bt.config["table_header"] = rdata_header;
                        _that.init = false; //重置表头和数据
                        _that.style_list = [_that.style_list[0]]; //重置样式
                        $("#bt_table_" + _that.random).remove(); //重置表样式
                        _that.$reader_content(_that.data, page); //刷新数据
                      }
                    );
                  }
                );
              });
          }
          /*** -------end-------- ***/

          if (checkbox.length) {
            checkbox.removeClass("active selected");
            _that.checkbox_list = [];
            _that.$set_batch_view();
          }
          do {
            var rows = _that.data[i],
              completion = 0;
            if (_that.data.length > 0) tbody += "<tr>";
            for (var j = 0; j < column.length; j++) {
              /*** 设置列显示隐藏存在 并且 不显示 则跳过 ***/
              if (setting_btn && column[j]["display"] === false) {
                if (!column[j].hasOwnProperty("class")) completion++;
                continue;
              }
              /*** -------end-------- ***/
              var item = column[j];
              if ($.isEmptyObject(item)) {
                completion++;
                continue;
              }
              if (i === 0 && !_that.init) {
                if (!_that.init)
                  _that.style_list.push(
                    _that.$dynamic_merge_style(item, j - completion)
                  );
                var sortName = "sort_" + _that.random + "",
                  checkboxName = "checkbox_" + _that.random,
                  sortValue = item.sortValue || "desc";
                thead +=
                  '<th class="' +
                  item.fid +
                  '"><span ' +
                  (item.sort
                    ? 'class="not-select ' +
                      sortName +
                      (item.sortValue ? " sort-active" : "") +
                      ' cursor-pointer"'
                    : "") +
                  ' data-index="' +
                  j +
                  '" ' +
                  (item.sort ? 'data-sort="' + sortValue + '"' : "") +
                  ">" +
                  (item.type == "checkbox"
                    ? '<label><i class="cust—checkbox cursor-pointer ' +
                      checkboxName +
                      '" data-checkbox="all"></i><input type="checkbox" class="cust—checkbox-input"></label>'
                    : "<span>" + item.title + "</span>") +
                  (item.sort
                    ? '<span class="glyphicon glyphicon-triangle-' +
                      (sortValue == "desc" ? "bottom" : "top") +
                      ' ml5"></span>'
                    : "") +
                  "</span></th>";
                if (i === 0) {
                  if (!event_list[sortName] && item.sort)
                    event_list[sortName] = {
                      event: _that.config.sortEvent,
                      eventType: "click",
                      type: "sort",
                    };
                  if (!event_list[checkboxName])
                    event_list[checkboxName] = {
                      event: item.checked,
                      eventType: "click",
                      type: "checkbox",
                    };
                }
              }
              if (rows !== undefined) {
                var template = "",
                  className = "event_" + item.fid + "_" + _that.random;
                if (item.template) {
                  template = _that.$custom_template_render(item, rows, j);
                }
                if (
                  typeof template === "undefined" ||
                  typeof item.template === "undefined"
                ) {
                  template = _that.$reader_column_type(item, rows);
                  event_list = $.extend(event_list, template[1]);
                  template = template[0];
                }
                var fixed = false;
                if (typeof item.fixed != "undefined" && item.fixed) {
                  if (typeof item.class != "undefined") {
                    if (item.class.indexOf("fixed") === -1)
                      item.class += " fixed";
                  } else {
                    item.class = "fixed";
                  }
                  fixed = true;
                }
                tbody +=
                  "<td><span " +
                  (fixed
                    ? 'style="width:' +
                      (item.width - 16) +
                      'px" title="' +
                      template +
                      '"'
                    : " ") +
                  (item["class"] ? 'class="' + item["class"] + '"' : "") +
                  " " +
                  (item.tips ? 'title="' + item.tips + '"' : "") +
                  ">" +
                  template +
                  "</span></td>";
                if (i === 0) {
                  if (!event_list[className] && item.event)
                    event_list[className] = {
                      event: item.event,
                      eventType: "click",
                      type: "rows",
                    };
                }
              }
            }
            if (_that.data.length > 0) tbody += "</tr>";
            if (_that.data.length == 0)
              tbody +=
                '<tr class="no-tr"><td colspan="' +
                column.length +
                '" style="text-align:center;">' +
                (_that.config["default"] || "数据为空") +
                "</td></tr>";
            i++;
          } while (i < _that.data.length);
          if (!_that.init) _that.$style_bind(_that.style_list);
          _that.$event_bind(event_list);
          if (!_that.init) {
            $(_that.config.el + " .divtable .table").remove();
            _that.config.thead(thead);
            $(_that.config.el + " .divtable").append(
              '<table class="table table-hover"><thead style="position: relative;z-index: 1;">' +
                thead +
                "</thead><tbody>" +
                tbody +
                "</tbody></table></div></div>"
            );
          } else {
            $(_that.config.el + " .divtable tbody").html(tbody);
            if (_that.config.page) {
              $(_that.config.el + " .page").replaceWith(
                _that.$reader_page(_that.config.page, page)
              );
            }
          }
          /*** 设置列显示隐藏---单独某个class处理 ***/
          if (setting_btn && _that.config.hasOwnProperty("setting_list")) {
            for (var j = 0; j < _that.cache_set_column.length; j++) {
              var obj = _that.cache_set_column[j];
              if (obj.hasOwnProperty("class")) {
                if (obj.value) $(_that.config.el + " ." + obj.class).show();
                else $(_that.config.el + " ." + obj.class).hide();
              }
            }
          }
          /*** -------end-------- ***/
          _that.init = true;
          if (_that.config.success) _that.config.success(_that);
        }
      },

      /**
       * @description 自定模板渲染
       * @param {object} item 当前元素模型
       * @param {object} rows 当前元素数据
       * @param {number} j 当前模板index
       * @return void
       */
      $custom_template_render: function (item, rows, j) {
        var className = "event_" + item.fid + "_" + this.random,
          _template = item.template(rows, j),
          $template = $(_template);
        if ($template.length > 0) {
          template = $template.addClass(className)[0].outerHTML;
        } else {
          if (item.type === "text") {
            template =
              '<span class="' +
              className +
              " " +
              item["class"] +
              '">' +
              _template +
              "</span>";
          } else {
            template =
              '<a href="javascript:;" class="btlink ' +
              className +
              '">' +
              _template +
              "</a>";
          }
        }
        return template;
      },

      /**
       * @description 替换table数据
       * @param {string} newValue 内容数据
       * @return void
       */
      $modify_row_data: function (newValue) {
        this.event_rows_model.rows = $.extend(
          this.event_rows_model.rows,
          newValue
        );
        var row_model = this.event_rows_model,
          template = null;
        if (typeof row_model.model.template != "undefined") {
          template = $(
            this.$custom_template_render(
              row_model.model,
              row_model.rows,
              row_model.index
            )
          );
          if (!template.length)
            template = $(
              this.$reader_column_type(row_model.model, row_model.rows)[0]
            );
        } else {
          template = $(
            this.$reader_column_type(row_model.model, row_model.rows)[0]
          );
        }
        if (row_model.model.type == "group") {
          $(row_model.el).parent().empty().append(template);
        } else {
          row_model.el.replaceWith(template);
        }
        row_model.el = template;
      },

      /**
       * @description 批量执行程序
       * @param {object} config 配置文件
       * @return void
       */
      $batch_success_table: function (config) {
        var _that = this,
          length = $(config.html).length;
        bt.open({
          type: 1,
          title: config.title,
          area: config.area || ["350px", "350px"],
          shadeClose: false,
          closeBtn: 2,
          content:
            config.content ||
            '<div class="batch_title"><span class><span class="batch_icon"></span><span class="batch_text">' +
              config.title +
              '操作完成！</span></span></div><div class="' +
              (length > 4 ? "fiexd_thead" : "") +
              ' batch_tabel divtable" style="margin: 15px 30px 15px 30px;overflow: auto;height: 200px;"><table class="table table-hover"><thead><tr><th>' +
              config.th +
              '</th><th style="text-align:right;width:120px;">操作结果</th></tr></thead><tbody>' +
              config.html +
              "</tbody></table></div>",
          success: function () {
            if (length > 4) _that.$fixed_table_thead(".fiexd_thead");
          },
        });
      },
      /**
       * @description 固定表头
       * @param {string} el DOM选择器
       * @return void
       */
      $fixed_table_thead: function (el) {
        $(el).scroll(function () {
          var scrollTop = this.scrollTop;
          this.querySelector("thead").style.transform =
            "translateY(" + (scrollTop - 1) + "px)";
        });
      },
      /**
       * @description 删除行内数据
       */
      $delete_table_row: function (index) {
        this.data.splice(index, 1);
        this.$reader_content(this.data);
      },

      /**
       * @description 设置批量操作显示
       * @return void 无
       */
      $set_batch_view: function () {
        if (typeof this.config.batch != "undefined") {
          //判断是否存在批量操作
          var bt_select_btn = $(this.config.el + " .set_batch_option");
          if (typeof this.config.batch.config != "undefined") {
            // 判断批量操作是多个还是单个
            if (this.checkbox_list.length > 0) {
              bt_select_btn
                .removeClass("bt-disabled btn-default")
                .addClass("btn-success")
                .text(
                  "批量" +
                    this.batch_active.title +
                    "(已选中" +
                    this.checkbox_list.length +
                    ")"
                );
            } else {
              bt_select_btn
                .addClass("bt-disabled btn-default")
                .removeClass("btn-success")
                .text("批量" + this.batch_active.title);
            }
          } else {
            var bt_select_val = $(
              this.config.el + " .bt_table_select_group .bt_select_value"
            );
            if (this.checkbox_list.length > 0) {
              bt_select_btn
                .removeClass("bt-disabled btn-default")
                .addClass("btn-success")
                .prev()
                .removeClass("bt-disabled");
              bt_select_val
                .find("em")
                .html("(已选中" + this.checkbox_list.length + ")");
            } else {
              bt_select_btn
                .addClass("bt-disabled btn-default")
                .removeClass("btn-success")
                .prev()
                .addClass("bt-disabled");
              bt_select_val.children().eq(0).html("请选择批量操作<em></em>");
              bt_select_val.next().find("li").removeClass("active");
              this.batch_active = {};
            }
          }
        }
      },

      /**
       * @description 渲染指定类型列内容
       * @param {object} data 渲染的数据
       * @param {object} rows 渲染的模板
       * @return void
       */
      $reader_column_type: function (item, rows) {
        var value = rows[item.fid],
          event_list = {},
          className = "click_" + item.fid + "_" + this.random,
          config = [],
          _that = this;
        switch (item.type) {
          case "text": //普通文本
            config = [value, event_list];
            break;
          case "checkbox": //单选内容
            config = [
              '<label><i class="cust—checkbox cursor-pointer checkbox_' +
                this.random +
                '"></i><input type="checkbox" class="cust—checkbox-input"></label>',
              event_list,
            ];
            break;
          case "password":
            var _copy = "",
              _eye_open = "",
              className = "ico_" + _that.random + "_",
              html =
                '<span class="bt-table-password mr10"><i>**********</i></span>';
            if (item.eye_open) {
              html +=
                '<span class="glyphicon cursor pw-ico glyphicon-eye-open mr10 ' +
                className +
                'eye_open" title="显示密码"></span>';
              if (!event_list[className + "eye_open"])
                event_list[className + "eye_open"] = {
                  type: "eye_open_password",
                };
            }
            if (item.copy) {
              html +=
                '<span class="ico-copy cursor btcopy mr10 ' +
                className +
                'copy" title="复制密码"></span>';
              if (!event_list[className + "copy"])
                event_list[className + "copy"] = {
                  type: "copy_password",
                };
            }
            config = [html, event_list];
            break;
          case "link": //超链接类型
            className += "_" + item.fid;
            if (!event_list[className] && item.event)
              event_list[className] = {
                event: item.event,
                type: "rows",
              };
            config = [
              '<a class="btlink ' +
                className +
                '" href="' +
                (item.href ? value : "javascript:;") +
                '" ' +
                (item.href
                  ? 'target="' + (item.target || "_blank") + '"'
                  : "") +
                ' title="' +
                value +
                '">' +
                value +
                "</a>",
              event_list,
            ];
            break;
          case "input": //可编辑类型
            blurName = "blur_" + item.fid + "_" + this.random;
            keyupName = "keyup_" + item.fid + "_" + this.random;
            if (!event_list[blurName] && item.blur)
              event_list[blurName] = {
                event: item.blur,
                eventType: "blur",
                type: "rows",
              };
            if (!event_list[keyupName] && item.keyup)
              event_list[keyupName] = {
                event: item.keyup,
                eventType: "keyup",
                type: "rows",
              };
            config = [
              '<input type="text" title="点击编辑内容，按回车或失去焦点自动保存"  class="table-input ' +
                blurName +
                " " +
                keyupName +
                '" data-value="' +
                value +
                '" value="' +
                value +
                '" />',
              event_list,
            ];
            break;
          case "status": // 状态类型
            var active = "";
            $.each(item.config.list, function (index, items) {
              if (items[0] === value) active = items;
            });
            if (!event_list[className] && item.event)
              event_list[className] = {
                event: item.event,
                type: "rows",
              };
            config = [
              '<a class="btlink ' +
                className +
                " " +
                (active[2].indexOf("#") > -1 ? "" : active[2]) +
                '" style="' +
                (active[2].indexOf("#") > -1
                  ? "color:" + active[2] + ";"
                  : "") +
                '" href="javascript:;"><span>' +
                active[1] +
                "</span>" +
                (item.config.icon
                  ? '<span class="glyphicon ' + active[3] + '"></span>'
                  : "") +
                "</a>",
              event_list,
            ];
            break;
          case "switch": //开关类型
            var active = "",
              _random = bt.get_random(5);
            active = new Number(value) == true ? "checked" : "";
            if (!event_list[className] && item.event)
              event_list[className] = {
                event: item.event,
                type: "rows",
              };
            config = [
              '<div class="bt_switch_group"><input class="btswitch btswitch-ios ' +
                className +
                '" id="' +
                _random +
                '" type="checkbox" ' +
                active +
                '><label class="btswitch-btn" for="' +
                _random +
                '" data-index="0" bt-event-click="set_site_server_status"></label></div>',
              event_list,
            ];
            break;
          case "group":
            var _html = "";
            $.each(item.group, function (index, items) {
              className =
                (item.fid ? item.fid : "group") +
                "_" +
                index +
                "_" +
                _that.random;
              var _hide = false;
              if (items.template) {
                var _template = items.template(rows, _that),
                  $template = $(_template);
                if ($template.length > 0) {
                  _html += $template.addClass(className)[0].outerHTML;
                } else {
                  _html +=
                    '<a href="javascript:;" class="btlink ' +
                    className +
                    '" title="' +
                    (items.title || "") +
                    '">' +
                    _template +
                    "</a>";
                }
              } else {
                if (typeof items.hide != "undefined") {
                  _hide =
                    typeof items.hide === "boolean"
                      ? items.hide
                      : items.hide(rows);
                  if (typeof _hide != "boolean") return false;
                }
                _html +=
                  '<a href="javascript:;" class="btlink ' +
                  className +
                  '" ' +
                  (_hide ? 'style="display:none;"' : "") +
                  ' title="' +
                  (items.tips || items.title) +
                  '">' +
                  items.title +
                  "</a>";
              }
              //当前操作按钮长度等于当前所以值时不向后添加分割
              if (!_hide)
                _html +=
                  item.group.length == index + 1
                    ? ""
                    : "&nbsp;&nbsp;|&nbsp;&nbsp;";
              if (!event_list[className] && items.event)
                event_list[className] = {
                  event: items.event,
                  type: "rows",
                };
            });
            config = [_html, event_list];
            break;
          default:
            config = [value, event_list];
            break;
        }
        return config;
      },
      /**
       * @description 渲染工具条
       * @param {object} data 配置参数
       * @return void
       */
      $reader_tootls: function (config) {
        var _that = this,
          event_list = {};

        /**
         * @description 请求方法
         * @param {Function} callback 回调函数
         * @returns void
         */
        function request(active, check_list) {
          var loadT = bt.load("正在执行批量" + active.title + "，请稍候..."),
            batch_config = {},
            list = _that.$get_data_batch_list(active.paramId, check_list);
          if (!active.beforeRequest) {
            batch_config[active.paramName] = list.join(",");
          } else {
            batch_config[active.paramName] = active.beforeRequest(check_list);
          }
          bt_tools.send(
            {
              url: active.url || _that.config.batch.url,
              data: $.extend(active.param || {}, batch_config),
            },
            function (res) {
              loadT.close();
              if (res.status === false && typeof res.success === "undefined") {
                bt_tools.msg(res);
                return false;
              }
              if (typeof active.tips === "undefined" || active.tips) {
                var html = "";
                $.each(res.error, function (key, item) {
                  html +=
                    '<tr><td><span class="text-overflow" title="' +
                    key +
                    '">' +
                    key +
                    '</span/></td><td><div style="float:right;" class="size_ellipsis"><span style="color:red">' +
                    item +
                    "</span></div></td></tr>";
                });
                $.each(res.success, function (index, item) {
                  html +=
                    '<tr><td><span class="text-overflow" title="' +
                    item +
                    '">' +
                    item +
                    '</span></td><td><div style="float:right;" class="size_ellipsis"><span style="color:#20a53a">操作成功</span></div></td></tr>';
                });
                _that.$batch_success_table({
                  title: "批量" + active.title,
                  th: active.theadName,
                  html: html,
                });
                if (active.refresh) _that.$refresh_table_list(true);
              } else {
                if (!active.success) {
                  var html = "";
                  $.each(check_list, function (index, item) {
                    html +=
                      '<tr><td><span class="text-overflow" title="' +
                      item.name +
                      '">' +
                      item.name +
                      '</span></td><td><div style="float:right;"><span style="color:' +
                      (res.status ? "#20a53a" : "red") +
                      '">' +
                      ((typeof active.theadValue != "undefined"
                        ? active.theadValue[res.status ? 0 : 1]
                        : null) || res.msg) +
                      "</span></div></td></tr>";
                  });
                  _that.$batch_success_table({
                    title: "批量" + active.title + "完成",
                    th: active.theadName,
                    html: html,
                  });
                  if (active.refresh) _that.$refresh_table_list(true);
                }
              }
              if (active.success) {
                active.success(res, check_list, _that);
              }
            }
          );
        }

        /**
         * @description 执行批量，包含递归批量和自动化批量
         * @returns void
         */
        function execute_batch(active, check_list, success) {
          // if(active.recursion) 递归方式
          var bacth = {
            loadT: 0,
            config: {},
            check_list: check_list,
            bacth_status: true,
            start_batch: function (param, callback) {
              var _this = this;
              if (typeof param == "undefined") param = {};
              if (typeof param == "function") (callback = param), (param = {});
              if (active.load)
                this.loadT = layer.msg(
                  "正在执行批量" +
                    active.title +
                    '，<span class="batch_progress">进度:0/' +
                    this.check_list.length +
                    "</span>,请稍候...",
                  {
                    icon: 16,
                    skin: "batch_tips",
                    shade: 0.3,
                    time: 0,
                    area: "400px",
                  }
                );
              this.config = {
                param: param,
                url: active.url,
              };
              this.bacth(callback);
            },
            /**
             *
             * @param {Number} index 递归批量程序
             * @param {Function} callback 回调函数
             * @return void(0)
             */
            bacth: function (index, callback) {
              var _this = this,
                param = {};
              if (typeof index === "function" || typeof index === "undefined")
                (callback = index), (index = 0);
              if (index < this.check_list.length) {
                "function" == typeof active.url
                  ? (this.config.url = active.url(check_list[index]))
                  : (this.config.url = active.url);
                if (typeof active.param == "function") {
                  param = active.param(check_list[index]);
                } else {
                  param = active.param;
                }
                this.config.param = $.extend(this.config.param, param);
                // this.config.param = param;
                if (typeof active.paramId != "undefined")
                  _this.config.param[active.paramName || active.paramId] =
                    _this.check_list[index][active.paramId];
                if (typeof active.beforeBacth != "undefined")
                  this.config.param = $.extend(
                    this.config.param,
                    active.beforeBacth(_this.check_list[index])
                  );
                if (
                  this.config.param["bacth"] &&
                  index == this.check_list.length - 1
                ) {
                  delete this.config.param["bacth"];
                }
                if (!_this.bacth_status) return false;
                if (active.load)
                  $("#layui-layer" + _this.loadT)
                    .find(".layui-layer-content")
                    .html(
                      '<i class="layui-layer-ico layui-layer-ico16"></i>正在执行批量' +
                        active.title +
                        '，<span class="batch_progress">进度:' +
                        index +
                        "/" +
                        _this.check_list.length +
                        "</span>，请稍候..." +
                        (active.clear
                          ? '<a href="javascript:;" class="btlink clear_batch" style="margin-left:20px;">取消</a>'
                          : "")
                    );
                bt_tools.send(
                  {
                    url: this.config.url,
                    data: this.config.param,
                    bacth: true,
                  },
                  function (res) {
                    $.extend(
                      _this.check_list[index],
                      {
                        request: {
                          status:
                            typeof res.status === "boolean"
                              ? res.status
                              : false,
                          msg: res.msg || "请求网络错误",
                        },
                      },
                      { requests: res }
                    );
                    index++;
                    _this.bacth(index, callback);
                  }
                );
              } else {
                if (success) success();
                if (callback) {
                  callback(this.check_list);
                }
                if (active.automatic) {
                  var html = "";
                  for (var i = 0; i < this.check_list.length; i++) {
                    var item = this.check_list[i];
                    html +=
                      "<tr><td>" +
                      (typeof item[active.paramThead] != "undefined"
                        ? item[active.paramThead]
                        : item.name) +
                      '</td><td><div style="float:right;"><span style="color:' +
                      (item.request.status ? "#20a53a" : "red") +
                      '">' +
                      item.request.msg +
                      "</span></div></td></tr>";
                  }
                  _that.$batch_success_table({
                    title: "批量" + active.title,
                    th: active.theadName,
                    html: html,
                  });
                  if (active.refresh) _that.$refresh_table_list(true);
                  _that.$clear_table_checkbox();
                }
                layer.close(this.loadT);
              }
            },
            clear_bacth: function () {
              this.bacth_status = false;
              layer.close(this.loadT);
            },
          };
          if (active.callback) {
            active.callback(bacth);
          } else {
            if (!active.confirm || active.recursion) {
              if (active.confirmVerify) {
                bt.show_confirm(
                  "批量操作" + active.title + "已选中",
                  "批量" + active.title + "，该操作可能会存在风险，是否继续？",
                  function (index) {
                    layer.close(index);
                    if (!active.recursion) {
                      request(active, check_list);
                    } else {
                      bacth.start_batch();
                    }
                  }
                );
              } else {
                bt.confirm(
                  {
                    title: "批量" + active.title,
                    msg:
                      typeof active.tips !== "undefined"
                        ? active.tips
                        : "批量" +
                          active.title +
                          "，该操作可能会存在风险，是否继续？",
                    shadeClose: active.shadeClose ? active.shadeClose : false,
                  },
                  function (index) {
                    layer.close(index);
                    if (!active.recursion) {
                      request(active, check_list);
                    } else {
                      bacth.start_batch();
                    }
                  }
                );
              }
            } else {
              request(active, check_list);
            }
          }
        }

        for (var i = 0; i < config.length; i++) {
          var template = "",
            item = config[i],
            positon = [];
          switch (item.type) {
            case "group":
              positon = item.positon || ["left", "top"];
              $.each(item.list, function (index, items) {
                var _btn = item.type + "_" + _that.random + "_" + index,
                  html = "";
                if (items.type == "division") {
                  template += '<span class="mlr5"></span>';
                } else {
                  if (!items.group) {
                    template +=
                      '<button type="button" title="' +
                      (items.tips || items.title) +
                      '" class="btn ' +
                      (items.active ? "btn-success" : "btn-default") +
                      " " +
                      _btn +
                      ' btn-sm mr5" ' +
                      that.$verify(_that.$reader_style(items.style), "style") +
                      ">" +
                      (items.icon
                        ? '<span class="glyphicon glyphicon-' +
                          items.icon +
                          ' mr5"></span>'
                        : "") +
                      "<span>" +
                      items.title +
                      "</span></button>";
                  } else {
                    template +=
                      '<div class="btn-group" style="vertical-align: top;">\
                        <button type="button" class="btn btn-default ' +
                      _btn +
                      ' btn-sm dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"><span style="margin-right:2px;">分类管理</span><span class="caret" style="position: relative;top: -1px;"></span></button>\
                        <ul class="dropdown-menu"></ul>\
                    </div>';
                    if (item.list) {
                      $.each(item.list, function (index, items) {
                        html +=
                          '<li><a href="javascript:;" ' +
                          +">" +
                          items[item.key] +
                          "</a></li>";
                      });
                    }
                    if (items.init)
                      setTimeout(function () {
                        items.init(_btn);
                      }, 400);
                  }
                }
                if (!event_list[_btn])
                  event_list[_btn] = {
                    event: items.event,
                    type: "button",
                  };
              });
              break;
            case "search":
              positon = item.positon || ["right", "top"];
              item.value = item.value || "";
              this.config.search = item;
              var _input = "search_input_" + this.random,
                _focus = "search_focus_" + this.random,
                _btn = "search_btn_" + this.random;
              template =
                '<div class="bt_search"><input type="text" class="search_input ' +
                _input +
                '" style="' +
                (item.width ? "width:" + item.width : "") +
                '" placeholder="' +
                (item.placeholder || "") +
                '"/><span class="glyphicon glyphicon-search ' +
                _btn +
                '" aria-hidden="true"></span></div>';
              if (!event_list[_input])
                event_list[_input] = {
                  eventType: "keyup",
                  type: "search_input",
                };
              if (!event_list[_focus])
                event_list[_focus] = {
                  type: "search_focus",
                  eventType: "focus",
                };
              if (!event_list[_btn])
                event_list[_btn] = {
                  type: "search_btn",
                };
              break;
            case "batch":
              positon = item.positon || ["left", "bottom"];
              item.placeholder = item.placeholder || "请选择批量操作";
              item.buttonValue = item.buttonValue || "批量操作";
              this.config.batch = item;
              var batch_list = [],
                _html = "",
                active = item.config;
              if (typeof item.config != "undefined") {
                _that.batch_active = active;
                $(_that.config.el).on(
                  "click",
                  ".set_batch_option",
                  function (e) {
                    var check_list = [];
                    for (var i = 0; i < _that.checkbox_list.length; i++) {
                      check_list.push(_that.data[_that.checkbox_list[i]]);
                    }
                    if ($(this).hasClass("bt-disabled")) {
                      layer.tips(
                        _that.config.batch.disabledTips ||
                          "请选择需要批量操作的数据",
                        $(this),
                        {
                          tips: [1, "red"],
                          time: 2000,
                        }
                      );
                      return false;
                    }
                    switch (typeof active.confirm) {
                      case "function":
                        active.confirm(active, function (param, callback) {
                          active.param = $.extend(active.param, param);
                          execute_batch(active, check_list, callback);
                        });
                        break;
                      case "undefined":
                        execute_batch(active, check_list);
                        break;
                      case "object":
                        var config = active.confirm;
                        bt.open({
                          title: config.title || "批量操作",
                          area: config.area || "350px",
                          btn: config.btn || ["确认", "取消"],
                          content: config.content,
                          success: function (layero, index) {
                            config.success(layero, index, active);
                          },
                          yes: function (index, layero) {
                            config.yes(
                              index,
                              layero,
                              function (param, callback) {
                                active.param = $.extend(active.param, param);
                                request(active, check_list);
                              }
                            );
                          },
                        });
                        break;
                    }
                  }
                );
              } else {
                $.each(item.selectList, function (index, items) {
                  if (items.group) {
                    $.each(items.group, function (indexs, itemss) {
                      batch_list.push($.extend({}, items, itemss));
                      _html += '<li class="item">' + itemss.title + "</li>";
                    });
                    delete items.group;
                  } else {
                    batch_list.push(items);
                    _html += '<li class="item">' + items.title + "</li>";
                  }
                });
                // 打开批量类型列表
                $(_that.config.el)
                  .unbind()
                  .on(
                    "click",
                    ".bt_table_select_group .bt_select_value",
                    function (e) {
                      var _this = this,
                        $parent = $(this).parent(),
                        bt_selects = $parent.find(".bt_selects"),
                        area = $parent.offset(),
                        _win_area = _that.$get_win_area();
                      if ($parent.hasClass("bt-disabled")) {
                        layer.tips(
                          _that.config.batch.disabledSelectValue,
                          $parent,
                          { tips: [1, "red"], time: 2000 }
                        );
                        return false;
                      }
                      if ($parent.hasClass("active")) {
                        $parent.removeClass("active");
                      } else {
                        $parent.addClass("active");
                      }
                      if (bt_selects.height() > _win_area[1] - area.top) {
                        bt_selects.addClass("top");
                      } else {
                        bt_selects.removeClass("top");
                      }
                      $(document).one("click", function () {
                        $(_that.config.el)
                          .find(".bt_table_select_group")
                          .removeClass("active");
                        return false;
                      });
                      return false;
                    }
                  );
                // 选择批量的类型
                $(_that.config.el).on(
                  "click",
                  ".bt_table_select_group .item",
                  function (e) {
                    var _text = $(this).text(),
                      _index = $(this).index();
                    $(this).addClass("active").siblings().removeClass("active");
                    $(_that.config.el + " .bt_select_tips").html(
                      "批量" +
                        _text +
                        "<em>(已选中" +
                        _that.checkbox_list.length +
                        ")</em>"
                    );
                    _that.batch_active = batch_list[_index];
                    if (!_that.checked)
                      $(".bt_table_select_group").removeClass("active");
                  }
                );
                // 执行批量操作
                $(_that.config.el).on(
                  "click",
                  ".set_batch_option",
                  function (e) {
                    var check_list = [],
                      active = _that.batch_active;
                    if ($(this).hasClass("bt-disabled")) {
                      layer.tips(
                        _that.config.batch.disabledSelectValue,
                        $(this),
                        {
                          tips: [1, "red"],
                          time: 2000,
                        }
                      );
                      return false;
                    }
                    for (var i = 0; i < _that.checkbox_list.length; i++) {
                      check_list.push(_that.data[_that.checkbox_list[i]]);
                    }
                    if (JSON.stringify(active) === "{}") {
                      var bt_table_select_group = $(
                        _that.config.el + " .bt_table_select_group"
                      );
                      layer.tips(
                        "请选择需要批量操作的类型",
                        bt_table_select_group,
                        {
                          tips: [1, "red"],
                          time: 2000,
                        }
                      );
                      bt_table_select_group.css("border", "1px solid red");
                      setTimeout(function () {
                        bt_table_select_group.removeAttr("style");
                      }, 2000);
                      return false;
                    }
                    switch (typeof active.confirm) {
                      case "function":
                        active.confirm(active, function (param, callback) {
                          active.param = $.extend(active.param, param);
                          execute_batch(active, check_list, callback);
                        });
                        break;
                      case "undefined":
                        execute_batch(active, check_list);
                        break;
                      case "object":
                        var config = active.confirm;
                        bt.open({
                          type: 1,
                          title: config.title || "批量操作",
                          area: config.area || "350px",
                          btn: config.btn || ["确认", "取消"],
                          content:
                            '<div class="pd20">' + config.content + "</div>",
                          success: function (layero, index) {
                            config.success(layero, index, active);
                          },
                          yes: function (index, layero) {
                            config.yes(
                              index,
                              layero,
                              function (param, callback) {
                                active.param = $.extend(active.param, param);
                                layer.close(index);
                                request(active, check_list);
                              }
                            );
                          },
                        });
                        break;
                    }
                  }
                );
              }
              template =
                '<div class="bt_batch"><label><i class="cust—checkbox cursor-pointer checkbox_' +
                this.random +
                '" data-checkbox="all"></i><input type="checkbox" lass="cust—checkbox-input" /></label>' +
                (typeof item.config != "undefined"
                  ? '<button type="button" class="btn btn-default btn-sm set_batch_option bt-disabled">批量' +
                    item.config.title +
                    "</button>"
                  : '<div class="bt_table_select_group bt-disabled not-select"><span class="bt_select_value"><span class="bt_select_tips">请选择批量操作<em></em></span><span class="glyphicon glyphicon-triangle-bottom ml5"></span></span><ul class="bt_selects ">' +
                    _html +
                    '</ul></div><button type="button" class="btn btn-default btn-sm set_batch_option bt-disabled" >' +
                    item.buttonValue +
                    "</button>") +
                "</div>";
              break;
            case "page":
              positon = item.positon || ["right", "bottom"];
              item.page = config.page || 1;
              item.pageParam = item.pageParam || "p";
              item.number = item.number || 20;
              item.numberList = item.numberList || [10, 20, 50, 100, 200];
              item.numberParam =
                typeof item.numberParam === "boolean"
                  ? item.numberParam
                  : item.numberParam || "limit";
              this.config.page = item;
              // var pageNumber = bt.get_cookie('page_number')
              var pageNumber = this.$get_page_number();
              // if (this.config.cookiePrefix && pageNumber) this.config.page.number = pageNumber
              if (pageNumber) this.config.page.number = pageNumber;
              template = this.$reader_page(
                this.config.page,
                '<div><span class="Pcurrent">1</span><span class="Pcount">共0条数据</span></div>'
              );
              break;
          }
          if (template) {
            var tools_group = $(_that.config.el + " .tootls_" + positon[1]);
            if (tools_group.length) {
              var tools_item = tools_group.find(".pull-" + positon[0]);
              tools_item.append(template);
            } else {
              var tools_group_elment =
                '<div class="tootls_group tootls_' +
                positon[1] +
                '"><div class="pull-left">' +
                (positon[0] === "left" ? template : "") +
                '</div><div class="pull-right">' +
                (positon[0] === "right" ? template : "") +
                "</div></div>";
              if (positon[1] === "top") {
                $(_that.config.el).append(tools_group_elment);
                if ($(_that.config.el + " .divtable").length === 0)
                  $(_that.config.el).append(
                    '<div class="divtable mtb10" style="max-height:' +
                      _that.config.height +
                      'px"></div>'
                  );
              } else {
                if ($(_that.config.el + " .divtable").length === 0)
                  $(_that.config.el).append(
                    '<div class="divtable mtb10" style="max-height:' +
                      _that.config.height +
                      'px"></div>'
                  );
                $(_that.config.el).append(tools_group_elment);
              }
            }
          }
        }
        if (!this.init) this.$event_bind(event_list);
      },

      $clear_table_checkbox: function () {
        $(this.config.el)
          .find(".bt_table .cust—checkbox")
          .removeClass("selected active");
      },
      /**
       * @description 获取数据批量列表
       * @param {string} 需要获取的字段
       * @return {array} 当前需要批量列表
       */
      $get_data_batch_list: function (fid, data) {
        var arry = [];
        $.each(data || this.data, function (index, item) {
          arry.push(item[fid]);
        });
        return arry;
      },

      /**
       * @description 渲染分页
       * @param {object} config 配置文件
       * @param {object} page 分页
       * @return string
       */
      $reader_page: function (config, page) {
        var template = "",
          eventList = {},
          _that = this,
          $page = null;
        // console.log(config, page)
        if (config.number && !page) {
          template =
            (config.page !== 1
              ? '<a class="Pnum page_link_' +
                this.random +
                '"  data-page="1">首页</a>'
              : "") +
            (config.page !== 1
              ? '<a class="Pnum page_link_' +
                this.random +
                '" data-page="' +
                (config.page - 1) +
                '">上一页</a>'
              : "") +
            (_that.data.length === config.number
              ? '<a class="Pnum page_link_' +
                this.random +
                '" data-page="' +
                (config.page + 1) +
                '">下一页</a>'
              : "") +
            '<span class="Pcount">第 ' +
            config.page +
            " 页</span>";
          eventList["page_link_" + this.random] = { type: "cut_page_number" };
        } else {
          if (typeof page === "number") page = this.$custom_page(page);
          $page = $(page);
          $page.find("a").addClass("page_link_" + this.random);
          template += $page.html();
          if (config.numberStatus) {
            var className = "page_select_" + this.random,
              number = _that.$get_page_number();
            template += '<select class="page_select_number ' + className + '">';
            $.each(config.numberList, function (index, item) {
              template +=
                '<option value="' +
                item +
                '" ' +
                ((number || config.number) == item ? "selected" : "") +
                ">" +
                item +
                "条/页</option>";
            });
            template += "</select>";
            eventList[className] = { eventType: "change", type: "page_select" };
          }
          if (config.jump) {
            var inputName = "page_jump_input_" + this.random;
            var btnName = "page_jump_btn_" + this.random;
            template +=
              '<div class="page_jump_group"><span class="page_jump_title">跳转到</span><input type="number" class="page_jump_input ' +
              inputName +
              '" value="' +
              config.page +
              '" /><span class="page_jump_title">页</span><button type="button" class="page_jump_btn ' +
              btnName +
              '">确认</button></div>';
            eventList[inputName] = {
              eventType: "keyup",
              type: "page_jump_input",
            };
            eventList[btnName] = {
              type: "page_jump_btn",
            };
          }
          eventList["page_link_" + this.random] = {
            type: "cut_page_number",
          };
          _that.config.page.total =
            $page.length === 0
              ? 0
              : typeof page == "number"
              ? page
              : parseInt(
                  $page
                    .find(".Pcount")
                    .html()
                    .match(/([0-9]*)/g)[1]
                );
        }

        _that.$event_bind(eventList);
        return '<div class="page">' + template + "</div>";
      },
      /**
       * @description 渲染样式
       * @param {object|string} data 样式配置
       * @return {string} 样式
       */
      $reader_style: function (data) {
        var style = "";
        if (typeof data === "string") return data;
        if (typeof data === "undefined") return "";
        $.each(data, function (key, item) {
          style += key + ":" + item + ";";
        });
        return style;
      },
      /**
       * @description 自定义分页
       * @param {}
       */
      $custom_page: function (total) {
        var html = '<div class="page">',
          config = this.config.page,
          page = Math.ceil(total / config.number),
          tmpPageIndex = 0;
        if (config.page > 1 && page > 1) {
          html +=
            '<a class="Pstart" href="p=1">首页</a><a class="Pstart" href="p=' +
            (config.page - 1) +
            '">上一页</a>';
        }
        if (page <= 10) {
          for (var i = 1; i <= page; i++) {
            i == config.page
              ? (html += '<span class="Pcurrent">' + i + "</span>")
              : (html += '<a class="Pnum" href="p=' + i + '">' + i + "</a>");
          }
        } else if (config.page < 10) {
          for (var i = 1; i <= 10; i++)
            i == config.page
              ? (html += '<span class="Pcurrent">' + i + "</span>")
              : (html += '<a class="Pnum" href="p=' + i + '">' + i + "</a>");
          html += "<span>...</span>";
        } else if (page - config.page < 7) {
          page - 7 > 1 &&
            ((html += '<a class="Pnum" href="p=1">1</a>'),
            (html += "<span>...</span>"));
          for (var i = page - 7; i <= page; i++)
            i == config.page
              ? (html += '<span class="Pcurrent">' + i + "</span>")
              : (html +=
                  1 == i
                    ? "<span>...</span>"
                    : '<a class="Pnum" href="p=' + i + '">' + i + "</a>");
        } else {
          0 == tmpPageIndex && (tmpPageIndex = config.page),
            (tmpPageIndex <= config.page - 5 ||
              tmpPageIndex >= config.page + 5) &&
              (tmpPageIndex = config.page),
            (html += '<a class="Pnum" href="p=1">1</a>'),
            (html += "<span>...</span>");
          for (var i = tmpPageIndex - 3; i <= tmpPageIndex + 3; i++)
            i == config.page
              ? (html += '<span class="Pcurrent">' + i + "</span>")
              : (html += '<a class="Pnum" href="p=' + i + '">' + i + "</a>");
          (html += "<span>...</span>"),
            (html += '<a class="Pnum" href="p=' + page + '">' + page + "</a>");
        }
        return (
          page > 1 &&
            config.page < page &&
            (html +=
              '<a class="Pstart" href="p=' +
              (config.page + 1) +
              '">下一页</a><a class="Pstart" href="p=' +
              page +
              '">尾页</a>'),
          (html += '<span class="Pcount">共' + total + "条</span></div>")
        );
      },

      /**
       * @deprecated 动态处理合并行内，css样式
       * @param {object} rows 当前行数据
       * @return {stinrg} className class类名
       * @return void
       */
      $dynamic_merge_style: function (column, index) {
        var str = "";
        $.each(column, function (key, item) {
          switch (key) {
            case "align":
              str += "text-align:" + item + ";";
              break;
            case "width":
              str +=
                "width:" + (typeof item == "string" ? item : item + "px") + ";";
              break;
            case "style":
              str += item;
              break;
            case "minWidth":
              str +=
                "min-width:" +
                (typeof item == "string" ? item : item + "px") +
                ";";
              break;
            case "maxWidth":
              str +=
                "max-width:" +
                (typeof item == "string" ? item : item + "px") +
                ";";
              break;
          }
        });
        return {
          index: index,
          css: str,
        };
      },

      /**
       * @description 事件绑定
       * @param {array} eventList 事件列表
       * @return void
       */
      $event_bind: function (eventList) {
        var _that = this;
        $.each(eventList, function (key, item) {
          if (
            _that.event_list[key] &&
            _that.event_list[key].eventType === item.eventType
          )
            return true;
          _that.event_list[key] = item;
          $(_that.config.el).on(
            item.eventType || "click",
            "." + key,
            function (ev) {
              var index = $(this).parents("tr").index(),
                data1 = $(this).data(),
                arry = [],
                column_data =
                  _that.config.column[$(this).parents("td").index()];
              switch (item.type) {
                case "rows":
                  _that.event_rows_model = {
                    el: $(this),
                    model: column_data,
                    rows: _that.data[index],
                    index: index,
                  };
                  arry = [
                    _that.event_rows_model.rows,
                    _that.event_rows_model.index,
                    ev,
                    key,
                    _that,
                  ];
                  break;
                case "sort":
                  var model = _that.config.column[data1.index];
                  if ($(this).hasClass("sort-active"))
                    $(".sort_" + _that.random + " .sort-active").data({
                      sort: "desc",
                    });
                  $(".sort_" + _that.random)
                    .removeClass("sort-active")
                    .find(".glyphicon")
                    .removeClass("glyphicon-triangle-top")
                    .addClass("glyphicon-triangle-bottom");
                  $(this).addClass("sort-active");
                  if (data1.sort == "asc") {
                    $(this).data({
                      sort: "desc",
                    });
                    $(this)
                      .find(".glyphicon")
                      .removeClass("glyphicon-triangle-top")
                      .addClass("glyphicon-triangle-bottom");
                  } else {
                    $(this).data({
                      sort: "asc",
                    });
                    $(this)
                      .find(".glyphicon")
                      .removeClass("glyphicon-triangle-bottom")
                      .addClass("glyphicon-triangle-top");
                  }
                  _that.config.sort = _that.config.sortParam({
                    name: model.fid,
                    sort: data1.sort,
                  });
                  _that.$refresh_table_list(true);
                  break;
                case "checkbox":
                  var all = $(_that.config.el + ' [data-checkbox="all"]'),
                    checkbox_list = $(
                      _that.config.el + " tbody .checkbox_" + _that.random
                    );
                  if (data1.checkbox == undefined) {
                    if (!$(this).hasClass("active")) {
                      $(this).addClass("active");
                      _that.checkbox_list.push(index);
                      if (_that.data.length === _that.checkbox_list.length) {
                        all.addClass("active").removeClass("selected");
                      } else if (_that.checkbox_list.length > 0) {
                        all.addClass("selected");
                      }
                    } else {
                      $(this).removeClass("active");
                      _that.checkbox_list.splice(
                        _that.checkbox_list.indexOf(index),
                        1
                      );
                      if (_that.checkbox_list.length > 0) {
                        all.addClass("selected").removeClass("active");
                      } else {
                        all.removeClass("selected active");
                      }
                    }
                  } else {
                    if (_that.checkbox_list.length === _that.data.length) {
                      _that.checkbox_list = [];
                      checkbox_list
                        .removeClass("active selected")
                        .next()
                        .prop("checked", "checked");
                      all.removeClass("active");
                    } else {
                      checkbox_list.each(function (index, item) {
                        if (!$(this).hasClass("active")) {
                          $(this)
                            .addClass("active")
                            .next()
                            .prop("checked", "checked");
                          _that.checkbox_list.push(index);
                        }
                      });
                      all.removeClass("selected").addClass("active");
                    }
                  }
                  _that.$set_batch_view();
                  break;
                case "button":
                  arry.push(ev, _that);
                  break;
                case "search_focus":
                  var search_tips = $(_that.config.el + " .bt_search_tips");
                  if ($(_that.config.el + " .bt_search_tips").length > 0) {
                    search_tips.remove();
                  }
                  break;
                case "search_input":
                  if (ev.keyCode == 13) {
                    $(_that.config.el + " .search_btn_" + _that.random).click();
                    return false;
                  }
                  break;
                case "search_btn":
                  var _search = $(_that.config.el + " .search_input"),
                    val = $(_that.config.el + " .search_input").val(),
                    _filterBox = $("<div></div>").text(val),
                    _filterText = _filterBox.html();

                  val = _filterText; //过滤xss
                  val = val.replace(/(^\s*)|(\s*$)/g, "");
                  _search.text(val);
                  _that.config.search.value = val;
                  if (_that.config.page) _that.config.page.page = 1;
                  _search.append(
                    '<div class="bt_search_tips"><span>' +
                      val +
                      '</span><i class="bt_search_close"></i></div>'
                  );
                  _that.$refresh_table_list(true);
                  break;
                case "page_select":
                  var limit = parseInt($(this).val());
                  _that.$set_page_number(limit);
                  _that.config.page.number = limit;
                  _that.config.page.page = 1;
                  _that.$refresh_table_list(true);
                  return false;
                  break;
                case "page_jump_input":
                  if (ev.keyCode === 13) {
                    $(
                      _that.config.el + " .page_jump_btn_" + _that.random
                    ).click();
                    $(this).focus();
                  }
                  return false;
                  break;
                case "page_jump_btn":
                  var jump_page = parseInt(
                      $(
                        _that.config.el + " .page_jump_input_" + _that.random
                      ).val()
                    ),
                    max_number = Math.ceil(
                      _that.config.page.total / _that.config.page.number
                    );
                  if (isNaN(jump_page) || Number(jump_page) < 1) jump_page = 1;
                  if (jump_page > max_number)
                    jump_page = _that.config.page.page;
                  _that.config.page.page = jump_page;
                  _that.$refresh_table_list(true);
                  break;
                case "cut_page_number":
                  var page =
                    $(this).data("page") ||
                    parseInt(
                      $(this)
                        .attr("href")
                        .match(/([0-9]*)$/)[0]
                    );
                  _that.config.page.page = page;
                  _that.$refresh_table_list(true);
                  return false;
                  break;
                case "eye_open_password":
                  if ($(this).hasClass("glyphicon-eye-open")) {
                    $(this)
                      .addClass("glyphicon-eye-close")
                      .removeClass("glyphicon-eye-open");
                    $(this).prev().text(_that.data[index][column_data.fid]);
                  } else {
                    $(this)
                      .addClass("glyphicon-eye-open")
                      .removeClass("glyphicon-eye-close");
                    $(this).prev().html("<i>**********</i>");
                  }
                  return false;
                  break;
                case "copy_password":
                  bt.pub.copy_pass(_that.data[index][column_data.fid]);
                  return false;
                  break;
              }
              if (item.event) item.event.apply(this, arry);
            }
          );
        });
      },

      /**
       * @description 样式绑定
       * @param {array} style_list 样式列表
       * @return void
       */
      $style_bind: function (style_list, status) {
        var str = "",
          _that = this;
        $.each(style_list, function (index, item) {
          if (item.css != "") {
            if (!item.className) {
              var item_index = style_list[0].hasOwnProperty("className")
                ? index
                : item.index + 1;
              str +=
                _that.config.el +
                " thead th:nth-child(" +
                item_index +
                ")," +
                _that.config.el +
                " tbody tr td:nth-child" +
                (item.span ? " span" : "") +
                "(" +
                item_index +
                "){" +
                item.css +
                "}";
            } else {
              str += item.className + "{" + item.css + "}";
            }
          }
        });
        if ($("#bt_table_" + _that.random).length == 0)
          $(_that.config.el).append(
            '<style type="text/css" id="bt_table_' +
              _that.random +
              '">' +
              str +
              "</style>"
          );
      },

      /**
       * @deprecated 获取WIN高度或宽度
       * @return 返回当期的宽度和高度
       */
      $get_win_area: function () {
        return [window.innerWidth, window.innerHeight];
      },

      /**
       * @description 获取分页条数
       * @return 返回分页条数
       */
      $get_page_number: function () {
        var name = this.config.pageName;
        if (name) {
          return bt.get_cookie(name + "_page_number");
        }
      },

      /**
       * @description 设置分页条数
       * @param {object} limit 分页条数
       * @return void
       */
      $set_page_number: function (limit) {
        var name = this.config.pageName;
        if (name) bt.set_cookie(name + "_page_number", limit);
      },

      /**
       * @description 请求数据，
       * @param {object} param 参数和请求路径
       * @return void
       */
      $http: function (load, success) {
        var page_number = this.$get_page_number(),
          that = this,
          param = {},
          config = this.config,
          _page = config.page,
          _search = config.search,
          _sort = config.sort || {};
        if (_page) {
          if (page_number && !_page.number) _page.number = page_number;
          if (_page.defaultNumber) _page.number = _page.defaultNumber;

          if (_page.numberParam) param[_page.numberParam] = _page.number;
          param[_page.pageParam] = _page.page;
        }

        if (_search) param[_search.searchParam] = _search.value;
        var params = $.extend(config.param, param, _sort);
        if (this.config.beforeRequest) {
          if (this.config.beforeRequest === "model") {
            config.param = (function () {
              if (
                params.hasOwnProperty("data") &&
                typeof params.data === "string"
              ) {
                var oldParams = JSON.parse(params["data"]);
                delete params["data"];
                return { data: JSON.stringify($.extend(oldParams, params)) };
              }
              return { data: JSON.stringify(params) };
            })();
          } else {
            config.param = this.config.beforeRequest(params);
          }
        } else {
          config.param = params;
        }
        bt_tools.send(
          {
            url: config.url,
            data: config.param,
          },
          function (res) {
            if (typeof config.dataFilter != "undefined") {
              var data = config.dataFilter(res, that);
              if (typeof data.tootls != "undefined")
                data.tootls = parseInt(data.tootls);
              if (success) success(data);
            } else {
              if (void 0 === res.data) {
                success &&
                  success({
                    data: res,
                  });
              } else
                success &&
                  success({
                    data: res.data,
                    page: res.page,
                  });
            }
          },
          {
            load: load ? "获取列表数据" : false,
            verify:
              typeof config.dataVerify === "undefined"
                ? true
                : !!config.dataVerify,
          }
        );
      },
    };
    var example = new ReaderTable(config);
    $(config.el).data("table", example);
    return example;
  },

  /**
   * @description 验证表单
   * @param {object} el 节点
   * @param {object} config 验证配置
   * @param {function} callback 验证成功回调
   */
  verifyForm: function (el, config, callback) {
    var verify = false,
      formValue = this.getFormValue(el, []);
    for (var i = 0; i < config.length; i++) {
      var item = config[i];
      verify = item.validator.apply(this, [formValue[item.name], formValue]);
      if (typeof verify === "string") {
        this.error(verify);
        return false;
      }
    }
    callback && callback(typeof verify !== "string", formValue);
  },
  /**
   * @description 获取表单值
   * @param {String} el 表单元素
   * @param {Array} filter 过滤列表
   * @returns {Object} 表单值
   */
  getFormValue: function (el, filter) {
    var form = $(el).serializeObject();
    filter = filter && [];
    for (var key in form) {
      if (filter.indexOf(key) > -1) delete form[key];
    }
    return form;
  },

  /**
   * @description 设置layer定位
   * @param {object} el 节点
   */
  setLayerArea: function (el) {
    var $el = $(el),
      width = $el.width(),
      height = $el.height(),
      winWidth = $(window).width(),
      winHeight = $(window).height();
    $el.css({ left: (winWidth - width) / 2, top: (winHeight - height) / 2 });
  },

  /**
   * @description 渲染表单行内容
   * @param {object} config 配置参数
   */
  line: function (config) {
    var $line = $(
      '<div class="line ' +
        (config.lineClass ? config.lineClass : "") +
        '" style="' +
        (config.labelStyle || "") +
        '"><span class="tname" style="' +
        (config.labelWidth ? "width:" + config.labelWidth : "") +
        '">' +
        ((typeof config.must !== "undefined" && config.must != ""
          ? '<span class="color-red mr5">' + config.must + "</span>"
          : "") + config.label || "") +
        '</span><div class="info-r" style="' +
        (config.labelWidth ? "margin-left:" + config.labelWidth : "") +
        '"></div></div>'
    );
    var $form = this.renderLineForm(config);
    $form.data({ line: $line });
    $line.find(".info-r").append($form);
    return {
      $line: $line,
      $form: $form,
    };
  },

  /**
   * @description 帮助提示
   * @param {object} config 配置参数
   */
  help: function (config) {
    var $help = "";
    for (var i = 0; i < config.list.length; i++) {
      var item = config.list[i];
      $help += "<li>" + item + "</li>";
    }
    return $(
      '<ul class="help-info-text c7" style="' +
        (config.style || "") +
        '">' +
        $help +
        "</ul>"
    );
  },

  /**
   * @description 渲染表单行内容
   * @param {object} config 配置参数
   * @returns {jQuery|HTMLElement|*}
   */
  renderLineForm: function (config) {
    config.type = config.type || "text";
    var lineFilter = [
      "label",
      "labelWidth",
      "group",
      "on",
      "width",
      "options",
      "type",
    ]; // 排除渲染这些属性
    var $form = null;
    var props = (function () {
      var attrs = {};
      for (var key in config) {
        if (lineFilter.indexOf(key) === -1) {
          attrs[key] = config[key];
        }
      }
      return attrs;
    })();
    var width = config.width ? 'style="width:' + config.width + '"' : "";
    switch (config.type) {
      case "textarea":
        $form = '<textarea class="bt-input-text mr5" ' + width + "></textarea>";
        break;
      case "select":
        var options = config.options,
          optionsHtml = "";
        for (var i = 0; i < options.length; i++) {
          var item = options[i],
            newItem = item;
          if (typeof item === "string") newItem = { label: item, value: item };
          optionsHtml +=
            '<option value="' +
            newItem.value +
            '">' +
            newItem.label +
            "</option>";
        }
        $form =
          '<select class="bt-input-text mr5" ' +
          width +
          ">" +
          optionsHtml +
          "</select>";
        break;
      case "text":
        $form = '<input type="text" class="bt-input-text mr5" />';
        break;
    }
    $form = $($form);
    $form.width(config.width || "100%").attr(props);
    if (!config.on) config.on = {};
    for (var onKey in config.on) {
      (function (onKey) {
        $form.on(onKey, function (ev) {
          config.on[onKey].apply(this, [ev, $(this).val()]);
        });
      })(onKey);
    }
    return $form;
  },

  /**
   * @description 渲染表单行组
   * @param {object} el 配置参数
   * @param {object} config 配置参数
   * @param {object|undefined} formData 表单数据
   */
  fromGroup: function (el, config, formData) {
    var $el = $(el),
      lineList = {};
    for (var i = 0; i < config.length; i++) {
      var item = config[i];
      if (item.type === "tips") {
        $el.append(this.help(item));
      } else {
        var line = this.line(item);
        if (typeof formData != "undefined")
          line.$form.val(formData[item.name] || "");
        lineList[line.$form.attr("name")] = line;
        $el.append(line.$line);
      }
    }
    return lineList;
  },

  /**
   * @description 渲染Form表单
   * @param {*} config
   * @return 当前实例对象
   */
  form: function (config) {
    var _that = this;
    function ReaderForm(config) {
      this.config = config;
      this.el = config.el;
      this.submit = config.submit;
      this.data = config.data || {};
      this.$load();
    }
    ReaderForm.prototype = {
      element: null,
      style_list: [], // 样式列表
      event_list: {}, // 事件列表,已绑定事件
      event_type: [
        "click",
        "event",
        "focus",
        "keyup",
        "blur",
        "change",
        "input",
      ],
      hide_list: [],
      form_element: {},
      form_config: {},
      random: bt.get_random(5),
      $load: function () {
        var that = this;
        if (this.el) {
          $(this.el).html(this.$reader_content());
          // $(this.el).find('input[type="text"],textarea').each(function () {
          //   var name = $(this).attr('name');
          //   $(this).val(that.data[name]);
          // });
          if ($("#editCrontabForm .bt_multiple_select_updown").length > 0) {
            var height = $("#editCrontabForm .bt_multiple_select_updown")
              .parent()
              .height();
            $("#editCrontabForm .line:eq(3) .tname").css({
              height: height + "px",
              "line-height": height + "px",
            });
          }
          this.$event_bind();
        }
      },

      /**
       * @description 渲染Form内容
       * @param {Function} callback 回调函数
       */
      $reader_content: function (callback) {
        var that = this,
          html = "",
          _content = "";
        $.each(that.config.form, function (index, item) {
          if (item.separate) {
            html +=
              '<div class="bt_form_separate"><span class="btn btn-sm btn-default">' +
              item.separate +
              "</span></div>";
          } else {
            html += that.$reader_content_row(index, item);
          }
        });
        that.element = $(
          '<form class="bt-form" data-form="' +
            that.random +
            '" onsubmit="return false">' +
            html +
            "</form>"
        );
        _content = $(
          '<div class="' + _that.$verify(that.config["class"]) + '"></div>'
        );
        _content.append(that.element);
        if (callback) callback();
        return _content[0].outerHTML;
      },

      /**
       * @description 渲染行内容
       * @param {object} data Form数据
       * @param {number} index 下标
       * @return {string} HTML结构
       */
      $reader_content_row: function (index, data) {
        try {
          var that = this,
            help = data.help || false,
            labelWidth = data.formLabelWidth || this.config.formLabelWidth;
          if (data.display === false)
            return '<div class="line" style="padding:0"></div>';
          return (
            '<div class="line' +
            _that.$verify(data["class"]) +
            _that.$verify(data.hide, "hide", true) +
            '"' +
            _that.$verify(data.id, "id") +
            ">" +
            (typeof data.label !== "undefined"
              ? '<span class="tname" ' +
                (labelWidth ? 'style="width:' + labelWidth + '"' : "") +
                ">" +
                (typeof data.must !== "undefined" && data.must != ""
                  ? '<span class="color-red mr5">' + data.must + "</span>"
                  : "") +
                data.label +
                "</span>"
              : "") +
            '<div class="' +
            (data.label ? "info-r" : "") +
            _that.$verify(data.line_class) +
            '"' +
            _that.$verify(
              that.$reader_style(
                $.extend(
                  data.style,
                  labelWidth ? { "margin-left": labelWidth } : {}
                )
              ),
              "style"
            ) +
            ">" +
            that.$reader_form_element(data.group, index) +
            (help
              ? '<div class="c9 mt5 ' +
                _that.$verify(help["class"], "class") +
                '" ' +
                _that.$verify(that.$reader_style(help.style), "style") +
                ">" +
                help.list.join("</br>") +
                "</div>"
              : "") +
            "</div>" +
            "</div>"
          );
        } catch (error) {
          console.log(error);
        }
      },

      /**
       * @description 渲染form类型
       * @param {object} data 表单数据
       * @param {number} index 下标
       * @return {string} HTML结构
       */
      $reader_form_element: function (data, index) {
        var that = this,
          html = "";
        if (!Array.isArray(data)) data = [data];
        $.each(data, function (key, item) {
          item.find_index = index;
          html += that.$reader_form_find(item);
          that.form_config[item.name] = item;
        });
        return html;
      },
      /**
       * @descripttion 渲染单个表单元素
       * @param {Object} item 配置
       * @return: viod
       */
      $reader_form_find: function (item) {
        var that = this,
          html = "",
          style =
            that.$reader_style(item.style) +
            _that.$verify(item.width, "width", "style"),
          attribute = that.$verify_group(item, [
            "name",
            "placeholder",
            "disabled",
            "readonly",
            "autofocus",
            "autocomplete",
            "min",
            "max",
          ]),
          event_group = that.$create_event_config(item),
          eventName = "",
          index = item.find_index;
        if (item.display === false) return html;
        html += item.label
          ? '<span class="mr5 inlineBlock">' + item.label + "</span>"
          : "";
        if (typeof item["name"] !== "undefined") {
          that.$check_event_bind(item.name, event_group);
        }
        html +=
          '<div class="' +
          (item.dispaly || "inlineBlock") +
          " " +
          _that.$verify(item.hide, "hide", true) +
          " " +
          (item["class"] || "") +
          '">';
        var _value =
          typeof that.data[item.name] !== "undefined" &&
          that.data[item.name] !== ""
            ? that.data[item.name]
            : item.value || "";
        // if(typeof that.data == 'undefined') that.data = {}
        // if(typeof item.value != 'undefined' && typeof that.data[item.name] == "undefined") that.data[item.name] = item.value
        switch (item.type) {
          case "text": // 文本选择
          case "checkbox": // 复选框
          case "password": // 密码
          case "radio": // 单选框
          case "number": // 数字
            var _event = "event_" + item.name + "_" + that.random;
            switch (item.type) {
              case "checkbox": // 复选框
                html +=
                  '<label class="cursor-pointer form-checkbox-label" ' +
                  _that.$verify(that.$reader_style(item.style), "style") +
                  '><i class="form-checkbox cust—checkbox cursor-pointer mr5 ' +
                  _event +
                  "_label " +
                  (_value ? "active" : "") +
                  '"></i><input type="checkbox" class="form—checkbox-input hide mr10 ' +
                  _event +
                  '" name="' +
                  item.name +
                  '" ' +
                  (_value ? "checked" : "") +
                  '/><span class="vertical_middle">' +
                  item.title +
                  "</span></label>";
                if (typeof item.disabled != "undefined" && item.disabled) {
                  //禁止复选框    同时可设置class:'check_disabled',使鼠标手为禁止状态
                } else {
                  that.$check_event_bind(_event + "_label", {
                    click: { type: "checkbox_icon", config: item },
                  });
                  that.$check_event_bind(_event, {
                    input: {
                      type: "checkbox",
                      config: item,
                      event: item.event,
                    },
                  });
                }
                break;
              case "radio":
                $.each(item.list, function (keys, rItem) {
                  var radioRandom = _event + "_radio_" + keys;
                  html +=
                    '<span class="form-radio"><input type="radio" name="' +
                    item.name +
                    '" ' +
                    (_value == rItem.value ? "checked" : "") +
                    ' id="' +
                    radioRandom +
                    '" class="' +
                    radioRandom +
                    '" value="' +
                    rItem.value +
                    '"><label for="' +
                    radioRandom +
                    '" class="mb0">' +
                    rItem.title +
                    "</span>";
                  that.$check_event_bind(radioRandom, {
                    input: { type: "radio", config: item, event: item.event },
                  });
                });
                break;
              default:
                html +=
                  '<input type="' +
                  item.type +
                  '"' +
                  attribute +
                  " " +
                  (item.icon ? 'id="' + _event + '"' : "") +
                  ' class="bt-input-' +
                  (item.type !== "select_path" &&
                  item.type !== "number" &&
                  item.type !== "password"
                    ? item.type
                    : "text") +
                  " mr10 " +
                  (item.label ? "vertical_middle" : "") +
                  _that.$verify(item["class"]) +
                  '"' +
                  _that.$verify(style, "style") +
                  ' value="' +
                  _value +
                  '"/>';
                break;
            }
            if (item.btn && !item.disabled) {
              html +=
                '<span class="btn ' +
                item.btn.type +
                " " +
                item.name +
                '_btn cursor" ' +
                _that.$verify(that.$reader_style(item.btn.style), "style") +
                ">" +
                item.btn.title +
                "</span>";
              if (typeof item.btn.event !== "undefined") {
                that.$check_event_bind(item.name + "_btn", {
                  click: {
                    config: item,
                    event: item.btn.event,
                  },
                });
              }
            }
            if (item.icon) {
              html +=
                '<span class="glyphicon ' +
                item.icon.type +
                " " +
                item.name +
                "_icon cursor " +
                (item.disabled ? "hide" : "") +
                ' mr10" ' +
                _that.$verify(that.$reader_style(item.icon.style), "style") +
                "></span>";
              if (typeof item.icon.event !== "undefined") {
                that.$check_event_bind(item.name + "_icon", {
                  click: {
                    type: "select_path",
                    select: item.icon.select || "",
                    config: item,
                    defaultPath: item.icon.defaultPath || "",
                    children: "." + item.name + "_icon",
                    event: item.icon.event,
                    callback: item.icon.callback,
                  },
                });
              }
            }
            break;
          case "textarea":
            html +=
              '<textarea class="bt-input-text"' +
              _that.$verify(style, "style") +
              attribute +
              " >" +
              _value +
              "</textarea>";
            $.each(["blur", "focus", "input"], function (index, items) {
              if (item.tips) {
                var added = null,
                  event = {};
                switch (items) {
                  case "blur":
                    added = function (ev, item, element) {
                      if ($(this).val() === "") $(this).next().show();
                      layer.close(item.tips.loadT);
                      $(ev.target).data("layer", "");
                    };
                    break;
                  case "focus":
                    added = function (ev, item) {
                      $(this).next().hide();
                      item.tips.loadT = layer.tips(tips, $(this), {
                        tips: [1, "#20a53a"],
                        time: 0,
                        area: $(this).width(),
                      });
                    };
                    break;
                }
              }
              that.event_list[item.name][items]
                ? (that.event_list[item.name][items]["added"] = added)
                : (that.event_list[item.name][items] = {
                    type: item.type,
                    cust: false,
                    event: item[items],
                    added: added,
                  });
            });
            if (item.tips) {
              var tips = "";
              if (typeof item.tips.list === "undefined") {
                tips = item.tips.text;
              } else {
                tips = item.tips.list.join("</br>");
              }
              html +=
                '<div class="placeholder c9 ' +
                item.name +
                '_tips" ' +
                _that.$verify(that.$reader_style(item.tips.style), "style") +
                ">" +
                tips +
                "</div>";
              that.$check_event_bind(item.name + "_tips", {
                click: {
                  type: "textarea_tips",
                  config: item,
                },
              });
            }
            break;
          case "select":
            html += that.$reader_select(item, style, attribute, index);
            that.$check_event_bind("custom_select", {
              click: {
                type: "custom_select",
                children: ".bt_select_value",
              },
            });
            that.$check_event_bind("custom_select_item", {
              click: {
                type: "custom_select_item",
                children: "li.item",
              },
            });
            break;
          case "multipleSelect":
            // 使用规则  【配置中必须含有value字段（无需默认值设置空数组）、需要选中的下拉项以数组逗号隔开】
            html += that.$reader_multipleSelect(item, style, attribute, index);
            that.$check_event_bind("custom_select", {
              click: {
                type: "custom_select",
                children: ".bt_select_value",
              },
            });
            that.$check_event_bind("custom_select_item", {
              click: {
                type: "custom_select_item",
                children: "li.item",
              },
            });
            that.$check_event_bind("icon_trem_close", {
              click: {
                type: "icon_trem_close",
                children: ".icon-trem-close",
              },
            });
            break;
          case "secondaryMenu": //下拉二级菜单
            html += that.$reader_secondaryMenu(item, style, attribute, index);
            that.$check_event_bind("secondary_menu_parent", {
              "mouseover click": {
                type: "secondary_menu_parent",
                children: ".item-parent",
              },
            });
            that.$check_event_bind("secondary_menu_child", {
              click: {
                type: "secondary_menu_child",
                children: ".item-child",
              },
            });
            break;
          case "link":
            eventName = "event_link_" + that.random + "_" + item.name;
            html +=
              '<a href="' +
              (item.href || "javascript:;") +
              '" class="' +
              (item["subclass"] ? item["subclass"] : "btlink") +
              " " +
              eventName +
              '" ' +
              _that.$verify(that.$reader_style(item.style), "style") +
              ">" +
              item.title +
              "</a>";
            that.$check_event_bind(eventName, {
              click: {
                type: "link_event",
                event: item.event,
              },
            });
            break;
          case "button":
            html +=
              '<button class="btn ' +
              (item.hasOwnProperty("active")
                ? item.active
                  ? "btn-success"
                  : "btn-default"
                : "btn-success ") +
              " btn-" +
              (item.size || "sm ") +
              " " +
              eventName +
              " " +
              _that.$verify(item["class"]) +
              '"  ' +
              _that.$verify(that.$reader_style(item.style), "style") +
              " " +
              attribute +
              ">" +
              item.title +
              "</button>";
            break;
          case "help":
            var _html = "";
            $.each(item.list, function (index, items) {
              _html += "<li>" + items + "</li>";
            });
            html +=
              '<ul class="help-info-text c7' +
              _that.$verify(item["class"]) +
              '"' +
              _that.$verify(that.$reader_style(item.style), "style") +
              " " +
              attribute +
              ">" +
              _html +
              "</ul>";
            break;
          case "other":
            html += item.boxcontent;
        }
        html += item.unit
          ? '<span class="' +
            (item.type === "text-tips" ? "text-tips" : "unit") +
            '">' +
            item.unit +
            "</span>"
          : "";
        html += item.suffix
          ? '<span class="text-tips ml10" ' +
            (item.type === "select") +
            ">" +
            item.suffix +
            "</span>"
          : "";
        html += "</div>";
        return html;
      },

      /**
       * @descripttion 检测检测名称
       * @param {string} eventName 配置
       * @param {object} config 事件配置
       */
      $check_event_bind: function (eventName, config) {
        if (!this.event_list[eventName]) {
          if (!this.event_list.hasOwnProperty(eventName)) {
            this.event_list[eventName] = config;
          }
        }
      },
      /**
       * @description 创建事件配置
       * @param {object} item 行内配置
       * @return {object} 配置信息
       */
      $create_event_config: function (item) {
        var config = {};
        if (typeof item["name"] === "undefined") return {};
        $.each(this.event_type, function (key, items) {
          if (item[items]) {
            config[items === "event" ? "click" : items] = {
              type: item.type,
              event: item[items],
              cust: ["select", "checkbox", "radio"].indexOf(item.type) > -1,
              config: item,
            };
          }
        });
        return config;
      },
      /**
       * @description 渲染样式
       * @param {object|string} data 样式配置
       * @return {string} 样式
       */
      $reader_style: function (data) {
        var style = "";
        if (typeof data === "string") return data;
        if (typeof data === "undefined") return "";
        $.each(data, function (key, item) {
          style += key + ":" + item + ";";
        });
        return style;
      },
      /**
       * @descripttion 局部刷新form表单元素
       * @param {String} name 需要刷新的元素
       * @param {String} name 元素新数据
       * @return: viod
       */
      $local_refresh: function (name, config) {
        var formFind = this.element.find("[data-name=" + name + "]");
        if (this.element.find("[data-name=" + name + "]").length === 0)
          formFind = this.element.find("[name=" + name + "]");
        formFind.parent().replaceWith(this.$reader_form_find(config));
        // if(config.type == 'text' || config.tyep == 'textarea'){
        //   if (this.element.find('[data-name=' + name + ']').length === 0) formFind = this.element.find('[name=' + name + ']')
        //   formFind.val(config.value)
        // }
      },
      /**
       * @description 渲染下拉，内容方法
       */
      $reader_select: function (item, style, attribute, index) {
        var that = this,
          list = "",
          option = "",
          active = {};
        if (typeof item.list === "function") {
          var event = item.list;
          event.call(this, this.config.form);
          item.list = [];
        }
        if (!Array.isArray(item.list)) {
          var config = item.list;
          bt_tools.send(
            {
              url: config.url,
              data: config.param || config.data || {},
            },
            function (res) {
              if (res.status !== false) {
                var list = item.list.dataFilter
                  ? item.list.dataFilter(res, that)
                  : res;
                if (item.list.success)
                  item.list.success(res, that, that.config.form[index], list);
                item.list = list;
                if (!item.list.length) {
                  item.disabled = true;
                  layer.msg(item.placeholder || "数据获取为空", { icon: 2 });
                }
                that.$replace_render_content(index);
              } else {
                bt.msg(res);
              }
            }
          );
          return false;
        }
        if (typeof that.data[item.name] === "undefined") active = item.list[0];
        $.each(item.list, function (key, items) {
          if (
            items.value === item.value ||
            items.value === that.data[item.name]
          ) {
            active = items;
            return false;
          }
        });
        $.each(item.list, function (key, items) {
          list +=
            '<li class="item' +
            _that.$verify(items.value === active.value ? "active" : "") +
            " " +
            (items.disabled ? "disabled" : "") +
            '" title="' +
            items.title +
            '">' +
            items.title +
            "</li>";
          option +=
            '<option value="' +
            items.value +
            '"' +
            (items.disabled ? "disabled" : "") +
            " " +
            _that.$verify(items.value === active.value ? "selected" : "") +
            ">" +
            items.title +
            "</option>";
        });
        var title = !Array.isArray(item.list)
          ? "获取数据中"
          : active
          ? active.title
          : item.placeholder;
        return (
          '<div class="bt_select_updown mr10 ' +
          (item.disabled ? "bt-disabled" : "") +
          " " +
          +_that.$verify(item["class"]) +
          '" ' +
          _that.$verify(style, "style") +
          ' data-name="' +
          item.name +
          '">' +
          '<span class="bt_select_value"><span class="bt_select_content" title="' +
          (title || item.placeholder) +
          '">' +
          (title || item.placeholder) +
          '</span><div class="icon-down"><svg width="12.000000" height="12.000000" viewBox="0 0 12 5" fill="none" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\n' +
          "\t<desc>\n" +
          "\t\t\tCreated with Pixso.\n" +
          "\t</desc>\n" +
          "\t<defs/>\n" +
          '\t<path id="path" d="M0.123291 0.809418L4.71558 5.84385C4.8786 6.02302 5.16846 6.04432 5.33038 5.86389L9.87927 0.783104C10.0412 0.602676 10.04 0.311989 9.87701 0.132816C9.79626 0.0446892 9.68945 0 9.58374 0C9.47693 0 9.36938 0.0459404 9.28827 0.136574L5.02881 4.89284L0.708618 0.15662C0.627869 0.0684967 0.522217 0.0238075 0.415405 0.0238075C0.307434 0.0238075 0.20105 0.0697479 0.119873 0.160381C-0.041626 0.338303 -0.0393677 0.630241 0.123291 0.809418Z" fill-rule="nonzero" fill="#999999"/>\n' +
          "</svg>\n</div></span>" +
          '<ul class="bt_select_list">' +
          (list ||
            '<div style="height:80px;display:inline-flex;align-items:center;justify-content:center;color:#999;width:100%">无数据</div>') +
          "</ul>" +
          "<select" +
          attribute +
          ' class="hide" ' +
          (item.disabled ? "disabled" : "") +
          ' autocomplete="off">' +
          (option || "") +
          "</select>" +
          '<div class="bt_select_list_arrow"></div><div class="bt_select_list_arrow_fff"></div>' +
          "</div>"
        );
      },
      /**
       * @description 渲染多选下拉，内容方法
       */
      $reader_multipleSelect: function (item, style, attribute, index) {
        var that = this,
          list = "",
          option = "",
          active = {},
          mulpActive = [],
          str = "";
        if (typeof item.list === "function") {
          var event = item.list;
          event.call(this, this.config.form);
          item.list = [];
        }
        if ($.isArray(item.value)) {
          mulpActive = item.value;
        } else {
          if (!Array.isArray(item.list)) {
            var config = item.list;
            bt_tools.send(
              {
                url: config.url,
                data: config.param || config.data || {},
              },
              function (res) {
                if (res.status !== false) {
                  var list = item.list.dataFilter
                    ? item.list.dataFilter(res, that)
                    : res;
                  if (item.list.success)
                    item.list.success(res, that, that.config.form[index], list);
                  item.list = list;
                  if (!item.list.length) {
                    item.disabled = true;
                    layer.msg(item.placeholder || "数据获取为空", { icon: 2 });
                  }
                  that.$replace_render_content(index);
                } else {
                  bt.msg(res);
                }
              }
            );
            return false;
          }
          if (typeof that.data[item.name] === "undefined")
            active = item.list[0];
          $.each(item.list, function (key, items) {
            if (
              items.value === item.value ||
              items.value === that.data[item.name]
            ) {
              active = items;
              return false;
            }
          });
        }
        $.each(item.list, function (key, items) {
          if ($.isArray(item.value)) {
            for (var i = 0; i < mulpActive.length; i++) {
              if (mulpActive.indexOf(items.value) > -1) {
                active.value = items.value;
              }
            }
          }
          list +=
            '<li class="item item1' +
            _that.$verify(items.value === active.value ? "active" : "") +
            " " +
            (items.disabled ? "disabled" : "") +
            '" title="' +
            items.title +
            '">\
            <span>' +
            items.title +
            '</span>\
            <span class="icon-item-active"></span>\
          </li>';
          option +=
            '<option value="' +
            items.value +
            '"' +
            (items.disabled ? "disabled" : "") +
            " " +
            _that.$verify(items.value === active.value ? "selected" : "") +
            ">" +
            items.title +
            "</option>";
        });
        for (var i = 0; i < item.list.length; i++) {
          if (mulpActive.indexOf(item.list[i].value) > -1) {
            str +=
              '<span class="bt_select_content"><span>' +
              item.list[i].title +
              '</span><span class="icon-trem-close"></span></span>';
          }
        }
        var title = !Array.isArray(item.list)
          ? "获取数据中"
          : active
          ? active.title
          : item.placeholder;
        return (
          '<div class="bt_multiple_select_updown bt_select_updown mr10 ' +
          (item.disabled ? "bt-disabled" : "") +
          " " +
          +_that.$verify(item["class"]) +
          '" ' +
          _that.$verify(style, "style") +
          ' data-name="' +
          item.name +
          '">' +
          '<span class="bt_select_value">' +
          (item.value.length == 0
            ? '<span class="bt_select_content"><span>' +
              (title || item.placeholder) +
              '</span><span class="icon-trem-close"></span></span>'
            : str) +
          '<div class="icon-down"><svg width="12.000000" height="12.000000" viewBox="0 0 12 5" fill="none" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><desc>Created with Pixso.</desc><defs></defs><path id="path" d="M0.123291 0.809418L4.71558 5.84385C4.8786 6.02302 5.16846 6.04432 5.33038 5.86389L9.87927 0.783104C10.0412 0.602676 10.04 0.311989 9.87701 0.132816C9.79626 0.0446892 9.68945 0 9.58374 0C9.47693 0 9.36938 0.0459404 9.28827 0.136574L5.02881 4.89284L0.708618 0.15662C0.627869 0.0684967 0.522217 0.0238075 0.415405 0.0238075C0.307434 0.0238075 0.20105 0.0697479 0.119873 0.160381C-0.041626 0.338303 -0.0393677 0.630241 0.123291 0.809418Z" fill-rule="nonzero" fill="#999999"></path></svg></div>\
            </span>' +
          '<ul class="bt_select_list">' +
          (list || "") +
          "</ul>" +
          "<select" +
          attribute +
          ' class="hide" ' +
          (item.disabled ? "disabled" : "") +
          ' autocomplete="off" multiple>' +
          (option || "") +
          "</select>" +
          '<div class="bt_select_list_arrow"></div><div class="bt_select_list_arrow_fff"></div>' +
          "</div>"
        );
      },
      /**
       * @description 渲染二级下拉
       */
      $reader_secondaryMenu: function (item, style, attribute, index) {
        // 规则限制  【通过配置中的data.xx值设置为空，可清除上次选中的内容】
        // 1.不可通过请求数据来渲染
        // 2.至少有一个一级内容，一级下拉不可点击
        var that = this,
          list = "",
          active = {};
        $.each(item.list, function (key, items) {
          list +=
            '<li class="item-parent"><div class="item-menu-title" style="' +
            (function () {
              for (var i = 0; i < items.child.length; i++) {
                if (
                  items.child[i].value == item.value ||
                  items.child[i].value == that.data[item.name]
                ) {
                  active = items.child[i];
                }
                if (items.child[i].value === active.value) {
                  return "color:#20a53a;";
                }
              }
            })() +
            '">' +
            items.title +
            "</div>" +
            (function () {
              var _con = "";
              if (items.child.length > 0) {
                _con =
                  '\
                 <svg style="margin-right: 10px;fill:#999999;" width="5.989136" height="10.000000" viewBox="0 0 5.98914 10" fill="none" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\
                 \t<desc>\
                 \t\t\tCreated with Pixso.\
                 \t</desc>\
                 \t<defs/>\
                 \t<path id="path" d="M0.809448 9.87672L5.84387 5.28442C6.02307 5.12138 6.04431 4.83153 5.86389 4.66962L0.783081 0.120728C0.602661 -0.0411835 0.312012 -0.0400543 0.132812 0.122986C0.0446777 0.203751 0 0.310562 0 0.416229C0 0.523041 0.0458984 0.6306 0.136597 0.711746L4.89282 4.97118L0.156616 9.29137C0.0684814 9.37213 0.0238037 9.4778 0.0238037 9.58461C0.0238037 9.69255 0.0697021 9.79898 0.1604 9.88011C0.338257 10.0416 0.630249 10.0394 0.809448 9.87672Z" fill-rule="nonzero" />\
                 </svg><div class="item-menu-body-list">\
								<ul class="">' +
                  (function () {
                    var str = "";
                    $.each(items.child, function (key, child) {
                      str +=
                        '<li class="item-child' +
                        _that.$verify(
                          child.value === active.value ? "active" : ""
                        ) +
                        '" title="' +
                        child.title +
                        '" data-value="' +
                        child.value +
                        '"><div class="item-menu-title">' +
                        child.title +
                        "</div></li>";
                    });
                    return str;
                  })() +
                  "</ul></div>";
              } else {
                _con = '<span style="top: 0;color: #ccc;">[空]</span>';
              }
              return _con;
            })() +
            "</li>";
        });
        return (
          '<div class="bt_select_updown bt_seconday_menu" ' +
          _that.$verify(style, "style") +
          ' data-name="' +
          item.name +
          '">\
					<span class="bt_select_value"><span class="bt_select_content">' +
          (!$.isEmptyObject(active) ? active.title : item.placeholder) +
          '</span>\
					<div class="icon-down"><svg width="12.000000" height="12.000000" viewBox="0 0 12 5" fill="none" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><desc>Created with Pixso.</desc><defs></defs><path id="path" d="M0.123291 0.809418L4.71558 5.84385C4.8786 6.02302 5.16846 6.04432 5.33038 5.86389L9.87927 0.783104C10.0412 0.602676 10.04 0.311989 9.87701 0.132816C9.79626 0.0446892 9.68945 0 9.58374 0C9.47693 0 9.36938 0.0459404 9.28827 0.136574L5.02881 4.89284L0.708618 0.15662C0.627869 0.0684967 0.522217 0.0238075 0.415405 0.0238075C0.307434 0.0238075 0.20105 0.0697479 0.119873 0.160381C-0.041626 0.338303 -0.0393677 0.630241 0.123291 0.809418Z" fill-rule="nonzero" fill="#999999"></path></svg></div>\
					</span>\
					<ul class="bt_select_list">' +
          list +
          "</ul>\
					<input " +
          attribute +
          ' class="hide" value="' +
          (active.value || "") +
          '">\
          <div class="bt_select_list_arrow"></div><div class="bt_select_list_arrow_fff"></div>\
					</div>'
        );
      },
      /**
       * @description 替换渲染内容
       */
      $replace_render_content: function (index) {
        var that = this,
          config = this.config.form[index],
          html = that.$reader_content_row(index, config);
        $("[data-form=" + that.random + "]")
          .find(".line:eq(" + index + ")")
          .replaceWith(html);
        this.$event_bind();
      },

      /**
       * @description 重新渲染内容
       * @param {object} formConfig 配置
       */
      $again_render_form: function (formConfig) {
        var formElement = $("[data-form=" + this.random + "]"),
          that = this;
        formConfig = formConfig || this.config.form;
        formElement.empty();
        for (var i = 0; i < formConfig.length; i++) {
          var config = formConfig[i];
          // if (config.display === false) continue
          formElement.append(that.$reader_content_row(i, config));
        }
        this.config.form = formConfig;
        this.$event_bind();

        // 处理复选框重新渲染第一次点击无效
        formElement.find(".form-checkbox-label").click();
        formElement.find(".form-checkbox-label").click();
      },

      /**
       * @description 事件绑定功能
       * @param {Object} eventList 事件列表
       * @param {Function} callback 回调函数
       * @return void
       */
      $event_bind: function (eventList, callback) {
        var that = this,
          _event = {};
        that.element = $(
          typeof eventList === "object"
            ? that.element
            : "[data-form=" + that.random + "]"
        );
        _event = eventList;
        if (typeof eventList === "undefined") _event = that.event_list;
        $.each(_event, function (key, item) {
          if ($.isEmptyObject(item)) return true;
          $.each(item, function (keys, items) {
            if (!!item.type) return false;
            if (!items.hasOwnProperty("bind")) {
              items.bind = true;
            } else {
              return false;
            }
            var childNode = "";
            if (typeof items.cust === "boolean") {
              childNode =
                "[" + (items.cust ? "data-" : "") + "name=" + key + "]";
            } else {
              childNode = "." + key;
            }
            (function (items, key) {
              if (items.onEvent === false) {
                switch (items.type) {
                  case "input_checked":
                    $(childNode).on(
                      keys != "event" ? keys : "click",
                      function (ev) {
                        items.event.apply(this, [ev, that]);
                      }
                    );
                    break;
                }
                return true;
              } else {
                if (items.type === "select") return true;
                that.element.on(
                  keys !== "event" ? keys : "click",
                  items.children ? items.children : childNode,
                  function (ev) {
                    var form = that.$get_form_element(true),
                      config = that.form_config[key];
                    switch (items.type) {
                      case "textarea_tips":
                        $(this).hide().prev().focus();
                        break;
                      case "custom_select":
                        if ($(this).parent().hasClass("bt-disabled"))
                          return false;
                        var select_value = $(this).next();
                        select_value
                          .parent(".bt_select_updown")
                          .css("border", "1px solid rgb(220, 223, 230)");
                        that.element.find(".item-parent").removeClass("down");
                        that.element
                          .find(".bt_select_list,.item-menu-body-list")
                          .parent(".bt_select_updown")
                          .css("border", "1px solid rgb(220, 223, 230)");
                        if (!select_value.hasClass("show")) {
                          $(".bt_select_list")
                            .removeClass("show")
                            .css("display", "none");
                          $(".bt_select_list_arrow").fadeOut(1);
                          $(".bt_select_list_arrow_fff").fadeOut(1);
                          $(".icon_up").remove();
                          $(".icon-down").show();
                          select_value.slideDown("fast");
                          select_value.addClass("show");
                          select_value
                            .prev()
                            .append(
                              "<div class='icon_up'>" +
                                '<svg width="12.000000" height="12.000000" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\n' +
                                "<desc>" +
                                "Created with Pixso." +
                                "</desc>" +
                                "<defs/>" +
                                '<path id="path" d="M1.12328 8.19058L5.71558 3.15616C5.87862 2.97699 6.16847 2.95569 6.33038 3.13611L10.8793 8.21689C11.0412 8.39731 11.04 8.68802 10.877 8.86719C10.7962 8.95532 10.6894 9 10.5838 9C10.477 9 10.3694 8.95407 10.2883 8.86343L6.02883 4.10715L1.70864 8.84338C1.62788 8.93152 1.5222 8.9762 1.41539 8.9762C1.30746 8.9762 1.20103 8.93024 1.11988 8.83963C0.958351 8.66171 0.960617 8.36975 1.12328 8.19058Z" fill-rule="nonzero" fill="#999999"/>\n' +
                                "</svg></div>"
                            );
                          select_value.prev().find(".icon-down").hide();
                          select_value
                            .parent(".bt_select_updown")
                            .css("border", "1px solid #20A53A");

                          var height = $(this).height();
                          select_value.css("top", height + 12 + "px");
                          $(select_value.siblings()[2]).css(
                            "top",
                            height - 4 + "px"
                          );
                          $(select_value.siblings()[3]).css(
                            "top",
                            height - 3 + "px"
                          );
                          $(select_value.siblings()[2]).show();
                          $(select_value.siblings()[3]).show();
                        } else {
                          select_value
                            .parent(".bt_select_updown")
                            .css("border", "1px solid rgb(220, 223, 230)");
                          $(".icon_up").remove();
                          $(".icon-down").show();
                          select_value.slideUp("fast");
                          select_value.removeClass("show");
                          $(".bt_select_list_arrow").fadeOut(300);
                          $(".bt_select_list_arrow_fff").fadeOut(300);
                        }
                        $(document).click(function () {
                          that.element
                            .find(".bt_select_list,.item-menu-body-list")
                            .slideUp("fast");
                          that.element
                            .find(".bt_select_list,.item-menu-body-list")
                            .removeClass("show");
                          that.element.find(".item-parent").removeClass("down");
                          that.element
                            .find(".bt_select_list,.item-menu-body-list")
                            .parent(".bt_select_updown")
                            .css("border", "1px solid rgb(220, 223, 230)");
                          $(".bt_select_list_arrow").fadeOut(300);
                          $(".bt_select_list_arrow_fff").fadeOut(300);
                          $(".icon_up").remove();
                          $(".icon-down").show();
                          $(this).unbind("click");
                          return false;
                        });
                        return false;
                        break;
                      case "custom_select_item":
                        config =
                          that.form_config[
                            $(this)
                              .parents(".bt_select_updown")
                              .attr("data-name")
                          ];
                        var item_config = config.list[$(this).index()];
                        var item = $(this).parent().find(".item"),
                          arry = [],
                          _html = "",
                          mulpVal = [];
                        if ($(this).hasClass("disabled")) {
                          $(this).parent().removeClass("show");
                          if (item_config.tips)
                            layer.msg(item_config.tips, { icon: 2 });
                          return true;
                        }
                        if (
                          !$(this).hasClass("active") &&
                          !$(this).hasClass("disabled")
                        ) {
                          var value = item_config.value.toString();
                          $(this)
                            .parent()
                            .prev()
                            .find(".bt_select_content")
                            .text($(this).text());
                          $(this)
                            .parent()
                            .prev()
                            .find(".bt_select_content")
                            .prop("title", $(this).text());
                          if (config.type != "multipleSelect") {
                            $(this)
                              .addClass("active")
                              .siblings()
                              .removeClass("active");
                            $(this).parent().next().val(value);
                            $(this).parent().slideUp("fast");
                            $(this).parent().removeClass("show");
                            $(".bt_select_list_arrow").fadeOut(200);
                            $(".bt_select_list_arrow_fff").fadeOut(200);
                          } else {
                            $(this).addClass("active");
                          }
                        } else {
                          if (config.type == "multipleSelect") {
                            // if($(this).parent().find('.active').length <= 1) return layer.msg('最少选择一个！！！')
                            $(this).removeClass("active");
                          }
                        }
                        if (config.type == "multipleSelect") {
                          for (var i = 0; i < item.length; i++) {
                            if (item.eq(i).hasClass("active")) {
                              arry.push(
                                item.eq(i).text().trim().replace(/\s/g, "")
                              );
                            }
                          }
                          for (var i = 0; i < config.list.length; i++) {
                            if (
                              arry.indexOf(
                                config.list[i].title.trim().replace(/\s/g, "")
                              ) > -1
                            ) {
                              mulpVal.push(config.list[i].value);
                            }
                          }
                          if (arry.length == 0) {
                            _html +=
                              '<span class="bt_select_content_def">' +
                              config.placeholder +
                              "</span>";
                          } else {
                            $(this)
                              .parent()
                              .prev()
                              .find(".bt_select_content_def")
                              .remove();
                            for (var i = 0; i < arry.length; i++) {
                              _html +=
                                '<span class="bt_select_content"><span>' +
                                arry[i] +
                                '</span><span class="icon-trem-close"></span></span>';
                            }
                          }
                          $(this)
                            .parent()
                            .prev()
                            .find(".bt_select_content")
                            .remove();
                          $(this)
                            .parent()
                            .prev()
                            .find(".icon-down")
                            .before(_html);
                          $(this).parent().next().val(mulpVal);
                          var height = $(this)
                            .parent()
                            .parent()
                            .parent()
                            .height();
                          $(this)
                            .parent()
                            .parent()
                            .parent()
                            .parent()
                            .siblings()
                            .css({
                              height: height + "px",
                              "line-height": height + "px",
                            });
                          $(this)
                            .parent()
                            .css("top", height + 12 + "px");
                          $(".bt_select_list_arrow_fff").css(
                            "top",
                            height - 3 + "px"
                          );
                          $(".bt_select_list_arrow").css(
                            "top",
                            height - 4 + "px"
                          );
                        }
                        $(".icon-trem-close").click(function () {
                          var str = $(this)
                            .siblings()
                            .text()
                            .trim()
                            .replace(/\s/g, "");
                          for (var i = 0; i < item.length; i++) {
                            if (str == item.eq(i).prop("title")) {
                              item.eq(i).click();
                            }
                          }
                          return false;
                        });
                        that.data[config.name] =
                          config.type == "multipleSelect" ? mulpVal : value;
                        if (items.event) items.event = null;
                        if (config.change) items.event = config.change;
                        ev.stopPropagation();
                        break;
                      case "icon_trem_close":
                        var str = $(this)
                            .siblings()
                            .text()
                            .trim()
                            .replace(/\s/g, ""),
                          item = $(this)
                            .parent()
                            .parent()
                            .siblings(".bt_select_list")
                            .find(".item");
                        for (var i = 0; i < item.length; i++) {
                          if (str == item.eq(i).prop("title")) {
                            item.eq(i).click();
                          }
                        }
                        return false;
                        break;
                      case "secondary_menu_parent":
                        $(".item-menu-title").removeAttr("style");
                        $(this)
                          .addClass("down")
                          .siblings()
                          .removeClass("down")
                          .find(".item-menu-body-list")
                          .removeClass("show");
                        $(this)
                          .siblings()
                          .children("svg")
                          .css("fill", "#999999");
                        $(".down").children("svg").css("fill", "#666666");
                        if ($(this).find(".item-menu-body-list").length > 0) {
                          $(this)
                            .find(".item-menu-body-list")
                            .addClass("show")
                            .parent()
                            .siblings()
                            .find(".item-menu-body-list")
                            .removeClass("show");
                        }
                        ev.stopPropagation();
                        break;
                      case "secondary_menu_child":
                        var _value = $(this).attr("data-value");
                        config =
                          that.form_config[
                            $(this)
                              .parents(".bt_select_updown")
                              .attr("data-name")
                          ];
                        that.data[config.name] = _value;
                        if (items.event) items.event = null;
                        if (config.change) items.event = config.change;
                        ev.stopPropagation();
                        break;
                      case "select_path":
                        bt.select_path(
                          "event_" +
                            $(this).prev().attr("name") +
                            "_" +
                            that.random,
                          items.select || "",
                          !items.callback || items.callback.bind(that),
                          items.defaultPath || ""
                        );
                        break;
                      case "checkbox":
                        var checked = $(this).is(":checked");
                        if (checked) {
                          $(this).prev().addClass("active");
                        } else {
                          $(this).prev().removeClass("active");
                        }
                        break;
                    }
                    if (items.event)
                      items.event.apply(this, [
                        that.$get_form_value(),
                        form,
                        that,
                        config,
                        ev,
                      ]); // 事件
                    if (items.added)
                      items.added.apply(this, [ev, config, form]);
                  }
                );
              }
            })(items, key);
          });
        });
        if (callback) callback();
      },

      /**
       * @description 获取表单数据
       * @return {object} 表单数据
       */
      $get_form_value: function () {
        var form = {},
          ev = this.element;
        ev.find('input,textarea[disabled="disabled"]').each(function (
          index,
          item
        ) {
          var val = $(this).val();
          if ($(this).attr("type") === "checkbox") {
            val = $(this).prop("checked");
          }
          if ($(this).attr("type") === "radio") {
            val = ev
              .find("input[name=" + $(this).attr("name") + "]:radio:checked")
              .val();
          }
          form[$(this).attr("name")] = val;
        });
        return $.extend({}, ev.serializeObject(), form);
      },

      /**
       * @description 设置指定数据
       *
       */
      $set_find_value: function (name, value) {
        var config = {},
          that = this;
        typeof name != "string" ? (config = name) : (config[name] = value);
        $.each(config, function (key, item) {
          that.form_element[key].val(item);
        });
      },

      /**
       * @description 获取Form，jquery节点
       * @param {Boolean} afresh 是否强制刷新
       * @return {object}
       */
      $get_form_element: function (afresh) {
        var form = {},
          that = this;
        if (afresh || $.isEmptyObject(that.form_element)) {
          this.element.find(":input").each(function (index) {
            form[$(this).attr("name")] = $(this);
          });
          that.form_element = form;
          return form;
        } else {
          return that.form_element;
        }
      },

      /**
       * @description 验证值整个列表是否存在，存在则转换成属性字符串格式
       */
      $verify_group: function (config, group) {
        var that = this,
          str = "";
        $.each(group, function (index, item) {
          if (typeof config[item] === "undefined") return true;
          if (["disabled", "readonly"].indexOf(item) > -1) {
            str += " " + (config[item] ? item + '="' + item + '"' : "");
          } else {
            str += " " + item + '="' + config[item] + '"';
          }
        });
        return str;
      },

      /**
       * @description 验证绑定事件
       * @param {String} value
       */
      $verify_bind_event: function (eventName, row, group) {
        var event_list = {};
        $.each(group, function (index, items) {
          var event_fun = row[items];
          if (event_fun) {
            if (typeof event_list[eventName] === "object") {
              if (!Array.isArray(event_list[eventName]))
                event_list[eventName] = [event_list[eventName]];
              event_list[eventName].push({
                event: event_fun,
                eventType: items,
              });
            } else {
              event_list[eventName] = {
                event: event_fun,
                eventType: items,
              };
            }
          }
        });
        return event_list;
      },

      /**
       * @description 验证值是否存在
       * @param {String} value 内容/值
       * @param {String|Boolean} attr 属性
       * @param {String} type 属性
       */
      $verify: function (value, attr, type) {
        if (!value) return "";
        if (type === true) return value ? " " + attr : "";
        if (type === "style") return attr ? attr + ":" + value + ";" : value;
        return attr ? " " + attr + '="' + value + '"' : " " + value;
      },
      /**
       * @description 验证form表单
       */
      $verify_form: function () {
        var form_list = {},
          form = this.config.form,
          form_value = this.$get_form_value(),
          form_element = this.$get_form_element(true),
          is_verify = true;
        for (var key = 0; key < form.length; key++) {
          var item = form[key];
          if (!Array.isArray(item.group)) item.group = [item.group];
          if (item.separate) continue;
          for (var i = 0; i < item.group.length; i++) {
            var items = item.group[i],
              name = items.name;
            if (items.type === "help") continue;
            if (typeof items.verify == "function") {
              var is_verify = items.verify(
                form_value[name],
                form_element[name],
                items,
                true
              );
              is_verify = typeof is_verify == "boolean" ? false : true;
            }
          }
        }
        if (!is_verify) return is_verify;
        return form_value;
      },
      /**
       * @description 提交内容，需要传入url
       * @param {Object|Function} param 附加参数或回调函数
       * @param {Function} callback 回调
       */
      $submit: function (param, callback, tips) {
        var form = this.$verify_form();
        if (typeof param === "function")
          (tips = callback), (callback = param), (param = {});
        if (!form) return false;
        form = $.extend(form, param);
        if (typeof this.config.url == "undefined") {
          bt_tools.msg("请求提交地址不能为空！", false);
          return false;
        }
        bt_tools.send(
          {
            url: this.config.url,
            data: form,
          },
          function (res) {
            if (callback) {
              callback(res, form);
            } else {
              bt_tools.msg(res);
            }
          },
          tips || "提交中"
        );
      },
    };
    return new ReaderForm(config);
  },
  /**
   * @description tab切换，支持三种模式
   * @param {object} config
   * @return 当前实例对象
   */
  tab: function (config) {
    var _that = this;

    function ReaderTab(config) {
      this.config = config;
      this.theme = this.config.theme || {};
      this.$load();
    }

    ReaderTab.prototype = {
      type: 1,
      theme_list: [
        {
          content: "tab-body",
          nav: "tab-nav",
          body: "tab-con",
          active: "on",
        },
        {
          content: "bt-w-body",
          nav: "bt-w-menu",
          body: "bt-w-con",
        },
      ],
      random: bt.get_random(5),
      $init: function () {
        var that = this,
          active = this.config.active,
          config = that.config.list,
          _theme = {};
        this.$event_bind();
        if (config[that.active].success) config[that.active].success();
        config[that.active]["init"] = true;
      },
      $load: function () {
        var that = this;
      },
      $reader_content: function () {
        var that = this,
          _list = that.config.list,
          _tab = "",
          _tab_con = "",
          _theme = that.theme,
          config = that.config;
        if (typeof that.active === "undefined") that.active = 0;
        if (!$.isEmptyObject(config.theme)) {
          _theme = this.theme_list[that.active];
          $.each(config.theme, function (key, item) {
            if (_theme[key]) _theme[key] += " " + item;
          });
          that.theme = _theme;
        }
        if (config.type && $.isEmptyObject(config.theme))
          this.theme = this.theme_list[that.active];
        $.each(_list, function (index, item) {
          var active = that.active === index,
            _active = _theme["active"] || "active";
          _tab +=
            '<span class="' +
            (active ? _active : "") +
            '">' +
            item.title +
            "</span>";
          _tab_con +=
            '<div class="tab-block ' +
            (active ? _active : "") +
            '">' +
            (active ? item.content : "") +
            "</div>";
        });
        that.element = $(
          '<div id="tab_' +
            that.random +
            '" class="' +
            _theme["content"] +
            _that.$verify(that.config["class"]) +
            '"><div class="' +
            _theme["nav"] +
            '" >' +
            _tab +
            '</div><div class="' +
            _theme["body"] +
            '">' +
            _tab_con +
            "</div></div>"
        );
        return that.element[0].outerHTML;
      },
      /**
       * @description 事件绑定
       *
       */
      $event_bind: function () {
        var that = this,
          _theme = that.theme,
          active = _theme["active"] || "active";
        if (!that.el) that.element = $("#tab_" + that.random);
        that.element.on(
          "click",
          "." + _theme["nav"].replace(/\s+/g, ".") + " span",
          function () {
            var index = $(this).index(),
              config = that.config.list[index];
            $(this).addClass(active).siblings().removeClass(active);
            $(
              "#tab_" +
                that.random +
                " ." +
                _theme["body"] +
                ">div:eq(" +
                index +
                ")"
            )
              .addClass(active)
              .siblings()
              .removeClass(active);
            that.active = index;
            if (!config.init) {
              // console.log(_theme)
              $(
                "#tab_" +
                  that.random +
                  " ." +
                  _theme["body"] +
                  ">div:eq(" +
                  index +
                  ")"
              ).html(config.content);
              if (config.success) config.success();
              config.init = true;
            }
          }
        );
      },
    };
    return new ReaderTab(config);
  },
  /**
   * @description loading过渡
   * @param {*} title
   * @param {*} is_icon
   * @return void
   */
  load: function (title) {
    var random = bt.get_random(5),
      layel = $(
        '<div class="layui-layer layui-layer-dialog layui-layer-msg layer-anim" id="' +
          random +
          '" type="dialog" style="z-index: 99891031;"><div class="layui-layer-content layui-layer-padding"><i class="layui-layer-ico layui-layer-ico16"></i>正在' +
          title +
          '，请稍候...</div><span class="layui-layer-setwin"></span></div><div class="layui-layer-shade" id="layer-mask-' +
          random +
          '" times="17" style="z-index:99891000; background-color:#000; opacity:0.3; filter:alpha(opacity=30);"></div>'
      ),
      mask = "",
      loadT = "";
    $("body").append(layel);
    var win = $(window),
      msak = $(".layer-loading-mask"),
      layel = $("#" + random);
    layel.css({ top: (win.height() - 64) / 2, left: (win.width() - 320) / 2 });
    if (title === true) loadT = layer.load();
    return {
      close: function () {
        if (typeof loadT == "number") {
          layer.close(loadT);
        } else {
          $("body")
            .find("#" + random + ",#layer-mask-" + random)
            .remove();
        }
      },
    };
  },
  /**
   * @description 弹窗方法，有默认的参数和重构的参数
   * @param {object} config  和layer参数一致
   * @require 当前关闭弹窗方法
   */
  open: function (config) {
    var _config = {},
      layerT = null,
      form = null;
    _config = $.extend(
      { type: 1, area: "640px", closeBtn: 2, btn: ["确认", "取消"] },
      config
    );
    if (typeof _config.content == "object") {
      var param = _config.content;
      form = bt_tools.form(param);
      _config.success = function (layero, indexs) {
        form.$event_bind();
        // $(layero).find('input[type="text"],textarea').each(function () {
        //   var name = $(this).attr('name');
        //   $(this).val(form.data[name]);
        // });
        if (typeof config.success != "undefined")
          config.success(layero, indexs, form);
      };
      _config.yes = function (indexs, layero) {
        var form_val = form.$verify_form();
        if (!form_val) return false;
        if (typeof config.yes != "undefined") {
          var yes = config.yes.apply(form, [form_val, indexs, layero]);
          if (!yes) return false;
        }
      };
      _config.content = form.$reader_content();
    }
    layerT = layer.open(_config);
    return {
      close: function () {
        layer.close(layerT);
      },
      form: form,
    };
  },
  /**
   * @description 封装msg方法
   * @param {object|string} param1 配置参数,请求方法参数
   * @param {number} param2 图标ID
   * @require 当前关闭弹窗方法
   */
  msg: function (param1, param2) {
    var layerT = null,
      msg = "",
      config = {};
    if (typeof param1 === "object") {
      if (typeof param1.status === "boolean") {
        (msg = param1.msg), (config = { icon: param1.status ? 1 : 2 });
        if (!param1.status)
          config = $.extend(config, {
            time: !param2 ? 0 : 3000,
            closeBtn: 2,
            shade: 0.3,
            shadeClose: true,
          });
      }
    }
    if (typeof param1 === "string") {
      (msg = param1),
        (config = {
          icon: typeof param2 !== "undefined" ? param2 : 1,
          shadeClose: true,
        });
    }
    layerT = layer.msg(msg, config);
    return {
      close: function () {
        layer.close(layerT);
      },
    };
  },

  /**
   * @description 成功提示
   * @param {string} msg 信息
   */
  success: function (msg) {
    this.msg({ msg: msg, status: true });
  },

  /**
   * @description 错误提示
   * @param {string} msg 信息
   */
  error: function (msg) {
    this.msg({ msg: msg, status: false });
  },
  /**
   * @description 请求封装
   * @param {string|object} conifg ajax配置参数/请求地址
   * @param {function|object} callback 回调函数/请求参数
   * @param {function} callback1 回调函数/可为空
   * @returns void 无
   */
  send: function (param1, param2, param3, param4, param5, param6) {
    var params = {},
      success = null,
      error = null,
      config = [],
      param_one = "";
    $.each(arguments, function (index, items) {
      config.push([items, typeof items]);
    });

    function diff_data(i) {
      try {
        success = config[i][1] == "function" ? config[i][0] : null;
        error = config[i + 1][1] == "function" ? config[i + 1][0] : null;
      } catch (error) {}
    }

    param_one = config[0];
    switch (param_one[1]) {
      case "string":
        $.each(config, function (index, items) {
          var value = items[0],
            type = items[1];
          if (
            index > 1 &&
            (type == "boolean" || type == "string" || type == "object")
          ) {
            var arry = param_one[0].split("/");
            params["url"] = "/" + arry[0] + "?action=" + arry[1];
            if (type == "object") {
              params["load"] = value.load;
              params["verify"] = value.verify;
              if (value.plugin)
                params["url"] =
                  "/plugin?action=a&name=" + arry[0] + "&s=" + arry[1];
            } else if (type == "string") {
              params["load"] = value;
            }
            return false;
          } else {
            params["url"] = param_one[0];
          }
        });
        if (config[1][1] === "object") {
          params["data"] = config[1][0];
          diff_data(2);
        } else {
          diff_data(1);
        }
        break;
      case "object":
        params["url"] = param_one[0].url;
        params["data"] = param_one[0].data || {};
        $.each(config, function (index, items) {
          var value = items[0],
            type = items[1];
          if (
            index > 1 &&
            (type == "boolean" || type == "string" || type == "object")
          ) {
            switch (type) {
              case "object":
                params["load"] = value.load;
                params["verify"] = value.verify;
                break;
              case "string":
                params["load"] = value;
                break;
            }
            return true;
          }
        });
        if (config[1][1] === "object") {
          params["data"] = config[1][0];
          diff_data(2);
        } else {
          diff_data(1);
        }
        break;
    }
		if (params.load) params.load = this.load(params.load);

		$.ajax({
      type: params.type || "POST",
      url: params.url,
      data: params.data || {},
      dataType: params.dataType || "JSON",
      complete: function (res) {
        if (params.load) params.load.close();
      },
      success: function (res) {
        if (typeof params.verify == "boolean" && !params.verify) {
          if (success) success(res);
          return false;
        }
        if (typeof res === "string") {
          layer.msg(res, {
            icon: 2,
            time: 0,
            closeBtn: 2,
          });
          return false;
        }
        if (params.batch) {
          if (success) success(res);
          return false;
        }
        if (
          res.status === false &&
          (res.hasOwnProperty("msg") || res.hasOwnProperty("error_msg"))
        ) {
          if (error) {
            error(res);
          } else {
            bt_tools.msg({
              status: res.status,
              msg: !res.hasOwnProperty("msg") ? res.error_msg : res.msg,
            });
          }
          return false;
        }

        if (params.tips) {
          bt_tools.msg(res);
        }
        if (success) success(res);
      },
    });
  },

  /**
   * @description 命令行输入
   */
  command_line_output: function (config) {
    var _that = this,
      uuid = bt.get_random(15);

    /**
     * @description 渲染
     * @param config
     * @return {object}
     * @constructor
     */
    function ReaderCommand(config) {
      var that = this;
      for (var key in _that.commandConnectionPool) {
        var item = _that.commandConnectionPool[key],
          element = $(item.config.el);
        if (config.shell === item.config.shell && element.length) {
          item.el = element;
          return item;
        }
      }
      if (typeof config === "undefined") config = {};
      this.config = $.extend({ route: "/sock_shell" }, config);
      this.xterm_config = $.extend(this.xterm_config, this.config.xterm);
      this.el = $(this.config.el);
      this.open = config.open;
      this.close = config.close;
      this.message = config.message;
      if (!this.config.hasOwnProperty("el")) {
        _that.msg({ msg: "请输入选择器element，不可为空", status: false });
        return false;
      }
      if (!this.config.hasOwnProperty("shell")) {
        _that.msg({ msg: "请输入命令，不可为空", status: false });
        return false;
      }
      if (this.config.hasOwnProperty("time")) {
        setTimeout(function () {
          that.close_connect();
        }, this.config.time);
      }
      this.init();
    }

    ReaderCommand.prototype = {
      socket: null, //websocket 连接保持的对象
      socketToken: null,
      timeout: 0, // 连接到期时间，为0代表永久有效
      monitor_interval: 2000,
      element_detection: null,
      uuid: uuid,
      fragment: [],
      error: 0, // 错误次数，用于监听元素内容是否还存在
      retry: 0, // 重试次数
      forceExit: false, // 强制断开连接
      /**
       * @description 程序初始化
       */
      init: function () {
        var oldUUID = bt.get_cookie("commandInputViewUUID"),
          that = this;
        if (!this.el[0]) {
          if (this.error > 10) return false;
          setTimeout(function () {
            that.init();
            this.error++;
          }, 2000);
          return false;
        }
        this.error = 0;
        if (this.el[0].localName !== "pre") {
          this.el.append('<pre class="command_output_pre"></pre>');
          this.el = this.el.find("pre");
          this.config.el = this.config.el + " pre";
        } else {
          this.el.addClass("command_output_pre");
        }
        if (Array.isArray(this.config.area)) {
          this.el.css({
            width: this.config.area[0],
            height: this.config.area[1],
          });
        } else {
          this.el.css({ width: "100%", height: "100%" });
        }
        if (
          oldUUID &&
          typeof _that.commandConnectionPool[oldUUID] != "undefined"
        ) {
          _that.commandConnectionPool[oldUUID].close_connect();
          delete _that.commandConnectionPool[oldUUID];
        }
        bt.set_cookie("commandInputViewUUID", this.uuid);
        this.element_detection = setInterval(function () {
          if (!$(that.config.el).length) {
            clearInterval(that.element_detection);
            that.forceExit = true;
            that.close_connect();
          }
        }, 1 * 60 * 1000);
        this.set_full_screen();
        this.create_websocket_connect(this.config.route, this.config.shell);
        this.monitor_element();
      },
      /**
       * @description 创建websocket连接
       * @param {string} url websocket连接地址
       * @param {string} shell 需要传递的命令
       */
      create_websocket_connect: function (url, shell) {
        var that = this;
        this.socket = new WebSocket(
          (location.protocol === "http:" ? "ws://" : "wss://") +
            location.host +
            url
        );
        this.socket.addEventListener("open", function (ev) {
          if (!this.socketToken) {
            var _token = window.vite_public_request_token;
            this.socketToken = { "x-http-token": _token };
          }
          this.send(JSON.stringify(this.socketToken));
          this.send(shell);
          if (that.open) that.open();
          that.retry = 0;
        });
        this.socket.addEventListener("close", function (ev) {
          if (!that.forceExit) {
            // console.log(ev.code,that.retry)
            if (ev.code !== 1000 && that.retry <= 10) {
              that.socket = that.create_websocket_connect(
                that.config.route,
                that.config.shell
              );
              that.retry++;
            }
            if (that.close) that.close(ev);
          }
        });
        this.socket.addEventListener("message", function (ws_event) {
          var result = ws_event.data;
          if (!result) return;
          that.refresh_data(result);
          if (that.message) that.message(result);
        });
        return this.socket;
      },

      /**
       * @description 设置全屏视图
       */
      set_full_screen: function () {
        // 1
      },

      htmlEncodeByRegExp: function (str) {
        if (str.length == 0) return "";
        return str
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/ /g, "&nbsp;")
          .replace(/\'/g, "&#39;")
          .replace(/\"/g, "&quot;")
          .replace(/\(/g, "&#40;")
          .replace(/\)/g, "&#41;")
          .replace(/`/g, "&#96;")
          .replace(/=/g, "＝");
      },

      /**
       * @description 刷新Pre数据
       * @param {object} data 需要插入的数据
       */
      refresh_data: function (data) {
        var rdata = this.htmlEncodeByRegExp(data);
        this.el = $(this.config.el);
        if (!this.el) return false;
        this.fragment.push(rdata);
        if (this.fragment.length >= 300) {
          this.fragment.splice(0, 150);
          this.el.html(this.fragment.join(""));
        } else {
          this.el.append(rdata);
        }
        if (this.el[0]) {
          this.el.scrollTop(this.el[0].scrollHeight);
        }
      },

      /**
       * @description 监听元素状态，判断是否移除当前的ws连接
       *
       */
      monitor_element: function () {
        var that = this;
        this.monitor_interval = setInterval(function () {
          if (!that.el.length) {
            that.close_connect();
            clearInterval(that.monitor_interval);
          }
        }, that.config.monitorTime || 2000);
      },

      /**
       * @description 断开命令响应和websocket连接
       */
      close_connect: function () {
        this.forceExit = true;
        this.socket.close();
        delete _that.commandConnectionPool[this.uuid];
      },
    };
    this.commandConnectionPool[uuid] = new ReaderCommand(config);
    return this.commandConnectionPool[uuid];
  },

  /**
   * @description 清理验证提示样式
   * @param {object} element  元素节点
   */
  $clear_verify_tips: function (element) {
    element.removeClass("bt-border-error bt-border-sucess");
    layer.close("tips");
  },

  /**
   * @description 验证提示
   * @param {object} element  元素节点
   * @param {string} tips 警告提示
   * @return void
   */
  $verify_tips: function (element, tips, is_error) {
    if (typeof is_error === "undefined") is_error = true;
    element
      .removeClass("bt-border-error bt-border-sucess")
      .addClass(is_error ? "bt-border-error" : "bt-border-sucess");
    element.focus();
    layer.tips('<span class="inlineBlock">' + tips + "</span>", element, {
      tips: [1, is_error ? "red" : "#20a53a"],
      time: 3000,
      area: element.width(),
    });
  },
  /**
   * @description 验证值是否存在
   * @param {String} value 内容/值
   * @param {String|Boolean} attr 属性
   * @param {String} type 属性
   */
  $verify: function (value, attr, type) {
    if (!value) return "";
    if (type === true) return value ? " " + attr : "";
    if (type === "style") return attr ? attr + ":" + value + ";" : value;
    return attr ? " " + attr + '="' + value + '"' : " " + value;
  },

  /**
   * @description 批量操作的结果
   * @param {*} config
   */
  $batch_success_table: function (config) {
    var _that = this,
      length = $(config.html).length;
    bt.open({
      type: 1,
      title: config.title,
      area: config.area || ["350px", "350px"],
      shadeClose: false,
      closeBtn: 2,
      content:
        config.content ||
        '<div class="batch_title"><span class><span class="batch_icon"></span><span class="batch_text">' +
          config.title +
          '操作完成！</span></span></div><div class="' +
          (length > 4 ? "fiexd_thead" : "") +
          ' batch_tabel divtable" style="margin: 15px 30px 15px 30px;overflow: auto;height: 200px;"><table class="table table-hover"><thead><tr><th>' +
          config.th +
          '</th><th style="text-align:right;width:120px;">操作结果</th></tr></thead><tbody>' +
          config.html +
          "</tbody></table></div>",
      success: function () {
        if (length > 4) _that.$fixed_table_thead(".fiexd_thead");
      },
    });
  },
  /**
   * @description 固定表头
   * @param {string} el DOM选择器
   * @return void
   */
  $fixed_table_thead: function (el) {
    $(el).scroll(function () {
      var scrollTop = this.scrollTop;
      this.querySelector("thead").style.transform =
        "translateY(" + (scrollTop - 1) + "px)";
    });
  },
  /**
   * @description 插件视图设置
   * @param {object|string} layid dom元素或layer_id
   * @param {object} config 插件宽度高度或其他配置
   */
  $piugin_view_set: function (layid, config) {
    var element = $(
        typeof layid === "string" ? "#layui-layer" + layid : layid
      ).hide(),
      win = $(window);
    setTimeout(function () {
      var width = config.width || element.width(),
        height = config.height || element.height();
      element
        .css(
          $.extend(config, {
            left: (win.width() - width) / 2,
            top: (win.height() - height) / 2,
          })
        )
        .addClass("custom_layer");
    }, 50);
    setTimeout(function () {
      element.show();
    }, 500);
  },
  /**
   * @description 简化版nps
   */
  nps: function (config) {
    var html =
      '\
      <div>\
         <div class="nps-star pd20" style="padding-top: 30px">\
            <div>\
              <div class="time-keeping" style="position: absolute;top: 4px;right: 28px;color: #999999;"><span style="color:red;">15&nbsp;</span>秒后自动关闭</div>\
              <div style="font-size: 14px;text-align: left;color: #000;">您对【' +
      config.name +
      '】功能的满意程度？</div>\
              <div class="star-container">\
                <div class="star">\
                  <div class="star-icon">\
                      <svg width="30" height="30" data-attr="1" style="color: #cccccc" viewBox="0 0 152.249 145.588" fill="none" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\
                        <desc>\
                          Created with Pixso.\
                        </desc>\
                        <defs/>\
                        <path id="矢量 104" d="M68.5163 5.52759L56.0289 43.9553C54.9577 47.2512 51.8863 49.4829 48.4207 49.4829L8.01495 49.4844C0.265564 49.4844 -2.95648 59.4011 3.31281 63.9564L36.0008 87.7075C38.8045 89.7446 39.9776 93.3553 38.9068 96.6514L26.4222 135.08C24.0278 142.45 32.4632 148.579 38.7328 144.024L71.4227 120.275C74.2265 118.239 78.0229 118.239 80.8267 120.275L113.517 144.024C119.786 148.579 128.222 142.45 125.827 135.08L113.343 96.6514C112.272 93.3553 113.445 89.7446 116.249 87.7075L148.937 63.9563C155.206 59.4011 151.984 49.4844 144.234 49.4844L103.829 49.4829C100.363 49.4829 97.2916 47.2512 96.2205 43.9553L83.7331 5.52759C81.3381 -1.84253 70.9113 -1.84253 68.5163 5.52759Z" \
                          fill-rule="evenodd" \
                          fill="currentColor"\
                        />\
                      </svg>\
                  </div>\
                  <div class="star-title" style="color: #FFFFFF">很不满意</div>\
                </div>\
                <div class="star">\
                  <div class="star-icon">\
                      <svg width="30" height="30" data-attr="2" style="color: #cccccc" viewBox="0 0 152.249 145.588" fill="none" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\
                        <desc>\
                          Created with Pixso.\
                        </desc>\
                        <defs/>\
                        <path id="矢量 104" d="M68.5163 5.52759L56.0289 43.9553C54.9577 47.2512 51.8863 49.4829 48.4207 49.4829L8.01495 49.4844C0.265564 49.4844 -2.95648 59.4011 3.31281 63.9564L36.0008 87.7075C38.8045 89.7446 39.9776 93.3553 38.9068 96.6514L26.4222 135.08C24.0278 142.45 32.4632 148.579 38.7328 144.024L71.4227 120.275C74.2265 118.239 78.0229 118.239 80.8267 120.275L113.517 144.024C119.786 148.579 128.222 142.45 125.827 135.08L113.343 96.6514C112.272 93.3553 113.445 89.7446 116.249 87.7075L148.937 63.9563C155.206 59.4011 151.984 49.4844 144.234 49.4844L103.829 49.4829C100.363 49.4829 97.2916 47.2512 96.2205 43.9553L83.7331 5.52759C81.3381 -1.84253 70.9113 -1.84253 68.5163 5.52759Z" \
                          fill-rule="evenodd" \
                          fill="currentColor"\
                        />\
                      </svg>\
                  </div>\
                  <div class="star-title" style="color: #FFFFFF">不满意</div>\
                </div>\
                <div class="star">\
                  <div class="star-icon">\
                      <svg width="30" height="30" data-attr="3" style="color: #cccccc" viewBox="0 0 152.249 145.588" fill="none" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\
                        <desc>\
                          Created with Pixso.\
                        </desc>\
                        <defs/>\
                        <path id="矢量 104" d="M68.5163 5.52759L56.0289 43.9553C54.9577 47.2512 51.8863 49.4829 48.4207 49.4829L8.01495 49.4844C0.265564 49.4844 -2.95648 59.4011 3.31281 63.9564L36.0008 87.7075C38.8045 89.7446 39.9776 93.3553 38.9068 96.6514L26.4222 135.08C24.0278 142.45 32.4632 148.579 38.7328 144.024L71.4227 120.275C74.2265 118.239 78.0229 118.239 80.8267 120.275L113.517 144.024C119.786 148.579 128.222 142.45 125.827 135.08L113.343 96.6514C112.272 93.3553 113.445 89.7446 116.249 87.7075L148.937 63.9563C155.206 59.4011 151.984 49.4844 144.234 49.4844L103.829 49.4829C100.363 49.4829 97.2916 47.2512 96.2205 43.9553L83.7331 5.52759C81.3381 -1.84253 70.9113 -1.84253 68.5163 5.52759Z" \
                          fill-rule="evenodd" \
                          fill="currentColor"\
                        />\
                      </svg>\
                  </div>\
                  <div class="star-title" style="color: #FFFFFF">一般</div>\
                </div>\
                <div class="star">\
                  <div class="star-icon">\
                      <svg width="30" height="30" data-attr="4" style="color: #cccccc" viewBox="0 0 152.249 145.588" fill="none" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\
                        <desc>\
                          Created with Pixso.\
                        </desc>\
                        <defs/>\
                        <path id="矢量 104" d="M68.5163 5.52759L56.0289 43.9553C54.9577 47.2512 51.8863 49.4829 48.4207 49.4829L8.01495 49.4844C0.265564 49.4844 -2.95648 59.4011 3.31281 63.9564L36.0008 87.7075C38.8045 89.7446 39.9776 93.3553 38.9068 96.6514L26.4222 135.08C24.0278 142.45 32.4632 148.579 38.7328 144.024L71.4227 120.275C74.2265 118.239 78.0229 118.239 80.8267 120.275L113.517 144.024C119.786 148.579 128.222 142.45 125.827 135.08L113.343 96.6514C112.272 93.3553 113.445 89.7446 116.249 87.7075L148.937 63.9563C155.206 59.4011 151.984 49.4844 144.234 49.4844L103.829 49.4829C100.363 49.4829 97.2916 47.2512 96.2205 43.9553L83.7331 5.52759C81.3381 -1.84253 70.9113 -1.84253 68.5163 5.52759Z" \
                          fill-rule="evenodd" \
                          fill="currentColor"\
                        />\
                      </svg>\
                  </div>\
                  <div class="star-title" style="color: #FFFFFF">满意</div>\
                </div>\
                <div class="star">\
                  <div class="star-icon">\
                      <svg width="30" height="30" data-attr="5" style="color: #cccccc" viewBox="0 0 152.249 145.588" fill="none" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\
                        <desc>\
                          Created with Pixso.\
                        </desc>\
                        <defs/>\
                        <path id="矢量 104" d="M68.5163 5.52759L56.0289 43.9553C54.9577 47.2512 51.8863 49.4829 48.4207 49.4829L8.01495 49.4844C0.265564 49.4844 -2.95648 59.4011 3.31281 63.9564L36.0008 87.7075C38.8045 89.7446 39.9776 93.3553 38.9068 96.6514L26.4222 135.08C24.0278 142.45 32.4632 148.579 38.7328 144.024L71.4227 120.275C74.2265 118.239 78.0229 118.239 80.8267 120.275L113.517 144.024C119.786 148.579 128.222 142.45 125.827 135.08L113.343 96.6514C112.272 93.3553 113.445 89.7446 116.249 87.7075L148.937 63.9563C155.206 59.4011 151.984 49.4844 144.234 49.4844L103.829 49.4829C100.363 49.4829 97.2916 47.2512 96.2205 43.9553L83.7331 5.52759C81.3381 -1.84253 70.9113 -1.84253 68.5163 5.52759Z" \
                          fill-rule="evenodd" \
                          fill="currentColor"\
                        />\
                      </svg>\
                  </div>\
                  <div class="star-title" style="color: #FFFFFF">非常满意</div>\
                </div>\
              </div>\
              <div class="nps-content">\
                  <textarea style="width: 100%;height: 100px;" placeholder="您对' +
      config.name +
      '有什么改进的方向和建议?"></textarea>\
              </div>' +
      (config.name === "网站"
        ? '<div class="mtb10 c6">如遇BUG问题请联系QQ群：<a class="btlink" title="宝塔面板交流群-2群" href="https://qm.qq.com/cgi-bin/qm/qr?k=pDI9rilMP7Bcf8NcXlk_9ar3_sTLEuaZ&jump_from=webapi&authKey=jLsyfgvmymKrdZrhWRAr3bTn8DkPA/PsqQ+cWw17PvbaKPcy+SteMP8ZmGVZW3yL" target="_blank">435590797</a></div>'
        : "") +
      '<div class="nps-submit">\
                <button class="btn btn-sm btn-success" style="width: 100%;height: 38px;">提交反馈</button>\
              </div>\
            </div>\
         </div>\
      </div>';
    var score = 0;

    /**
     * @description 切换星星颜色
     */
    function switchColor() {
      var _index = $(this).data("attr");
      score = _index;
      $(this)
        .parents(".star-container")
        .find(".star-icon svg")
        .each(function (index, item) {
          if (index < _index) {
            if (_index <= 2) {
              $(item).css("color", "#EF0808");
            } else if (_index <= 3) {
              $(item).css("color", "#F0AD4E");
            }
            if (_index >= 4) $(item).css("color", "#20A53A");
          } else {
            $(item).css("color", "#cccccc");
          }
        });
    }

    /**
     * @description 文字颜色
     * @param index
     * @param _index
     * @param item
     */
    function textColor(index, _index, item) {
      if (index == _index - 1) {
        if (_index <= 2) {
          $(item).parent().next().css({
            color: "#EF0808",
            "background-color": "rgba(239, 8, 8, 0.05)",
            border: "1px solid rgb(239 8 8 / 26%)",
          });
        } else if (_index <= 3) {
          $(item).parent().next().css({
            color: "#f7be56",
            "background-color": "rgb(247 190 86 / 17%)",
            border: "1px solid rgb(247 190 86 / 26%)",
          });
        } else {
          $(item).parent().next().css({
            color: "#69be3d",
            "background-color": "rgb(105 190 61 / 17%)",
            border: "1px solid rgb(105 190 61 / 26%)",
          });
        }
      } else {
        $(item).parent().next().removeAttr("style");
      }
    }

    /**
     * @description 移除星星鼠标移入移出
     */
    function selectRemoveHover() {
      var _index = $(this).data("attr");
      $(this)
        .parents(".star-container")
        .find(".star-icon svg")
        .each(function (index, item) {
          textColor(index, _index, item);
        });
    }

    var timeOutIndex = null;
    var close = false;
    /**
     * @description 鼠标移入星星
     * @param layero
     */
    function starHover(layero) {
      $(".nps-content textarea").removeClass("textarea-error");
      $(".nps-content textarea").next().remove();
      layero.find(".nps-star .star-icon svg").hover(
        function () {
          clearTimeout(timeOutIndex);
          var that = this;
          var _index = $(this).data("attr");
          $(this).parent().next().show();
          $(this)
            .parents(".star-container")
            .find(".star-icon svg")
            .each(function (index, item) {
              textColor(index, _index, item);
              if (index < _index) {
                if (_index <= 2) {
                  $(item).css("color", "#ed6d68");
                } else if (_index <= 3) {
                  $(item).css("color", "#f7be56");
                }
                if (_index >= 4) $(item).css("color", "#69be3d");
              } else {
                $(item).css("color", "#cccccc");
              }
            });
        },
        function () {
          switchColor.call(this);
        }
      );
    }

    var index = layer.open({
      type: 1,
      content: html,
      area: ["310px"],
      title: "",
      id: "nps",
      shade: 0,
      cancel: function (index, layero) {
        close = true;
        $(".nps-submit button").click();
      },
      success: function (layero, index) {
        layero
          .find(".nps-star .star-icon svg")
          .parents(".star-container")
          .find(".star-icon svg")
          .each(function (index, item) {
            if (index == 0) {
              $(item).parent().next().css({
                color: "#EF0808",
                "background-color": "rgba(239, 8, 8, 0.05)",
                border: "1px solid rgb(239 8 8 / 26%)",
              });
            }
            if (index == 2) {
              $(item).parent().next().css({
                color: "#f7be56",
                "background-color": "rgb(247 190 86 / 17%)",
                border: "1px solid rgb(247 190 86 / 26%)",
              });
            }
            if (index == 4) {
              $(item).parent().next().css({
                color: "#69be3d",
                "background-color": "rgb(105 190 61 / 17%)",
                border: "1px solid rgb(105 190 61 / 26%)",
              });
            }
          });
        var tiem = 15;
        var time_index = setInterval(function () {
          tiem--;
          if (tiem == 0) {
            close = true;
            $(".nps-submit button").click();
            clearInterval(time_index);
          }
          $(".time-keeping").html(
            '<span style="color: red">' +
              tiem +
              "</span>&nbsp;" +
              "秒后自动关闭"
          );
        }, 1000);
        $(".time-keeping");
        layero.hover(function () {
          clearInterval(time_index);
          $(".time-keeping").hide();
        });
        starHover(layero);
        $(".nps-content textarea").focus(function () {
          if (score != 0) {
            $(".nps-star .star-icon svg")
              .unbind("mouseenter")
              .unbind("mouseleave");
          }
        });
        $(".nps-content textarea").blur(function () {
          starHover(layero);
        });
        $(".nps-star .star-icon svg").click(function () {
          selectRemoveHover.call(this);
          switchColor.call(this);
          var _index = $(this).data("attr");
          $(".nps-content textarea").focus();
        });

        function submitNPS(_data, success) {
          bt_tools.send(
            { url: "config?action=write_nps_new", data: _data },
            function (res) {
              layer.close(index);
              if (res.status && success) {
                layer.open({
                  title: false,
                  btn: false,
                  shadeClose: true,
                  shade: 0.1,
                  closeBtn: 0,
                  skin: "qa_thank_dialog",
                  area: "230px",
                  content:
                    '<div class="qa_thank_box" style="background-color:#F1F9F3;text-align: center;padding: 20px 0;"><img src="/static/img/feedback/QA_like.png" style="width: 55px;"><p style="margin-top: 15px;">感谢您的参与!</p></div>',
                  success: function (layero, index) {
                    $(layero).find(".layui-layer-content").css({
                      padding: "0",
                      "border-radius": "5px",
                    });
                    $(layero).css({
                      "border-radius": "5px",
                      "min-width": "230px",
                    });
                    setTimeout(function () {
                      layer.close(index);
                    }, 3000);
                  },
                });
              }
            }
          );
        }

        bt_tools.send(
          {
            url: "config?action=get_nps_new",
            data: { version: -1, product_type: config.type },
          },
          function (res) {
            var data = res.msg[0];
            var question = {};
            $(".nps-submit button").click(function () {
              question[data.id] = $(".nps-content textarea").val();
              var _data = {
                rate: score,
                product_type: config.type,
                software_name: config.soft,
                questions: JSON.stringify(question),
              };
              if (close) {
                _data.rate = 0;
                submitNPS(_data, false);
              } else {
                if (score == 0) {
                  layer.msg("打个分数再提交吧，麻烦您了~", {
                    icon: 0,
                  });
                  return false;
                }
                if ($(".nps-content textarea").val() == "") {
                  $(".nps-content textarea").addClass("textarea-error").focus();
                  if ($(".nps-content textarea").next().length == 0) {
                    $(".nps-content textarea").after(
                      '<span style="color: red;position: absolute;top: 222px;left: 22px;">请填写下您的建议再提交吧，麻烦您了~</span>'
                    );
                  }
                } else {
                  $(".nps-content textarea").css("border", "1px solid #ccc");
                  $(".nps-content textarea").next().remove();
                  submitNPS(_data, true);
                }
              }
            });
          }
        );
      },
    });
  },
};


// 终端操作
var Term = {
  bws: null, //websocket对象
  route: '/webssh', //被访问的方法
  term: null,
  term_box: null,
  ssh_info: {},
  last_body: false,
  last_cd: null,
  config: {
    cols: 0,
    rows: 0,
    fontSize: 12,
  },

  // 	缩放尺寸
  detectZoom: (function () {
    var ratio = 0,
      screen = window.screen,
      ua = navigator.userAgent.toLowerCase();
    if (window.devicePixelRatio !== undefined) {
      ratio = window.devicePixelRatio;
    } else if (~ua.indexOf('msie')) {
      if (screen.deviceXDPI && screen.logicalXDPI) {
        ratio = screen.deviceXDPI / screen.logicalXDPI;
      }
    } else if (window.outerWidth !== undefined && window.innerWidth !== undefined) {
      ratio = window.outerWidth / window.innerWidth;
    }

    if (ratio) {
      ratio = Math.round(ratio * 100);
    }
    return ratio;
  })(),

  /**
   * @description 连接服务器
   */
  connect: function () {
    if (!Term.bws || Term.bws.readyState == 3 || Term.bws.readyState == 2) {
      //连接
      ws_url = (window.location.protocol === 'http:' ? 'ws://' : 'wss://') + window.location.host + Term.route;
      Term.bws = new WebSocket(ws_url);
      //绑定事件
      Term.bws.addEventListener('message', Term.on_message);
      Term.bws.addEventListener('close', Term.on_close);
      Term.bws.addEventListener('error', Term.on_error);
      Term.bws.addEventListener('open', Term.on_open);
    }
  },

  /**
   * @description 连接服务器成功
   * @param {Object} ws_event websocket事件
   */
  on_open: function (ws_event) {
    var http_token = window.vite_public_request_token;
    Term.send(JSON.stringify({ 'x-http-token': http_token }));
    if (JSON.stringify(Term.ssh_info) !== '{}') Term.send(JSON.stringify(Term.ssh_info));
    // Term.term.FitAddon.fit();
    Term.resize();
    var f_path = $('#fileInputPath').val() || getCookie('Path');
    if (f_path) {
      Term.last_cd = 'cd ' + f_path;
      Term.send(Term.last_cd + '\n');
    }
  },

  /**
   * @description 服务器消息事件
   * @param {Object} ws_event websocket事件 
   * @returns 
   */
  on_message: function (ws_event) {
    result = ws_event.data;
    if ((result.indexOf('@127.0.0.1:') != -1 || result.indexOf('@localhost:') != -1) && result.indexOf('Authentication failed') != -1) {
      Term.term.write(result);
      Term.localhost_login_form();
      Term.close();
      return;
    }
    if (Term.last_cd) {
      if (result.indexOf(Term.last_cd) != -1 && result.length - Term.last_cd.length < 3) {
        Term.last_cd = null;
        return;
      }
    }
    if (result === '\r服务器连接失败!\r' || result == '\r用户名或密码错误!\r') {
      Term.close();
      return;
    }
    if (result.length > 1 && Term.last_body === false) {
      Term.last_body = true;
    }

    Term.term.write(result);
    if (result == '\r\n登出\r\n' || result == '\r\n注销\r\n' || result == '注销\r\n' || result == '登出\r\n' || result == '\r\nlogout\r\n' || result == 'logout\r\n') {
      setTimeout(function () {
        layer.close(Term.term_box);
        Term.term.dispose();
      }, 500);
      Term.close();
      Term.bws = null;
    }
  },

  /**
   * @description websocket关闭事件
   * @param {Object} ws_event websocket事件
   */
  on_close: function (ws_event) {
    Term.bws = null;
  },

  /**
   * @description  websocket错误事件
   * @param {Object} ws_event websocket事件
   * @returns 
   */
  on_error: function (ws_event) {
    if (ws_event.target.readyState === 3) {
      if (Term.state === 3) return;
      Term.term.write(msg);
      Term.state = 3;
    } else {
      // console.log(ws_event)
    }
  },

  /**
   * @description 关闭websocket
   * @returns
   */
  close: function () {
    if (Term.bws) {
      Term.bws.close();
    }
  },

  /**
   * @description 重置终端大小
   */
  resize: function () {
    $('#term').height($('.term_box_all .layui-layer-content').height() - 30);
    setTimeout(function () {
      Term.term.FitAddon.fit();
      Term.send(JSON.stringify({ resize: 1, rows: Term.term.rows, cols: Term.term.cols }));
      Term.term.focus();
    }, 400);
  },

  /**
   * 
   * @description 发送数据
   * @param {String} data 发送的数据
   * @param {Number} num 重试次数
   * @returns
   */
  send: function (data, num) {
    //如果没有连接，则尝试连接服务器
    if (!Term.bws || Term.bws.readyState == 3 || Term.bws.readyState == 2) {
      Term.connect();
    }

    //判断当前连接状态,如果!=1，则100ms后尝试重新发送
    if (Term.bws.readyState === 1) {
      Term.bws.send(data);
    } else {
      if (Term.state === 3) return;
      if (!num) num = 0;
      if (num < 5) {
        num++;
        setTimeout(function () {
          Term.send(data, num++);
        }, 100);
      }
    }
  },

  /**
   * @description 运行终端
   * @param {Object} ssh_info ssh信息
   */
  run: function (ssh_info) {
    var loadT = layer.msg('正在加载终端所需文件，请稍候...', { icon: 16, time: 0, shade: 0.3 });
    layer.close(loadT);
    Term.term = new Terminal({
      rendererType: 'canvas',
      cols: 100,
      rows: 34,
      fontSize: 15,
      screenKeys: true,
      useStyle: true,
    });
    Term.term.setOption('cursorBlink', true);
    Term.last_body = false;
    Term.term_box = layer.open({
      type: 1,
      title: '宝塔终端',
      area: ['930px', '640px'],
      closeBtn: 2,
      shadeClose: false,
      skin: 'term_box_all',
      content:
        '<link rel="stylesheet" href="/static/css/xterm.css" />\
            <div class="term-box" style="background-color:#000" id="term"></div>',
      cancel: function (index, lay) {
        bt.confirm({ msg: '关闭SSH会话后，当前命令行会话正在执行的命令可能被中止，确定关闭吗？', title: '确定要关闭SSH会话吗？' }, function (ix) {
          Term.term.dispose();
          layer.close(index);
          layer.close(ix);
          Term.close();
        });
        return false;
      },
      success: function () {
        $('.term_box_all').css('background-color', '#000');
        Term.term.open(document.getElementById('term'));
        Term.term.FitAddon = new FitAddon.FitAddon();
        Term.term.loadAddon(Term.term.FitAddon);
        Term.term.WebLinksAddon = new WebLinksAddon.WebLinksAddon();
        Term.term.loadAddon(Term.term.WebLinksAddon);
        Term.term.focus();
      },
    });
    Term.term.onData(function (data) {
      try {
        Term.bws.send(data);
      } catch (e) {
        Term.term.write('\r\n连接丢失,正在尝试重新连接!\r\n');
        Term.connect();
      }
    });
    if (ssh_info) Term.ssh_info = ssh_info;
    Term.connect();
  },

  /**
   * @description 重置登录
   */
  reset_login: function () {
    var ssh_info = {
      data: JSON.stringify({
        host: $("input[name='host']").val(),
        port: $("input[name='port']").val(),
        username: $("input[name='username']").val(),
        password: $("input[name='password']").val(),
      }),
    };
    bt_tools.send({url: '/term_open',data: ssh_info}, function (rdata) {
      if (rdata.status === false) {
        layer.msg(rdata.msg);
        return;
      }
      layer.closeAll();
      Term.connect();
      Term.term.scrollToBottom();
      Term.term.focus();
    },{verify: false});
  },

  /**
   * @description 本地登录表单
   */
  localhost_login_form: function () {
    var template =
      '<div class="localhost-form-shade"><div class="localhost-form-view bt-form-2x"><div class="localhost-form-title"><i class="localhost-form_tip"></i><span style="vertical-align: middle;">无法自动认证，请填写本地服务器的登录信息!</span></div>\
        <div class="line input_group">\
            <span class="tname">服务器IP</span>\
            <div class="info-r">\
                <input type="text" name="host" class="bt-input-text mr5" style="width:240px" placeholder="输入服务器IP" value="127.0.0.1" autocomplete="off" />\
                <input type="text" name="port" class="bt-input-text mr5" style="width:60px" placeholder="端口" value="22" autocomplete="off"/>\
            </div>\
        </div>\
        <div class="line">\
            <span class="tname">SSH账号</span>\
            <div class="info-r">\
                <input type="text" name="username" class="bt-input-text mr5" style="width:305px" placeholder="输入SSH账号" value="root" autocomplete="off"/>\
            </div>\
        </div>\
        <div class="line">\
            <span class="tname">验证方式</span>\
            <div class="info-r ">\
                <div class="btn-group">\
                    <button type="button" tabindex="-1" class="btn btn-sm auth_type_checkbox btn-success" data-ctype="0">密码验证</button>\
                    <button type="button" tabindex="-1" class="btn btn-sm auth_type_checkbox btn-default data-ctype="1">私钥验证</button>\
                </div>\
            </div>\
        </div>\
        <div class="line c_password_view show">\
            <span class="tname">密码</span>\
            <div class="info-r">\
                <input type="text" name="password" class="bt-input-text mr5" placeholder="请输入SSH密码" style="width:305px;" value="" autocomplete="off"/>\
            </div>\
        </div>\
        <div class="line c_pkey_view hidden">\
            <span class="tname">私钥</span>\
            <div class="info-r">\
                <textarea rows="4" name="pkey" class="bt-input-text mr5" placeholder="请输入SSH私钥" style="width:305px;height: 80px;line-height: 18px;padding-top:10px;"></textarea>\
            </div>\
        </div><button type="submit" class="btn btn-sm btn-success">登录</button></div></div>';
    $('.term-box').after(template);
    $('.auth_type_checkbox').click(function () {
      var index = $(this).index();
      $(this).addClass('btn-success').removeClass('btn-default').siblings().removeClass('btn-success').addClass('btn-default');
      switch (index) {
        case 0:
          $('.c_password_view').addClass('show').removeClass('hidden');
          $('.c_pkey_view').addClass('hidden').removeClass('show').find('input').val('');
          break;
        case 1:
          $('.c_password_view').addClass('hidden').removeClass('show').find('input').val('');
          $('.c_pkey_view').addClass('show').removeClass('hidden');
          break;
      }
    });
    $('.localhost-form-view > button').click(function () {
      var form = {};
      $('.localhost-form-view input,.localhost-form-view textarea').each(function (index, el) {
        var name = $(this).attr('name'),
          value = $(this).val();
        form[name] = value;
        switch (name) {
          case 'port':
            if (!bt.check_port(value)) {
              bt.msg({ status: false, msg: '服务器端口格式错误！' });
              return false;
            }
            break;
          case 'username':
            if (value == '') {
              bt.msg({ status: false, msg: '服务器用户名不能为空!' });
              return false;
            }
            break;
          case 'password':
            if (value == '' && $('.c_password_view').hasClass('show')) {
              bt.msg({ status: false, msg: '服务器密码不能为空!' });
              return false;
            }
            break;
          case 'pkey':
            if (value == '' && $('.c_pkey_view').hasClass('show')) {
              bt.msg({ status: false, msg: '服务器秘钥不能为空!' });
              return false;
            }
            break;
        }
      });
      form.ps = '本地服务器';
      var loadT = bt.load('正在添加服务器信息，请稍候...');
      bt.send('create_host', 'xterm/create_host', form, function (res) {
        loadT.close();
        bt.msg(res);
        if (res.status) {
          bt.msg({ status: true, msg: '登录成功！' });
          $('.layui-layer-shade').remove();
          $('.term_box_all').remove();
          Term.term.dispose();
          Term.close();
          web_shell();
        }
      });
    });
    $('.localhost-form-view [name="password"]')
      .keyup(function (e) {
        if (e.keyCode == 13) {
          $('.localhost-form-view > button').click();
        }
      })
      .focus();
  },
};

// 基于punblic的扩展方法，将插件需要的方法挂载到windows上
var win_mount = {
  /**
   * @description ajax 设置
   */
  ajaxSetup: function () {
    var my_headers = {};
    var request_token = window.vite_public_request_token;
    if (request_token) my_headers["x-http-token"] = request_token;
    var request_token_key =
      window.location.protocol.indexOf("https:") == 0
        ? "https_request_token"
        : "request_token";
    request_token_cookie = bt.get_cookie(request_token_key);
    if (request_token_cookie) {
      my_headers["x-cookie-token"] = request_token_cookie;
    }
		
    if (my_headers) {
      $.ajaxSetup({
        headers: my_headers,
        error: function (jqXHR, textStatus, errorThrown) {
          var pro = parseInt(bt.get_cookie("pro_end") || -1);
          var ltd = parseInt(bt.get_cookie("ltd_end") || -1);
          isBuy = false;
          if (pro == 0 || ltd > 0) isBuy = true; //付费
          if (jqXHR.responseText.indexOf("404 Not Found") > -1) return;
          if (!jqXHR.responseText) return;
          //会话失效时自动跳转到登录页面
          if (typeof jqXHR.responseText == "string") {
            if (
              (jqXHR.responseText.indexOf("/static/favicon.ico") != -1 &&
                jqXHR.responseText.indexOf("/static/img/qrCode.png") != -1) ||
              jqXHR.responseText.indexOf("<!DOCTYPE html>") === 0
            ) {
              window.location.href = "/login";
              return;
            }
          }
          if (typeof String.prototype.trim === "undefined") {
            String.prototype.trim = function () {
              return String(this).replace(/^\s+|\s+$/g, "");
            };
          }

          error_key =
            "We need to make sure this has a favicon so that the debugger does";
          error_find = jqXHR.responseText.indexOf(error_key);
          gl_error_body = jqXHR.responseText;
          if (
            jqXHR.status == 500 &&
            jqXHR.responseText.indexOf("运行时发生错误") != -1
          ) {
            if (
              jqXHR.responseText.indexOf("建议按顺序逐一尝试以下解决方案") != -1
            ) {
              error_msg = jqXHR.responseText
                .split("Error: ")[1]
                .split("</pre>")[0]
                .replace("面板运行时发生错误:", "")
                .replace("public.PanelError:", "")
                .trim();
            } else {
              error_msg =
                "<h3>" +
                jqXHR.responseText.split("<h3>")[1].split("</h3>")[0] +
                "</h3>";
              error_msg +=
                '<a style="color:dimgrey;font-size:none">' +
                jqXHR.responseText
                  .split('<h4 style="font-size: none;">')[1]
                  .split("</h4>")[0]
                  .replace("面板运行时发生错误:", "")
                  .replace("public.PanelError:", "")
                  .trim() +
                "</a>";
            }

            error_msg +=
              "<br><a class='btlink' onclick='showErrorMessage()'> >>点击查看详情</a>" +
              (isBuy
                ? "<span class='ml33'><span class='wechatEnterpriseService' style='vertical-align: middle;'></span><span class='btlink error_kefu_consult'>微信客服</span>"
                : "") +
              "</span>";
          } else if (jqXHR.responseText != "Internal Server Error") {
            showErrorMessage();
            return false;
          } else {
            return false;
          }
          $(".layui-layer-padding").parents(".layer-anim").remove();
          $(".layui-layer-shade").remove();
          setTimeout(function () {
            layer.open({
              title: false,
              content: error_msg,
              closeBtn: 2,
              btn: false,
              shadeClose: false,
              shade: 0.3,
              icon: 2,
              area: "600px",
              success: function () {
                $("pre").scrollTop(100000000000);

                $(".error_kefu_consult").click(function () {
                  bt.onlineService();
                });
              },
            });
          }, 100);
        },
			});
			$.ajaxPrefilter(function (options) {
				if (window.plugin_view.isDev()) {
					options.url = `/api/${options.url}`.replace('//', '/')
					if (options.type.toUpperCase() === 'POST') {
						options.data = $.param($.extend(options.data, window.plugin_view.getToken()));
					}
				}
      });
    }
  },

  /**
   * @description 显示错误信息
   * @param {string} gltxt 错误信息
   * @param {number} find 错误信息位置
   * @param {boolean} Buy 是否付费
   */
  showErrorMessage: function (gltxt, find, Buy) {
    if (gltxt) {
      //兼容面板设置
      error_find = find;
      gl_error_body = gltxt;
      isBuy = Buy;
    }
    var error_body;
    if (error_find != -1) {
      error_body = gl_error_body.split("<!--")[2].replace("-->", "");
      var tmp = error_body.split(
        "During handling of the above exception, another exception occurred:"
      );
      error_body = tmp[tmp.length - 1];
      error_msg =
        '<div class="pd20">\
        <h3 style="margin-bottom: 10px;">出错了，面板运行时发生错误！</h3>\
        <pre style="height:435px;word-wrap: break-word;white-space: pre-wrap;margin: 0 0 0px">' +
        error_body.trim() +
        '</pre>\
        <ul class="help-info-text err_project_ul" style="display:inline-block">\
          <li style="list-style: none;"><b>很抱歉，面板运行时意外发生错误，请尝试按以下顺序尝试解除此错误：</b></li>\
          <li style="list-style: none;">修复方案一：在[首页]右上角点击修复面板，并退出面板重新登录。</li>\
          <li style="list-style: none;">修复方案二：如上述尝试未能解除此错误，请截图此窗口到宝塔论坛发贴寻求帮助, 论坛地址：<a class="btlink" href="https://www.bt.cn/bbs" target="_blank">https://www.bt.cn/bbs</a><a href="javascript:;" class="btlink mlr15 copy_error">点击复制错误信息</a></li>\
          <li style="list-style: none;display:' +
        (isBuy ? "block" : "none") +
        '">修复方案三(<span style="color:#ff7300">推荐</span>)：使用微信扫描右侧二维码，联系技术客服。</li>\
        </ul>\
        <div style="position: relative;margin-top: 20px;margin-right: 40px;text-align: center;font-size: 12px;display:' +
        (isBuy ? "block" : "none") +
        '" class="pull-right">\
          <span id="err_kefu_img" style="padding: 5px;border: 1px solid #20a53a;display: inline-block;height: 113px;"><img src="/static/images/customer-qrcode.png" alt="qrcode" style="width:100px;width:100px;" /></span>\
          <div>【微信客服】</div>\
        </div>\
      </div>';
      $(".layui-layer-padding").parents(".layer-anim").remove();
      $(".layui-layer-shade").remove();
    } else {
      error_msg = gl_error_body;
    }

    setTimeout(function () {
      layer.open({
        type: 1,
        title: false,
        content: error_msg,
        closeBtn: 2,
        area: [
          "1200px",
          error_find != -1
            ? isBuy
              ? "670px"
              : "625px"
            : isBuy
            ? "750px"
            : "720px",
        ],
        btn: false,
        shadeClose: false,
        shade: 0.3,
        success: function (layers) {
          $("pre").scrollTop(100000000000);
          $(layers)
            .find(".layui-layer-content")
            .find(".err_project_ul li")
            .css("line-height", "32px");
          if (isBuy) $(".consult_project").show();

          $(layers)
            .find(".repairPanel")
            .unbind("click")
            .click(function () {
              layer.confirm(
                lan.index.rep_panel_msg,
                { title: lan.index.rep_panel_title, closeBtn: 2, icon: 3 },
                function () {
                  bt.system.rep_panel(function (rdata) {
                    if (rdata.status) {
                      bt.msg({ msg: lan.index.rep_panel_ok, icon: 1 });
                      return;
                    }
                    bt.msg(rdata);
                  });
                }
              );
            });
          $(layers)
            .find(".copy_error")
            .click(function () {
              var value = "";
              if (error_find != -1) {
                value = $(layers).find("pre").eq(0).text();
              } else {
                value =
                  $(layers).find("pre").eq(0).text() +
                  "\n" +
                  $(layers).find("pre").eq(1).text();
              }
              bt.pub.copy_pass(value);
            });
        },
      });
    }, 100);
  },

  /**
   * 
   * @description 生成随机字符串
   * @param {number} b 生成字符串长度
   * @returns
   */
  RandomStrPwd: function (b) {
    b = b || 32;
    var c = "AaBbCcDdEeFfGHhiJjKkLMmNnPpRSrTsWtXwYxZyz2345678";
    var a = c.length;
    while (true) {
      var d = "";
      for (i = 0; i < b; i++) {
        d += c.charAt(Math.floor(Math.random() * a));
      }
      if (/^(?:(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9]))/.test(d)) {
        return d;
      }
    }
  },

  /**
   * @description 转换文件大小
   * @param {number} a 大小
   * @returns 
   */
  ToSize:function(a) {
    var d = [' B', ' KB', ' MB', ' GB', ' TB', ' PB'];
    var e = 1024;
    for (var b = 0; b < d.length; b++) {
      if (a < e) {
        return (b == 0 ? a : a.toFixed(2)) + d[b];
      }
      a /= e;
    }
  },

  /**
   * @description 获取本地时间
   * @param {number} a 时间戳
   * @returns 
   */
  getLocalTime:function(a) {
    a = a.toString();
    if (a.length > 10) {
      a = a.substring(0, 10);
    }
    return new Date(parseInt(a) * 1000).format('yyyy/MM/dd hh:mm:ss');
  },

  /** 
   * @description 是否为中文字符
   * @param {string} b 字符
   * @returns 
   */
  isChineseChar:function(b) {
    var a = /[\u4E00-\u9FA5\uF900-\uFA2D]/;
    return a.test(b);
  },

  /**
   * @description 选择文件目录
   * @param {string} d 目录
   */
  ChangePath:function(d) {
    setCookie('SetId', d);
    setCookie('SetName', '');
    var c = layer.open({
      type: 1,
      area: '750px',
      title: lan.bt.dir,
      closeBtn: 2,
      shift: 5,
      shadeClose: false,
      content:
        "<div class='changepath'><div class='path-top'><button type='button' class='btn btn-default btn-sm' onclick='BackFile()'><span class='glyphicon glyphicon-share-alt'></span> " +
        lan.public.return +
        "</button><div class='place' id='PathPlace'>" +
        lan.bt.path +
        "：<span></span></div></div><div class='path-con'><div class='path-con-left'><dl><dt id='changecomlist' onclick='BackMyComputer()'>" +
        lan.bt.comp +
        "</dt></dl></div><div class='path-con-right'><ul class='default' id='computerDefautl'></ul><div class='file-list divtable'><table class='table table-hover' style='border:0 none'><thead><tr class='file-list-head'><th width='40%'>" +
        lan.bt.filename +
        "</th><th width='20%'>" +
        lan.bt.etime +
        "</th><th width='10%'>" +
        lan.bt.access +
        "</th><th width='10%'>" +
        lan.bt.own +
        "</th><th width='10%'></th></tr></thead><tbody id='tbody' class='list-list'></tbody></table></div></div></div></div><div class='getfile-btn' style='margin-top:0'><button type='button' class='btn btn-default btn-sm pull-left' onclick='CreateFolder()'>" +
        lan.bt.adddir +
        "</button><button type='button' class='btn btn-danger btn-sm mr5' onclick=\"layer.close(getCookie('ChangePath'))\">" +
        lan.public.close +
        "</button> <button type='button' class='btn btn-success btn-sm' onclick='GetfilePath()'>" +
        lan.bt.path_ok +
        '</button></div>',
      success:function(index, layero) {
        setCookie('ChangePath', layero);
        var b = $('#' + d).val();
        tmp = b.split('.');
        tmp = b.split('/');
        b = '';
        for (var a = 0; a < tmp.length - 1; a++) {
          b += '/' + tmp[a];
        }
        setCookie('SetName', tmp[tmp.length - 1]);
        b = b.replace(/\/\//g, '/');
        GetDiskList(b); // 获取磁盘列表
        ActiveDisk(); // 选中磁盘
      }
    });
  },
  
  /**
   * @description 获取文件目录
   * @param {string} b 目录
   * @returns 
   */
  GetDiskList:function(b) {
    var d = '';
    var a = '';
    var c = 'path=' + b + '&disk=True&showRow=500';
    bt.send('GetDir','files/GetDir', {path: b,disk: 'True',showRow: 500}, function (h) {
      if (h.DISK != undefined) {
        for (var f = 0; f < h.DISK.length; f++) {
          a += '<dd onclick="GetDiskList(\'' + h.DISK[f].path + "')\"><span class='glyphicon glyphicon-hdd'></span>&nbsp;<span>" + h.DISK[f].path + '</span></div></dd>';
        }
        $('#changecomlist').html(a);
      }
      for (var f = 0; f < h.DIR.length; f++) {
        var g = h.DIR[f].split(';');
        var e = g[0];
        if (e.length > 20) {
          e = e.substring(0, 20) + '...';
        }
        if (isChineseChar(e)) {
          if (e.length > 10) {
            e = e.substring(0, 10) + '...';
          }
        }
        d +=
          '<tr><td onclick="GetDiskList(\'' +
          h.PATH +
          '/' +
          g[0] +
          "')\" title='" +
          g[0] +
          "'><span class='glyphicon glyphicon-folder-open'></span>" +
          e +
          '</td><td>' +
          getLocalTime(g[2]) +
          '</td><td>' +
          g[3] +
          '</td><td>' +
          g[4] +
          "</td><td><span class='delfile-btn' onclick=\"NewDelFile('" +
          h.PATH +
          '/' +
          g[0] +
          '\')">X</span></td></tr>';
      }
      if (h.FILES != null && h.FILES != '') {
        for (var f = 0; f < h.FILES.length; f++) {
          var g = h.FILES[f].split(';');
          var e = g[0];
          if (e.length > 20) {
            e = e.substring(0, 20) + '...';
          }
          if (isChineseChar(e)) {
            if (e.length > 10) {
              e = e.substring(0, 10) + '...';
            }
          }
          d +=
            "<tr><td title='" +
            g[0] +
            "'><span class='glyphicon glyphicon-file'></span><span>" +
            e +
            '</span></td><td>' +
            getLocalTime(g[2]) +
            '</td><td>' +
            g[3] +
            '</td><td>' +
            g[4] +
            '</td><td></td></tr>';
        }
      }
      $('.default').hide();
      $('.file-list').show();
      $('#tbody').html(d);
      if (h.PATH.substr(h.PATH.length - 1, 1) != '/') {
        h.PATH += '/';
      }
      $('#PathPlace').find('span').html(h.PATH);
      ActiveDisk();
      return;
    });
  },
  
  /**
   * @description 创建文件夹
   */
  CreateFolder:function() {
    var a =
      "<tr><td colspan='2'><span class='glyphicon glyphicon-folder-open'></span> <input id='newFolderName' class='newFolderName' type='text' value=''></td><td colspan='3'><button id='nameOk' type='button' class='btn btn-success btn-sm'>" +
      lan.public.ok +
      "</button>&nbsp;&nbsp;<button id='nameNOk' type='button' class='btn btn-default btn-sm'>" +
      lan.public.cancel +
      '</button></td></tr>';
    if ($('#tbody tr').length == 0) {
      $('#tbody').append(a);
    } else {
      $('#tbody tr:first-child').before(a);
    }
    $('.newFolderName').focus();
    $('#nameOk').click(function () {
      var c = $('#newFolderName').val();
      var b = $('#PathPlace').find('span').text();
      newTxt = b.replace(new RegExp(/(\/\/)/g), '/') + c;
      var d = 'path=' + newTxt;
      bt.send('CreateDir','files/CreateDir', {path: newTxt}, function (e) {
        if (e.status == true) {
          layer.msg(e.msg, {
            icon: 1,
          });
        } else {
          layer.msg(e.msg, {
            icon: 2,
          });
        }
        $('#btn_refresh').click()
      });
    });
    $('#nameNOk').click(function () {
      $(this).parents('tr').remove();
    });
  },
  
  /**
   * @description 删除文件
   * @param {string} c 文件
   */
  NewDelFile:function(c) {
    var a = $('#PathPlace').find('span').text();
    newTxt = c.replace(new RegExp(/(\/\/)/g), '/');
    var b = 'path=' + newTxt + '&empty=True';
    bt.send('DeleteDir','files/DeleteDir', {path: newTxt,empty: 'True'}, function (d) {
      if (d.status == true) {
        layer.msg(d.msg, {
          icon: 1,
        });
      } else {
        layer.msg(d.msg, {
          icon: 2,
        });
      }
      this.get_file_list(a);
    });
  },
  
  /**
   * @description 磁盘列表
   */
  ActiveDisk:function() {
    var a = $('#PathPlace').find('span').text().substring(0, 1);
    switch (a) {
      case 'C':
        $('.path-con-left dd:nth-of-type(1)').css('background', '#eee').siblings().removeAttr('style');
        break;
      case 'D':
        $('.path-con-left dd:nth-of-type(2)').css('background', '#eee').siblings().removeAttr('style');
        break;
      case 'E':
        $('.path-con-left dd:nth-of-type(3)').css('background', '#eee').siblings().removeAttr('style');
        break;
      case 'F':
        $('.path-con-left dd:nth-of-type(4)').css('background', '#eee').siblings().removeAttr('style');
        break;
      case 'G':
        $('.path-con-left dd:nth-of-type(5)').css('background', '#eee').siblings().removeAttr('style');
        break;
      case 'H':
        $('.path-con-left dd:nth-of-type(6)').css('background', '#eee').siblings().removeAttr('style');
        break;
      default:
        $('.path-con-left dd').removeAttr('style');
    }
  },
  
  /**
   * @description 返回我的电脑
   */
  BackMyComputer:function () {
    $('.default').show();
    $('.file-list').hide();
    $('#PathPlace').find('span').html('');
    ActiveDisk();
  },

  /**
   * @description 返回上级目录
   */
  BackFile:function() {
    var c = $('#PathPlace').find('span').text();
    if (c.substr(c.length - 1, 1) == '/') {
      c = c.substr(0, c.length - 1);
    }
    var d = c.split('/');
    var a = '';
    if (d.length > 1) {
      var e = d.length - 1;
      for (var b = 0; b < e; b++) {
        a += d[b] + '/';
      }
      GetDiskList(a.replace('//', '/'));
    } else {
      a = d[0];
    }
  },
  
  /**
   * @description 获取文件路径
   */
  GetfilePath:function() {
    var a = $('#PathPlace').find('span').text();
    a = a.replace(new RegExp(/(\\)/g), '/');
		setCookie('path_dir_change', a);
    $('#' + getCookie('SetId')).val(a + getCookie('SetName'));
    layer.close(getCookie('ChangePath'));
  },
  
  /**
   * @description 设置cookie
   * @param {string} a cookie名称
   * @param {string} c cookie值
   */
  setCookie:function(a, c) {
    bt.set_cookie(a, c);
  },
  
  /**
   * @description 获取cookie
   * @param {string} b cookie名称
   * @returns 
   */
  getCookie:function(b) {
    return bt.get_cookie(b);
  },

  /**
   * @description 打开路径
   * @param {string} a 路径
   */
  openPath:function(a) {
    setCookie('Path', a);
    bt.refreshMain(window.location.origin + '/files')
  },

  /**
   * @description 转换文件配置
   * @param {string} fileName 文件名
   */
  fileSuffixType:function(fileName) {
    var splitList = fileName.split('.');
    var suffix = splitList[splitList.length - 1];
    var modeList = {"Apache_Conf":["^htaccess|^htgroups|^htpasswd|^conf|htaccess|htgroups|htpasswd"],"BatchFile":["bat|cmd"],"C_Cpp":["cpp|c|cc|cxx|h|hh|hpp|ino"],"CSharp":["cs"],"CSS":["css"],"Dockerfile":["^Dockerfile"],"golang":["go"],"HTML":["html|htm|xhtml|vue|we|wpy"],"Java":["java"],"JavaScript":["js|jsm|jsx"],"JSON":["json"],"JSP":["jsp"],"LESS":["less"],"Lua":["lua"],"Makefile":["^Makefile|^GNUmakefile|^makefile|^OCamlMakefile|make"],"Markdown":["md|markdown"],"MySQL":["mysql"],"Nginx":["nginx|conf"],"INI":["ini|conf|cfg|prefs"],"ObjectiveC":["m|mm"],"Perl":["pl|pm"],"Perl6":["p6|pl6|pm6"],"pgSQL":["pgsql"],"PHP_Laravel_blade":["blade.php"],"PHP":["php|inc|phtml|shtml|php3|php4|php5|phps|phpt|aw|ctp|module"],"Powershell":["ps1"],"Python":["py"],"R":["r"],"Ruby":["rb|ru|gemspec|rake|^Guardfile|^Rakefile|^Gemfile"],"Rust":["rs"],"SASS":["sass"],"SCSS":["scss"],"SH":["sh|bash|^.bashrc"],"SQL":["sql"],"SQLServer":["sqlserver"],"Swift":["swift"],"Text":["txt"],"Typescript":["ts|typescript|str"],"VBScript":["vbs|vb"],"Verilog":["v|vh|sv|svh"],"XML":["xml|rdf|rss|wsdl|xslt|atom|mathml|mml|xul|xbl|xaml"],"YAML":["yaml|yml"],"Compress":["tar|zip|7z|rar|gz|arj|z"],"images":["icon|jpg|jpeg|png|bmp|gif|tif|emf"]}
    var mode = '';
    for (var key in modeList) {
      var reg = new RegExp(modeList[key].join('|'), 'i');
      if (reg.test(suffix)) mode = key;
      console.log(reg);
    }
    return mode;
  },

  /**
   * @description 编辑器文件
   * @param {number} k 类型 ，1：读取文件，0：显示编辑器视图
   * @param {string} f 文件路径
   */
  OnlineEditFile:function(k, f) {
    bt.pub.on_edit_file(k, f, fileSuffixType(f))
  },

  /**
   * @description 安全信息
   * @param {string} j 标题
   * @param {string} h 提示信息
   * @param {function} g 回调函数
   * @param {string} f 附加信息
   */
  SafeMessage:function(j, h, g, f) {
    if (f == undefined)  f = '';
    var d = Math.round(Math.random() * 9 + 1);
    var c = Math.round(Math.random() * 9 + 1);
    var e = '';
    var checked_name = [];
    e = d + c;
    sumtext = d + ' + ' + c;
    setCookie('vcodesum', e);
    var mess = layer.open({
      type: 1,
      title: j,
      area: '350px',
      closeBtn: 2,
      shadeClose: true,
      content:
        "<div class='bt-form webDelete pd20 pb70'>" +
        '<p>' +  h + '</p>' +
        f +
        "<div class='vcode'>" + lan.bt.cal_msg + "<span class='text'>" + sumtext + '</span>=' +
        "<input type='number' id='vcodeResult' value=''></div>" +
        "<div class='bt-form-submit-btn'><button type='button' class='btn btn-danger btn-sm bt-cancel'>" +
        lan.public.cancel +
        '</button>' +
        " <button type='button' id='toSubmit' class='btn btn-success btn-sm' >" +
        lan.public.ok +
        '</button>' +
        '</div></div>',
      success: function (index) {
        // 全选操作
        $('#change_all').prop('checked', true);
        $('#file_check').click(function () {
          $('input[name=skip_checked]').prop('checked', $(this).prop('checked'));
        });
        $('#file_check').click();
        $('input[name=skip_checked]').change(function () {
          var _check_length = $('.webDelete tbody').find('input:checked').length;
          var _all_input = $('.webDelete tbody').find('input').length;
          var check_value = _all_input == _check_length ? true : false;
          $('#file_check').prop('checked', check_value);
        });
      },
    });
    $('#vcodeResult')
      .focus()
      .keyup(function (a) {
        if (a.keyCode == 13) {
          $('#toSubmit').click();
        }
      });
    $('.bt-cancel').click(function () {
      layer.close(mess);
    });
    $('#toSubmit').click(function () {
			var a = $('#vcodeResult').val().replace(/ /g, '');
			console.log(a);
      if (a == undefined || a == '') {
        layer.msg('请正确输入计算结果!');
        return;
      }
      if (a != getCookie('vcodesum')) {
        layer.msg('请正确输入计算结果!');
        return;
      }
      layer.close(mess);
      var _check_length = $('.webDelete tbody').find('input:checked').length;
      for (var k = 0; k < _check_length; k++) {
        checked_name.push(String($('.webDelete tbody').find('input:checked').eq(k).data('name')));
      }
      g(checked_name);
    });
  },

  /**
   * @description 加载脚本
   * @param {array} arry 脚本列表
   * @param {object} param 参数
   * @param {function} callback 回调函数
   */
  loadScript:function(arry, param, callback) {
    var ready = 0;
    if (typeof param === 'function') callback = param;
    for (var i = 0; i < arry.length; i++) {
      if (!Array.isArray(bt['loadScript'])) bt['loadScript'] = [];
      if (!is_file_existence(arry[i], true)) {
        if (arry.length - 1 === i && callback) callback();
        continue;
      }
      var script = document.createElement('script'),_arry_split = arry[i].split('/');
      script.type = 'text/javascript';
      if (typeof callback != 'undefined') {
        if (script.readyState) {
          (function (i) {
            script.onreadystatechange = function () {
              if (script.readyState == 'loaded' || script.readyState == 'complete') {
                script.onreadystatechange = null;
                bt['loadScript'].push(arry[i]);
                ready++;
              }
            };
          })(i);
        } else {
          (function (i) {
            script.onload = function () {
              bt['loadScript'].push(arry[i]);
              ready++;
            };
          })(i);
        }
      }
      script.src = arry[i];
      document.body.appendChild(script);
    }
    var time = setInterval(function () {
      if (ready === arry.length) {
        clearTimeout(time);
        callback();
      }
    }, 10);
  },

  /**
   * @description 服务管理
   * @param {string} a 服务名称
   * @param {string} b 服务类型
   */
  ServiceAdmin:function(a, b) {
    if (!isNaN(a)) {
      a = 'php-fpm-' + a;
    }
    a = a.replace('_soft', '');
    var c = 'name=' + a + '&type=' + b;
    var d = '';
  
    switch (b) {
      case 'stop':
        d = lan.bt.stop;
        break;
      case 'start':
        d = lan.bt.start;
        break;
      case 'restart':
        d = lan.bt.restart;
        break;
      case 'reload':
        d = lan.bt.reload;
        break;
    }
    layer.confirm(
      lan.get('service_confirm', [d, a]),
      {
        icon: 3,
        closeBtn: 2,
      },
      function () {
        var e = layer.msg(lan.get('service_the', [d, a]), {
          icon: 16,
          time: 0,
        });
        bt.send('ServiceAdmin','system/ServiceAdmin', {name: a,type: b}, function (g) {
          layer.close(e);
  
          var f = g.status ? lan.get('service_ok', [a, d]) : lan.get('service_err', [a, d]);
          layer.msg(f, {
            icon: g.status ? 1 : 2,
          });
          if (b != 'reload' && g.status == true) {
            setTimeout(function () {
              window.location.reload();
            }, 1000);
          }
          if (!g.status) {
            layer.msg(g.msg, {
              icon: 2,
              time: 0,
              shade: 0.3,
              shadeClose: true,
            });
          }
        }).error(function () {
          layer.close(e);
          layer.msg(lan.public.success, {
            icon: 1,
          });
        });
      }
    );
  },

  /**
   * @description 获取PHP版本
   * @param {string} codename 代码名称
   * @param {string} versions 版本
   * @param {string} title 标题
   * @param {string} enable_functions 函数
   */
  onekeyCodeSite:function(codename, versions, title, enable_functions) {
    $.post('/site?action=GetPHPVersion', function (rdata) {
      var php_version = "";
      var n = 0;
      for (var i = rdata.length - 1; i >= 0; i--) {
        if (versions.indexOf(rdata[i].version) != -1) {
          php_version += "<option value='" + rdata[i].version + "'>" + rdata[i].name + "</option>";
          n++;
        }
      }
      if (n == 0) {
        layer.msg('缺少被支持的PHP版本，请安装!', {
          icon: 5
        });
        return;
      }
      var default_path = bt.get_cookie('sites_path');
      if (!default_path) default_path = '/www/wwwroot';
      var con = '<form class="bt-form pd20 pb70" id="addweb">\
            <div class="line"><span class="tname">域名</span>\
              <div class="info-r c4"><textarea id="mainDomain" class="bt-input-text" name="webname_1" style="width:398px;height:100px;line-height:22px"></textarea>\
                <div class="placeholder c9" style="top:10px;left:10px">每行填写一个域名，默认为80端口<br>泛解析添加方法 *.domain.com<br>如另加端口格式为 www.domain.com:88</div>\
              </div>\
            </div>\
            <div class="line"><span class="tname">备注</span>\
              <div class="info-r c4"><input id="Wbeizhu" class="bt-input-text" name="ps" placeholder="网站备注" style="width:398px" type="text"> </div>\
            </div>\
            <div class="line"><span class="tname">根目录</span>\
              <div class="info-r c4"><input id="inputPath" class="bt-input-text mr5" name="path" value="' + default_path + '" placeholder="网站根目录" style="width:398px" type="text"><span class="glyphicon glyphicon-folder-open cursor" onclick="bt.select_path(\'inputPath\',\'dir\')"></span> </div>\
            </div>\
            <div class="line"><span class="tname">数据库</span>\
              <div class="info-r c4">\
                <input id="datauser" class="bt-input-text" name="datauser" placeholder="用户名/数据库名" style="width:190px;margin-right:13px" type="text">\
                <input id="datapassword" class="bt-input-text" name="datapassword" placeholder="密码" style="width:190px" type="text">\
              </div>\
            </div>\
            <div class="line"><span class="tname">源码</span>\
              <input class="bt-input-text mr5 disable" name="code" style="width:190px" value="' + title + '" disabled>\
              <span class="c9">准备为你部署的源码程序</span>\
            </div>\
            <div class="line"><span class="tname">PHP版本</span>\
              <select class="bt-input-text mr5" name="version" id="c_k3" style="width:100px">\
                ' + php_version + '\
              </select>\
              <span class="c9">请选择源码程序支持的php版本</span>\
            </div>\
            <div class="bt-form-submit-btn">\
              <button type="button" class="btn btn-danger btn-sm onekeycodeclose">取消</button>\
              <button type="button" class="btn btn-success btn-sm" onclick="AddSite(\'' + codename + '\',\'' + title + '\')">提交</button>\
            </div>\
          </from>';
      add = layer.open({
        type: 1,
        title: "宝塔一键部署【" + title + '】',
        area: '560px',
        closeBtn: 2,
        shadeClose: false,
        content: con
      });
  
      if (enable_functions.length > 2) {
        layer.msg("<span style='color:red'>注意：部署此项目，以下函数将被解禁:<br> " + enable_functions + "</span>", {
          icon: 7,
          time: 10000
        });
      }
      var placeholder = "<div class='placeholder c9' style='top:10px;left:10px'>每行填写一个域名，默认为80端口<br>泛解析添加方法 *.domain.com<br>如另加端口格式为 www.domain.com:88</div>";
      $(".onekeycodeclose").click(function () {
        layer.close(add);
      });
      $('#mainDomain').after(placeholder);
      $(".placeholder").click(function () {
        $(this).hide();
        $('#mainDomain').focus();
      })
      $('#mainDomain').focus(function () {
        $(".placeholder").hide();
      });
  
      $('#mainDomain').blur(function () {
        if ($(this).val().length == 0) {
          $(".placeholder").show();
        }
      });
      //FTP账号数据绑定域名
      $('#mainDomain').on('input', function () {
        var defaultPath = bt.get_cookie('sites_path');
        if (!defaultPath) defaultPath = '/www/wwwroot';
        var array;
        var res, ress;
        var str = $(this).val();
        var len = str.replace(/[^\x00-\xff]/g, "**").length;
        array = str.split("\n");
        ress = array[0].split(":")[0];
        res = ress.replace(new RegExp(/([-.])/g), '_');
        if (res.length > 15) res = res.substr(0, 15);
        if ($("#inputPath").val().substr(0, defaultPath.length) == defaultPath) $("#inputPath").val(defaultPath + '/' + array[0].replace(new RegExp(/([-.])/g), '_').replace(/:/g,'_'));
        if (!isNaN(res.substr(0, 1))) res = "sql" + res;
        if (res.length > 15) res = res.substr(0, 15);
        $("#Wbeizhu").val(ress);
        $("#datauser").val(res);
      })
      $('#Wbeizhu').on('input', function () {
        var str = $(this).val();
        var len = str.replace(/[^\x00-\xff]/g, "**").length;
        if (len > 20) {
          str = str.substring(0, 20);
          $(this).val(str);
          layer.msg('不要超出20个字符', {
            icon: 0
          });
        }
      })
      //获取当前时间时间戳，截取后6位
      var timestamp = new Date().getTime().toString();
      var dtpw = timestamp.substring(7);
      $("#datauser").val("sql" + dtpw);
      $("#datapassword").val(bt.get_random(10));
    });
  },

  /**
   * @description html转义
   * @param {string} val 值
   * @returns 
   */
  escapeHTML:function(val) {
    val = "" + val;
    return val.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, '&quot;').replace(/'/g, "‘").replace(/\(/g, "&#40;").replace(/\&#60;/g, "&lt;").replace(/\&#62;/g, "&gt;").replace(/`/g, "&#96;").replace(/=/g, "＝");
  },
  
  /**
   * @description 调用终端界面
   */
  web_shell:function() {
    Term.run()
  },
    /**
   * @description 安装告警模块视图跳转
   * @param {String} type 模块类型
   * @param {Object} el 刷新的元素类名
   * @param {function} callback 配置成功后的回调函数
   */
  openAlertModuleInstallView:function(type, el, callback) {
    bt_tools.send({ url: '/config?action=get_msg_configs', data: {} }, function (_configData) {
      switch (type) {
        case 'mail':
          renderMailConfigView(_configData[type], el, callback);
          break;
        case 'dingding':
        case 'feishu':
        case 'weixin':
          renderAlertUrlTypeChannelView(_configData[type], el, callback);
          break;
        case 'wx_account':
        case 'sms':
          alertOtherTypeInstall(_configData[type], el, callback);
          break;
      }
    });
  },
  /**
   * @description 渲染邮箱配置视图
   */
  renderMailConfigView:function(data, el, callback) {
    layer.open({
      type: 1,
      closeBtn: 2,
      title: '发送者配置',
      area: ['470px', '400px'],
      btn: ['保存', '取消'],
      skin: 'alert-send-view',
      content:
        '<div class="bt-form pd15">\
                    <div class="line">\
                            <span class="tname">发送人邮箱</span>\
                            <div class="info-r">\
                                    <input name="sender_mail_value" class="bt-input-text mr5" type="text" style="width: 300px">\
                            </div>\
                    </div>\
                    <div class="line">\
                            <span class="tname">SMTP密码</span>\
                            <div class="info-r">\
                                    <input name="sender_mail_password" class="bt-input-text mr5" type="password" style="width: 300px">\
                            </div>\
                    </div>\
                    <div class="line">\
                            <span class="tname">SMTP服务器</span>\
                            <div class="info-r">\
                                    <input name="sender_mail_server" class="bt-input-text mr5" type="text" style="width: 300px">\
                            </div>\
                    </div>\
                    <div class="line">\
                            <span class="tname">端口</span>\
                            <div class="info-r">\
                                    <input name="sender_mail_port" class="bt-input-text mr5" type="text" style="width: 300px">\
                            </div>\
                    </div>\
                    <ul class="help-info-text c7">\
                            <li>推荐使用465端口，协议为SSL/TLS</li>\
                            <li>25端口为SMTP协议，587端口为STARTTLS协议</li>\
                            <li><a href="' +
        data.help +
        '" target="_blank" class="btlink">配置教程</a></li>\
                    </ul>\
            </div>',
      success: function () {
        if (!$.isEmptyObject(data) && !$.isEmptyObject(data.data.send)) {
          var send = data.data.send,
            mail_ = send.qq_mail || '',
            stmp_pwd_ = send.qq_stmp_pwd || '',
            hosts_ = send.hosts || '',
            port_ = send.port || '';

          $('input[name=sender_mail_value]').val(mail_);
          $('input[name=sender_mail_password]').val(stmp_pwd_);
          $('input[name=sender_mail_server]').val(hosts_);
          $('input[name=sender_mail_port]').val(port_);
        } else {
          $('input[name=sender_mail_port]').val('465');
        }
      },
      yes: function (indexs) {
        var _email = $('input[name=sender_mail_value]').val(),
          _passW = $('input[name=sender_mail_password]').val(),
          _server = $('input[name=sender_mail_server]').val(),
          _port = $('input[name=sender_mail_port]').val();

        if (_email == '') return layer.msg('邮箱地址不能为空！', { icon: 2 });
        if (_passW == '') return layer.msg('STMP密码不能为空！', { icon: 2 });
        if (_server == '') return layer.msg('STMP服务器地址不能为空！', { icon: 2 });
        if (_port == '') return layer.msg('请输入有效的端口号', { icon: 2 });

        if (!data.setup) {
          bt_tools.send(
            { url: '/config?action=install_msg_module&name=' + data.name, data: {} },
            function (res) {
              if (res.status) {
                bt_tools.send(
                  { url: '/config?action=set_msg_config&name=mail', data: { send: 1, qq_mail: _email, qq_stmp_pwd: _passW, hosts: _server, port: _port } },
                  function (configM) {
                    if (configM.status) {
                      layer.close(indexs);
                      layer.msg(configM.msg, {
                        icon: configM.status ? 1 : 2,
                      });
                      if ($('.alert-view-box').length >= 0) $('.alert-view-box .tab-nav-border span:eq(1)').click();
                      if ($('.content_box.news-channel').length > 0) {
                        $('.bt-w-menu p').eq(0).click();
                      }
                      if (el) $(el).click();
                      if (callback) callback();
                    }
                  },
                  '设置邮箱配置'
                );
              } else {
                layer.msg(res.msg, { icon: 2 });
              }
            },
            '创建' + data.title + '模块'
          );
        } else {
          bt_tools.send(
            {
              url: '/config?action=set_msg_config&name=mail',
              data: {
                send: 1,
                qq_mail: _email,
                qq_stmp_pwd: _passW,
                hosts: _server,
                port: _port,
              },
            },
            function (configM) {
              if (configM.status) {
                layer.close(indexs);
                layer.msg(configM.msg, {
                  icon: configM.status ? 1 : 2,
                });
              }
              if ($('.content_box.news-channel').length > 0) {
                $('.bt-w-menu p').eq(0).click();
              }
              if (el) $(el).click();
              if (callback) callback();
            },
            '设置邮箱配置'
          );
        }
      },
    });
  },
/**
 * @description 渲染url通道方式视图
 */
  renderAlertUrlTypeChannelView:function(data, el, callback) {
    var isEmpty = $.isEmptyObject(data.data);
    layer.open({
      type: 1,
      closeBtn: 2,
      title: data['title'] + '机器人配置',
      area: ['520px', '345px'],
      btn: ['保存', '取消'],
      skin: 'alert-send-view',
      content:
        '<div class="pd15 bt-form">\
                <div class="line"><span class="tname">名称</span><div class="info-r"><input type="text" name="chatName" value="' +
        (isEmpty ? '' : data.data.list.default.title) +
        '" class="bt-input-text mr10 " style="width:350px;" placeholder="机器人名称或备注"></div></div>\
                <div class="line">\
                <span class="tname">URL</span><div class="info-r">\
                    <textarea name="channel_url_value" class="bt-input-text mr5" type="text" placeholder="请输入' +
        data.title +
        '机器人url" style="width: 350px; height:120px; line-height:20px"></textarea>\
                </div>\
                <ul class="help-info-text c7">\
                        <li><a class="btlink" href="' +
        data.help +
        '" target="_blank">如何创建' +
        data.title +
        '机器人</a></li>\
                </ul>\
                </div></div>',
      success: function () {
        if (!$.isEmptyObject(data.data)) {
          var url = data['data'][data.name + '_url'] || '';
          $('textarea[name=channel_url_value]').val(url);
        }
      },
      yes: function (indexs) {
        var _index = $('.alert-view-box span.on').index();
        var _url = $('textarea[name=channel_url_value]').val(),
          _name = $('input[name=chatName]').val();
        if (_name == '') return layer.msg('请输入机器人名称或备注', { icon: 2 });
        if (_url == '') return layer.msg('请输入' + data.title + '机器人url', { icon: 2 });
        if (!data.setup) {
          bt_tools.send(
            { url: '/config?action=install_msg_module&name=' + data.name, data: {} },
            function (res) {
              if (res.status) {
                setTimeout(function () {
                  bt_tools.send(
                    {
                      url: '/config?action=set_msg_config&name=' + data.name,
                      data: {
                        url: _url,
                        title: _name,
                        atall: 'True',
                      },
                    },
                    function (rdata) {
                      layer.close(indexs);
                      layer.msg(rdata.msg, {
                        icon: rdata.status ? 1 : 2,
                      });
                      if ($('.alert-view-box').length >= 0) {
                        $('.alert-view-box .tab-nav-border span:eq(' + _index + ')').click();
                      }
                      if ($('.content_box.news-channel').length > 0) {
                        $('.bt-w-menu p').eq(0).click();
                      }
                      if (el) $(el).click();
                      if (callback) callback();
                    },
                    '设置' + data.title + '配置'
                  );
                }, 100);
              } else {
                layer.msg(res.msg, { icon: 2 });
              }
            },
            '创建' + data.title + '模块'
          );
        } else {
          bt_tools.send(
            {
              url: '/config?action=set_msg_config&name=' + data.name,
              data: {
                url: _url,
                title: _name,
                atall: 'True',
              },
            },
            function (rdata) {
              layer.close(indexs);
              layer.msg(rdata.msg, {
                icon: rdata.status ? 1 : 2,
              });
              if ($('.alert-view-box').length >= 0) {
                $('.alert-view-box .tab-nav-border span:eq(' + _index + ')').click();
              }
              if ($('.content_box.news-channel').length > 0) {
                $('.bt-w-menu p').eq(0).click();
              }
              if (el) $(el).click();
              if (callback) callback();
            },
            '设置' + data.title + '配置'
          );
        }
      },
    });
  },

  /**
 * @description 微信公众号、短信模块安装
 */
  alertOtherTypeInstall:function(data, el, callback) {
    if (!data.setup) {
      bt_tools.send(
        { url: '/config?action=install_msg_module&name=' + data.name, data: {} },
        function (res) {
          layer.msg(res.msg, {
            icon: res.status ? 1 : 2,
          });
          if (!res.status) return false;
          if (data.name === 'wx_account') {
            var _data = data.data;
            if (!_data.is_subscribe || !_data.is_bound) renderAccountAlertView();
          }
          if ($('.alert-view-box').length >= 0) {
            var _index = $('.alert-view-box span.on').index();
            $('.alert-view-box .tab-nav-border span:eq(' + _index + ')').click();
          }
          if ($('.content_box.news-channel').length > 0) {
            $('.bt-w-menu p').eq(0).click();
          }
          if (el) $(el).click();
          if (callback) callback();
        },
        '创建' + data.title + '模块'
      );
    } else if (data.name === 'wx_account') {
      renderAccountAlertView(el);
    }
  },

  /**
 * @description 微信公众号
 */
  renderAccountAlertView:function(el, callback) {
    layer.open({
      type: 1,
      closeBtn: 2,
      title: '微信公众号',
      area: ['420px', '280px'],
      skin: 'BTwxAccountView',
      content:
        '<div class="wx_account_box pd15"><div class="bt-form">\
            <div class="form-item">\
                <div class="form-label">绑定微信公众号</div>\
                <div class="form-content">\
                    <div class="bind_account hide">\
                        <span style="color: #20a53a;">已绑定</span>\
                        <span style="color: red;cursor: pointer;margin-left:10px" class="unbind-wx">[解绑]</span>\
                    </div>\
                    <div class="nobind_account">\
                        <span class="red">未绑定</span>\
                        <button class="btn btn-xs btn-success btn-bind-account">立即绑定</button>\
                    </div>\
                </div>\
            </div>\
            <div class="form-item">\
                <div class="form-label">绑定微信账号</div>\
                <div class="form-content">\
                    <div class="bind_wechat hide">\
                        <div class="userinfo"></div>\
                    </div>\
                    <div class="nobind_wechat">\
                        <span class="red">未绑定</span>\
                    </div>\
                    <button class="btn btn-xs btn-success btn-bind-wechat">立即绑定</button>\
                </div>\
            </div>\
            <div class="form-item hide">\
                <div class="form-label">今日剩余发送次数</div>\
                <div class="form-content">\
                    <span class="account_remaining">0</span>\
                    <button class="btn btn-xs btn-success btn-send-test">发送测试消息</button>\
                </div>\
            </div>\
        </div>\
        <ul class="help-info-text c7">\
            <li>没有绑定微信公众号无法接收面板告警消息</li>\
            <li>当前为体验版,限制每个宝塔账号发送频率100条/天</li>\
        </ul>\
        </div>',
      success: function () {
        getWxAccountConfig(el, callback);
        // 发送测试信息
        $('.btn-send-test').click(function () {
          bt_tools.send(
            { url: '/config?action=get_msg_fun', data: { module_name: 'wx_account', fun_name: 'push_data', msg: '发送测试信息' } },
            function (res) {
              if (res.status) {
                var num = Number($('.account_remaining').html());
                if (!isNaN(num)) {
                  num -= 1;
                  $('.account_remaining').text(num);
                }
              }
            },
            '测试信息'
          );
        });
        wxAccountBind(el, callback);
        $('.unbind-wx').click(function(){
          bt.compute_confirm({title: '解绑微信公众号', msg: '风险操作，解绑微信公众号后，所有使用绑定该微信公众号账号的机器，将会全部解绑，继续操作？'},function (index) {
            bt_tools.send({
              url:'panel/push/unbind_wx_account'
            },function(res){
              bt.msg({msg:res.msg.res,status:res.msg.success})
              getWxAccountConfig(el, callback);

            })
          })
        })
      },
    });
  },

  /**
 * @description 获取微信公众号配置
 */
  getWxAccountConfig:function(el, callback) {
    bt_tools.send(
      { url: '/config?action=get_msg_fun', data: { module_name: 'wx_account', fun_name: 'get_web_info' } },
      function (res) {
        if (res.status === false) {
          bt.msg(res);
        }
        var data = res && res.msg && res.msg.res ? res.msg.res : {};
        // 绑定微信账号
        if (data.is_bound === 1) {
          $('.userinfo').html('<img src="' + data.head_img + '" /><div>' + data.nickname + '</div>');
          $('.btn-bind-wechat').text('更换微信账号');
          $('.bind_wechat').removeClass('hide');
          $('.nobind_wechat').addClass('hide');
        } else {
          $('.btn-bind-wechat').text('立即绑定');
          $('.bind_wechat').addClass('hide');
          $('.nobind_wechat').removeClass('hide');
        }
        // 判断是否绑定公众号
        if (data.is_subscribe === 1) {
          $('.bind_account').removeClass('hide');
          $('.nobind_account').addClass('hide');
          if ($('.content_box.news-channel').length > 0) {
            $('.bt-w-menu p').eq(0).click();
          }
          if (el) $(el).click();
          if (callback) callback();
        } else {
          $('.bind_account').addClass('hide');
          $('.nobind_account').removeClass('hide');
        }
        // 判断是否存在发送消息
        if (data.remaining === undefined) {
          $('.account_remaining').parents('.form-item').addClass('hide');
        } else {
          $('.account_remaining').parents('.form-item').removeClass('hide');
          $('.account_remaining').text(data.remaining);
        }
      },
      '获取绑定信息'
    );
  },

  /**
   * @description 绑定微信公众号
   * @param {element} el 元素
   * @param {function} callback 回调函数 
   */
  wxAccountBind:function(el, callback) {
    // 绑定微信公众号
    $('.btn-bind-account').click(function () {
      var that = this;
      layer.open({
        type: 1,
        area: '280px',
        title: '绑定微信公众号',
        content:
          '<div class="bind_wechat_box pd20">\
                  <div class="text-center">微信扫码</div>\
                  <div class="mt10">\
                      <div class="qrcode" style="text-align: center;">\
                          <img src="https://www.bt.cn/Public/img/bt_wx.jpg" style="width: 180px;"/>\
                      </div>\
                  </div>\
              </div>',
        cancel: function () {
          if ($(that).hasClass('bterror')) {
            $('.alert-view-box span.on').click();
          } else {
            getWxAccountConfig(el, callback);
          }
        },
      });
    });
    // 更换绑定账号
    $('.btn-bind-wechat').click(function () {
      var that = this;
      layer.open({
        type: 1,
        area: '280px',
        title: '绑定微信账号',
        content:
          '<div class="bind_wechat_box pd20">\
                        <div class="text-center">微信扫码</div>\
                        <div class="mt10">\
                            <div class="qrcode" id="wechat-qrcode" style="text-align: center;"></div>\
                        </div>\
                    </div>',
        success: function () {
          bt_tools.send(
            { url: '/config?action=get_msg_fun', data: { module_name: 'wx_account', fun_name: 'get_auth_url' } },
            function (res) {
              jQuery
                .ajax({
                  url: '/static/js/jquery.qrcode.min.js?v=1764728423',
                  dataType: 'script',
                  cache: true,
                })
                .done(function () {
                  $('#wechat-qrcode').qrcode({
                    render: 'canvas',
                    width: 180,
                    height: 180,
                    text: res.msg.res,
                    correctLevel: 1,
                  });
                });
            },
            '生成二维码信息'
          );
        },
        cancel: function () {
          if ($(that).hasClass('bterror')) {
            $('.alert-view-box span.on').click();
          } else {
            getWxAccountConfig(el, callback);
          }
        },
      });
    });
  }
}

// RSA加密
var rsa = {
  publicKey: null,
  /**
   * @name 使用公钥加密
   * @param {string} text
   * @returns string
   */
  encrypt_public: function (text) {
    this.publicKey = document.querySelector('.public_key').attributes.data.value;
    if (this.publicKey.length < 10) return text;
    var encrypt = new JSEncrypt();
    encrypt.setPublicKey(this.publicKey);
    return encrypt.encrypt(text);
  },
  /**
   * @name 使用公钥解密
   * @param {string} text
   * @returns string
   */
  decrypt_public: function (text) {
    this.publicKey = document.querySelector('.public_key').attributes.data.value;
    if (this.publicKey.length < 10) return null;
    var decrypt = new JSEncrypt();
    decrypt.setPublicKey(this.publicKey);
    return decrypt.decryptp(text);
  },
};

// 自定义软件管理
var soft = {
    is_install: false,
  is_setup: false,
  is_setup_name: "",
  refresh_data: [],
	alert_modules:[], // 告警模块存储列表
  ignore_list: [], // 忽略列表
  /**
   * @description 获取配置菜单
   * @param {string} name 菜单名称
   * @returns
  */
  get_config_menu: function (name){
    var meun = '';
    if (bt.os == 'Linux') {
      var datas = {
        public: [{
          type: 'config',
          title: lan.soft.config_edit
        },
          {
            type: 'change_version',
            title: lan.soft.nginx_version
          }
        ],
        mysqld: [{
            type: 'change_data_path',
            title: lan.soft.save_path
          },
          {
            type: 'change_mysql_port',
            title: lan.site.port
          },
          {
            type: 'get_mysql_run_status',
            title: lan.soft.status
          },
          {
            type: 'get_mysql_status',
            title: lan.soft.php_main7
          },
          {
            type: 'mysql_error_log',
            title: lan.soft.error_log
          },
          {
            type: 'mysql_slow_log',
            title: lan.public.slow_log
          },
          {
            type: 'mysql_log_bin',
            title: lan.public.bin_log
          },
        ],
        phpmyadmin: [{
          type: 'phpmyadmin_php',
          title: lan.soft.php_version
        },
          {
            type: 'phpmyadmin_safe',
            title: lan.soft.safe
          }
        ],
        memcached: [{
          type: 'memcached_status',
          title: '负载状态'
        },
          {
            type: 'memcached_set',
            title: '性能调整'
          },
        ],
        redis: [{
          type: 'get_redis_status',
          title: '负载状态'
        },],
        tomcat: [{
          type: 'log',
          title: '运行日志'
        }],
        apache: [{
          type: 'apache_set',
          title: '性能调整'
        },
          {
            type: 'apache_status',
            title: lan.soft.nginx_status
          },
          {
            type: 'log',
            title: '运行日志'
          }
        ],
        openlitespeed: [{
          type: 'openliMa_set',
          title: '参数设置'
        }],
        nginx: [{
          type: 'nginx_set',
          title: '性能调整'
        },
          {
            type: 'nginx_status',
            title: lan.soft.nginx_status
          },
          {
            type: 'log',
            title: '错误日志'
          }
        ]
      };
      var arrs = datas.public;
      if (name === 'phpmyadmin') arrs = [];
      if (name === 'openlitespeed') arrs.length = 1;
      if (name === 'pureftpd') arrs.push({type: 'pureftpd_log', title: '日志管理'});
      if (name === 'mysqld') arrs.length = 1;
      arrs = arrs.concat(datas[name]);
      if (arrs) {
        for (var i = 0; i < arrs.length; i++) {
          var item = arrs[i];
          if (item) {
            meun += '<p onclick="soft.get_tab_contents(\'' + item.type + '\',this)">' + item.title + '</p>';
          }
        }
      }
    }
    return meun;
  },

  /**
   * @description 设置软件配置
   * @param {string} name 软件名称
   */
  set_soft_config: function (name) {
    //软件设置
    var _this = this;
    var loading = bt.load();
    bt.soft.get_soft_find(name, function (rdata) {
      loading.close();
      if (name == 'mysql') name = 'mysqld';
      var menuing = bt.open({
        type: 1,
        area: (name === 'mysqld' ? ['800px', '634px'] : name.indexOf('php-') > -1 ? ['796px' , '644px'] : "660px"),
        title: name + lan.soft.admin,
        closeBtn: 2,
        shift: 0,
        content: '<div class="bt-w-main" style="width:100%;' + (name === 'mysqld' ? 'height: 590px;' : (name.indexOf('php-') > -1 ? 'height: 600px;' : '')) + '"><div class="bt-w-menu bt-soft-menu"></div><div id="webEdit-con" class="bt-w-con pd15" style="height:' + (name === 'mysqld' ? '100%' : name.indexOf('php-') > -1 ? '600px' : '560px') + ';overflow:auto"><div class="soft-man-con bt-form"></div></div></div>'
      });
      var menu = $('.bt-soft-menu').data("data", rdata);
      setTimeout(function () {
        menu.append($('<p class="bgw bt_server" onclick="soft.get_tab_contents(\'service\',this)">' + lan.soft.service + '</p>'))
        if (rdata.version_coexist) {
          var ver = name.split('-')[1].replace('.', '');
          var opt_list = [{
            type: 'set_php_config',
            val: ver,
            title: lan.soft.php_main5
          },
            {
              type: 'config_edit',
              val: ver,
              title: lan.soft.config_edit
            },
            {
              type: 'set_upload_limit',
              val: ver,
              title: lan.soft.php_main2
            },
            {
              type: 'set_timeout_limit',
              val: ver,
              title: lan.soft.php_main3,
              php53: true
            },
            {
              type: 'config',
              val: ver,
              title: lan.soft.php_main4
            },
            {
              type: 'fpm_config',
              val: ver,
              title: 'FPM配置文件'
            },
            {
              type: 'set_dis_fun',
              val: ver,
              title: lan.soft.php_main6
            },
            {
              type: 'set_fpm_config',
              val: ver,
              title: lan.soft.php_main7,
              apache24: true,
              php53: true
            },
            {
              type: 'get_php_status',
              val: ver,
              title: lan.soft.php_main8,
              apache24: true,
              php53: true
            },
            {
              type: 'get_php_session',
              val: ver,
              title: lan.soft.php_main9,
              apache24: true,
              php53: true
            },
            {
              type: 'get_fpm_logs',
              val: ver,
              title: lan.soft.log,
              apache24: true,
              php53: true
            },
            {
              type: 'get_slow_logs',
              val: ver,
              title: lan.public.slow_log,
              apache24: true,
              php53: true
            },
            {
              type: 'get_phpinfo',
              val: ver,
              title: 'phpinfo'
            }
          ]
          if (ver !== '52' && ver !== '82') {
            opt_list.unshift({
              type: 'set_php_site',
              val: ver,
              title: '<span class="glyphicon icon-vipLtd" style="margin-left: -23px;"></span> 站点防护'
            })
          }
          var phpSort = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
            webcache = bt.get_cookie('serverType') == 'openlitespeed' ? true : false;
          for (var i = 0; i < phpSort.length; i++) {
            var item = opt_list[i];
            if (item) {
              if (item.os == undefined || item['os'] == bt.os) {
                if (name.indexOf("5.2") >= 0 && item.php53) continue;
                if (webcache && (item.type == 'set_fpm_config' || item.type == 'fpm_config' || item.type == 'get_php_status')) continue;
                var apache24 = item.apache24 ? 'class="apache24"' : '';
                menu.append($('<p data-id="' + i + '" ' + apache24 + ' onclick="soft.get_tab_contents(\'' + item.type + '\',this)" >' + item.title + '</p>').data('item', item))
              }
            }
          }
          if (name.indexOf('php-') > -1) {
            $('.bt-w-menu p').css({'padding-left': '38px'})
            $('.bt-w-menu').css({'width': '126px'})
          }
        } else {
          menu.append(soft.get_config_menu(name));
        }
        $(".bt-w-menu p").click(function () {
          $(this).addClass("bgw").siblings().removeClass("bgw");
        });
        $(".bt-w-menu p:eq(0)").trigger("click");
        if (name.indexOf('php-') != -1 || name.indexOf('apache') != -1) {
          bt.soft.get_soft_find('apache', function (rdata) {
            if (rdata.setup) {
              if (rdata.version.indexOf('2.2') >= 0) {
                if (name.indexOf('php-') != -1) {
                  $(".apache24").hide();
                  $(".bt_server").remove();
                  $(".bt-w-menu p:eq(0)").trigger("click");
                }

                if (name.indexOf('apache') != -1) {
                  $(".bt-soft-menu p:eq(3)").remove()
                  $(".bt-soft-menu p:eq(3)").remove()
                }
              }
            }
          })
        }
      }, 100)
    })
  },

  /**
  * @description 告警类型展示内容
  * @param {Object} formData  表单数据
  */
  switchPushType:function(formData){
    $.ajaxSettings.async = false;
    var alertListModule = [],isCheckType = [],accountConfigStatus = false,_checklist = []
    // 获取告警通道
    bt_tools.send({url:'config?action=get_msg_configs'},function(rdata){
      var resetChannelMessage = [],prevArray = []
      Object.getOwnPropertyNames(rdata).forEach(function(key) {
        var mod = rdata[key]
        key == 'wx_account' ? prevArray.push(mod) :resetChannelMessage.push(mod)
      })
      alertListModule = prevArray.concat(resetChannelMessage)
      soft.alert_modules = alertListModule
      alertListModule.forEach(function(mod, i) {
        if(formData){
            isCheckType = formData.module.split(',')
        }
        if(mod.name === 'wx_account'){
            if(!$.isEmptyObject(mod.data) && mod.data.res.is_subscribe && mod.data.res.is_bound){
                accountConfigStatus = true   //安装微信公众号模块且绑定
            }
        }
        if(mod.name !== 'sms'){
          _checklist.push({
            type: 'checkbox',
            name:mod.name,
            class:'module-check '+((!mod.setup || $.isEmptyObject(mod.data))?'check_disabled':((mod.name == 'wx_account' && !accountConfigStatus)?'check_disabled':''))+'',
            style:{'margin-right': '10px'},
            disabled:(!mod.setup || $.isEmptyObject(mod.data))?true:((mod.name == 'wx_account' && !accountConfigStatus)?true:false),
            value:$.inArray(mod.name,isCheckType) >= 0 ?1:0,
            title:(mod.name == 'wx_account'?'<b style="color: #fc6d26;">[推荐]</b>':'')+mod.title+((!mod.setup || $.isEmptyObject(mod.data))?'<span style="color:red;cursor: pointer;" class="alertInstall">[点击安装]</span>':(((mod.name == 'wx_account' && !accountConfigStatus)?'[<a target="_blank" class="bterror alertInstall">未配置</a>]':''))),
          })

        }
      })
    })
    $.ajaxSettings.async = true;
    return _checklist
  },

  /**
   * @description 设置高级配置
   * @param {params} params 参数
   * @param {function} callback 回调函数
   */
  set_push_config:function(params,callback){
    bt_tools.send({url:'/push?action=set_push_config',data:{name:'site_push',data:JSON.stringify(params),id:Date.now ()}},function(res){
      layer.msg(res.msg,{icon:res.status?'1':'2'})
      if(callback) callback(res)
    },{verify:false,msg:'设置告警状态'})
  },

}

// 产品推荐
var product_recommend = {
  data: null,
  /**
   * @description 初始化
   */
  init: function (callback) {
    var _this = this;
    if (location.pathname.indexOf('bind') > -1) return;
    this.get_product_type(function (rdata) {
      _this.data = rdata;
      if (callback) callback(rdata);
    });
  },
    /**
   * @description 获取支付状态
   */
    get_pay_status: function (cnf) {
      if (typeof cnf === 'undefined') cnf = { isBuy: false };
      var pro_end = parseInt(bt.get_cookie('pro_end') || -1);
      var ltd_end = parseInt(bt.get_cookie('ltd_end') || -1);
      var is_pay = pro_end > -1 || ltd_end > -1 || cnf.isBuy; // 是否购买付费版本
      var advanced = 'ltd'; // 已购买，企业版优先显示
      if (pro_end === -2 || pro_end > -1) advanced = 'pro';
      if (ltd_end === -2 || ltd_end > -1) advanced = 'ltd';
      var end_time = advanced === 'ltd' ? ltd_end : pro_end; // 到期时间
      return { advanced: advanced, is_pay: is_pay, end_time: end_time };
    },
  /**
   * @description 获取推荐类型
   * @param {object} type 参数{type:类型}
   */
  get_recommend_type: function (type) {
    var config = null,
      pathname = location.pathname.replace('/', '') || 'home';
    for (var i = 0; i < this.data.length; i++) {
      var item = this.data[i];
      if (item.type == type && item.show) config = item;
    }
    return config;
  },
}

$(function () {
  // 对象序列化
  if ($.fn && !$.fn.serializeObject) {
    $.fn.serializeObject = function () {
      var hasOwnProperty = Object.prototype.hasOwnProperty;
      return this.serializeArray().reduce(function (data, pair) {
        if (!hasOwnProperty.call(data, pair.name)) {
          data[pair.name] = pair.value;
        }
        return data;
      }, {});
    };
  }

  // 固定表头
  $.fn.extend({
    fixedThead: function (options) {
      var _that = $(this);
      var option = {
        height: 400,
        shadow: true,
        resize: true,
      };
      options = $.extend(option, options);
      if ($(this).find("table").length === 0) {
        return false;
      }
      var _height = $(this)[0].style.height,
        _table_config = _height.match(/([0-9]+)([%\w]+)/);
      if (_table_config === null) {
        _table_config = [null, options.height, "px"];
      } else {
        $(this).css({
          boxSizing: "content-box",
          paddingBottom: $(this).find("thead").height(),
        });
      }
      $(this).css({ position: "relative" });
      var _thead = $(this).find("thead")[0].outerHTML,
        _tbody = $(this).find("tbody")[0].outerHTML,
        _thead_div = $(
          '<div class="thead_div"><table class="table table-hover mb0"></table></div>'
        ),
        _shadow_top = $('<div class="tbody_shadow_top"></div>'),
        _tbody_div = $(
          '<div class="tbody_div" style="height:' +
            _table_config[1] +
            _table_config[2] +
            ';"><table class="table table-hover mb0" style="margin-top:-' +
            $(this).find("thead").height() +
            'px"></table></div>'
        ),
        _shadow_bottom = $('<div class="tbody_shadow_bottom"></div>');
      _thead_div.find("table").append(_thead);
      _tbody_div.find("table").append(_thead);
      _tbody_div.find("table").append(_tbody);
      $(this).html("");
      $(this).append(_thead_div);
      $(this).append(_shadow_top);
      $(this).append(_tbody_div);
      $(this).append(_shadow_bottom);
      var _table_width = _that.find(".thead_div table")[0].offsetWidth,
        _body_width = _that.find(".tbody_div table")[0].offsetWidth,
        _length = _that.find("tbody tr:eq(0)>td").length;
      $(this)
        .find("tbody tr:eq(0)>td")
        .each(function (index, item) {
          var _item = _that.find("thead tr:eq(0)>th").eq(index);
          if (index === _length - 1) {
            _item.attr(
              "width",
              $(item)[0].clientWidth + (_table_width - _body_width)
            );
          } else {
            _item.attr("width", $(item)[0].offsetWidth);
          }
        });
      if (options.resize) {
        $(window).resize(function () {
          var _table_width = _that.find(".thead_div table")[0].offsetWidth,
            _body_width = _that.find(".tbody_div table")[0].offsetWidth,
            _length = _that.find("tbody tr:eq(0)>td").length;
          _that.find("tbody tr:eq(0)>td").each(function (index, item) {
            var _item = _that.find("thead tr:eq(0)>th").eq(index);
            if (index === _length - 1) {
              _item.attr(
                "width",
                $(item)[0].clientWidth + (_table_width - _body_width)
              );
            } else {
              _item.attr("width", $(item)[0].offsetWidth);
            }
          });
        });
      }
      if (options.shadow) {
        var table_body = $(this).find(".tbody_div")[0];
        if (_table_config[1] >= table_body.scrollHeight) {
          $(this).find(".tbody_shadow_top").hide();
          $(this).find(".tbody_shadow_bottom").hide();
        } else {
          $(this).find(".tbody_shadow_top").hide();
          $(this).find(".tbody_shadow_bottom").show();
        }
        $(this)
          .find(".tbody_div")
          .scroll(function (e) {
            var _scrollTop = $(this)[0].scrollTop,
              _scrollHeight = $(this)[0].scrollHeight,
              _clientHeight = $(this)[0].clientHeight,
              _shadow_top = _that.find(".tbody_shadow_top"),
              _shadow_bottom = _that.find(".tbody_shadow_bottom");
            if (_scrollTop == 0) {
              _shadow_top.hide();
              _shadow_bottom.show();
            } else if (
              _scrollTop > 0 &&
              _scrollTop < _scrollHeight - _clientHeight
            ) {
              _shadow_top.show();
              _shadow_bottom.show();
            } else if (_scrollTop == _scrollHeight - _clientHeight) {
              _shadow_top.show();
              _shadow_bottom.hide();
            }
          });
      }
    },
  });

  // 对象转数组
  if (!Object.values) {
    Object.values = function (obj) {
      var vals = [];
      for (var key in obj) {
        if (obj.hasOwnProperty(key)) {
          vals.push(obj[key]);
        }
      }
      return vals;
    };
  }

  // 日期格式化
  Date.prototype.format = function (b) {
    var c = {
      "M+": this.getMonth() + 1,
      "d+": this.getDate(),
      "h+": this.getHours(),
      "m+": this.getMinutes(),
      "s+": this.getSeconds(),
      "q+": Math.floor((this.getMonth() + 3) / 3),
      S: this.getMilliseconds(),
    };
    if (/(y+)/.test(b)) {
      b = b.replace(
        RegExp.$1,
        (this.getFullYear() + "").substr(4 - RegExp.$1.length)
      );
    }
    for (var a in c) {
      if (new RegExp("(" + a + ")").test(b)) {
        b = b.replace(
          RegExp.$1,
          RegExp.$1.length == 1
            ? c[a]
            : ("00" + c[a]).substr(("" + c[a]).length)
        );
      }
    }
    return b;
  };

  for (var key in win_mount) {
    if (win_mount.hasOwnProperty(key)) {
      window[key] = win_mount[key];
    }
  }
  ajaxSetup()
});

function GetfilePath() {
  var a = $('#PathPlace').find('span').text();
  a = a.replace(new RegExp(/(\\)/g), '/');
  setCookie('path_dir_change', a);
  $('#' + getCookie('SetId')).val(a + getCookie('SetName'));
  layer.close(getCookie('ChangePath'));
}

function openPath(a) {
  setCookie('Path', a);
  bt.refreshMain(window.location.origin + '/files')
}

/* ! 宝塔文件上传组件 License  https://www.bt.cn  */
var bt_upload_file={f:null,f_total:0,f_path:null,split_size:1024*1024*2,_files:[],_error:0,_start_time:0,_t_start_time:0,collback_to:null,upload_url:"/files?action=upload",_loadT:null,open:function(path,is_exts,ps,collback_to){bt_upload_file.f_path=path.replace("//","/");user_agent=navigator.userAgent.toLowerCase();var btn_dir="";var accept_ext="";if(!is_exts){if(user_agent.indexOf("chrome")!==-1||user_agent.indexOf("firefox")!==-1){btn_dir='<input type="file" id="dir_input" onchange="bt_upload_file.list(this.files)" style="display:none;"  multiple="true" autocomplete="off" multiple webkitdirectory /><button type="button" style="margin-left: 10px;"  id="opt" onclick="$(\'#dir_input\').click()" autocomplete="off" title="支持的浏览器: Chrome、Firefox、Edge、有极速模式的国产浏览器">选择目录</button>'}}else{accept_ext='accept="'+is_exts+'"'}var other_ps="";if(ps){other_ps=' --- <span style="color:red;">'+ps+"</span>"}else{other_ps=" --- 支持断点续传"}if(collback_to){bt_upload_file.collback_to=collback_to}bt_upload_file._loadT=layer.open({type:1,title:"上传文件到["+bt_upload_file.f_path+"]"+other_ps,area:["550px","500px"],shadeClose:false,closeBtn:2,content:'<div class="fileUploadDiv"><input type="file" id="file_input" onchange="bt_upload_file.list(this.files)"  multiple="true" autocomplete="off" '+accept_ext+' /><button type="button"  id="opt" onclick="$(\'#file_input\').click()" autocomplete="off">选择文件</button>'+btn_dir+'<span id="totalProgress" style="position: absolute;top: 7px;right: 10px;"></span><span><button type="button" id="up" autocomplete="off" onclick="bt_upload_file.start(0)">开始上传</button><button type="button" id="filesClose" autocomplete="off" onClick="layer.close(bt_upload_file._loadT)" >关闭</button></span><ul id="up_box"><li id="tipsUpdataText" style="height: 97%;line-height: 280px;text-align: center;color: #ccc;font-size: 32px;"><span>请将需要上传的文件拖到此处</span></li></ul></div>'});bt_upload_file._files=[];document.addEventListener("drop",function(e){e.preventDefault()});document.addEventListener("dragleave",function(e){e.preventDefault()});document.addEventListener("dragenter",function(e){e.preventDefault()});document.addEventListener("dragover",function(e){e.preventDefault()});var area=document.getElementById("up_box");area.addEventListener("drop",function(e){e.preventDefault();var fileList=e.dataTransfer.files;if(fileList.length==0){return false}bt_upload_file.list(fileList)})},list:function(_files){$("#totalProgress").html("");$("#tipsUpdataText").remove();if(_files.length==0){return false}var file_data=$.extend(true,{},_files);for(var i=0;i<file_data.length;i++){bt_upload_file._files.push(file_data[i])}var fileList=bt_upload_file._files;$("#up_box").html("");var loadT=layer.msg("正在加载文件列表...",{time:0,icon:16,shade:0.3});for(var i=0;i<fileList.length;i++){var f_name=fileList[i].name;if(fileList[i].webkitRelativePath){f_name=fileList[i].webkitRelativePath}$("#up_box").append('<li class="offset-'+i+'"><span class="filename" title="上传到: '+bt_upload_file.f_path+"/"+f_name+'">'+f_name+'</span><span class="filesize">'+bt_upload_file.to_size(fileList[i].size)+"</span><em>等待上传</em></li>")}layer.close(loadT)},to_size:function(a){var d=[" B"," KB"," MB"," GB"," TB"," PB"];var e=1024;for(var b=0;b<d.length;b+=1){if(a<e){return(b===0?a:a.toFixed(2))+d[b]}a/=e}},start:function(i){var len=bt_upload_file._files.length;if(len===0){layer.msg("请选择文件!",{icon:2});return false}if(i===0){bt_upload_file._t_start_time=new Date()}$("#filesClose,#up,#opt").attr("disabled","disabled");var total_time=bt_upload_file.diff_time(bt_upload_file._t_start_time,new Date());$("#totalProgress").html("<p>已上传("+i+"/"+len+"),"+total_time+'</p> <progress value="'+i+'" max="'+len+'"></progress>');if(len<=i){$("#totalProgress").html("<p>上传完成("+i+"/"+len+"), "+total_time+'</p> <progress value="'+i+'" max="'+len+'"></progress>');bt_upload_file._files=[];$("#filesClose,#up,#opt").removeAttr("disabled");if(bt_upload_file.collback_to){bt_upload_file.collback_to(bt_upload_file.f_path)}return false}if(i>10){$("#up_box").scrollTop(35*(i-10)+50)}bt_upload_file._start_time=new Date();bt_upload_file._error=0;bt_upload_file.f=bt_upload_file._files[i];bt_upload_file.f_total=Math.ceil(bt_upload_file.f.size/bt_upload_file.split_size);bt_upload_file.upload(0,i)},upload:function(start,i){var end=Math.min(bt_upload_file.f.size,start+bt_upload_file.split_size);var len=bt_upload_file._files.length;var f_path=bt_upload_file.f_path;if(bt_upload_file.f.webkitRelativePath){f_path=bt_upload_file.f_path+"/"+bt_upload_file.f.webkitRelativePath.replace("/"+bt_upload_file.f.name,"")}var form=new FormData();form.append("f_path",f_path.replace("//","/"));form.append("f_name",bt_upload_file.f.name);form.append("f_size",bt_upload_file.f.size);form.append("f_start",start);form.append("blob",bt_upload_file.f.slice(start,end));$.ajax({url:bt_upload_file.upload_url,type:"POST",data:form,async:true,processData:false,contentType:false,success:function(data){if(typeof(data)==="number"){var progress=parseInt(data/bt_upload_file.f.size*100);
var total_time=bt_upload_file.diff_time(bt_upload_file._t_start_time,new Date());$("#totalProgress").html("<p>已上传("+i+"/"+len+"),"+total_time+'</p> <progress value="'+i+'" max="'+len+'"></progress>');$("#up_box li em")[i].outerHTML='<em style="color:green;">上传进度:'+progress+"%</em>";$("#up_box li .filesize")[i].outerHTML='<span class="filesize">'+bt_upload_file.to_size(data)+"/"+bt_upload_file.to_size(bt_upload_file.f.size)+"</span>";$("#up_box li em")[i].focus();bt_upload_file.upload(data,i)}else{if(data.status){var f_time=bt_upload_file.diff_time(bt_upload_file._start_time,new Date());$("#up_box li em")[i].outerHTML='<em style="color:green;">已完成('+f_time+")</em>";$("#up_box li .filesize")[i].outerHTML='<span class="filesize">'+bt_upload_file.to_size(bt_upload_file.f.size)+"/"+bt_upload_file.to_size(bt_upload_file.f.size)+"</span>"}else{$("#up_box li em")[i].outerHTML='<em style="color:red;">'+data.msg+"</em>"}bt_upload_file.start(i+1)}},error:function(e){if(bt_upload_file._error>5){$("#up_box li em")[i].outerHTML='<em style="color:red;">上传失败</em>';bt_upload_file.start(i+1);return}bt_upload_file._error+=1;bt_upload_file.upload(start,i)}})},diff_time:function(start_date,end_date){var diff=end_date.getTime()-start_date.getTime();var minutes=Math.floor(diff/(60*1000));var leave3=diff%(60*1000);var seconds=(leave3/1000).toFixed(2);var result=seconds+"秒";if(minutes>0){result=minutes+"分"+result}return result}};