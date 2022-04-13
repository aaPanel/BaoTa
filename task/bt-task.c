
// +-------------------------------------------------------------------
// | 宝塔Linux面板
// +-------------------------------------------------------------------
// | Copyright (c) 2022-2099 宝塔软件(http://bt.cn) All rights reserved.
// +-------------------------------------------------------------------
// | Author: hwliang <hwl@bt.cn>
// +-------------------------------------------------------------------

//---------------------------
// 后台任务主程序
//---------------------------
#include "bt-task.h"
#include "bt-sqlite.c"
#include "bt-psutil.c"

char is_task_file[] = "/tmp/panelTask.pl";  // 任务标记文件
char log_file[] = "/tmp/panelExec.log";     // 任务执行日志存储文件
char db_file[] = "/www/server/panel/data/default.db";   // 面板数据库文件
char system_db_file[] = "/www/server/panel/data/system.db"; // 监控数据库文件
char system_tip_file[] = "/www/server/panel/data/control.conf"; // 监控标记文件（包含存储天数配置）
char panel_restart_tip_file[] = "/www/server/panel/data/restart.pl"; // 面板重启标记文件
char panel_reload_tip_file[] = "/www/server/panel/data/reload.pl"; // 面板重载标记文件
char panel_pid_file[] = "/www/server/panel/logs/panel.pid"; // 面板进程PID文件
char pid_file[] = "/www/server/panel/logs/task.pid"; // 任务进程PID文件
char task_path[] = "/www/server/panel/tmp"; // 任务日志临时路径
char down_log_total_file[] = "/tmp/download_total.pl"; //文件下载统计文件
char download_url_root[] = "https://download.bt.cn"; //下载地址
char task_tips[] = "/dev/shm/bt_task_now.pl"; // 文件管理器任务标记文件
char class_path[] = "/www/server/panel/class/"; // 面板类文件路径

char file_mode[] = "r"; // 文件模式(读)
char file_mode_write[] = "w+"; // 文件模式(写)



/**
 * @brief 获取任务列表
 * @author hwliang
 * @param task_list <struct task_info *> 用于存储任务列表的结构体数组
 * @return void
 */
void get_task_list(struct task_info *task_list){

    // 如果标记文件不存在，则不获取任务列表
    if (!file_exists(is_task_file)) return;

    // 标记上次未执行成功的任务
    
    char *_sql_last = sqlite3_mprintf("UPDATE tasks SET status=0 WHERE status=-1");
    execute(_sql_last, db_file);
    sqlite3_free(_sql_last);

    // 查询未执行的任务
    char *_sql = sqlite3_mprintf("SELECT id,type,execstr FROM tasks WHERE status=0");
    char **table_data;
    int nrow = query(_sql,db_file,&table_data);
    sqlite3_free(_sql);

    // 如果任务数量为0，则删除标记文件
    if(nrow == 0){
        if(file_exists(is_task_file)){
            unlink(is_task_file);
        }
        return;
    }

    // 将任务信息写入到task_list中
    int field_num = 3; // 字段数量
    int ncolumn = nrow * field_num + field_num; // 计算实际数组长度
    int n = 0;
    for(int i=field_num;i<ncolumn;i++){
        if(table_data[i] == NULL) continue;
        int m = i % field_num; // 计算所属字段编号 0=id,1=type,2=execstr
        switch(m){
            case 0:
                task_list[n].id = atoi(table_data[i]);
                break;
            case 1:
                strcpy(task_list[n].type,table_data[i]);
                break;
            case 2:
                strcpy(task_list[n].execstr,table_data[i]);
                n++; // 行数加1
                break;
        }
    }

    // 释放数据表内存
    sqlite3_free_table(table_data);

    // 调试遍历任务列表
    // for(int i=0;i<n;i++){
    //     printf("id:%d,type:%s,execstr:%s\n",task_list[i].id,task_list[i].type,task_list[i].execstr);
    // }
}

/**
 * @brief 开始执行后台任务
 * @author hwliang
 * @return void
 */
void *start_task(void * arg){
    char _cmd[512];
    int start;
    int end;
    int _cycle = 2;
    struct task_info task_list[20] = {0,"",""};
    while(1){
        //获取等待执行的任务列表
        get_task_list(task_list);

        //遍历并执行任务
        for(int i=0;i<20;i++){
            if(task_list[i].id == 0) break;
            //标记状态和开始时间
            start = get_time();
            char *_sql1 = sqlite3_mprintf("UPDATE tasks SET status=-1,start=%d WHERE id=%d",start,task_list[i].id);
            if(strcmp(task_list[i].type,"execshell") == 0){ //执行shell命令
                _cmd[0] = '\0';
                sprintf(_cmd,"/bin/bash -c '%s' > %s 2>&1",task_list[i].execstr,log_file);
                execute(_sql1,db_file);
                system(_cmd);
            }
            sqlite3_free(_sql1);

            //标记状态和结束时间
            end = get_time();
            char *_sql2 = sqlite3_mprintf("UPDATE tasks SET status=1,end=%d WHERE id=%d",end,task_list[i].id);
            execute(_sql2,db_file);
            sqlite3_free(_sql2);
        }
        sleep(_cycle);
    }
    
}

/**
 * @brief 创建系统监控数据表
 * @author hwliang
 * @return void
 */
void system_create_table(){
    char _sql[] = "CREATE TABLE IF NOT EXISTS `load_average` (\n\
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,\n\
  `pro` REAL,\n\
  `one` REAL,\n\
  `five` REAL,\n\
  `fifteen` REAL,\n\
  `addtime` INTEGER\n\
  )";
    execute(_sql, system_db_file);
}

/**
 * @brief 数据监控数据保存天数
 * @author hwliang
 * @return int 
 */
int get_control_save_day(){
    int _day = 30; //默认30天
    if(!file_exists(system_tip_file)) return _day;
    char _control_day[12];
    char _mode[] = "r";
    read_file(system_tip_file,_mode, _control_day);
    _day = atoi(_control_day);

    if(_day < 1) _day = 30; 
    return _day;
}



/**
 * @brief 插入监控数据
 * @author hwliang
 * @param load_average <struct load_average_info *> 负载数据指针
 * @param mem_info <struct memory_info *> 内存数据指针
 * @param disk_io <struct disk_info_all *> 磁盘IO数据指针
 * @param net_io <struct network_info_all *> 网络IO数据指针
 * @param cpu_percent <float> cpu使用率
 * @param mem_percent <float> 内存使用率
 * @param x <int> 计数器
 * @return int 0=打开数据库失败，1=成功
 */
int insert_control_data(struct load_average_info *load_average,
                struct memory_info *mem_info,
                struct disk_info_all *disk_io,
                struct network_info_all *net_io,
                float cpu_percent,
                float mem_percent,
                int x){
        int rc;
        float lpro;
        int _time = get_time();
        int deltime;

        // 插入数据

        // 实例化sqlite3数据库
        sqlite3 *db;
        sqlite3_stmt *stmt = NULL; 
        rc = sqlite3_open_v2(system_db_file, &db, SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE | SQLITE_OPEN_FULLMUTEX, NULL);
        if (rc != SQLITE_OK) {
            fprintf(stderr, "Cannot open database: %s\n", sqlite3_errmsg(db));
            sqlite3_close(db);
            db = NULL;
            return 0;
        }

        // rc = sqlite3_prepare_v2(db,"PRAGMA cache_size = -512",-1,&stmt,NULL);
        // if (rc == SQLITE_OK) sqlite3_step(stmt);
        // sqlite3_finalize(stmt);

        // 插入load_average数据
        int cpu_count = get_cpu_count();    // CPU核心数
        lpro = load_average->load_average_1min / (cpu_count * 2 * 0.75) * 100;
        char *query_sql8 = sqlite3_mprintf("INSERT INTO load_average(pro,one,five,fifteen,addtime) VALUES(%f,%f,%f,%f,%d)",
            lpro,
            load_average->load_average_1min,
            load_average->load_average_5min,
            load_average->load_average_15min,
            _time
        );
        rc = sqlite3_prepare_v2(db, query_sql8, -1, &stmt, NULL);
        if (rc == SQLITE_OK) sqlite3_step(stmt);
        sqlite3_finalize(stmt);
        sqlite3_free(query_sql8);

        // 插入CPU、内存数据
        char *query_sql7 = sqlite3_mprintf("INSERT INTO cpuio(pro,mem,addtime) VALUES(%f,%f,%d)",cpu_percent,mem_percent,_time);
        rc = sqlite3_prepare_v2(db, query_sql7, -1, &stmt, NULL);
        if (rc == SQLITE_OK) sqlite3_step(stmt);
        sqlite3_finalize(stmt);
        sqlite3_free(query_sql7);

        // 插入磁盘IO数据
        char *query_sql6 = sqlite3_mprintf("INSERT INTO diskio(read_count,write_count,read_bytes,write_bytes,read_time,write_time,addtime) VALUES(%d,%d,%d,%d,%d,%d,%d)",
            disk_io->read_count,
            disk_io->write_count,
            disk_io->read_bytes,
            disk_io->write_bytes,
            disk_io->read_time,
            disk_io->write_time,
            _time
        );
        rc = sqlite3_prepare_v2(db, query_sql6, -1, &stmt, NULL);
        if (rc == SQLITE_OK) sqlite3_step(stmt);
        sqlite3_finalize(stmt);
        sqlite3_free(query_sql6);
        
        // 插入网络IO数据
        char *query_sql5 = sqlite3_mprintf("INSERT INTO network(up,down,total_up,total_down,down_packets,up_packets,addtime) VALUES(%.2f,%.2f,%.2f,%.2f,'%s','%s',%d)",
            net_io->bytes_sent,
            net_io->bytes_recv,
            net_io->total_bytes_sent,
            net_io->total_bytes_recv,
            net_io->recv_json,
            net_io->sent_json,
            _time
        );
        rc = sqlite3_prepare_v2(db, query_sql5, -1, &stmt, NULL);
        if (rc == SQLITE_OK) sqlite3_step(stmt);
        sqlite3_finalize(stmt);
        sqlite3_free(query_sql5);

        // 每60次采样删除一次过期数据
        if(x > 60){
            int day = get_control_save_day(); // 存储天数
            deltime = _time - day * 86400;
            char *query_sql1 = sqlite3_mprintf("DELETE FROM load_average WHERE addtime < %d",deltime);
            rc = sqlite3_prepare_v2(db, query_sql1, -1, &stmt, NULL);
            if (rc == SQLITE_OK) sqlite3_step(stmt);
            sqlite3_finalize(stmt);
            sqlite3_free(query_sql1);

            char *query_sql2 = sqlite3_mprintf("DELETE FROM cpuio WHERE addtime < %d",deltime);
            rc = sqlite3_prepare_v2(db, query_sql2, -1, &stmt, NULL);
            if (rc == SQLITE_OK) sqlite3_step(stmt);
            sqlite3_finalize(stmt);
            sqlite3_free(query_sql2);

            char *query_sql3 = sqlite3_mprintf("DELETE FROM diskio WHERE addtime < %d",deltime);
            rc = sqlite3_prepare_v2(db, query_sql3, -1, &stmt, NULL);
            if (rc == SQLITE_OK) sqlite3_step(stmt);
            sqlite3_finalize(stmt);
            sqlite3_free(query_sql3);

            char *query_sql4 = sqlite3_mprintf("DELETE FROM network WHERE addtime < %d",deltime);
            rc = sqlite3_prepare_v2(db, query_sql4, -1, &stmt, NULL);
            if (rc == SQLITE_OK) sqlite3_step(stmt);
            sqlite3_finalize(stmt);
            sqlite3_free(query_sql4);
            
        }
        // 释放sqlite资源
        sqlite3_db_release_memory(db);
        sqlite3_close(db);
        db = NULL;
        stmt = NULL;
        return 1;
}


/**
 * @brief 启动数据监控线程
 * @author hwliang
 * @return void
 */
void* system_task(void* arg){
    system_create_table();
    int system_cycle = 60; // 监控周期（单位：秒）
    int cycle = 1; // CPU/磁盘/网络 计算周期
    struct load_average_info load_average;
    struct memory_info mem_info;
    struct disk_info_all disk_io;
    struct network_info_all net_io;
    
    
    float cpu_percent;
    float mem_percent;
    
    int x = 0;
    while(1){
        // 等待cycle秒
        sleep(system_cycle);
        
        // 获取CPU使用率
        cpu_percent = get_cpu_percent(cycle);

        // 获取系统负载

        get_load_average(&load_average);

        // 获取内存使用率
        get_memory_info(&mem_info);
        mem_percent = mem_info.percent;

        // 获取磁盘IO
        get_disk_io(&disk_io,cycle);

        // 获取网络IO
        get_network_io(&net_io,cycle);

        // 插入数据
        insert_control_data(&load_average,&mem_info,&disk_io,&net_io,cpu_percent,mem_percent,x);

        // 插入次数计数
        x++;
    }
    
}

/**
 * @brief 面板服务管理
 * @author hwliang
 * @param action <const char *> 动作 start|stop|restart|reload
 * @return int 
 */
int service_panel(const char *action){
    char _cmd[64];
    sprintf(_cmd,"nohup bash /www/server/panel/init.sh %s &>/dev/null &",action);
    return system(_cmd);
}

/**
 * @brief 面板重载或重启
 * @author hwliang
 * @return void
 */
void *restart_panel_service(void* arg){
    unsigned int cycle = 1;
    while(1){
        if(file_exists(panel_restart_tip_file)){
            unlink(panel_restart_tip_file);
            service_panel("restart");
            printf("is restarting panel service\n");
        }else if(file_exists(panel_reload_tip_file)){
            unlink(panel_reload_tip_file);
            service_panel("reload");
            printf("is reloading panel service\n");
        }
        sleep(cycle);
    }
    
}

/**
 * @brief 启动面板服务 带延迟
 * @author hwliang
 * @return void
 */
void start_panel_service(){
    service_panel("start");
    sleep(3);
}

/**
 * @brief 面板守护进程
 * @author hwliang
 * @return void
 */
void *daemon_panel(void* arg){
    int cycle = 10;
    char panel_pid_str[16];
    char _proc_cmd_file[64];
    char _comm[32];
    int panel_pid = 0;
    while(1){
        sleep(cycle);
        if(!file_exists(panel_pid_file)) continue;  //跳过正常关闭的情况
        panel_pid_str[0] = '\0';
        read_file(panel_pid_file,file_mode,panel_pid_str);
        panel_pid = atoi(panel_pid_str);
        if(!panel_pid){
            start_panel_service();
            printf("\033[31m[%s]\033[0m\n",panel_pid_file);
            continue;
        }

        sprintf(_proc_cmd_file,"/proc/%d/comm",panel_pid);
        if(!file_exists(_proc_cmd_file)){
            start_panel_service();
            printf("panel process not exists,start panel service\n");
            continue;
        }
        
        read_file(_proc_cmd_file,file_mode,_comm);
        if(strncmp(_comm,"BT-Panel",8) != 0){
            start_panel_service();
            printf("\033[31m[%s]\033[0m\n",_comm);
            continue;
        }
        panel_pid = 0;
    }
    
    return 0;
}

void kill_other_task(){
    if(!file_exists(pid_file)) return;
    char task_pid_str[16];
    read_file(pid_file,file_mode,task_pid_str);
    int task_pid = atoi(task_pid_str);
    if(!task_pid) return;
    char _proc_cmd_file[64];
    char _comm[32];
    sprintf(_proc_cmd_file,"/proc/%d/comm",task_pid);
    if(!file_exists(_proc_cmd_file)) return;
    read_file(_proc_cmd_file,file_mode,_comm);
    if(strncmp(_comm,"BT-Task",7) == 0){
        kill(task_pid,SIGKILL);
        printf("已关闭多余任务进程: %s,PID: %d",_comm,task_pid);
    }
}

/**
 * @brief 任务守护进程
 * @author hwliang
 * @return void
 */
void daemon_process(){
    // int pid = fork();
    // if(pid < 0){
    //     exit(0);
    // }else if(pid > 0){
    //     exit(0);
    // }
    // setsid();
    // umask(0);
    // chdir("/www/server/panel");
    // close(STDIN_FILENO);
    // close(STDOUT_FILENO);
    // close(STDERR_FILENO);
    kill_other_task();
    pid_t process_pid = getpid();
    char pid_str[16];
    sprintf(pid_str,"%d",process_pid);
    write_file(pid_file,pid_str,file_mode_write);
}

/**
 * @brief 修改任务数据
 * @author hwliang
 * @param id <char *> 任务标识
 * @param key <char *> 字段名称
 * @param value <char *> 字段值
 * @return void
 */
void modify_task(char *id,const char *key,int value){
    char *_sql = sqlite3_mprintf("UPDATE `task_list` SET `%s`='%d' WHERE id=%s",key,value,id);
    execute(_sql,db_file);
    sqlite3_free(_sql);
}

/**
 * @brief 安装rar
 * @author hwliang
 * @return void
 */
void install_rar(){
    char unrar_file[] = "/www/server/rar/unrar";
    char rar_file[] = "/www/server/rar/rar";
    char bin_unrar[] = "/usr/local/bin/unrar";
    char bin_rar[] = "/usr/local/bin/rar";
    int os_bit = get_os_bit();
    char _cmd[128];
    char tmp_file[] = "/tmp/bt_rar.tar.gz";
    sprintf(_cmd,"wget -O %s %s/src/rarlinux-%d-5.6.1.tar.gz",tmp_file,download_url_root,os_bit);
    system(_cmd);
    if (file_exists(unrar_file)) system("rm -rf /www/server/rar");
    sprintf(_cmd,"tar -zxvf %s -C /www/server/",tmp_file);
    system(_cmd);

    if (file_exists(unrar_file)) return;
    if (file_exists(bin_unrar)) unlink(bin_unrar);
    if (file_exists(bin_rar)) unlink(bin_rar);

    sprintf(_cmd,"ln -s %s %s",unrar_file,bin_unrar);
    system(_cmd);

    sprintf(_cmd,"ln -s %s %s",rar_file,bin_rar);
    system(_cmd);    
}

/**
 * @brief 解压缩文件
 * @author hwliang
 * @param sfile <char *> 压缩文件
 * @param dfile <char *> 解压到
 * @param password <char *> 解压密码
 * @param _log_file <char *> 日志文件
 * @return void
 */
void _unzip(char *sfile,char *dfile,char *password,char *_log_file){
    int s_len = strlen(sfile);
    char file_ext4[5];
    char file_ext7[8];
    right_cut(sfile,file_ext4,4);
    right_cut(sfile,file_ext7,7);
    char _cmd[256];
    _cmd[0] = '\0';
    if(strcmp(file_ext4 , ".zip") == 0 || strcmp(file_ext4 , ".war") == 0){
        sprintf(_cmd,"unzip -o -q -P %s %s -d %s &> %s",password,sfile,dfile,_log_file);
        system(_cmd);
    }else if(strcmp(file_ext7 , ".tar.gz") == 0 || strcmp(file_ext4 , ".tgz") == 0){
        sprintf(_cmd,"tar -xzvf '%s' -C '%s' &> %s",sfile,dfile,_log_file);
        system(_cmd);
    }else if(strcmp(file_ext4 , ".rar") == 0){
        char rar_file[] = "/www/server/rar/unrar";
        if(!file_exists(rar_file)) install_rar();
        sprintf(_cmd,"echo '%s'|%s  x -u -y '%s' '%s' &> %s",password,rar_file,sfile,dfile,_log_file);
        system(_cmd);
    }else if(strcmp(file_ext4 , ".bz2")){
        sprintf(_cmd,"tar -xjvf '%s' -C '%s' &> %s",sfile,dfile,_log_file);
        system(_cmd);
    }else{
        char _dst_file[128];
        left_cut(sfile,_dst_file,s_len-4);
        sprintf(_cmd,"gunzip -c %s %s > %s",sfile,_dst_file,_log_file);
        system(_cmd);
    }
}

/**
 * @brief 压缩文件
 * @author hwliang
 * @param path <char *> 被压缩的文件所在路径
 * @param sfile <char *> 被压缩的文件名称(多个用逗号分隔),不包含路径
 * @param dfile <char *> 压缩文件名称(全路径)
 * @param _log_file <char *> 日志文件
 * @param z_type <char *> 压缩类型 zip/tar.gz/rar
 */
void _zip(char *path,char *sfile, char *dfile,char *_log_file,char *z_type){
    char sfiles[8192];
    char delim[] = ",";
    char *p = strtok(sfile, delim);
    char s[128];
    sfiles[0] = '\0';
    while(p){
        if(!p) continue;
        sprintf(s," '%s'",p);
        strcat(sfiles,s);
        p = strtok(NULL, delim);
    }
    trim(sfiles);
    char _cmd[10240];
    _cmd[0] = '\0';
    if (strcmp(z_type,"zip") == 0){
        sprintf(_cmd,"cd '%s' && zip '%s' -r %s &> %s",path,dfile,sfiles,_log_file);
        system(_cmd);
    }else if(strcmp(z_type,"tar.gz") == 0){
        sprintf(_cmd,"cd '%s' && tar -zcvf '%s' %s &> %s",path,dfile,sfiles,_log_file);
        system(_cmd);
    }else if(strcmp(z_type, "rar") == 0){
        char rar_file[] = "/www/server/rar/rar";
        if(!file_exists(rar_file)) install_rar();
        sprintf(_cmd,"cd '%s' && %s a -r '%s' %s &> %s",path,rar_file,dfile,sfiles,_log_file);
        system(_cmd);
    }
}

/**
 * @brief 解析解压任务中的other参数
 * @author hwliang
 * @param other <char *> other参数
 * @param dfile <char *> 用于保存dfile的指针
 * @param password <char *> 用于保存password的指针
 * @return void
 */
void parse_unzip_other(char *other,char *dfile,char *password){
    cJSON* root = NULL;
    cJSON* item = NULL;
    int value_len = 0;
    dfile[0] = '\0';
    password[0] = '\0';

    // 解析JSON
    root = cJSON_Parse(other);
    if(root == NULL) return;

    // 获取dfile字段
    item = cJSON_GetObjectItem(root, "dfile");
    if(item != NULL){
        value_len = strlen(item->valuestring);
        if(value_len > 0){
            strcpy(dfile,item->valuestring);
            dfile[value_len] = '\0';
        }
    }

    // 获取password字段
    item = cJSON_GetObjectItem(root, "password");
    if(item != NULL){
        value_len = strlen(item->valuestring);
        if(value_len > 0){
            strcpy(password,item->valuestring);
            password[value_len] = '\0';
        }
    }

    // 释放JSON对象
    cJSON_Delete(root);
    item = NULL;
    root = NULL;
}

/**
 * @brief 解析压缩任务中的other参数
 * @author hwliang
 * @param other <char *> other参数
 * @param dfile <char *> 用于保存dfile的指针
 * @param sfile <char *> 用于保存sfile的指针
 * @param z_type <char *> 用于保存z_type的指针
 * @return void
 */
void parse_zip_other(char *other,char *dfile,char *sfile,char *z_type){
    cJSON* root = NULL;
    cJSON* item = NULL;
    int value_len = 0;
    dfile[0] = '\0';
    sfile[0] = '\0';
    z_type[0] = '\0';

    // 解析JSON
    root = cJSON_Parse(other);
    if(root == NULL) return;

    // 获取dfile字段
    item = cJSON_GetObjectItem(root, "dfile");
    if(item != NULL){
        value_len = strlen(item->valuestring);
        if(value_len > 0){
            strcpy(dfile,item->valuestring);
            dfile[value_len] = '\0';
        }
    }

    // 获取sfile字段
    item = cJSON_GetObjectItem(root, "sfile");
    if(item != NULL){
        value_len = strlen(item->valuestring);
        if(value_len > 0){
            strcpy(sfile,item->valuestring);
            sfile[value_len] = '\0';
        }
    }

    // 获取z_type字段
    item = cJSON_GetObjectItem(root, "z_type");
    if(item != NULL){
        value_len = strlen(item->valuestring);
        if(value_len > 0){
            strcpy(z_type,item->valuestring);
            z_type[value_len] = '\0';
        }else{
            // 默认压缩类型为tar.gz
            strcpy(z_type,"tar.gz");
        }
    }

    // 释放JSON对象
    cJSON_Delete(root);
    item = NULL;
    root = NULL;
}

/**
 * @brief 处理文件管理器的后台任务
 * @author hwliang
 * @param id <char *> 任务ID
 * @param task_type <char *> 任务类型
 * @param task_shell <char *> 任务shell
 * @param other <char *> 任务other参数
 * @return void
 */
void execute_file_task(char *id,char *task_type,char *task_shell,char *other){
    if(!file_exists(task_path)){
        mkdir(task_path,0600);
    }
    char _log_file[128];
    sprintf(_log_file,"%s/%s.log",task_path,id);
    modify_task(id,"status",-1);
    modify_task(id,"exectime",get_time());
    char dfile[128];
    char _cmd[384];
    char sfile[8192];
    char z_type[32];
    char password[128];
    _cmd[0] = '\0';
    switch(atoi(task_type)){
        case 0:
            // 执行shell
            sprintf(_cmd,"%s &> %s",task_shell,_log_file);
            system(_cmd);
            break;
        case 1:
            // 下载文件
            if(file_exists(down_log_total_file)) unlink(down_log_total_file);
            sprintf(_cmd,"wget -O '%s' '%s' --no-check-certificate -T 30 -t 5 -d &> %s",other,task_shell,_log_file);
            system(_cmd);
            if(file_exists(_log_file)) unlink(_log_file);
            break;
        case 2:
            // 解压文件
            parse_unzip_other(other,dfile,password);
            _unzip(task_shell,dfile,password,_log_file);
            break;
        case 3:
            // 压缩文件
            parse_zip_other(other,dfile,sfile,z_type);
            _zip(task_shell,sfile,dfile,_log_file,z_type);
            break;
    }

    modify_task(id,"status",1);
    modify_task(id,"endtime",get_time());
}

/**
 * @brief 获取文件管理器后台任务列表
 * @author hwliang
 * @param task_list <struct file_task_info *> 任务列表
 */
int get_file_task_list(struct file_task_info *task_list){
    // 查询未执行的任务
    char *_sql = sqlite3_mprintf("SELECT id,type,shell,other FROM task_list WHERE status=0");
    char **table_data;
    int nrow = 0;
    int ncolumn = 0;
    sqlite3 *db;
    sqlite3_initialize();
    int rc = sqlite3_open_v2(db_file, &db, SQLITE_OPEN_READWRITE|SQLITE_OPEN_CREATE, NULL);
    if (rc != SQLITE_OK) {
        sqlite3_close(db);
        return 0;
    }
    rc = sqlite3_get_table(db, _sql, &table_data, &nrow, &ncolumn, NULL);
    sqlite3_free(_sql);
    if (rc != SQLITE_OK) {
        sqlite3_free_table(table_data);
        sqlite3_close(db);
        return 0;
    }

    if(nrow <= 0) {
        sqlite3_free_table(table_data);
        sqlite3_close(db);
        return 0;
    }

    // 将任务信息写入到task_list中
    int field_num = 4; // 字段数量
    ncolumn = nrow * field_num + field_num; // 计算实际数组长度
    int n = 0;
    for(int i=field_num;i<ncolumn;i++){
        if(table_data[i] == NULL) continue;
        int m = i % field_num; // 计算所属字段编号 0=id,1=type,2=shell,3=other
        switch(m){
            case 0:
                strcpy(task_list[n].id,table_data[i]);
                break;
            case 1:
                strcpy(task_list[n].type,table_data[i]);
                break;
            case 2:
                strcpy(task_list[n].shell,table_data[i]);
                break;
            case 3:
                strcpy(task_list[n].other,table_data[i]);
                n++;
                break;
        }
    }

    // 释放数据表内存
    sqlite3_free_table(table_data);
    sqlite3_db_release_memory(db);
    sqlite3_close(db);
    sqlite3_shutdown();
    return nrow;
}

/**
 * @brief 开始文件管理器后台任务线程
 * @author hwliang
 * @return void* 
 */
void *start_file_task(void * arg){
    int noe = 0;
    int n = 0;
    int _cycle = 1;
    char _sql[] = "UPDATE task_list SET status=0 WHERE status=-1";
    while(1){
        sleep(_cycle);
        n++;

        // 每600次循环做一次完整检测
        int is_tips = file_exists(task_tips);
        if(!is_tips && noe > 0 && n < 10) continue;

        if(is_tips) unlink(task_tips);
        noe = 1;
        n = 0;
        
        // 标记上次未执行完的任务
        execute(_sql,db_file);

        // 遍历所有未执行任务
        struct file_task_info file_task_list[10];
        int num = get_file_task_list(file_task_list);
        if(num <= 0) continue;
        for(int i=0;i<num;i++){
            if(file_task_list[i].id[0] == '\0') break;
            execute_file_task(file_task_list[i].id,file_task_list[i].type,file_task_list[i].shell,file_task_list[i].other);
        }
    }
    
}


/**
 * @brief 网站到期时间处理
 * @author hwliang
 * @return void* 
 */
void *site_end_date(void * arg){
    char old_date[11];
    char edate_file[] = "/www/server/panel/data/edate.pl";

    // 从文件中获取标记的日期
    old_date[0] = '\0';
    read_file(edate_file,file_mode,old_date);
    if(old_date[0] == '\0'){
        strncpy(old_date,"0000-00-00",11);
    }
    char now_date[11];
    char _cmd[] = "/www/server/panel/pyenv/bin/python3 /www/server/panel/script/site_task.py > /dev/null";
    int _cycle = 3600;
    char _format[] = "%Y-%m-%d";

    while(1){
        // 比较当前日期与上一次执行的日期是否一致
        format_date(_format,now_date);
        if(strcmp(old_date,now_date) == 0) {
            sleep(_cycle);
            continue;
        }

        // 重新标记执行日期并执行到期网站脚本
        old_date[0] = '\0';
        strncpy(old_date,now_date,11);
        system(_cmd);
    }
    
}

/**
 * @brief 检查MySQL配额
 * @author hwliang
 * @return void* 
 */
void *mysql_quota_check(void * arg){
    int _cycle = 3600;
    char _cmd[] = "/www/server/panel/pyenv/bin/python3 /www/server/panel/script/mysql_quota.py > /dev/null";

    while(1){
        sleep(_cycle);
        system(_cmd);
    }
    
}

/**
 * @brief 面板SESSION过期处理
 * @author hwliang
 * @return void* 
 */
void *sess_expire(void * arg){
    char sess_path[] = "/www/server/panel/data/session";
    int _cycle = 3600;
    char path[256];
    while(1){
        sleep(_cycle);
        if(!file_exists(sess_path)) continue;
        int s_time = get_time();
        DIR *dir = opendir(sess_path);
        if(dir == NULL) continue;
        struct dirent *ent;
        while((ent = readdir(dir)) != NULL){
            path[0] = '\0';
            strcpy(path,sess_path);
            strcat(path,"/");
            strcat(path,ent->d_name);
            struct stat st;
            stat(path,&st);
            int f_time = s_time - st.st_mtime;
            if (f_time > 3600) { // 删除超过1小时没有任何操作的会话
                unlink(path);
                continue;
            }

            // 删除60秒内没有成功登录的临时会话
            if(st.st_size < 256 && strlen(ent->d_name) == 32){
                if(f_time > 60) unlink(path);
            }
        }
        closedir(dir);
        free(ent);
    }
    
}

/**
 * @brief 检测邮件信息
 * @author hwliang
 * @return void* 
 */
void *send_mail_time(void * arg){
    int _cycle = 180;
    char _cmd[] = "/www/server/panel/pyenv/bin/python3 /www/server/panel/script/mail_task.py &> /dev/null";
    while(1){
        sleep(_cycle);
        system(_cmd);
    }
    
}

/**
 * @brief 面板消息提醒
 * @author hwliang
 * @return void* 
 */
void *check_panel_msg(void * arg){
    int _cycle = 3600;
    char _cmd[] = "/www/server/panel/pyenv/bin/python3 /www/server/panel/script/check_msg.py &> /dev/null";
    while(1){
        sleep(_cycle);
        system(_cmd);
    }
    
}

/**
 * @brief 检查面板关键文件
 * @author hwliang
 */
void check_files(){

    // 获取响应结果
    char _cmd[] = "/www/server/panel/pyenv/bin/python3 /www/server/panel/script/check_files.py";
    FILE *fp = popen(_cmd, "r");
    if(fp == NULL) return;
    
    int buff_size = 256;
    char buff[256] = {0};
    char *result = (char *)malloc(sizeof(char) * buff_size);
    result[0] = '\0';
    int _size = 0;
    int tmp_len = 0;
    while(fgets(buff, buff_size, fp)){
        tmp_len = strlen(buff);
        _size += tmp_len;
        result = (char *)realloc(result,sizeof(char) * (_size +1));
        strncat(result,buff,tmp_len);
    }
    pclose(fp);

    // 是否为有效响应
    if(result[0] == '\0' || strstr(result,"md5") == NULL) {
        free(result);
        return; 
    }

    // 解析返回的数据
    cJSON *json = cJSON_Parse(result);
    if(json == NULL) {
        free(result);
        return;
    }
    cJSON *file_list = json->child;
    cJSON *item;
    
    while(file_list != NULL){
        // 取MD5
        item = cJSON_GetObjectItem(file_list,"md5");
        char *md5 = item->valuestring;

        // 取文件名
        item = cJSON_GetObjectItem(file_list,"name");
        char *name = item->valuestring;

        // 拼接文件全路径
        char *filename = (char *)malloc(sizeof(char) * (strlen(class_path) + strlen(name) + 1));
        filename[0] = '\0';
        strcat(filename,class_path);
        strcat(filename,name);

        // 文件是否存在
        if(!file_exists(filename)) {
            free(filename);
            continue;
        }
        // 计算当前文件MD5
        char md5_str[33];
        md5_str[0] = '\0';
        get_file_md5(filename,md5_str);

        // 比较新旧文件MD5，如果不一致，写入新的文件内容
        if(strcmp(md5_str,md5) != 0){
            item = cJSON_GetObjectItem(file_list,"body");
            write_file(filename,item->valuestring,file_mode_write);
            service_panel("reload"); // 重载面板
        }

        // 迭代下一行，并释放内存
        file_list = file_list->next;
        md5 = NULL;
        name = NULL;
        free(filename);
    }
    // 释放cJSON对象
    cJSON_Delete(json);
    free(result);
}

/**
 * @brief 检查面板关键文件线程
 * @author hwliang
 * @return void* 
 */
void *check_files_panel(void * arg){
    int _cycle = 600; // 10分钟检测一次
    while(1){
        sleep(_cycle);
        check_files();
    }
    
}


int main(){
    // 启动守护进程
    daemon_process();

    // 启动任务线程
    pthread_t daemon_panel_tid;
    pthread_create(&daemon_panel_tid,NULL,daemon_panel,NULL);

    pthread_t restart_panel_service_tid;
    pthread_create(&restart_panel_service_tid,NULL,restart_panel_service,NULL);


    pthread_t system_task_tid;
    pthread_create(&system_task_tid,NULL,system_task,NULL);

    pthread_t start_file_task_tid;
    pthread_create(&start_file_task_tid,NULL,start_file_task,NULL);


    pthread_t site_end_date_tid;
    pthread_create(&site_end_date_tid,NULL,site_end_date,NULL);


    pthread_t mysql_quota_check_tid;
    pthread_create(&mysql_quota_check_tid,NULL,mysql_quota_check,NULL);


    pthread_t sess_expire_tid;
    pthread_create(&sess_expire_tid,NULL,sess_expire,NULL);

    pthread_t send_mail_time_tid;
    pthread_create(&send_mail_time_tid,NULL,send_mail_time,NULL);

    pthread_t check_files_panel_tid;
    pthread_create(&check_files_panel_tid,NULL,check_files_panel,NULL);

    pthread_t check_panel_msg_tid;
    pthread_create(&check_panel_msg_tid,NULL,check_panel_msg,NULL);
    printf("任务进程启动成功\n");
    start_task(NULL);
    return 0;
}
