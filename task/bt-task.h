// +-------------------------------------------------------------------
// | 宝塔Linux面板
// +-------------------------------------------------------------------
// | Copyright (c) 2022-2099 宝塔软件(http://bt.cn) All rights reserved.
// +-------------------------------------------------------------------
// | Author: hwliang <hwl@bt.cn>
// +-------------------------------------------------------------------

//---------------------------
// 后台任务头文件
//---------------------------

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <dirent.h>
#include <pthread.h>
#include <signal.h>
// #include <map>
// #include <vector>
// using namespace std;
#include <sys/types.h>
#include <sys/stat.h>
#include "cJSON.c"
#include "public.c"

/**
 * @brief 内存信息
 * @author hwliang<2022-03-07>
 */
struct memory_info {
    long total; // 内存总量
    long available; // 可用内存
    float percent; // 内存使用率
    long used; // 已使用内存
    long free; // 空闲内存
    long active; // 活跃内存
    long inactive; // 不活跃内存
    long buffers; // 缓冲内存
    long cached; // 缓存内存
    long shared; // 共享内存
    long slab; // 内核缓冲
    long swap_total; // 交换分区总量
    long swap_free; // 交换分区剩余
} memory_info_default = {0,0,0.0,0,0,0,0,0,0,0,0,0,0};

/**
 * @brief CPU时间信息
 * @author hwliang<2022-03-08>
 */
struct cpu_times {
    float user; // 用户态时间
    float nice; // 优先级为nice的时间
    float system; // 系统态时间
    float idle; // 空闲时间
    float iowait; // 等待I/O操作的时间
    float irq; // 硬中断时间
    float softirq; // 软中断时间
    float steal; // 被其他进程抢占的时间
    float guest; // 虚拟CPU时间
    float guest_nice; // 虚拟CPU优先级nice的时间
}cpu_times_default = {0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0};

/**
 * @brief 进程信息
 * @author hwliang<2022-03-08>
 */
struct process_info {
    char status[32]; //进程状态
    char name[32]; //进程名称
    int pid; //进程ID
    int ppid; //父进程ID
    int cpu_num; //使用CPU个数
    int create_time; //创建时间
    float user; //用户时间
    float system;  //系统时间
    float children_user; //子进程用户时间
    float children_system; //子进程系统时间
    float iowait; //IO等待时间
    int read_time; //读取时间戳
}process_info_default = {"","",0,0,0,0,0.0,0.0,0.0,0.0,0.0,0};

/**
 * @brief 磁盘信息
 * @author hwliang
 */
struct disk_info {
    char name[32]; // 磁盘名称
    unsigned long read_count; // 读次数
    unsigned long write_count; // 写次数
    unsigned long long read_bytes; // 读字节数
    unsigned long long write_bytes; // 写字节数
    unsigned int read_time; // 读时间
    unsigned int write_time; // 写时间
    unsigned int read_merged_count; // 合并读次数
    unsigned int write_merged_count; // 合并写次数
    unsigned int busy_time; // 平均磁盘IO时间
}disk_info_default = {"",0,0,0,0,0,0,0,0,0};

struct disk_info_all {
    unsigned long read_count; // 读次数
    unsigned long write_count; // 写次数
    unsigned long long read_bytes; // 读字节数
    unsigned long long write_bytes; // 写字节数
    unsigned int read_time; // 读时间
    unsigned int write_time; // 写时间
    unsigned int read_merged_count; // 合并读次数
    unsigned int write_merged_count; // 合并写次数
}disk_info_all_default = {0,0,0,0,0,0,0,0};

/**
 * @brief 网络信息
 * @author hwliang
 */
struct network_info {
    char name[32]; // 网卡名称
    unsigned long long bytes_sent; // 发送字节数
    unsigned long long bytes_recv; // 接收字节数
    unsigned long packets_sent; // 发送包数
    unsigned long packets_recv; // 接收包数
    unsigned int errin; // 接收错误包数
    unsigned int errout; // 发送错误包数
    unsigned int dropin; // 接收丢弃包数
    unsigned int dropout; // 发送丢弃包数
}network_info_default = {"",0,0,0,0,0,0,0,0};

/**
 * @brief 网络IO信息
 * @author hwliang
 */
struct network_info_all {
    float total_bytes_sent; // 发送字节数
    float total_bytes_recv; // 接收字节数
    float bytes_sent; // 发送字节数
    float bytes_recv; // 接收字节数
    unsigned long packets_sent; // 发送包数
    unsigned long packets_recv; // 接收包数
    unsigned int errin; // 接收错误包数
    unsigned int errout; // 发送错误包数
    unsigned int dropin; // 接收丢弃包数
    unsigned int dropout; // 发送丢弃包数
    char sent_json[1024]; // 所有网卡的发送json
    char recv_json[1024]; // 所有网卡的接收json
} network_info_all_default = {0.0,0.0,0.0,0.0,0,0,0,0,0,0,"",""};

/**
 * @brief 系统负载信息
 * @author hwliang
 */
struct load_average_info {
    float load_average_1min;    // 最近1分钟平均负载
    float load_average_5min;    // 最近5分钟平均负载
    float load_average_15min;   // 最近15分钟平均负载
    int running_processes; // 活动进程数
    int total_processes;  // 总进程数
    int last_pid;       // 最后一个进程的pid
}load_average_info_default = {0.0,0.0,0.0,0,0,0};

struct sys_stat{
    int ctxt; // 上下文切换数
    int btime; // 系统启动时间
    int processes; // 进程数
    int procs_running; // 运行中的进程数
    int procs_blocked; // 阻塞中的进程数
}sys_stat_default = {0,0,0,0,0};

/**
 * @brief 任务信息
 * @author hwliang
 */
struct task_info{
    int id; // 任务id
    char type[32]; // 任务类型
    char execstr[256]; // 任务执行命令
}task_info_default={0,"",""};

/**
 * @brief 文件任务信息
 * @author hwliang
 */
struct file_task_info{
    char id[32]; // 任务id
    char type[8]; // 任务类型
    char shell[512]; // 任务执行命令
    char other[8192]; // 任务执行路径
}file_task_info_default={"","","",""};


// system_task();
    // struct load_average_info load_average;
    // get_load_average(&load_average);
    // printf("load_average_1min:%f\n",load_average.load_average_1min);
    // printf("load_average_5min:%f\n",load_average.load_average_5min);
    // printf("load_average_15min:%f\n",load_average.load_average_15min);
    // printf("running_processes:%d\n",load_average.running_processes);
    // printf("total_processes:%d\n",load_average.total_processes);
    // printf("last_pid:%d\n",load_average.last_pid);


    // struct network_info network_info_list[100];
    // get_network_info(network_info_list);
    // for(int i=0;i<100;i++){
    //     if(network_info_list[i].name[0] == '\0') break;
    //     printf("name: %s,bytes_sent: %ld,bytes_recv: %ld,packets_sent: %ld,packets_recv: %ld,errin: %d,errout: %d,dropin: %d,dropout: %d\n",
    //         network_info_list[i].name,network_info_list[i].bytes_sent,network_info_list[i].bytes_recv,network_info_list[i].packets_sent,network_info_list[i].packets_recv,
    //         network_info_list[i].errin,network_info_list[i].errout,network_info_list[i].dropin,network_info_list[i].dropout);
    // }

    // struct disk_info disk_info_list[100];
    // get_disk_info(disk_info_list);

    // for(int i=0;i<100;i++){
    //     if(disk_info_list[i].name[0] == '\0'){
    //         break;
    //     }
    //     printf("name: %s,read_count: %d,write_count: %d,read_bytes: %d,write_bytes: %ld,read_time: %d,write_time: %d\n",disk_info_list[i].name,disk_info_list[i].read_count,disk_info_list[i].write_count,disk_info_list[i].read_bytes,disk_info_list[i].write_bytes,disk_info_list[i].read_time,disk_info_list[i].write_time);
    // }


    // start_task();
    // char result[819200];
    // char url[] = "https://www.bt.cn/api/getipaddress";
    // int res = http_get(url,result,15);
    // printf("%s\n",result);
    // int res = http_post("https://www.bt.cn/api/panel/get_bind_info", "token=ibRXK36tpNeTdLBT2WsmBh46XNjBja8S&address=103.224.251.67", result, 15);
    // printf("%d\n",res);
    // printf("%s\n",result);
    

    // char **result;
    // int nrow= query("select count(*) from users", "/www/server/panel/data/default.db",&result);
    // int ncolumn = arr_len(result);
    // int value_start = ncolumn/2;
    // for(int i=value_start;i<ncolumn;i++){
    //     if(result[i] != NULL){
    //         printf("%s=%s\t",result[i-value_start],result[i]);
    //     }
        
    // }
    // printf("\n");
    // sqlite3_free_table(result);
    // result = NULL;

    // char a[1024];
    // read_file("/www/server/panel/data/userInfo.json","r",a);
    // printf("%s\n",a);

    // char a[24];
    // get_datetime(a);
    // printf("%s\n",a);

    // int stime = get_time();
    // printf("%d\n",stime);

    // int cpu_count = get_cpu_count();
    // printf("%d\n",cpu_count);

    // long mem_total = get_memory_total();
    // printf("%ld\n",mem_total);

    // long mem_free = get_memory_free();
    // printf("%ld\n",mem_free);

    // struct memory_info info;
    // get_memory_info(&info);
    // printf("total: %ldMB\n",info.total / 1024 / 1024);
    // printf("free: %ldMB\n",info.free / 1024 / 1024);
    // printf("used: %ldMB\n",info.used / 1024 / 1024);
    // printf("buffers: %ldMB\n",info.buffers / 1024 / 1024);
    // printf("cached: %ldMB\n",info.cached / 1024 / 1024);
    // printf("active: %ldMB\n",info.active / 1024 / 1024);
    // printf("inactive: %ldMB\n",info.inactive / 1024 / 1024);
    // printf("slab: %ldMB\n",info.slab / 1024 / 1024);
    // printf("swap_total: %ldMB\n",info.swap_total / 1024 / 1024);
    // printf("swap_free: %ldMB\n",info.swap_free / 1024 / 1024);
    // printf("percent: %fMB\n",info.percent);


    // float cpu_percent = get_cpu_percent(1);
    // printf("%0.2f\n",cpu_percent);

    // struct process_info p_info = {0};
    // get_process_info(31712,&p_info);
    // printf("user: %f\n",p_info.user);
    // printf("system: %f\n",p_info.system);
    // printf("children_user: %f\n",p_info.children_user);
    // printf("children_system: %f\n",p_info.children_system);
    // printf("iowait: %f\n",p_info.iowait);
    // printf("cpu_num: %d\n",p_info.cpu_num);
    // printf("create_time: %d\n",p_info.create_time);
    // printf("status: %s\n",p_info.status);
    // printf("name: %s\n",p_info.name);
    // printf("pid: %d\n",p_info.pid);
    // printf("ppid: %d\n",p_info.ppid);

    // sleep(1);

    // struct process_info p_info2 = {0};
    // int res = get_process_info(31712,&p_info2);
    // printf("res: %d\n",res);
    
    // float new_time = p_info2.user + p_info2.system + p_info2.children_user + p_info2.children_system;
    // float old_time = p_info.user + p_info.system + p_info.children_user + p_info.children_system;
    // float used_time = new_time - old_time;
    // printf("%f\n",new_time);
    // printf("%f\n",old_time);
    // printf("%f\n",used_time);

    // float process_cpu_percent =  used_time / 1 / get_cpu_count() * 100;
    // printf("process_cpu_percent: %f\n",process_cpu_percent);

    

    // struct sys_stat stat_info;
    // get_sys_stat(&stat_info);
    // printf("ctxt: %d\n",stat_info.ctxt);
    // printf("btime: %d\n",stat_info.btime);
    // printf("processes: %d\n",stat_info.processes);
    // printf("procs_running: %d\n",stat_info.procs_running);
    // printf("procs_blocked: %d\n",stat_info.procs_blocked);

    // int boot_time = get_boot_time();
    // printf("%d\n",boot_time);


    // get_process_cpu_percent(31712);

//     cJSON* root = NULL;
//     cJSON* item = NULL;
//     root = cJSON_Parse("{\
//   \"JOBS\": \
//     {\
//       \"id\": \"1\",\
//       \"func\": \"jobs:control_task\",\
//       \"args\": null,\
//       \"trigger\": \"interval\",\
//       \"seconds\": 15\
//     }\
//     }");
//     if(root == NULL){
//         printf("root is null\n");
//         return -1;
//     }

//     for(int i=0;i<cJSON_GetArraySize(root);i++){
//         item = cJSON_GetArrayItem(root,i);
//         if (item->type == cJSON_String) {
//             printf("%s: %s\n",item->string,item->valuestring);
//         }else if (item->type == cJSON_Number)
//         {
//             printf("%s: %d\n",item->string,item->valueint);
//         }
//         else if (item->type == cJSON_Object)
//         {
//             printf("%s: \n",item->string);
//             for(int j=0;j<cJSON_GetArraySize(item);j++){
//                 cJSON* item2 = cJSON_GetArrayItem(item,j);
//                 if (item2->type == cJSON_String) {
//                     printf("\t%s: %s\n",item2->string,item2->valuestring);
//                 }else if (item2->type == cJSON_Number)
//                 {
//                     printf("\t%s: %d\n",item2->string,item2->valueint);
//                 }
//             }
//         }
//         else if (item->type == cJSON_Array)
//         {
//             printf("%s: \n",item->string);
//             for(int j=0;j<cJSON_GetArraySize(item);j++){
//                 cJSON* item2 = cJSON_GetArrayItem(item,j);
//                 if (item2->type == cJSON_String) {
//                     printf("\t%d: %s\n",j,item2->valuestring);
//                 }else if (item2->type == cJSON_Number)
//                 {
//                     printf("\t%d: %d\n",j,item2->valueint);
//                 }
//             }
//         }
//     }

//     cJSON_Delete(root);



    // struct process_info p_info[1024];
    // // p_info = malloc(1024 * sizeof(struct p_info*)); //分配结构体集合内存
	// // memset(p_info, 0, sizeof(struct p_info*)*1024);

    // // read_process_info_all(p_info);
    // int n = 1024;
    // char _cc[8];
    // int s;
    
    // int pid = 29820;

    // float s = get_process_cpu_percent(pid);
    // printf("%f\n",s);
    // sleep(100);
    
    // get_panel_pid();
    // char ss[] = "'''123'''";
    // strip(ss,'\'');
    // printf("'%s'\n",ss);
    // printf("%d\n",strlen(ss));
    // char ss[32];
    // get_randmo_str(ss,32);
    // printf("%s\n",ss);

    // vector<int> pids;
    // get_pids(pids);
    // for(int i=0;i<pids.size();i++){
    //     printf("%d\n",pids[i]);
    // }
    // char ss[32];
    // char m[] = "你好";
    // get_string_md5(m,ss);
    // printf("%s\n",ss);

    // char filename[] = "/www/server/panel/data/default.db";
    // get_file_md5(filename,ss);
    // printf("%s\n",ss);


// /**
//  * @brief 构造文件检查请求参数
//  * @author hwliang
//  * @param data <char *> 用于存储请求参数的指针
//  */
// void get_check_args(char *data){
//     char pdata[40960],version[24];
//     char *iplist[1024];

//     // 获取并拼接panel_version参数
//     pdata[0] = '\0';
//     version[0] = '\0';
//     int rc = get_panel_version(version);
//     if(rc == 0) return;
//     strcat(pdata,"panel_version=");
//     strncat(pdata,version,strlen(version));

//     // 从本地获取IP地址列表
//     int ip_num = get_ipaddress(iplist);
//     for(int i=0;i<1024;i++){
//         // 跳过空数据
//         if(iplist[i] == NULL){
//             free(iplist[i]);
//             break;
//         } 
//         // 跳过无效数据
//         int slen = strlen(iplist[i]);
//         if(slen < 7) {
//             free(iplist[i]);
//             continue;
//         }

//         //拼接address参数
//         strcat(pdata,"&address[]=");
//         strncat(pdata,iplist[i],slen);

//         // 释放内存
//         free(iplist[i]);
//     }

//     if(ip_num == 0){
//         strcat(pdata,"&address=");
//     }
//     int p_len = strlen(pdata);
//     data = (char *)malloc(sizeof(char) * (p_len + 1));
//     data[0] = '\0';
//     strncpy(data,pdata,p_len);
// }

// char url[] = "http://check.bt.cn/api/panel/check_files";
// char class_path[] = "/www/server/panel/class/";

// /**
//  * @brief 检查面板关键文件
//  * @author hwliang
//  * @param pdata <char *> 请求参数
//  */
// void check_files(char *pdata){
//     // 发送请求
//     char *result = (char *)malloc(curl_buff_size);
//     result[0] = '\0';
//     http_post(url,pdata,result,30);
//     printf("%s\n",result);
//     // 是否为有效响应
//     if(result[0] == '\0' || strstr(result,"md5") == NULL) {
//         free(result);
//         return; 
//     }

//     // 解析返回的数据
//     cJSON *json = cJSON_Parse(result);
//     if(json == NULL) {
//         free(result);
//         return;
//     }
//     cJSON *file_list = json->child;
//     cJSON *item;
    
//     while(file_list != NULL){
//         // 取MD5
//         item = cJSON_GetObjectItem(file_list,"md5");
//         char *md5 = item->valuestring;

//         // 取文件名
//         item = cJSON_GetObjectItem(file_list,"name");
//         char *name = item->valuestring;

//         // 拼接文件全路径
//         char *filename = (char *)malloc(sizeof(char) * (strlen(class_path) + strlen(name) + 1));
//         filename[0] = '\0';
//         strcat(filename,class_path);
//         strcat(filename,name);

//         // 文件是否存在
//         if(!file_exists(filename)) {
//             free(filename);
//             continue;
//         }
//         // 计算当前文件MD5
//         char md5_str[33];
//         md5_str[0] = '\0';
//         get_file_md5(filename,md5_str);

//         // 比较新旧文件MD5，如果不一致，写入新的文件内容
//         if(strcmp(md5_str,md5) != 0){
//             item = cJSON_GetObjectItem(file_list,"body");
//             write_file(filename,item->valuestring,file_mode_write);
//             service_panel("reload"); // 重载面板
//         }

//         // 迭代下一行，并释放内存
//         file_list = file_list->next;
//         md5 = NULL;
//         name = NULL;
//         free(filename);
//     }
//     // 释放cJSON对象
//     cJSON_Delete(json);
//     free(result);
// }