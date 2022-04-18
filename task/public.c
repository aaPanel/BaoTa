// +-------------------------------------------------------------------
// | 宝塔Linux面板
// +-------------------------------------------------------------------
// | Copyright (c) 2022-2099 宝塔软件(http://bt.cn) All rights reserved.
// +-------------------------------------------------------------------
// | Author: hwliang <hwl@bt.cn>
// +-------------------------------------------------------------------

//---------------------------
// 公共函数
//---------------------------

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdarg.h>
#include <regex.h>
#include <unistd.h>
#include <time.h>
#include "md5.h"

const char panel_path[] = "/www/server/panel";
int curl_buff_size = 1024;


/**
 * @brief 取数组长度
 * @author hwliang<2022-04-01>
 * @param arr 
 * @return int 
 */
int arr_len(char **arr){
    int i=0;
    while(arr[i]!=NULL){
        i++;
    }
    return i;
}

/**
 * @brief 读取文件内容
 * @author hwliang<2021-09-25>
 * @param filename <char*> 文件名
 * @param mode <char*> 文件打开模式
 * @param fbody <char*> 用于存储文件内容的指针
 * @return void
 */
void read_file(char *filename, const char *mode, char *fbody)
{
    int buff_size = 128;
    char buff[buff_size];
    FILE *fp = NULL;
    fp = fopen(filename, mode);
    if(!fp) return;
    // //重置游标
    rewind(fp);
    fbody[0] = '\0';
    //读取文件内容
    while (fgets(buff, buff_size, fp) != NULL)
    {
        strncat(fbody, buff, strlen(buff));
    }

    fclose(fp);
}

/**
 * @brief 正则匹配
 * @author hwliang<2021-09-25>
 * @param str <char *> 要被匹配的字符串
 * @param pattern <char *> 正则表达式
 * @return int
 */
int match(char *str, char *pattern)
{
    regex_t reg;
    size_t nmatch = 1;
    regmatch_t pmatch[1];
    int cflags = REG_EXTENDED;
    regcomp(&reg, pattern, cflags);
    int ret = regexec(&reg, str, nmatch, pmatch, 0);
    regfree(&reg);
    if (ret == 0)
    {
        return 1;
    }
    return 0;
}

/**
 * @brief 是否为IPv4地址
 * @author hwliang<2021-09-25>
 * @param ip <char *> 要被匹配的字符串
 * @return int
 */
int is_ipv4(char *ip)
{
    char pattern[] = "^(([0-9]{1,3}[.]){3}[0-9]{1,3}|([0-9]{1,3}[.]){3}[0-9]{1,3}/[0-9]{1,2}|([0-9]{1,3}[.]){3}[0-9]{1,3}-([0-9]{1,3}[.]){3}[0-9]{1,3})$";
    int ret = match(ip, pattern);
    return ret;
}

/**
 * @brief 写入文件
 * @author hwliang<2021-09-25>
 * @param filename <char*> 文件名
 * @param fbody <char*> 内容
 * @param mode <char*> 文件打开模式
 * @return int
 */
int write_file(char *filename, char *fbody, char *mode)
{
    FILE *fp = NULL;
    int result;
    fp = fopen(filename, mode);
    result = fputs(fbody, fp);
    fclose(fp);
    return result;
}

/**
 * @brief 执行SHELL命令
 * @author hwliang<2021-09-25>
 * @param cmd <char *> SHELL命令
 * @param result <char *> 用于存储命令执行结果的指针
 * @param 注意：此处执行命令只存储管道1的结果，如果需要其它管道的内容，请重定向到管道1
 * @return void
 */
void exec_shell(char *cmd, char *result)
{
    FILE *fp = NULL;
    fp = popen(cmd, "r");
    int buff_size = 128;
    char buff[buff_size];
    result[0] = '\0';
    while (fgets(buff, buff_size, fp) != NULL)
    {
        strcat(result, buff);
    }
    pclose(fp);
}

/**
 * @brief 判断文件是否存在
 * @author hwliang<2021-09-25>
 * @param filename <char*> 文件名
 * @return int
 */
int file_exists(char *filename)
{
    if (access(filename, F_OK) != -1)
    {
        return 1;
    }
    return 0;
}

/**
 *  获取格式化时间
 * @author hwliang<2021-09-25>
 * @param format <char *> 格式，示例：%Y-%m-%d %H:%M:%S
 * @param date_time <char *> 用于存储格式化时间的指针
 * @return void
 */
void format_date(char* format,char* date_time)
{
    time_t now;
    struct tm *tm_now;

    time(&now);
    tm_now = localtime(&now);

    strftime(date_time, 24, format, tm_now);
}

/**
 * @brief 获取格式化时间日期 %Y-%m-%d %H:%M:%S
 * @author hwliang<2022-04-01> 
 * @return char 
 */
void get_datetime(char* date_time)
{
    char format[] = "%Y-%m-%d %H:%M:%S";
    format_date(format,date_time);
}



/**
 * @brief 获取时间戳
 * @author hwliang<2022-04-01> 
 * @return int 
 */
int get_time(){
    time_t now;
    time(&now);
    return now;
}

/**
 * @brief 分割字符串
 * @author hwliang<2022-03-08>
 * @param str <char *> 字符串
 * @param delim <char *> 分隔符
 * @param dest <char **> 用于存储分割后的字符串的指针
 * @return int 分割后的字符串个数
 */
int split(char *str, char *delim,char **dest)
{
    if(str == NULL || strlen(str) == 0) return 0;
    if(delim == NULL || strlen(delim) == 0) return 0;
    int num = 0;
    char *p = strtok(str, delim);
    while (p != NULL)
    {
        *dest++ = p;
        ++num;
        p = strtok(NULL, delim);
    }
    return num;
}

/**
 * @brief 拼接字符串
 * @author hwliang<2022-04-01>
 * @param result <char *> 用于存储拼接后的字符串的指针
 * @param num <int> 要拼接的字符串个数
 * @param ... <char *> 要拼接的字符串(可变参数，参数个数为num)
 * @return int 拼接后的字符串长度
 */
int str_join(char *result,int num,...){
    int i = 0,len = 0,result_len = 0;
    char *str = NULL;
    va_list ap;
    va_start(ap,num);
    result[0] = '\0';
    while(1){
        str = va_arg(ap,char *);
        if(str == NULL) break;
        len = strlen(str);
        strncat(result,str,len+1);
        result_len += len;
        ++i;
    }
    va_end(ap);
    return result_len;
}

/**
 * @brief 去除字符串首尾空
 * @author hwliang<2022-04-01>
 * @param str <char *> 字符串
 * @return void
 */
void trim(char *str)
{
    int i = 0, j = 0;
    int len = strlen(str);
    while (str[i] == ' ' || str[i] == '\n' || str[i] == '\r' || str[i] == '\t') ++i;
    while (str[len - 1] == ' ' || str[len - 1] == '\n' || str[len - 1] == '\r' || str[len - 1] == '\t') --len;
    for (j = 0; j < len; ++j) str[j] = str[i + j];
    while(str[len-1] == ' ' || str[len-1] == '\n' || str[len-1] == '\r'|| str[len-1] == '\t')
    {
        str[len-1] = '\0';
        --len;
    }
}

/**
 * @brief 去除字符串首尾指定字符
 * @author hwliang<2022-04-01>
 * @param str <char *> 字符串
 * @param strip_char <char *> 去除的字符
 * @return void
 */
void strip(char *str,char strip_char)
{
    int i = 0, j = 0;
    int len = strlen(str);
    while (str[i] == strip_char) ++i;
    while (str[len - 1] == strip_char) --len;
    for (j = 0; j < len; ++j) str[j] = str[i + j];
    while(str[len-1] == strip_char)
    {
        str[len-1] = '\0';
        --len;
    }
}

/**
 * @brief 获取面板PID
 * @author hwliang<2022-04-01>
 * @return int 
 */
int get_panel_pid(){
    //pid_file路径
    char pid_file[64];
    int str_len = str_join(pid_file,2,panel_path,"/logs/panel.pid");

    //读取pid文件
    if(!file_exists(pid_file)) return 0;
    char pid_str[16];
    char mode[] = "r";
    read_file(pid_file,mode,pid_str);
    if (strlen(pid_str) == 0) return 0;

    //转换为整数
    int pid = atoi(pid_str);

    return pid;
}

/**
 * @brief 获取随机字符串
 * @author hwliang<2022-04-01>
 * @param str <char *> 用于存储随机字符串的指针
 * @param len <int> 随机字符串长度
 * @return void
 */
void get_randmo_str(char *str,int len){
    int i = 0;
    //随机数字符串
    char chars[] = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    int chars_len = strlen(chars) -1;

    //设置随机数种子
    time_t t;
    srand((unsigned) time(&t));

    //生成随机字符串
    for(i = 0;i < len;i++){
        str[i] = chars[rand() % chars_len];
    }
    str[len] = '\0';
}

/**
 * @brief 计算机字符串MD5
 * @author hwliang
 * @param encrypt <char *> 被计算MD5的字符串
 * @param result <char *> 用于存储计算结果的指针
 * @return void
 */
void get_string_md5(char *encrypt,char *result){
    MD5_CTX md5s;
    unsigned char decrypt[16];
    MD5Init(&md5s);
    MD5Update(&md5s,(unsigned char *)encrypt,strlen((char *)encrypt));
    MD5Final(&md5s,decrypt);
    char buff[2] = {0};
    result[0] = '\0';
    int i;
    for(i=0;i<16;i++){
        sprintf(buff,"%02x",decrypt[i]);
        strncat(result,buff,2);
    }
}


/**
 * @brief 获取文件MD5
 * @author hwliang<2022-04-01>
 * @param file <char *> 文件路径
 * @param result <char *> 用于存储计算结果的指针
 * @return void
 */
void get_file_md5(char *file,char *result){
    FILE *fp = fopen(file,"rb");
    if(fp == NULL) return;
    MD5_CTX md5s;
    unsigned char decrypt[16];
    MD5Init(&md5s);
    int len = 0;
    unsigned char buff[1024];
    while((len = fread(buff,1,1024,fp)) > 0){
        MD5Update(&md5s,buff,len);
    }
    MD5Final(&md5s,decrypt);
    char buff_str[2] = {0};
    result[0] = '\0';
    int i;
    for(i=0;i<16;i++){
        sprintf(buff_str,"%02x",decrypt[i]);
        strncat(result,buff_str,2);
    }
    fclose(fp);
}

/**
 * @brief 截取指定字符串
 * @author hwliang
 * @param str <char *> 被截取的字符串
 * @param result <char *> 用于存储截取结果的指针
 * @param start <int> 截取开始位置
 * @param len <int> 截取长度
 * @return int 0=失败 1=成功
 */
int str_cut(char *str,char *result,int start,int len){
    int i = 0;
    int str_len = strlen(str);
    if(start > str_len) return 0;
    if(start + len > str_len) len = str_len - start;
    for(i = 0;i < len;i++){
        result[i] = str[start + i];
    }
    result[len] = '\0';
    return 1;
}

/**
 * @brief 截取字符串右边指定位数
 * @author hwliang
 * @param str <char *> 被截取的字符串
 * @param result <char *> 用于存储截取结果的指针
 * @param len <int> 截取长度
 * @return int 0=失败 1=成功
 */
int right_cut(char *str,char *result,int len){
    int str_len = strlen(str);
    return str_cut(str,result,str_len - len,len);
}

/**
 * @brief 截取字符串左边指定位数
 * @author hwliang
 * @param str <char *> 被截取的字符串
 * @param result <char *> 用于存储截取结果的指针
 * @param len <int> 截取长度
 * @return int 0=失败 1=成功
 */
int left_cut(char *str,char *result,int len){
    return str_cut(str,result,0,len);
}

/**
 * @brief 获取操作系统位数
 * @author hwliang
 * @return int 32/64
 */
int get_os_bit(){
    int os_bit = 64;
    #ifdef __x86_64__
        os_bit = 64;
    #elif __aarch64__
        os_bit = 64;
    #else
        os_bit = 32;
    #endif
    return os_bit;
}

/**
 * @brief 判断系统架构是否为aarch64
 * @author hwliang
 * @return int 0=否 1=是
 */
int is_aarch64(){
    int arm = 0;
    #ifdef __aarch64__
        arm = 1;
    #else
        arm = 0;
    #endif
    return arm;
}

/**
 * @brief 获取本地IP地址列表
 * @author hwliang
 * @param iplist <char **> 用于存储IP地址的指针
 * @return int IP地址数量
 */
int get_ipaddress(char **iplist){
    char _cmd[] = "ip a |grep inet|grep -v inet6|grep -v 127.0.0.1|grep -v 'inet 192.168.'|grep -v 'inet 172.17.'|grep -v 'inet 10.'|awk '{print $2}'|sed 's#/[0-9]*##g'";
    FILE *fp = popen(_cmd,"r");
    if(fp == NULL) return 0;
    char buff[256] = {0};
    int i = 0;
    buff[0] = '\0';
    while(fgets(buff,256,fp) != NULL){
        if(strlen(buff) > 7){
            trim(buff);
            int blen = strlen(buff);
            if(buff[blen - 1] == '\n') buff[blen - 1] = '\0';
            blen = strlen(buff);
            iplist[i] = (char *)malloc(sizeof(char) * blen);
            iplist[i][0] = '\0';
            strcpy(iplist[i],buff);
            i++;
        }
        buff[0] = '\0';
    }
    pclose(fp);
    return i;
}

/**
 * @brief 获取面板版本
 * @author hwliang
 * @param version <char *> 用于存储版本的指针
 * @return int 0=失败 1=成功
 */
int get_panel_version(char *version){
    char comm_file[] = "/www/server/panel/class/common.py";
    if(!file_exists(comm_file)) return 0;
    struct stat st;
    stat(comm_file,&st);
    char *comm_body = (char *)malloc(st.st_size);
    read_file(comm_file,"r",comm_body);
    char *p = strstr(comm_body,"version = ");
    if(p == NULL){
        free(comm_body);
        return 0;
    } 
    p += 11;
    char *p2 = strstr(p,"'\n");
    if(p2 == NULL) {
        free(comm_body);
        return 0;
    }
    int len = p2 - p;
    strncpy(version,p,len);
    free(comm_body);
    return 1;
}