//
//  common.h
//  ftp_test
//
//  Created by 刘译键 on 2018/10/27.
//  Copyright © 2018年 刘译键. All rights reserved.
//

#ifndef common_h
#define common_h

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <pwd.h>
#include <netinet/in.h>
#include <time.h>
#include <dirent.h>
#include <arpa/inet.h>
#include <getopt.h>
#include <errno.h>
#include <memory.h>
#include <ctype.h>
#include <pthread.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <fcntl.h>
#include <ifaddrs.h>


//定义默认块大小
#define BSIZE 8192
//定义服务器默认端口
#define DEFAULT_SERVER_PORT 8021
//定义服务器默认根目录
#define DEFAULT_SERVER_ROOT "/tmp"
//定义接受socket或连接socket
#define RECEIVE 0
#define SEND 1
//定义判别函数
#define equal(x, y) (strcmp((x), (y))==0)
//定义字符串常量
#define USERNAME "anonymous"
#define GREETING "220 Anonymous FTP server ready.\r\n"
#define BYE "221 Goodbye.\r\n"
#define LOGIN_OK "230 User logged in, proceed.\r\n"
#define USER_ACCEPTED "331 correct username, need password.\r\n"
#define NEED_USERNAME "332 Need username before password.\r\n"
#define TYPE_HARD "215 UNIX Type: L8\r\n"
#define TYPE_SET_I "200 Type set to I.\r\n"
#define PORT_OK "200 PORT command sucessful\r\n"
#define NEED_TRANSFER "425 You have to call PORT or PASV first.\r\n"
#define NEED_TRANSFER_TCP1 "425 no data transfer TCP has been accepted.\r\n"
#define NEED_TRANSFER_TCP2 "425 no data transfer TCP has been connected.\r\n"
#define NO_FILE "451 no such file.\r\n"
#define HAVE_FILE "213 find this file.\r\n"
#define TRANSFER_START "150 Opening BINARY mode data connection.\r\n"
#define TRANSFER_OK "226 Transfer successful, close transfer link then.\r\n"
#define NOT_PERMIT "550 Permission denined.\r\n"
#define USER_DENIED "530 user denied.\r\n"
#define NOT_ACCEPT_PARA "501 not acceptable parameter.\r\n"
#define FILE_OPEN "150 Opening BINARY mode data connection.\r\n"
#define CHANGE_DIR "250 Directory successfully changed.\r\n"
#define NOT_CHANGE_DIR "550 Failed to change directory.\r\n"
#define NOT_MAKE_DIR "550 Failed to create directory. Check path or permissions.\r\n"
#define WROND_COMMAND "500 wrong command\r\n"
#define MAKE_DIR "257 new Directory successfully created.\r\n"
#define ALREADY_DIR "550 directory already exist.\r\n"
#define REMOVE_DIR "250 Directory already removed.\r\n"
#define NOT_REMOVE_DIR "550 Not a valid directory.\r\n"
#define RENAME_FILE "250 Requested file action okay, file renamed.\r\n"
#define NOT_RENAME_FILE "553 Cannot rename file.\r\n"

//维护连接状态
typedef struct State
{
    int mode;//0（none），1（pasv），2（port）
    int logged_in;//0（not login），1（login）
    int username_ok;//0 （not ok），1（ok）
    char* username;
    char* message;
    int connection;//新套接字对象
    int sock_pasv;
    int sock_port;
    char ip[50];//暂存ip ”127.0.0.1“形式
    int port;
    int transfer_pid;
    char temp_directory[BSIZE];//当前工作目录
    char oldname[50];
}State;

//命令结构体
typedef struct Command
{
    char command[5];
    char arg[BSIZE];
}Command;

//传输结构体
typedef struct Tran
{
    int connection;
    char temp_directory[BSIZE];
}Tran;

//函数列表

//发送消息
long int send_string(int, char*);
//响应客户端命令
void response(Command*, State*);
//新建网络套接字
int create_socket(int, char*, int, int);
//服务客户的函数
void* serve_client(void*);
//生成随机端口
int generate_port(void);
//获取公网ip，暂不可用，用于pasv模式
int getlocalip(char*);
//发送文件,不关文件符
void send_file(FILE*, int);
//接收文件,不关文件符
void recv_file(FILE*, int);

#endif /* common_h */
