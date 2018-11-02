# -*- coding: utf-8 -*-
import socket
import time
import threading as th

class FTP():
    def __init__(self,ip,port):
        #服务器ip
        self.ip = ip
        #服务器端口
        self.port = port
        #本机ip
        self.ip_port = '0.0.0.0'
        #本机控制端口
        self.listen_port = 0
        #pasv的对应ip
        self.ip_pasv = '0.0.0.0'
        #pasv的对应端口
        self.port_pasv = 0
        #port模式告诉服务器的端口，告诉服务器的ip默认为本机
        self.port_port = 0
        #缓冲区的大小
        self.size = 8192
        #当前传输模式
        self.mode = 0
        #缓冲区
        self.buffer = ''
        #本机控制socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #port模式下用于监听数据端连接的端口
        self.port_sock = 0
        #pasv下用于发送数据的socket
        self.pasv_sock = 0
        #port下用于发送数据的socket
        self.new_sock = 0
        self.connect_ftp(ip,port)
    
    def connect_ftp(self,ip,port):
        try:
            # self.sock.bind((self.ip_port,self.listen_port))
            self.sock.connect((ip,port))
            self.ip_port,self.listen_port = self.sock.getsockname()
            self.buffer = self.sock.recv(self.size).decode('utf-8')
            print(self.buffer)
            return 1
        except:
            print("cannot connect to this ip and port")
            return 0

    def user_command(self,username = "uftp"):
        self.sock.send(("USER %s\r\n"%(username)).encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)

    def pass_command(self,password="myt123"):
        self.sock.send(("PASS %s\r\n"%(password)).encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)

    def pasv_command(self):
        self.sock.send("PASV\r\n".encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)
        temp = self.buffer.split('(')[1].split(')')[0].split(',')
        self.ip_pasv = temp[0]+'.'+temp[1]+'.'+temp[2]+'.'+temp[3]
        self.port_pasv = int(temp[4]) * 256 +int(temp[5])
        self.mode = 1

    def port_command(self,port):
        self.port_port = port
        ip_and_port = self.ip_port.replace('.',',')+','+str(self.port_port//256)+','+str(self.port_port%256)
        self.sock.send(("PORT %s\r\n"%(ip_and_port)).encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)
        self.port_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port_sock.bind((self.ip_port,self.port_port))
        self.port_sock.listen(5)
        self.mode = 2

    def retr_command(self,filename):

        if(self.mode == 1):
            self.pasv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.pasv_sock.connect((self.ip_pasv,self.port_pasv))

        self.sock.send(("RETR %s\r\n"%(filename)).encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)

        if(self.buffer.startswith('5')):
            if(self.mode == 1):
                self.pasv_sock.close()
            self.mode = 0
            return
        
        if(self.mode == 1):
            #收文件
            f = open(filename,'wb')
            while(1):
                buffer = self.pasv_sock.recv(self.size)
                print('1')
                if(buffer == b''):
                    break
                f.write(buffer)
            f.close()
            self.pasv_sock.close()
            self.mode = 0
            #显示transfer successful
            self.buffer = self.sock.recv(self.size).decode('utf-8')
            print(self.buffer)

        elif(self.mode == 2):
            self.new_sock = self.port_sock.accept()[0]
            #收文件
            f = open(filename,'wb')
            while(1):
                buffer = self.new_sock.recv(self.size)
                if(buffer == b''):
                    break
                f.write(buffer)
            f.close()
            self.new_sock.close()
            self.port_sock.close()
            self.mode = 0
            #显示transfer successful
            self.buffer = self.sock.recv(self.size).decode('utf-8')
            print(self.buffer)
        else:
            pass
        
    def stor_command(self,filename):
        
        if(self.mode == 1):
            self.pasv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.pasv_sock.connect((self.ip_pasv,self.port_pasv))

        self.sock.send(("STOR %s\r\n"%(filename)).encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)

        if(self.mode == 1):
            f = open(filename,'rb')
            while(1):
                buffer = f.read(self.size)
                if(buffer == b''):
                    break
                self.pasv_sock.send(buffer)
            f.close()
            self.pasv_sock.close()
            self.mode = 0
            #显示transfer successful
            self.buffer = self.sock.recv(self.size).decode('utf-8')
            print(self.buffer)

        elif(self.mode == 2):
            self.new_sock = self.port_sock.accept()[0]
            print(self.new_sock)
            print('1')
            f = open(filename,'rb')
            print('1')
            while(1):
                buffer = f.read(self.size)
                print('1')
                if(buffer == b''):
                    break
                self.new_sock.send(buffer)
            f.close()
            self.new_sock.close()
            self.port_sock.close()
            self.mode = 0
            #显示transfer successful
            self.buffer = self.sock.recv(self.size).decode('utf-8')
            print(self.buffer)
        else:
            pass

    def mkd_command(self,dirname):
        self.sock.send(("MKD %s\r\n"%(dirname)).encode('utf-8'))
        self.buffer = self.sock.recv(self.size)
        print(self.buffer.decode('utf-8'))

    def cwd_command(self,dirname):
        self.sock.send(("CWD %s\r\n"%(dirname)).encode('utf-8'))
        self.buffer = self.sock.recv(self.size)
        print(self.buffer.decode('utf-8'))

    def pwd_command(self):
        self.sock.send("PWD\r\n".encode('utf-8'))
        self.buffer = self.sock.recv(self.size)
        print(self.buffer.decode('utf-8'))

    def rmd_command(self,dirname):
        self.sock.send(("RMD %s\r\n"%(dirname)).encode('utf-8'))
        self.buffer = self.sock.recv(self.size)
        print(self.buffer.decode('utf-8'))

    def list_command(self,filename):
        if(self.mode == 1):
            self.pasv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.pasv_sock.connect((self.ip_pasv,self.port_pasv))

        self.sock.send(("LIST %s\r\n"%(filename)).encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)

        if(self.buffer.startswith('5')):
            if(self.mode == 1):
                self.pasv_sock.close()
            self.mode = 0
            return
        
        if(self.mode == 1):
            while(1):
                buffer = self.pasv_sock.recv(self.size).decode('utf-8')
                print(buffer,end='')
                if(buffer == ''):
                    break
            self.pasv_sock.close()
            self.mode = 0
            #显示transfer successful
            self.buffer = self.sock.recv(self.size).decode('utf-8')
            print(self.buffer)

        elif(self.mode == 2):
            self.new_sock = self.port_sock.accept()[0]
            #收文件
            while(1):
                buffer = self.new_sock.recv(self.size).decode('utf-8')
                print(buffer,end='')
                if(buffer == ''):
                    break
            self.new_sock.close()
            self.port_sock.close()
            self.mode = 0
            #显示transfer successful
            self.buffer = self.sock.recv(self.size).decode('utf-8')
            print(self.buffer)
        else:
            pass

    def rnfr_command(self,filename):
        self.sock.send(("RNFR %s\r\n"%(filename)).encode('utf-8'))
        self.buffer = self.sock.recv(self.size)
        print(self.buffer.decode('utf-8'))

    def rnto_command(self,filename):
        self.sock.send(("RNTO %s\r\n"%(filename)).encode('utf-8'))
        self.buffer = self.sock.recv(self.size)
        print(self.buffer.decode('utf-8'))

    def syst_command(self):
        self.sock.send("SYST\r\n".encode('utf-8'))
        self.buffer = self.sock.recv(self.size)
        print(self.buffer.decode('utf-8'))

    def type_command(self,para):
        self.sock.send(("TYPE %s\r\n"%(para)).encode('utf-8'))
        self.buffer = self.sock.recv(self.size)
        print(self.buffer.decode('utf-8'))

    def quit_command(self):
        self.sock.send("QUIT\r\n".encode('utf-8'))
        self.buffer = self.sock.recv(self.size)
        print(self.buffer.decode('utf-8'))
        self.mode = 0
        try:
            self.port_sock.close()
        except:
            pass
        try:
            self.pasv_sock.close()
        except:
            pass
        self.sock.close()
    
    def wrong_command(self):
        self.sock.send("QQQQ\r\n".encode('utf-8'))
        self.buffer = self.sock.recv(self.size)
        print(self.buffer.decode('utf-8'))
    


# 标准服务器操作
# def test0():
#     s = FTP("47.93.96.117",21) 
#     s.user_command()
#     s.pass_command()
#     s.port_command(10002)
#     s.list_command('./')
#     s.port_command(10002)
#     s.list_command('./t')
#     s.port_command(10002)
#     s.list_command('test.txt')
#     s.port_command(10002)
#     s.retr_command('test.txt')
#     s.wrong_command()
#     s.quit_command()

# 用标准服务器测试
def test1():
    s = FTP("166.111.80.237",8279)
    s.user_command('cn2018')
    s.pass_command('ftp')
    s.type_command('I')
    s.syst_command()
    # 2
    s.pasv_command()
    s.list_command('./')
    s.pasv_command()
    s.retr_command('yyyy.txt')
    #3
    s.mkd_command('2016013239')
    s.list_command('./')
    s.rmd_command('2016013239')
    s.list_command('./')
    #4
    s.mkd_command('2016013239')
    s.pasv_command()
    s.list_command('./')
    s.cwd_command('2016013239')
    s.pwd_command()
    #5
    s.port_command(10002)
    s.stor_command('2016013239.txt')
    s.pasv_command()
    s.list_command('./')
    s.rnfr_command('2016013239.txt')
    s.rnto_command('2016013239-1.txt')
    s.pasv_command()
    s.list_command('./')
 #6
    s.quit_command()

def test2():
    s = FTP("127.0.0.1",8021)
    s.user_command('anonymous')
    s.pass_command('')
    s.type_command('I')
    s.syst_command()
    # 2
    s.pasv_command()
    s.list_command('./')
    # s.pasv_command()
    # s.retr_command('2.txt')
    # #3
    # s.mkd_command('2016013239')
    # s.list_command('./')
    # s.rmd_command('2016013239')
    # s.list_command('./')
    # #4
    # s.mkd_command('2016013239')
    # s.pasv_command()
    # s.list_command('./')
    # s.cwd_command('2016013239')
    # s.pwd_command()
    # #5
    # s.port_command(10004)
    # s.stor_command('2016013239.txt')
    # s.pasv_command()
    # s.list_command('./')
    # s.rnfr_command('2016013239.txt')
    # s.rnto_command('2016013239-1.txt')
    # s.pasv_command()
    # s.list_command('./')
    #6
    s.quit_command()

# t1 = th.Thread(target=test1)
# t1.start()

t2 = th.Thread(target=test2)
t2.start()










