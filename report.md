#FTP实验说明文档
***

###FTP服务器项目说明

* 系统环境：ubuntu16.04

* 编译器：gcc 5.4.0

* 编程语言：c

* 文件结构
	* common.h
		* 定义结构体State，维护每一个客户的ftp连接的状态
		* 定义结构体Cmd，解析每个客户发送到控制端的消息中每一条的命令及参数
		* 定义服务器返回给客户的消息的宏
		* 定义默认运行目录，默认监听端口
		* 声明相关函数
	* common.c
		*  消息处理函数: void response(Command* cmd, State\* state)
		*  创建连接函数: int create_socket(int send-or-recv, char* ip, int port, int listen-max-num)
		*  服务客户函数： void serve_client(void* _c)
		*  自动生成端口函数：int generate_port()
	* main.c
		*  读取命令行参数来修改root和port
		*  while循环接收客户连接，并为每个客户创建一个新线程
	* makefile
		*  定义编译依赖关系，用于ubuntu下make操作
	* server
		*  linux可执行文件
* 实现的ftp命令
	* USER PASS 
	* PASV PORT 
	* STOR RETR 
	* RNFR RNTO 
	* MKD PWD CWD RMD 
	* LIST
	* TYPE 
	* SYST 
	* ABOR QUIT
	
***

###FTP客户端项目说明


#####运行环境
*	python3.7

*	调用库：socket，time，threading

#####运行方法
* client.py是一个自动化测试的脚本

* client.py实现了ftp客户端的命令功能

* 可自定义新线程，使用封装好的函数组合来完成新样例测试

#####实现说明
* 定义了一个FTP类，将标准FTP的命令封装成类中的方法
* 在\__init__方法中,初始化该ftp连接所需要用到的一些属性，具体见代码中注释

*** 

### 相关库函数介绍

#####sprintf函数
```c
//构造pasv的返回命令
sprintf(msg,"227 Entering Passive Mode(%d,%d,%d,%d,%d,%d)\r\n",
		127,0,0,1,port/256,port%256);
```
#####getcwd函数
```c
//获取当前目录
getcwd(state->temp_directory,sizeof(state->temp_directory));
```
#####sscanf函数
```c
//解析命令
sscanf(buffer,"%s %s",cmd->command,cmd->arg);
```
#####getopt_long\_only函数
```c
//获取命令行参数
c = getopt_long_only(argc, argv, "rp:", long_options, &option_index);
```
#####snprintf函数
```c
//拿到list命令对应的内容
snprintf(list_info, BSIZE, "ls -l %s",cmd->arg);
```
***

###坑的总结
* linux和MacOS调用sendfile的内核方法时，函数存在差异，前者为4参数，后者为6参数
* read函数在socket出错或其他异常情况下的时候返回值小于等于0，忘记判断将导致线程死循环
* 客户退出后，要回收为该客户分配的资源
* list命令中用到popen()函数，必须使用pclose()函数关闭，否则会有僵尸进程
* 测评脚本测试21端口时，需要sudo权限，在server可执行文件的相同目录下运行命令 sudo python autograde.py
* makefile文件需要添加 -lpthread 选项
* warning出现的地方主要是将某些int型改变成long int型，适应64位系统
* 客户端编写时在pasv和port模式下注意创建socket和发送命令的先后顺序不同
* 客户端每个命令都必须recv()正确的次数，防止recv()错位的问题，一开始要recv()一个220欢迎信息

***

###编程技巧
* 在if中执行命令，这样若有异常，处理起来比较方便
* 向线程传递多个参数时，可以将这些参数包装成一个结构体，传指针，再在新线程中解析该结构体拿到多个参数
* 将createsocket包装成一个函数，便于创建本地监听套接字或连接远端套接字


