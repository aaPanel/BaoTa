// +-------------------------------------------------------------------
// | 宝塔Linux面板
// +-------------------------------------------------------------------
// | Copyright (c) 2022-2099 宝塔软件(http://bt.cn) All rights reserved.
// +-------------------------------------------------------------------
// | Author: hwliang <hwl@bt.cn>
// +-------------------------------------------------------------------

//---------------------------
// 系统状态获取程序
//---------------------------

/**
 * @brief 获取CPU核心数
 * @author hwliang<2022-03-07>
 * @return int 
 */
int get_cpu_count(){
    FILE *fp = fopen("/proc/cpuinfo", "r");
    if(fp == NULL){
        return 0;
    }
    char line[1024];
    int count = 0;
    while(fgets(line, sizeof(line), fp)){
        if(strncmp(line, "processor", 9) == 0){
            count++;
        }
    }
    fclose(fp);
    return count;
}

/**
 * @brief 获取CPU时钟
 * @author hwliang
 * @return int 
 */
int get_clock_ticks(){
    return (int)sysconf(_SC_CLK_TCK);
}

/**
 * @brief 获取系统状态
 * @author hwliang
 * @param info <sys_stat> 系统状态结构体指针
 * @return void
 */
void get_sys_stat(struct sys_stat *info){
    FILE *fp = fopen("/proc/stat", "r");
    if(fp == NULL){
        return;
    }
    char line[1024];
    while(fgets(line, sizeof(line), fp)){
        if(strncmp(line, "ctxt", 4) == 0){
            info->ctxt = atoi(line + 4);
        }else if(strncmp(line, "btime", 5) == 0){
            info->btime = atoi(line+5);
        }else if(strncmp(line, "processes", 9) == 0){
            info->processes = atoi(line+9);
        }else if(strncmp(line, "procs_running", 13) == 0){
            info->procs_running = atoi(line+13);
        }else if(strncmp(line, "procs_blocked", 13) == 0){
            info->procs_blocked = atoi(line+13);
        }
    }
    fclose(fp);
}

/**
 * @brief 获取系统开机时间
 * @author hwliang<2022-03-08>
 * @return int 
 */
int get_boot_time(){
    struct sys_stat info = {0};
    get_sys_stat(&info);
    return info.btime;
}

/**
 * @brief 获取内存信息
 * @author hwliang<2022-03-07>
 * @return struct memory_info 
 */
int get_memory_info(struct memory_info *info){
    FILE *fp = fopen("/proc/meminfo", "r");
    if(fp == NULL){
        return 1;
    }
    char line[1024];
    while(fgets(line, sizeof(line), fp)){
        if(strncmp(line, "MemTotal", 8) == 0){
            info->total = atol(line+9) * 1024;
        }else if(strncmp(line, "MemFree", 7) == 0){
            info->free = atol(line+8) * 1024;
        }else if(strncmp(line, "Buffers", 7) == 0){
            info->buffers = atol(line+8) * 1024;
        }else if(strncmp(line, "Cached", 6) == 0){
            info->cached = atol(line+7) * 1024;
        }else if(strncmp(line, "SwapTotal", 9) == 0){
            info->swap_total = atol(line+10) * 1024;
        }else if(strncmp(line, "SwapFree", 8) == 0){
            info->swap_free = atol(line+9) * 1024;
        }else if(strncmp(line, "MemAvailable", 12) == 0){
            info->available = atol(line+13) * 1024;
        }else if(strncmp(line, "Inactive:", 9) == 0){
            info->inactive = atol(line+10) * 1024;
        }else if(strncmp(line, "Active:", 7) == 0){
            info->active = atol(line+8) * 1024;
        }else if(strncmp(line, "Shmem", 5) == 0){
            info->shared = atol(line+6) * 1024;
        }else if(strncmp(line, "Slab", 4) == 0){
            info->slab = atol(line+5) * 1024;
        }
    }
    fclose(fp);
    info->used = info->total - info->free - info->buffers - info->cached - info->slab;
    info->percent = (float)info->used / info->total * 100;
    return 0;
}

/**
 * @brief 获取CPU时间信息
 * @author hwliang<2022-03-08>
 * @param struct cpu_times 
 * @return void
 */
void get_cpu_times(struct cpu_times *cpu_time){
    FILE *fp = fopen("/proc/stat", "r");
    if(fp == NULL){
        return;
    }
    char line[512];
    float user, nice, system, idle, iowait, irq, softirq, steal, guest, guest_nice;
    char delim[] = " ";
    char *p;
    int CLOCK_TICKS = get_clock_ticks();
    while(fgets(line, sizeof(line), fp)){
        if(strncmp(line, "cpu", 3) == 0){
            p = strtok(line, delim);
            int i = 0;
            while(1){
                p = strtok(NULL, delim);
                if(p == NULL) break;
                if(i == 0){
                    user = atof(p);
                }else if(i == 1){
                    nice = atof(p);
                }else if(i == 2){
                    system = atof(p);
                }else if(i == 3){
                    idle = atof(p);
                }else if(i == 4){
                    iowait = atof(p);
                }else if(i == 5){
                    irq = atof(p);
                }else if(i == 6){
                    softirq = atof(p);
                }else if(i == 7){
                    steal = atof(p);
                }else if(i == 8){
                    guest = atof(p);
                }else if(i == 9){
                    guest_nice = atof(p);
                }
                i++;
            }

            cpu_time->user = user / CLOCK_TICKS;
            cpu_time->nice = nice / CLOCK_TICKS;
            cpu_time->system = system / CLOCK_TICKS;
            cpu_time->idle = idle / CLOCK_TICKS;
            cpu_time->iowait = iowait / CLOCK_TICKS;
            cpu_time->irq = irq / CLOCK_TICKS;
            cpu_time->softirq = softirq / CLOCK_TICKS;
            cpu_time->steal = steal / CLOCK_TICKS;
            cpu_time->guest = guest / CLOCK_TICKS;
            cpu_time->guest_nice = guest_nice / CLOCK_TICKS;
            break;
        }
    }
    fclose(fp);
}


/**
 * @brief 取CPU使用时间
 * @author hwliang<2022-03-08>
 * @return float 
 */
float get_cpu_used_time(){
    struct cpu_times cpu_time = {0};
    get_cpu_times(&cpu_time);
    return cpu_time.user + cpu_time.nice + cpu_time.system;
}

/**
 * @brief 获取CPU使用率
 * @author hwliang<2022-03-08>
 * @param cycle 周期(秒)
 * @return float 使用率百分比
 */
float get_cpu_percent(int cycle){
    float cpu_time1 = get_cpu_used_time();
    sleep(cycle);
    float cpu_time2 = get_cpu_used_time();
    int cpu_count = get_cpu_count();
    float cpu_percent = (cpu_time2 - cpu_time1) / cycle / cpu_count * 100.00;
    return cpu_percent;
}

/**
 * @brief 获取指定进程信息
 * @author hwliang<2022-03-08>
 * @param pid <int> 进程ID
 * @param p_info <struct process_info> 进程信息结构体指针
 * @return int 
 */
int get_process_info(int pid,struct process_info *p_info){
    char p_stat_file[32];
    sprintf(p_stat_file, "/proc/%d/stat", pid);
    if(!file_exists(p_stat_file)) return -1;   
    FILE *fp = fopen(p_stat_file, "r");
    if(fp == NULL) return -2;

    int boot_time = get_boot_time();
    int CLOCK_TICKS = get_clock_ticks();
    char line[512];
    char delim[] = " ";
    char *p;

    fgets(line, sizeof(line), fp);
    p = strtok(line, delim);
    int i = 0;
    p_info->pid = pid;

    while(1){
        if(p == NULL) break;
        
        if(i == 2){
            strncpy(p_info->status, p, strlen(p));
        }else if(i == 1){
            strncpy(p_info->name, p+1, strlen(p)-2);
        }else if(i == 3){
            p_info->ppid = atoi(p);
        }else if(i == 21){
            p_info->create_time =  atoi(p) / CLOCK_TICKS + boot_time;
        }else if(i == 38){
            p_info->cpu_num = atoi(p);
        }else if(i == 13){
            p_info->user = atof(p) / CLOCK_TICKS;
        }else if(i == 14){
            p_info->system = atof(p) / CLOCK_TICKS;
        }else if(i == 15){
            p_info->children_user = atof(p) / CLOCK_TICKS;
        }else if(i == 16){
            p_info->children_system = atof(p) / CLOCK_TICKS;
        }else if(i == 41){
            p_info->iowait = atof(p) / CLOCK_TICKS;
        }
        i++;
        p = strtok(NULL, delim);
    }
    fclose(fp);
    p_info->read_time = get_time();
    return 0;
}

// /**
//  * @brief 获取进程CPU使用率
//  * @author hwliang
//  * @param pid <int> 进程ID
//  * @return float <float> 进程CPU使用率
//  */
// float get_process_cpu_percent(int pid){

//     if (process_old_list.count(pid) == 0){
//         struct process_info p_info;
//         get_process_info(pid, &p_info);
//         if(p_info.pid == 0) p_info.pid = pid;
//         process_old_list[pid] = p_info;
//     }

//     int cpu_count = get_cpu_count();
//     struct process_info p_info2;
//     get_process_info(pid, &p_info2);

//     int cycle = p_info2.read_time - process_old_list[pid].read_time;
//     if (cycle == 0) cycle = 1;
//     float cpu_percent = ((p_info2.user + p_info2.system + p_info2.children_system + p_info2.children_user) - (process_old_list[pid].user + process_old_list[pid].system + process_old_list[pid].children_system + process_old_list[pid].children_user)) / cycle / cpu_count * 100.00;
//     process_old_list[pid] = p_info2;
//     return cpu_percent;
// }

// /**
//  * @brief 获取PID列表
//  * @author hwliang
//  * @param pids <vector<int>> 用于存储PID列表的vector
//  * @return int 成功返回0
//  */
// int get_pids(int *pids){
//     DIR *dir;
//     struct dirent *ptr;
//     dir = opendir("/proc");
//     if (dir == NULL) return -1;
//     while ((ptr = readdir(dir)) != NULL){
//         if (ptr->d_name[0] >= '0' && ptr->d_name[0] <= '9') {
//             pids.push_back(atoi(ptr->d_name));
//         }
//     }
//     closedir(dir);
//     free(ptr);
//     return 0;
// }

/**
 * @brief 获取磁盘IO信息
 * @author hwliang
 * @param disk_info_list <struct disk_info *> 用于存储磁盘IO信息的结构体数组
 * @return int 磁盘分区数量
 */
int get_disk_info(struct disk_info *disk_info_list){
    FILE *fp = fopen("/proc/diskstats", "r");
    if(fp == NULL) return 0;
    char line[512];
    char delim[] = " ";
    char *p;
    int i = 0;
    int n = 0;
    int DISK_SECTOR_SIZE = 512; //磁盘扇区大小，似乎在Linux中512是一个不受磁盘实际分区情况影响的常数
    while(fgets(line, sizeof(line), fp) != NULL){
        p = strtok(line, delim);
        while(1){
            if(p == NULL) break;
            if(i == 2){
                sprintf(disk_info_list[n].name, "%s", p);
            }else if(i == 3){
                disk_info_list[n].read_count = atol(p);
            }else if(i == 4){
                disk_info_list[n].read_merged_count = atoi(p);
            }else if(i == 5){
                disk_info_list[n].read_bytes = atol(p) * DISK_SECTOR_SIZE;
            }else if(i == 6){
                disk_info_list[n].read_time = atoi(p);
            }else if(i == 7){
                disk_info_list[n].write_count = atol(p);
            }else if(i == 8){
                disk_info_list[n].write_merged_count = atoi(p);
            }else if(i == 9){
                disk_info_list[n].write_bytes = atol(p) * DISK_SECTOR_SIZE;
            }else if(i == 10){
                disk_info_list[n].write_time = atoi(p);
            }else if(i == 12){
                disk_info_list[n].busy_time = atoi(p);
            }

            i++;
            p = strtok(NULL, delim);
        }
        i = 0;
        n++;
    }
    fclose(fp);
    // unsigned long long total_read_bytes = 0;
    // for(int i = 0; i < n; i++){
    //     char s = disk_info_list[i].name[strlen(disk_info_list[i].name) -1];
    //     char e = disk_info_list[i].name[strlen(disk_info_list[i].name) -2];
    //     if(e != '-' && (s > '0' && s < '9')) continue;
    //     total_read_bytes += disk_info_list[i].read_bytes;
    //     printf("name: %s, read_bytes: %ld, write_bytes: %ld, write_count: %ld, read_count: %ld\n", disk_info_list[i].name, disk_info_list[i].read_bytes, disk_info_list[i].write_bytes, disk_info_list[i].write_count, disk_info_list[i].read_count);
    // }
    return n;
}

/**
 * @brief 获取磁盘IO状态信息
 * @author hwliang
 * @param disk_io <struct disk_info_all *> 用于存储磁盘IO状态信息的结构体指针
 * @param cycle <int> 计算周期
 * @return void
 */
void get_disk_io(struct disk_info_all *disk_io,int cycle) {
    struct disk_info disk_info_list1[20];
    struct disk_info disk_info_list2[20];
    int disk_count = get_disk_info(disk_info_list1);

    struct disk_info_all disk_io1 = {0,0,0,0,0,0,0,0};
    struct disk_info_all disk_io2 = {0,0,0,0,0,0,0,0};
    for(int i=0;i<disk_count;i++){
        char s = disk_info_list1[i].name[strlen(disk_info_list1[i].name) -1];
        char e = disk_info_list1[i].name[strlen(disk_info_list1[i].name) -2];
        if(e != '-' && (s > '0' && s < '9')) continue;
        disk_io1.read_count += disk_info_list1[i].read_count;
        disk_io1.read_merged_count += disk_info_list1[i].read_merged_count;
        disk_io1.read_bytes += disk_info_list1[i].read_bytes;
        disk_io1.read_time += disk_info_list1[i].read_time;
        disk_io1.write_count += disk_info_list1[i].write_count;
        disk_io1.write_merged_count += disk_info_list1[i].write_merged_count;
        disk_io1.write_bytes += disk_info_list1[i].write_bytes;
        disk_io1.write_time += disk_info_list1[i].write_time;
    }

    sleep(cycle);

    disk_count = get_disk_info(disk_info_list2);
    for(int i=0;i<disk_count;i++){
        char s = disk_info_list2[i].name[strlen(disk_info_list2[i].name) -1];
        char e = disk_info_list2[i].name[strlen(disk_info_list2[i].name) -2];
        if(e != '-' && (s > '0' && s < '9')) continue;
        disk_io2.read_count += disk_info_list2[i].read_count;
        disk_io2.read_merged_count += disk_info_list2[i].read_merged_count;
        disk_io2.read_bytes += disk_info_list2[i].read_bytes;
        disk_io2.read_time += disk_info_list2[i].read_time;
        disk_io2.write_count += disk_info_list2[i].write_count;
        disk_io2.write_merged_count += disk_info_list2[i].write_merged_count;
        disk_io2.write_bytes += disk_info_list2[i].write_bytes;
        disk_io2.write_time += disk_info_list2[i].write_time;
    }

    disk_io->read_count = disk_io2.read_count - disk_io1.read_count;
    disk_io->read_merged_count = disk_io2.read_merged_count - disk_io1.read_merged_count;
    disk_io->read_bytes = disk_io2.read_bytes - disk_io1.read_bytes;
    disk_io->read_time = disk_io2.read_time - disk_io1.read_time;
    disk_io->write_count = disk_io2.write_count - disk_io1.write_count;
    disk_io->write_merged_count = disk_io2.write_merged_count - disk_io1.write_merged_count;
    disk_io->write_bytes = disk_io2.write_bytes - disk_io1.write_bytes;
    disk_io->write_time = disk_io2.write_time - disk_io1.write_time;

    // printf("disk_io->read_count:%ld\n",disk_io->read_count);
    // printf("disk_io->read_merged_count:%ld\n",disk_io->read_merged_count);
    // printf("disk_io->read_bytes:%ld\n",disk_io->read_bytes);
    // printf("disk_io->read_time:%ld\n",disk_io->read_time);
    // printf("disk_io->write_count:%ld\n",disk_io->write_count);
    // printf("disk_io->write_merged_count:%ld\n",disk_io->write_merged_count);
    // printf("disk_io->write_bytes:%ld\n",disk_io->write_bytes);
    // printf("disk_io->write_time:%ld\n",disk_io->write_time);

}



/**
 * @brief 获取网络IO信息
 * @author hwliang
 * @param network_info_list <struct network_info *> 用于存储网络IO信息的结构体数组
 * @return int 网卡数量
 */
int get_network_info(struct network_info *network_info_list){
    FILE *fp = fopen("/proc/net/dev", "r");
    if(fp == NULL) return 0;
    char line[512];
    char delim[] = " ";
    char *p;
    int i = 0;
    int n = 0;
    while(fgets(line, sizeof(line), fp) != NULL){
        if(strncmp(line, "Inter", 5) == 0 || strncmp(line, " face", 5) == 0){
            continue;
        }
        p = strtok(line, delim);
        while(1){
            if(p == NULL) break;
            if(i == 0){
                p[strlen(p) - 1] = '\0';
                sprintf(network_info_list[n].name, "%s", p);
            }else if(i == 1){
                network_info_list[n].bytes_recv = atol(p);
            }else if(i == 2){
                network_info_list[n].packets_recv = atol(p);
            }else if(i == 3){
                network_info_list[n].errin = atoi(p);
            }else if(i == 4){
                network_info_list[n].dropin = atoi(p);
            }else if(i == 9){
                network_info_list[n].bytes_sent = atol(p);
            }else if(i == 10){
                network_info_list[n].packets_sent = atol(p);
            }else if(i == 11){
                network_info_list[n].errout = atoi(p);
            }else if(i == 12){
                network_info_list[n].dropout = atoi(p);
            }
            i++;
            p = strtok(NULL, delim);
        }
        i = 0;
        n++;
    }
    fclose(fp);
    return n;
}

/**
 * @brief 获取网络IO状态信息
 * @author hwliang
 * @param network_io <struct network_info_all *> 用于存储网络IO状态信息的结构体指针 
 * @param cycle <int> 计算周期
 * @return void
 */
void get_network_io(struct network_info_all *network_io,int cycle){
    struct network_info network_info_list1[20];
    struct network_info network_info_list2[20];
    int network_count = get_network_info(network_info_list1);

    struct network_info_all network_io1 = {0.0,0.0,0.0,0.0,0,0,0,0,0,0,"",""};
    struct network_info_all network_io2 = {0.0,0.0,0.0,0.0,0,0,0,0,0,0,"",""};
    for(int i=0;i<network_count;i++){
        network_io1.bytes_recv += network_info_list1[i].bytes_recv;
        network_io1.packets_recv += network_info_list1[i].packets_recv;
        network_io1.errin += network_info_list1[i].errin;
        network_io1.dropin += network_info_list1[i].dropin;
        network_io1.bytes_sent += network_info_list1[i].bytes_sent;
        network_io1.packets_sent += network_info_list1[i].packets_sent;
        network_io1.errout += network_info_list1[i].errout;
        network_io1.dropout += network_info_list1[i].dropout;
    }

    sleep(cycle);

    network_count = get_network_info(network_info_list2);
    strncpy(network_io->sent_json, "{", 1);
    strncpy(network_io->recv_json, "{", 1);
    network_io->sent_json[1] = '\0';
    network_io->recv_json[1] = '\0';
    char j_str[128];
    for(int i=0;i<network_count;i++){
        network_io2.bytes_recv += network_info_list2[i].bytes_recv;
        network_io2.packets_recv += network_info_list2[i].packets_recv;
        network_io2.errin += network_info_list2[i].errin;
        network_io2.dropin += network_info_list2[i].dropin;
        network_io2.bytes_sent += network_info_list2[i].bytes_sent;
        network_io2.packets_sent += network_info_list2[i].packets_sent;
        network_io2.errout += network_info_list2[i].errout;
        network_io2.dropout += network_info_list2[i].dropout;
        // network_info_list2[i].name[strlen(network_info_list2[i].name)-1] = '\0';
        sprintf(j_str, "\"%s\":%.2f,", network_info_list2[i].name, (network_info_list2[i].bytes_sent - network_info_list1[i].bytes_sent) / 1024.0);
        strcat(network_io->sent_json, j_str);
        sprintf(j_str, "\"%s\":%.2f,", network_info_list2[i].name, (network_info_list2[i].bytes_recv - network_info_list1[i].bytes_recv) / 1024.0);
        strcat(network_io->recv_json, j_str);
    }
    network_io->sent_json[strlen(network_io->sent_json) - 1] = '}';
    network_io->recv_json[strlen(network_io->recv_json) - 1] = '}';
    // printf("network_io->sent_json:%s\n",network_io->sent_json);
    // printf("network_io->recv_json:%s\n",network_io->recv_json);

    network_io->total_bytes_sent = network_io2.bytes_sent;
    network_io->total_bytes_recv = network_io2.bytes_recv;
    network_io->bytes_recv = (network_io2.bytes_recv - network_io1.bytes_recv) / 1024.0;
    network_io->packets_recv = network_io2.packets_recv - network_io1.packets_recv;
    network_io->errin = network_io2.errin - network_io1.errin;
    network_io->dropin = network_io2.dropin - network_io1.dropin;
    network_io->bytes_sent = (network_io2.bytes_sent - network_io1.bytes_sent) / 1024.0;
    network_io->packets_sent = network_io2.packets_sent - network_io1.packets_sent;
    network_io->errout = network_io2.errout - network_io1.errout;
    network_io->dropout = network_io2.dropout - network_io1.dropout;

}

/**
 * @brief 获取系统负载信息
 * @author hwliang
 * @param load_average <struct load_average *> 用于存储系统负载信息的结构体指针
 * @return void
 */
void get_load_average(struct load_average_info *load_average){
    FILE *fp = fopen("/proc/loadavg", "r");
    if(fp == NULL) return;
    char line[128];
    char delim[] = " ";
    char *p;
    int i = 0;
    while(fgets(line, sizeof(line), fp) != NULL){
        p = strtok(line, delim);
        while(1){
            if(p == NULL) break;
            if(i == 0){
                load_average->load_average_1min = atof(p);
            }else if(i == 1){
                load_average->load_average_5min = atof(p);
            }else if(i == 2){
                load_average->load_average_15min = atof(p);
            }else if(i == 3){
                // 分割活动进程数/总进程数
                char **p1;
                char delim1[] = "/"; 
                // split(p, delim1, p1);
                // load_average->running_processes = atoi(p1[0]);
                // load_average->total_processes = atoi(p1[1]);
            }else if(i == 4){
                load_average->last_pid = atoi(p);
            }
            i++;
            p = strtok(NULL, delim);
        }
        i = 0;
    }
    fclose(fp);
}



