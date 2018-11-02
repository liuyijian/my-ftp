//
//  main.c
//  ftp_test
//
//  Created by 刘译键 on 2018/10/27.
//  Copyright © 2018年 刘译键. All rights reserved.
//

#include "common.h"



int main(int argc, char** argv)
{
    //控制端口
    int listening_port = DEFAULT_SERVER_PORT;
    //工作目录
    char working_directory[BSIZE] = DEFAULT_SERVER_ROOT;
    //读取命令行参数
    static struct option long_options[] = {{"root", required_argument , 0, 'r'},{"port", required_argument , 0, 'p'},{0, 0, 0, 0}};
    int option_index = 0;
    int c;
    while(1)
    {
        c = getopt_long_only(argc, argv, "rp:", long_options, &option_index);
        switch(c)
        {
            case 'r':
                strcpy(working_directory, optarg);
                break;
            case 'p':
                listening_port = atoi(optarg);
                break;
            default:
                goto outer_break;
        }
    }
outer_break:
    //进入目录
    if(chdir(working_directory) < 0)
    {
        printf("cannot enter working directory %s",working_directory);
    }
    //创建套接字
    char ip[] = "0.0.0.0";
    int control_sock = create_socket(RECEIVE,ip,listening_port,5);

    while(1)
    {
        int* connection = (int*)malloc(sizeof(int));
        //接受连接，返回新套接字
        if((*connection = accept(control_sock, NULL, NULL)) == -1)
        {
            printf("Error accept(): %s(%d)\n", strerror(errno), errno);
            free(connection);
            continue;
        }
        //创建服务线程
        pthread_t pid;
        Tran* tran = (Tran*)malloc(sizeof(Tran));
        tran->connection = *connection;
        strcpy(tran->temp_directory,working_directory);
        if(pthread_create(&pid, NULL, serve_client, tran) != 0)
        {
            printf("error when creating a thread");
        }
    }
    //关闭套接字
    //close(control_sock);
    return 0;
}

