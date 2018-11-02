//
//  common.c
//  ftp_test
//
//  Created by 刘译键 on 2018/10/27.
//  Copyright © 2018年 刘译键. All rights reserved.
//

#include "common.h"

long int send_string(int sock, char *str)
{
    long int total = 0; // how many bytes we've sent
    long int charsleft = strlen(str); // how many we have left to send
    long int n = 0;
    while(total < strlen(str))
    {
        n = send(sock, str+total, charsleft, 0);
        if (n == -1)
        {
            break;
        }
        total += n;
        charsleft -= n;
    }
    if(n == -1)
    {
        printf("Error send(): %s(%d)\n", strerror(errno), errno);
    }
    else
    {
//        printf("sent %ld bytes\n", total);
    }
    return n==-1 ? -1 : total; // return -1 on failure, 0 on success
}

void response(Command* cmd, State* state)
{
    char* verb = cmd->command;
    char* para = cmd->arg;
    printf("%s ",verb);
    printf("%s\n",para);
    if(equal(verb,"USER"))
    {
        if(equal(para,"anonymous"))
        {
            state->username_ok = 1;
            send_string(state->connection,USER_ACCEPTED);
        }
        else
        {
            send_string(state->connection, USER_DENIED);
        }
    }
    else if(equal(verb,"PASS"))
    {
        if(state->username_ok)
        {
            state->logged_in = 1;
            send_string(state->connection, LOGIN_OK);
        }
        else
        {
            send_string(state->connection, NEED_USERNAME);
        }
    }
    else if(equal(verb,"PASV"))
    {
        if(state->logged_in)
        {
            //pasv模式下，使用公网ip
            //char ip[100];
            //getlocalip(ip);
            char ip[] = "127.0.0.1";
            int port = generate_port();
            printf("%d",port);
            char msg[100];
            sprintf(msg,"227 Entering Passive Mode(%d,%d,%d,%d,%d,%d)\r\n",127,0,0,1,port/256,port%256);
            state->sock_pasv = create_socket(RECEIVE, ip, port, 5);
            state->mode = 1;
            send_string(state->connection, msg);
        }
        else
        {
            send_string(state->connection, USER_DENIED);
        }
    }
    else if(equal(verb,"PORT"))
    {
        if(state->logged_in)
        {
            int ip[6];
            int port;
            char seps[] = ",";
            char ip_ch[50];
            char* token = strtok(cmd->arg,seps);
            for(int i = 0; i < 6; i++)
            {
                ip[i] = atoi(token);
                token = strtok(NULL,seps);
            }
            port = ip[4]*256+ip[5];
            sprintf(ip_ch,"%d.%d.%d.%d",ip[0],ip[1],ip[2],ip[3]);
            strcpy(state->ip,ip_ch);
            state->port = port;
            state->mode = 2;
            send_string(state->connection,PORT_OK);
        }
        else
        {
            send_string(state->connection, USER_DENIED);
        }
    }
    else if(equal(verb,"RETR"))
    {
        if(state->logged_in)
        {
            if(state->mode == 0)
            {
                send_string(state->connection, NEED_TRANSFER);
                return;
            }
            if(state->mode == 1)
            {
                FILE* fd;
                //能打开文件
                fd = fopen(cmd->arg,"rb");
                printf("1");
                if(!fd)
                {
                    send_string(state->connection, NO_FILE);
                    if(state->sock_pasv)
                        close(state->sock_pasv);
                    state->mode = 0;
                    return;
                }
                send_string(state->connection, TRANSFER_START);
                //有TCP连接
                if((state->transfer_pid = accept(state->sock_pasv, NULL, NULL)) == -1)
                {
                    send_string(state->connection, NEED_TRANSFER_TCP1);
                    return;
                }
                //开始传输
                send_file(fd, state->transfer_pid);
                //结束传输
                fclose(fd);
                send_string(state->connection, TRANSFER_OK);
                close(state->sock_pasv);
                close(state->transfer_pid);
                state->mode = 0;
            }
            if(state->mode == 2)
            {
                FILE* fd;

                //能打开文件
                fd = fopen(cmd->arg,"rb");
                sleep(1);
                if(!fd)
                {
                    send_string(state->connection, NO_FILE);
                    state->mode = 0;
                    return;
                }
                send_string(state->connection, TRANSFER_START);
                //有TCP连接
                state->transfer_pid = create_socket(SEND, state->ip, state->port, 0);
                if(state->transfer_pid== -1)
                {
                    send_string(state->connection, NEED_TRANSFER_TCP2);
                    return;
                }
                //开始传输
                send_file(fd, state->transfer_pid);
                //结束传输
                fclose(fd);
                close(state->transfer_pid);
                send_string(state->connection, TRANSFER_OK);
//                close(state->sock_port);
                state->mode = 0;
            }
        }
        else
        {
            send_string(state->connection, USER_DENIED);
        }
    }
    else if(equal(verb,"STOR"))
    {
        if(state->logged_in)
        {
            if(state->mode == 0)
            {
                send_string(state->connection, NEED_TRANSFER);
                return;
            }
            if(state->mode == 1)
            {
                FILE* fd;
                //能打开文件
                fd = fopen(cmd->arg,"wb");
                if(!fd)
                {
                    send_string(state->connection, NO_FILE);
                    printf("1");
                    if(state->sock_pasv)
                        close(state->sock_pasv);
                    state->mode = 0;
                    return;
                }
                //有TCP连接
                if((state->transfer_pid = accept(state->sock_pasv, NULL, NULL)) == -1)
                {
                    send_string(state->connection, NEED_TRANSFER_TCP1);
                    return;
                }
                //开始传输
                send_string(state->connection, TRANSFER_START);
                recv_file(fd, state->transfer_pid);
                //结束传输
                fclose(fd);
                send_string(state->connection, TRANSFER_OK);
                close(state->transfer_pid);
                state->mode = 0;
            }
            if(state->mode == 2)
            {
                FILE* fd;
                //能打开文件
                fd = fopen(cmd->arg,"wb");
                if(!fd)
                {
                    send_string(state->connection, NO_FILE);
                    if(state->transfer_pid)
                        close(state->transfer_pid);
                    state->mode = 0;
                    return;
                }
                //有TCP连接
                state->transfer_pid = create_socket(SEND, state->ip, state->port, 0);
                if(state->transfer_pid== -1)
                {
                    send_string(state->connection, NEED_TRANSFER_TCP2);
                    return;
                }
                //开始传输
                send_string(state->connection, TRANSFER_START);
                recv_file(fd, state->transfer_pid);
                //结束传输
                fclose(fd);
                send_string(state->connection, TRANSFER_OK);
                close(state->transfer_pid);
                state->mode = 0;
            }
        }
        else
        {
            send_string(state->connection, USER_DENIED);
        }
    }
    else if(equal(verb,"PWD"))
    {
        if(state->logged_in)
        {
            char buffer[BSIZE+100];
            memset(buffer,0,BSIZE+100);
            getcwd(state->temp_directory,sizeof(state->temp_directory));
            sprintf(buffer,"257 \"%s\"\r\n",state->temp_directory);
            send_string(state->connection, buffer);
        }
        else
        {
            send_string(state->connection, USER_DENIED);
        }
    }
    else if(equal(verb,"CWD"))
    {
        if(state->logged_in)
        {
            if(chdir(cmd->arg) == 0)
            {
                send_string(state->connection, CHANGE_DIR);
            }
            else
            {
                send_string(state->connection, NOT_CHANGE_DIR);
            }
        }
        else
        {
            send_string(state->connection, USER_DENIED);
        }
    }
    else if(equal(verb,"MKD"))
    {
        if(state->logged_in)
        {
            if(mkdir(cmd->arg,S_IRWXU)==0)
            {
                send_string(state->connection, MAKE_DIR);
            }
            else
            {
                send_string(state->connection, NOT_MAKE_DIR);
            }
        }
        else
        {
            send_string(state->connection, USER_DENIED);
        }
    }
    else if(equal(verb,"LIST"))
    {
        if(state->logged_in)
        {
            if(state->mode == 0)
            {
                send_string(state->connection, NEED_TRANSFER);
                return;
            }
            send_string(state->connection, TRANSFER_START);
            FILE* f;
            char list_info[BSIZE];
            memset(list_info,0,BSIZE);
            snprintf(list_info, BSIZE, "ls -l %s",cmd->arg);
            if((f = popen(list_info, "r")) == NULL)
            {
                send_string(state->connection, NO_FILE);
                if(state->sock_pasv)
                {
                    close(state->sock_pasv);
                }
                state->mode = 0;
                return;
            }

            if(state->mode == 1)
            {
                long int n;
                char buf[BSIZE];
                if((state->transfer_pid = accept(state->sock_pasv, NULL, NULL)) == -1)
                {
                    send_string(state->connection, NEED_TRANSFER_TCP1);
                    pclose(f);
                    return;
                }
                do
                {
                    n = fread(buf, 1, 8190, f);
                    send(state->transfer_pid, buf, n, 0);
                } while (n > 0);
                pclose(f);
                send_string(state->connection, TRANSFER_OK);
                close(state->transfer_pid);
                close(state->sock_pasv);
                state->mode = 0;
            }
            if(state->mode == 2)
            {
                long int n;
                char buf[BSIZE];
                state->transfer_pid = create_socket(SEND, state->ip, state->port, 0);
                if(state->transfer_pid== -1)
                {
                    send_string(state->connection, NEED_TRANSFER_TCP2);
                    pclose(f);
                    return;
                }
                do
                {
                    n = fread(buf, 1, 8190, f);
                    send(state->transfer_pid, buf, n, 0);
                } while (n > 0);
                pclose(f);
                send_string(state->connection, TRANSFER_OK);
                close(state->transfer_pid);
                state->mode = 0;
            }
        }
        else
        {
            send_string(state->connection, USER_DENIED);
        }
    }
    else if(equal(verb,"RMD"))
    {
        if(state->logged_in)
        {
            if(remove(cmd->arg) == 0)
            {
                send_string(state->connection, REMOVE_DIR);
            }
            else
            {
                send_string(state->connection, NOT_REMOVE_DIR);
            }
        }
        else
        {
            send_string(state->connection, USER_DENIED);
        }
    }
    else if(equal(verb,"RNFR"))
    {
        if(state->logged_in)
        {
            if(access(cmd->arg,0) == 0)
            {
                strcpy(state->oldname,cmd->arg);
                send_string(state->connection, HAVE_FILE);
            }
            else
            {
                send_string(state->connection, NO_FILE);
            }
        }
        else
        {
            send_string(state->connection, USER_DENIED);
        }
        
    }
    else if(equal(verb,"RNTO"))
    {
        if(state->logged_in)
        {
            if(rename(state->oldname, cmd->arg) == 0)
            {
                send_string(state->connection, RENAME_FILE);
            }
            else
            {
                send_string(state->connection, NOT_RENAME_FILE);
            }
        }
        else
        {
            send_string(state->connection, USER_DENIED);
        }
    }
    else if(equal(verb,"SYST"))
    {
        if(state->logged_in)
        {
            send_string(state->connection, TYPE_HARD);
        }
        else
        {
            send_string(state->connection, USER_DENIED);
        }
    }
    else if(equal(verb,"QUIT"))
    {
        if(state->logged_in)
        {
            if(state->mode == 1)
            {
                //close(state->sock_pasv);
            }
            send_string(state->connection, BYE);
        }
        else
        {
            send_string(state->connection, USER_DENIED);
        }
        state->username_ok = 0;
        state->username = NULL;
        state->logged_in = 0;
        state->mode = 0;
//        printf("a");
    }
    else if(equal(verb,"ABOR"))
    {
        if(state->logged_in)
        {
            if(state->mode == 1)
            {
                //close(state->sock_pasv);
            }
            send_string(state->connection, BYE);
        }
        else
        {
            send_string(state->connection, USER_DENIED);
        }
        state->username_ok = 0;
        state->username = NULL;
        state->logged_in = 0;
        state->mode = 0;
    }
    else if(equal(verb,"TYPE"))
    {
        if(state->logged_in)
        {
            if(equal(para,"I"))
            {
                send_string(state->connection, TYPE_SET_I);
            }
            else
            {
                send_string(state->connection, NOT_ACCEPT_PARA);
            }
        }
        else
        {
            send_string(state->connection, USER_DENIED);
        }
    }
    else
    {
        send_string(state->connection, WROND_COMMAND);
    }
}

int create_socket(int send_or_recv, char* ip, int port, int listen_max_num)
{
    int sock;
    int reuse = 1;
    struct sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_port = htons(port);
    address.sin_addr.s_addr = inet_addr(ip);
    bzero(&(address.sin_zero), 8);
    
    if((sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)) < 0)
    {
        fprintf(stderr, "Cannot open socket");
        return -1;
    }
    
    if(send_or_recv == RECEIVE)
    {
        setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof reuse);
        if(bind(sock,(struct sockaddr*) &address, sizeof(address)) < 0)
        {
            printf("cannot bind %s",strerror(errno));
            return -1;
        }
        if (listen(sock,listen_max_num) == -1)
        {
            printf("cannot listen");
            return -1;
        }
    }
    if(send_or_recv == SEND)
    {
        if(connect(sock,(struct sockaddr*)&address,sizeof(struct sockaddr)) == -1)
        {
            fprintf(stderr,"Cannot connect to client specific port");
            return -1;
        }
    }
    return sock;
}

int getlocalip(char* ip)
{
    struct ifaddrs * ifAddrStruct=NULL;
    void * tmpAddrPtr=NULL;
    
    getifaddrs(&ifAddrStruct);
    int i = 0;
    while (ifAddrStruct!=NULL)
    {
        if (ifAddrStruct->ifa_addr->sa_family==AF_INET)
        {   // check it is IP4
            // is a valid IP4 Address
            tmpAddrPtr = &((struct sockaddr_in *)ifAddrStruct->ifa_addr)->sin_addr;
            char addressBuffer[INET_ADDRSTRLEN];
            inet_ntop(AF_INET, tmpAddrPtr, addressBuffer, INET_ADDRSTRLEN);
            if(i == 0)
            {
                i++;
                ifAddrStruct = ifAddrStruct->ifa_next;
                continue;
            }
            strcpy(ip,addressBuffer);
            return 1;
        }
        ifAddrStruct = ifAddrStruct->ifa_next;
    }
    return 0;
}

int generate_port()
{
    int port = (2 * rand()) % 3536 + 40000;
    return port;
}

void send_file(FILE* f, int sock)
{
    long int n;
    char buf[BSIZE];
    do
    {
        n = fread(buf, 1, BSIZE-2, f);
        send(sock, buf, n, 0);
    } while (n > 0);
    return;
}

void recv_file(FILE* f, int sock)
{
    long int n;
    char buf[BSIZE];
    do
    {
        n = recv(sock, buf, BSIZE-2, 0);
        fwrite(buf, 1, n, f);
    } while (n > 0);
    return;
}

void* serve_client(void* _c)
{
    //服务器对应该客户的套接字
    Tran tran = *(Tran*)_c;
    int sock = tran.connection;
    long int bytes;
    Command* cmd = (Command*)malloc(sizeof(Command));
    State* state = (State*)malloc(sizeof(State));
    char buffer[BSIZE];
    //初始化
    memset(buffer,0,BSIZE);
    state->username = NULL;
    state->connection = sock;
    state->mode = 0;
    strcpy(state->temp_directory,tran.temp_directory);
    chdir(state->temp_directory);
    send_string(sock,GREETING);
    //接受命令
    while(1)
    {
        //读取客户输入
        bytes = read(sock,buffer,BSIZE);
        if(bytes <= 0)
        {
            printf("connect error");
            break;
        }
        //解析命令
        sscanf(buffer,"%s %s",cmd->command,cmd->arg);
        response(cmd,state);
        sleep(0.01);
        if(equal(cmd->command,"ABOR") || equal(cmd->command,"QUIT"))
            break;
        //重置buffer和cmd
        memset(buffer,0,BSIZE);
        memset(cmd,0,sizeof(Command));
    }
    //回收资源
    free(cmd);
    free(state);
    close(sock);
    //printf("Client disconnected.\n");
    return NULL;
}
