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
