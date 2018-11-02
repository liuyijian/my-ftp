from tkinter import *
from tkinter.messagebox import *
from tkinter.filedialog import *
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
    
    def connect(self):
        try:
            # self.sock.bind((self.ip_port,self.listen_port))
            self.sock.connect((self.ip,self.port))
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
        return self.buffer

    def pass_command(self,password="myt123"):
        self.sock.send(("PASS %s\r\n"%(password)).encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)
        return self.buffer

    def pasv_command(self):
        self.sock.send("PASV\r\n".encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)
        temp = self.buffer.split('(')[1].split(')')[0].split(',')
        self.ip_pasv = temp[0]+'.'+temp[1]+'.'+temp[2]+'.'+temp[3]
        self.port_pasv = int(temp[4]) * 256 +int(temp[5])
        self.mode = 1
        return self.buffer

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
        return self.buffer

    def retr_command(self,filename,showframe):
        if(self.mode == 1):
            self.pasv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.pasv_sock.connect((self.ip_pasv,self.port_pasv))

        self.sock.send(("RETR %s\r\n"%(filename)).encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)
        showframe.insert(END,self.buffer)
        showframe.see(showframe.index(END))
        if(self.buffer.startswith('5') or self.buffer.startswith('4')):
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
            showframe.insert(END,self.buffer)
            showframe.see(showframe.index(END))

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
            showframe.insert(END,self.buffer)
            showframe.see(showframe.index(END))
        else:
            pass
        
    def stor_command(self,filename,showframe):
        
        if(self.mode == 1):
            self.pasv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.pasv_sock.connect((self.ip_pasv,self.port_pasv))

        self.sock.send(("STOR %s\r\n"%(filename)).encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)
        showframe.insert(END,self.buffer)
        showframe.see(showframe.index(END))
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
            showframe.insert(END,self.buffer)
            showframe.see(showframe.index(END))

        elif(self.mode == 2):
            self.new_sock = self.port_sock.accept()[0]
            f = open(filename,'rb')
            while(1):
                buffer = f.read(self.size)
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
            showframe.insert(END,self.buffer)
            showframe.see(showframe.index(END))
        else:
            pass

    def mkd_command(self,dirname):
        self.sock.send(("MKD %s\r\n"%(dirname)).encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)
        return self.buffer

    def cwd_command(self,dirname):
        self.sock.send(("CWD %s\r\n"%(dirname)).encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)
        return self.buffer

    def pwd_command(self):
        self.sock.send("PWD\r\n".encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)
        return self.buffer

    def rmd_command(self,dirname):
        self.sock.send(("RMD %s\r\n"%(dirname)).encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)
        return self.buffer

    def list_command(self,filename,showframe):
        if(self.mode == 1):
            self.pasv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.pasv_sock.connect((self.ip_pasv,self.port_pasv))

        self.sock.send(("LIST %s\r\n"%(filename)).encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)
        showframe.insert(END,self.buffer)

        if(self.buffer.startswith('5')):
            if(self.mode == 1):
                self.pasv_sock.close()
            self.mode = 0
            return
        
        if(self.mode == 1):
            temp = ''
            while(1):
                buffer = self.pasv_sock.recv(self.size).decode('utf-8')
                print(buffer,end='')
                temp += buffer
                if(buffer == ''):
                    break
            self.pasv_sock.close()
            self.mode = 0
            temp_list = temp.split('\n')
            for i in temp_list:
                showframe.insert(END,i)    
            #显示transfer successful
            self.buffer = self.sock.recv(self.size).decode('utf-8')
            print(self.buffer)
            showframe.insert(END,self.buffer)

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
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)
        return self.buffer

    def rnto_command(self,filename):
        self.sock.send(("RNTO %s\r\n"%(filename)).encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)
        return self.buffer

    def syst_command(self):
        self.sock.send("SYST\r\n".encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)
        return self.buffer

    def type_command(self,para):
        self.sock.send(("TYPE %s\r\n"%para).encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)
        return self.buffer

    def quit_command(self):
        self.sock.send("QUIT\r\n".encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)
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
        return self.buffer

    def wrong_command(self):
        self.sock.send("QQQQ\r\n".encode('utf-8'))
        self.buffer = self.sock.recv(self.size).decode('utf-8')
        print(self.buffer)
        return self.buffer


class GUI():
    #初始化界面参数
    def __init__(self):
        #建立窗口
        self.root = Tk()
        self.root.title('ftp客户端')
        self.root.geometry('600x400')
        self.root.resizable(0,0)
        self.ftp = 0
        #用户名相关
        self.user = StringVar()
        self.user.set('anonymous')
        self.user_label = Label(self.root, text='用户名')
        self.user_entry = Entry(self.root, textvariable=self.user,width=15)
        self.user_label.place(x=10,y=21,anchor=NW)
        self.user_entry.place(x=60,y=20,anchor=NW)
        #密码相关
        self.password = StringVar()
        self.password.set('')
        self.password_label = Label(self.root,text='密码')
        self.password_entry = Entry(self.root,textvariable=self.password,show='*', width=15)
        self.password_label.place(x=10,y=51,anchor=NW)
        self.password_entry.place(x=60,y=50,anchor=NW)
        #服务器ip
        self.server_ip = StringVar()
        self.server_ip.set('127.0.0.1')
        self.server_ip_label = Label(self.root,text='服务器ip地址')
        self.server_ip_entry = Entry(self.root,textvariable=self.server_ip,width=15)
        self.server_ip_label.place(x=220,y=21,anchor=NW)
        self.server_ip_entry.place(x=320,y=20,anchor=NW)
        #服务器端口
        self.server_port = StringVar()
        self.server_port.set(8021)
        self.server_port_label = Label(self.root,text='服务器控制端口')
        self.server_port_entry = Entry(self.root,textvariable=self.server_port,width=15)
        self.server_port_label.place(x=220,y=51,anchor=NW)
        self.server_port_entry.place(x=320,y=50,anchor=NW)
        #登录相关
        self.log_sign = IntVar()
        self.log_sign.set(0)
        self.log_button_text = StringVar()
        self.log_button_text.set('登录')
        self.log_button = Button(self.root, textvariable=self.log_button_text, font='Arial -25', activeforeground='#BC8F8F')
        self.log_button.bind('<Button-1>',self.log_in_out)
        self.log_button.place(x=500,y=30,anchor=NW)
        #展示相关——区域
        self.frame = Frame(height=200,width=560)
        self.frame.place(x=15,y=80,anchor=NW)
        #展示相关——窗口
        self.reponse = StringVar()
        self.response_window = Listbox(self.frame,listvariable=self.reponse,width=60)
        self.response_window.place(x=0,y=0,anchor=NW)
        #展示相关——进度条
        self.bar = Scrollbar(self.frame)
        self.bar.place(x=550,y=0,anchor=NW,relheight=0.87)
        #展示关联——同步绑定
        self.response_window['yscrollcommand'] = self.bar.set
        self.bar['command'] = self.response_window.yview
        '''功能相关'''
        #下载文件
        self.retr_label = Label(self.root,text='下载文件')
        self.retr_path = StringVar()
        self.retr_path.set('')
        self.retr_mode = StringVar()
        self.retr_mode.set('PASV')
        self.retr_mode_menu = OptionMenu(self.root,self.retr_mode,'PASV','PORT')
        self.retr_entry = Entry(self.root,textvariable = self.retr_path,width=15)
        self.retr_button = Button(self.root,text='下载')
        self.retr_button.bind('<Button-1>',self.download)
        self.retr_entry['state'] = 'disabled'
        self.retr_mode_menu['state'] = 'disabled'
        self.retr_button['state'] = 'disabled'
        self.retr_label.place(x=10,y=260,anchor=NW)
        self.retr_entry.place(x=70,y=260,anchor=NW)
        self.retr_mode_menu.place(x=296,y=262,anchor=NW)
        self.retr_button.place(x=365,y=263,anchor=NW)
        #上传文件
        self.stor_label = Label(self.root,text='上传文件')
        self.stor_path = StringVar()
        self.stor_path.set('')
        self.stor_mode = StringVar()
        self.stor_mode.set('PASV')
        self.stor_mode_menu = OptionMenu(self.root,self.stor_mode,'PASV','PORT')
        self.stor_entry = Entry(self.root,textvariable = self.stor_path,width=15)
        self.stor_button = Button(self.root,text='上传')
        self.stor_button.bind('<Button-1>',self.upload)
        self.choose_file_button = Button(self.root,text='选择文件')
        self.choose_file_button.bind('<Button-1>',self.filechoose)
        self.stor_entry['state'] = 'disabled'
        self.choose_file_button['state'] = 'disabled'
        self.stor_mode_menu['state'] = 'disabled'
        self.stor_button['state'] = 'disabled'
        self.stor_label.place(x=10,y=290,anchor=NW)
        self.stor_entry.place(x=70,y=290,anchor=NW)
        self.choose_file_button.place(x=230,y=293,anchor=NW)
        self.stor_mode_menu.place(x=296,y=292,anchor=NW)
        self.stor_button.place(x=365,y=293,anchor=NW)
        #目录改变
        self.dir = StringVar()
        self.dir_mode = StringVar()
        self.dir_mode.set('PWD')
        self.dir_mode_menu = OptionMenu(self.root,self.dir_mode,'PWD','CWD','MKD','RMD','LIST')
        self.dir_mode_menu['state'] = 'disabled'
        self.dir_label = Label(self.root,text='目录名称')
        self.dir_entry = Entry(self.root,textvariable = self.dir,width=15)
        self.dir_entry['state']='disabled'
        self.dir_button = Button(self.root,text='确认')
        self.dir_button['state'] = 'disabled'
        self.dir_button.bind('<Button-1>',self.opdir)
        self.dir_label.place(x=10,y=323,anchor=NW)
        self.dir_entry.place(x=70,y=323,anchor=NW)
        self.dir_mode_menu.place(x=296,y=322,anchor=NW)
        self.dir_button.place(x=365,y=323,anchor=NW)
        #重命名
        self.last_name = StringVar()
        self.new_name = StringVar()
        self.last_name_label = Label(self.root,text='原文件名')
        self.last_name_entry = Entry(self.root,textvariable=self.last_name,width=10)
        self.last_name_entry['state'] = 'disabled'
        self.new_name_label = Label(self.root,text='新文件名')
        self.new_name_entry = Entry(self.root,textvariable=self.new_name,width=10)
        self.new_name_entry['state'] = 'disabled'
        self.name_button = Button(self.root,text='重命名')
        self.name_button.bind('<Button-1>',self.rename)
        self.name_button['state']='disabled'
        self.last_name_label.place(x=10,y=353,anchor=NW)
        self.last_name_entry.place(x=70,y=353,anchor=NW)
        self.new_name_label.place(x=170,y=353,anchor=NW)
        self.new_name_entry.place(x=230,y=353,anchor=NW)
        self.name_button.place(x=365,y=353,anchor=NW)
        #syst和type
        self.syst_button = Button(self.root,text='系统')
        self.type_button = Button(self.root,text='类型')
        self.syst_button.bind('<Button-1>',self.syst_do)
        self.type_button.bind('<Button-1>',self.type_do)
        self.syst_button['state']='disabled'
        self.type_button['state']='disabled'
        self.syst_button.place(x=500,y=353,anchor=NW)
        self.type_button.place(x=500,y=323,anchor=NW)

    def run(self):
        self.root.mainloop()

    def log_in_out(self,event):
        if self.log_sign.get() == 0:
            try:
                self.ftp = FTP(self.server_ip.get(), int(self.server_port.get()))
                print(self.user.get(),self.password.get())
                if(not self.ftp.connect()):
                    raise ValueError
                # showinfo(message='连接成功')
                self.response_window.insert(END,self.ftp.user_command(username=self.user.get()))
                self.response_window.see(self.response_window.index(END))
                self.response_window.insert(END,self.ftp.pass_command(password=self.password.get()))    
                self.response_window.see(self.response_window.index(END)) 
            except: 
                showerror(message='连接失败')
                return     
            self.log_button_text.set('注销')
            self.user_entry['state'] = 'disabled'
            self.password_entry['state'] = 'disabled'
            self.server_ip_entry['state'] = 'disabled'
            self.server_port_entry['state'] = 'disabled'
            self.log_sign.set(1)
            self.retr_entry['state'] = 'normal'
            self.retr_mode_menu['state'] = 'normal'
            self.retr_button['state'] = 'normal'
            self.stor_entry['state'] = 'normal'
            self.choose_file_button['state'] = 'normal'
            self.stor_mode_menu['state'] = 'normal'
            self.stor_button['state'] = 'normal'
            self.dir_entry['state']='normal'
            self.dir_mode_menu['state'] = 'normal'
            self.dir_button['state'] = 'normal'
            self.name_button['state']='normal'
            self.new_name_entry['state']='normal'
            self.last_name_entry['state']='normal'
            self.syst_button['state']='normal'
            self.type_button['state']='normal'
        else:
            try:
                self.response_window.insert(END,self.ftp.quit_command())
                self.response_window.see(self.response_window.index(END))
                self.log_button_text.set('登录')
                self.user_entry['state'] = 'normal'
                self.password_entry['state'] = 'normal'
                self.server_ip_entry['state'] = 'normal'
                self.server_port_entry['state'] = 'normal'
                self.log_sign.set(0)
                self.retr_entry['state'] = 'disabled'
                self.retr_mode_menu['state'] = 'disabled'
                self.retr_button['state'] = 'disabled'
                self.stor_entry['state'] = 'disabled'
                self.choose_file_button['state'] = 'disabled'
                self.stor_mode_menu['state'] = 'disabled'
                self.stor_button['state'] = 'disabled'
                self.dir_entry['state']='disabled'
                self.dir_mode_menu['state'] = 'disabled'
                self.dir_button['state'] = 'disabled'
                self.name_button['state']='disabled'
                self.new_name_entry['state']='disabled'
                self.last_name_entry['state']='disabled'
                self.syst_button['state']='disabled'
                self.type_button['state']='disabled'
                self.response_window.delete(0,END)
            except:
                return
    
    def upload(self,event):
        
        if self.stor_mode.get() == 'PASV':
            self.response_window.insert(END,self.ftp.pasv_command())
            self.ftp.mode = 1
            self.ftp.stor_command(self.stor_path.get(),self.response_window)
        
        else:
            self.response_window.insert(END,self.ftp.port_command(10000))
            self.ftp.mode = 2
            self.ftp.stor_command(self.stor_path.get(),self.response_window)
    
    
    def download(self,event):
       
        if self.retr_mode.get() == 'PASV':
            self.response_window.insert(END,self.ftp.pasv_command())
            self.response_window.see(self.response_window.index(END))
            self.ftp.mode = 1
            self.ftp.retr_command(self.retr_path.get(),self.response_window)
            print('finish')
        
        else:
            self.response_window.insert(END,self.ftp.port_command(10005))
            self.response_window.see(self.response_window.index(END))
            self.ftp.mode = 2
            print('2')
            print(self.retr_path.get())
            self.ftp.retr_command(self.retr_path.get(),self.response_window)
    
    
    def filechoose(self,event):

        self.stor_path.set(LoadFileDialog(self.root).go())
        return

    def opdir(self,event):
        mode = self.dir_mode.get()
        if(mode=='PWD'):
            self.response_window.insert(END,self.ftp.pwd_command())
        elif(mode=='CWD'):
            self.response_window.insert(END,self.ftp.cwd_command(self.dir.get()))
        elif(mode=='MKD'):
            self.response_window.insert(END,self.ftp.mkd_command(self.dir.get()))
        elif(mode=='RMD'):
            self.response_window.insert(END,self.ftp.rmd_command(self.dir.get()))
        elif(mode=='LIST'):
            self.response_window.insert(END,self.ftp.pasv_command())
            self.ftp.mode = 1
            self.ftp.list_command(self.dir.get(),self.response_window)
        
        self.response_window.see(self.response_window.index(END))
    
    def rename(self,event):
        self.response_window.insert(END,self.ftp.rnfr_command(self.last_name.get()))
        self.response_window.insert(END,self.ftp.rnto_command(self.new_name.get()))
        self.response_window.see(self.response_window.index(END))

    def syst_do(self,event):
        self.response_window.insert(END,self.ftp.syst_command())
        self.response_window.see(self.response_window.index(END))
    
    def type_do(self,event):
        self.response_window.insert(END,self.ftp.type_command('I'))
        self.response_window.see(self.response_window.index(END))

        
g = GUI()
g.run()
    
