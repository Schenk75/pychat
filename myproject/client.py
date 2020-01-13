import socket
import threading
import json 
import tkinter
import tkinter.messagebox
from tkinter.scrolledtext import ScrolledText 
import time
import os
from tkinter import filedialog
import webbrowser
from PIL import Image, ImageTk

IP = ''
PORT = ''
user = ''
# 本地图片缓存
client_cache = './imgcache_client'
# 若文件夹不存在，则创建
if not os.path.exists(client_cache):
    os.mkdir(client_cache)

################################################################## 登录窗口 #################################################################
root_login = tkinter.Tk()
root_login.title('登陆')
root_login['height'] = 200
root_login['width'] = 400
root_login.resizable(0, 0)  # 禁止放缩窗口

# 服务器标签UI
ip_server = tkinter.StringVar()
ip_server.set('127.0.0.1:50007')  # 设置服务器默认地址
label_ip = tkinter.Label(root_login, text='服务器地址')
label_ip.place(x=60, y=50, width=100, height=20)
entry_ip = tkinter.Entry(root_login, width=80, highlightcolor='red', highlightthickness=0.5, textvariable=ip_server)
entry_ip.place(x=170, y=50, width=130, height=20)

# 用户名标签UI
user = tkinter.StringVar()
user.set('')
label_user = tkinter.Label(root_login, text='用户名')
label_user.place(x=80, y=90, width=80, height=20)
entry_user = tkinter.Entry(root_login, width=80, highlightcolor='red', highlightthickness=0.5, textvariable=user)
entry_user.place(x=170, y=90, width=130, height=20)

# 登陆按钮
def login(*args):
    global IP, PORT, user
    IP, PORT = ip_server.get().split(':')
    PORT = int(PORT)
    user = entry_user.get()
    root_login.destroy()

root_login.bind('<Return>', login)
button_login = tkinter.Button(root_login, text='登陆', command=login)
button_login.place(x=165, y=140, width=70, height=30)
root_login.mainloop()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((IP, PORT))
if user:
    s.send(user.encode())  # 发送用户名
else:
    s.send('no'.encode())  # 没有输入用户名则标记no

# 如果没有用户名则将ip和端口号设置为用户名
addr = s.getsockname()  # 获取客户端ip和端口号
address = addr[0] + ':' + str(addr[1])
if user == '':
    user = address
else:
    user = user + '[' + str(addr[1]) + ']'

################################################################## 聊天窗口 #################################################################
user_list = []  # 在线用户列表
pic_dic = {}  # 图片字典
chat = '-------------群聊-------------'  # 聊天对象, 默认为群聊
root = tkinter.Tk()
root.title(user)
root['height'] = 600
root['width'] = 800
root.resizable(0, 0)  # 禁止放缩窗口

############################## 创建显示消息的主文本框
listbox = ScrolledText(root, bg='#F5F5DC')
listbox.place(x=160, y=0, width=640, height=500)
# 文本框使用的字体颜色
listbox.tag_config('red', foreground='red')
listbox.tag_config('blue', foreground='blue')
listbox.tag_config('green', foreground='green')
listbox.tag_config('purple', foreground='purple')
listbox.insert(tkinter.END, '欢迎来到这个简陋的小聊天室!斯是陋室，惟吾德馨！', 'blue')
# 设置文本框内容不能修改
listbox.configure(state='disabled')

############################## 创建显示在线用户的文本框
online_user_box_on = 0  # 在线用户列表框开关状态
online_user_box = tkinter.Listbox(root, bg='#F5FFFA')  
online_user_box.place(x=0, y=0, width=160, height=500)
# 打开关闭在线用户列表
def users_online():
    global online_user_box, online_user_box_on
    if online_user_box_on == 1:
        online_user_box.place(x=0, y=0, width=160, height=500)
        listbox.place(x=160, y=0, width=640, height=500)
        online_user_box_on = 0
    else:
        online_user_box.place_forget()  # 隐藏控件
        listbox.place(x=0, y=0, width=800, height=500)
        online_user_box_on = 1
# 查看在线用户按钮
button_online = tkinter.Button(root, text='在线用户', command=users_online)
button_online.place(x=715, y=500, width=80, height=40)
# 私聊功能通过点击在线用户实现
def private(*args):
    global chat, online_user_box
    # 获取点击的索引然后得到内容(用户名)
    id_clicks = online_user_box.curselection()
    id_click = id_clicks[0]
    chat = online_user_box.get(id_click)
    # 如果是群聊，不用调用私聊的函数
    if chat == '-------------群聊-------------':
        root.title(user)
        return       
    t = user + '  -->  ' + chat
    root.title(t)
online_user_box.bind('<ButtonRelease-1>', private)

############################## 创建输入消息的文本框
m = tkinter.StringVar()
m.set('')
entry_send_mes = tkinter.Entry(root, width=150, highlightcolor='red', highlightthickness=0.5, textvariable=m)
entry_send_mes.place(x=10, y=540, width=700, height=50)
def send(*args): 
    user_list.append('-------------群聊-------------')
    if chat not in user_list:
        tkinter.messagebox.showerror('发送失败', message='没有聊天对象!')
        return
    mes = entry_send_mes.get() + '$&' + user + '$&' + chat
    s.send(mes.encode())
    m.set('')  # 发送后清空文本框
# 创建发送按钮
button_send_mes = tkinter.Button(root, text='发送', command=send)
button_send_mes.place(x=720, y=550, width=70, height=40)
root.bind('<Return>', send)  # 绑定回车发送信息


############################## 接收服务端发送的信息并打印
def print_message():
    global user_list, pic_dic
    while True:
        data = s.recv(1024)
        data = data.decode()
        # 没有异常表示接收到的是在线用户列表
        try:
            data_user = json.loads(data)
            user_list = data_user
            online_user_box.delete(0, tkinter.END)  # 清空列表框
            number = ('        在线人数: ' + str(len(data_user)) + ' 人')
            online_user_box.insert(tkinter.END, number)
            online_user_box.itemconfig(tkinter.END, bg="#F08080")
            online_user_box.insert(tkinter.END, '-------------群聊-------------')
            online_user_box.itemconfig(tkinter.END, fg='green')
            for i in range(len(data_user)):
                online_user_box.insert(tkinter.END, (data_user[i]))
                online_user_box.itemconfig(tkinter.END, fg='green') 
        # 有异常表示接收到消息
        except:
            data = data.split('$&')
            # 消息形式为IP:PORT: 消息
            data_message = data[0].strip()  
            data_sender = data[1]  # 发送信息的用户名
            data_receiver = data[2]  # 接收消息者
            # print(data_message)
            # print(data_sender)
            # 将文本框改为可修改，打印信息
            listbox.configure(state='normal')

            # 开始发消息
            # 判断是不是表情或者图片
            if (data_message in emoji_dic) or data_message[:3] == '*^`':
                data_pic = '\n' + data_sender + ' ' + time.strftime('%Y-%m-%d,%H:%M:%S', time.localtime()) + ':\n '  
                if data_receiver == '-------------群聊-------------':
                    if data_sender == user:  # 如果是自己则将字体变为绿色
                        listbox.insert(tkinter.END, data_pic, 'green')
                    else:
                        listbox.insert(tkinter.END, data_pic)
                    # 发送表情
                    if data_message in emoji_dic:
                        # 将表情图贴到聊天框
                        listbox.image_create(tkinter.END, image=emoji_dic[data_message])
                    # 发送图片
                    else:
                        # print(pic_dic)
                        while True:
                            # 如果本地缓存有该图片就不用重复下载
                            try:
                                listbox.image_create(tkinter.END, image=pic_dic[data_message[3:]])
                                break
                            except:
                                download_img(data_message[3:])
                elif data_sender == user or data_receiver == user:  # 显示私聊
                    listbox.insert(tkinter.END, data_pic, 'red') 
                    # 发送表情
                    if data_message in emoji_dic:
                        # 将表情图贴到聊天框
                        listbox.image_create(tkinter.END, image=emoji_dic[data_message])
                    # 发送图片
                    else:
                        while True:
                            # 如果本地缓存有该图片就不用重复下载
                            try:
                                listbox.image_create(tkinter.END, image=pic_dic[data_message[3:]])
                                break
                            except:
                                download_img(data_message[3:])
            # 判断是不是广播消息
            elif data_message[-2:] == '%^':
                data_broad = '\n\n' + data_message[:-2] + '\n'
                listbox.insert(tkinter.END, data_broad, 'purple')
            # 其他文字消息
            else:
                data_word = '\n' + data_sender + ' ' + time.strftime('%Y-%m-%d,%H:%M:%S', time.localtime()) + ':\n ' + data_message
                if data_receiver == '-------------群聊-------------':
                    if data_sender == user:  # 如果是自己则将字体变为绿色
                        listbox.insert(tkinter.END, data_word, 'green')
                    else:
                        listbox.insert(tkinter.END, data_word)
                elif data_sender == user or data_receiver == user:  # 显示私聊
                    listbox.insert(tkinter.END, data_word, 'red') 
            listbox.see(tkinter.END)  # 显示在最后
            # 发送完消息将文本框改为只读
            listbox.configure(state='disabled')

# 更新图片字典
for _, _, namelist in os.walk(client_cache):
    for name in namelist:
        pic_path = client_cache + '\\' + name
        img = ImageTk.PhotoImage(Image.open(pic_path))
        pic_dic[name] = img
r = threading.Thread(target=print_message)
r.start()

################################################################# 表情功能 
# 将表情图片打开存入变量中
p1 = tkinter.PhotoImage(file = './emoji/zan.png')
p2 = tkinter.PhotoImage(file = './emoji/ai.png')
p3 = tkinter.PhotoImage(file = './emoji/dai.png')
p4 = tkinter.PhotoImage(file = './emoji/wen.png')
p5 = tkinter.PhotoImage(file = './emoji/ku.png')
# 用一些特殊符号，尽量防止用户可能输入em1而调用表情
emoji_dic = {'em1#$':p1, 'em2#$':p2, 'em3#$':p3, 'em4#$':p4, 'em5#$':p5}  # 用字典存储表情
emoji_open = 0  # 判断表情面板开关的标志
# 发送表情图标记
def mark(mk):
    mes = mk + '$&' + user + '$&' + chat
    s.send(mes.encode())
def emoji1():
    mark('em1#$')
def emoji2():
    mark('em2#$')
def emoji3():
    mark('em3#$')
def emoji4():
    mark('em4#$')
def emoji5():
    mark('em5#$')
def emoji_box():
    global b1, b2, b3, b4, b5, emoji_open
    # 表情面板关闭的时候点一下按钮打开表情面板
    if emoji_open == 0:
        emoji_open = 1
        b1 = tkinter.Button(root, command=emoji1, image=p1, relief=tkinter.FLAT ,bd=0)
        b2 = tkinter.Button(root, command=emoji2, image=p2, relief=tkinter.FLAT ,bd=0)
        b3 = tkinter.Button(root, command=emoji3, image=p3, relief=tkinter.FLAT ,bd=0)
        b4 = tkinter.Button(root, command=emoji4, image=p4, relief=tkinter.FLAT ,bd=0)
        b5 = tkinter.Button(root, command=emoji5, image=p5, relief=tkinter.FLAT ,bd=0)
        b1.place(x=10, y=450)
        b2.place(x=60, y=450)
        b3.place(x=110, y=450)
        b4.place(x=160, y=450)
        b5.place(x=210, y=450)
    # 表情面板打开的时候点一下按钮关闭表情面板
    else:
        emoji_open = 0
        b1.destroy()
        b2.destroy()
        b3.destroy()
        b4.destroy()
        b5.destroy() 
# 创建表情按钮
button_emoji = tkinter.Button(root, text='表情', command=emoji_box)
button_emoji.place(x=10, y=505, width=80, height=30)

################################################################# 文件传输功能
def file_client():
    PORT_FILE = 50008
    s_file = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_file.connect((IP, PORT_FILE))
    
    # 打印当前目录文件列表
    def print_file(path):
        c = 'show!@'
        s_file.send(c.encode())
        data = s_file.recv(4096)  
        data = json.loads(data.decode())
        listbox_file.delete(0, tkinter.END)  # 清空列表框
        path = path.split('\\')
        if len(path) != 1:
            listbox_file.insert(tkinter.END, ' 返回上级目录')
            listbox_file.itemconfig(0, fg='green')
        for i in range(len(data)):
            listbox_file.insert(tkinter.END, (' '+data[i]))
            # 文件夹显示橙色
            if not '.' in data[i]:
                listbox_file.itemconfig(tkinter.END, fg='orange')
            # 文件显示蓝色
            else:
                listbox_file.itemconfig(tkinter.END, fg='blue')

    # 跳转指定目录并刷新文件列表
    def refresh(mes):
        global label_file
        s_file.send(mes.encode())
        current_path = s_file.recv(1024).decode()
        try:
            label_file.destroy()
            label_file = tkinter.Label(root, text=current_path)
            label_file.place(x=805, y=3)
        except:
            label_file = tkinter.Label(root, text=current_path)
            label_file.place(x=805, y=3)
        print_file(current_path)

    # 处理在文件列表中的点击事件
    def event_filelist(*args):
        # 获取点击的文件路径
        id_clicks = listbox_file.curselection()
        id_click = id_clicks[0]
        path = listbox_file.get(id_click)
        path = path.strip()
        # 文件名有.则认为是单个文件，进行下载
        if '.' in path:
            mes = 'download!@' + path
            download(mes)
            refresh('cd!@same')
        elif path == '返回上级目录':
            refresh('cd!@..')
        # 点击的是文件夹，则进入文件夹
        else:
            mes = 'cd!@' + path
            refresh(mes)    

    # 将文件以比特串形式上传至服务器
    def upload():
        file_path = tkinter.filedialog.askopenfilename(title='选择上传文件')
        if file_path:
            file_name = file_path.split('/')[-1]
            request = 'upload!@' + file_name
            s_file.send(request.encode())
            with open(file_path, 'rb') as f:
                lines = f.read()
                s_file.sendall(lines)
            # 文件以EOF结尾
            s_file.send('EOF'.encode())
            # 接收同步消息
            s_file.settimeout(100)
            x = s_file.recv(1024).decode()
            if x == 'ok':
                tkinter.messagebox.showinfo(title='提示', message='上传完成!')
                refresh('cd!@same')

    # 从服务器端下载文件
    def download(mes):
        file_name = mes.split('!@')[-1]
        file_path = tkinter.filedialog.asksaveasfilename(title='文件下载至..', initialfile=file_name)
        if file_path:
            s_file.send(mes.encode())
            with open(file_path, 'wb') as f:
                while True:
                    line = s_file.recv(1024)
                    if 'EOF'.encode() in line:
                        f.write(line[:-3])
                        break
                    f.write(line)
                # 发送同步消息
                s_file.send('ok'.encode())
                tkinter.messagebox.showinfo(title='提示', message='下载完成!')
    
    # 关闭文件列表，退出文件服务器
    def quit_filelist():
        listbox_file.destroy()
        root['height'] = 600
        root['width'] = 800
        mes = 'quit!@'
        s_file.send(mes.encode())
        s_file.close()

    # 修改root窗口大小显示文件管理的组件
    root['height'] = 600
    root['width'] = 1000
    # 创建文件管理列表栏
    listbox_file = tkinter.Listbox(root, bg='#F5FFFA')
    listbox_file.place(x=800, y=25, width=190, height=530)
    listbox_file.bind('<ButtonRelease-1>', event_filelist)
    # 创建上传按钮
    button_upload = tkinter.Button(root, text='上传', command=upload)
    button_upload.place(x=805, y=560, height=30, width=90)
    # 创建退出按钮
    button_quit = tkinter.Button(root, text='退出', command=quit_filelist)
    button_quit.place(x=900, y=560, height=30, width=90)
    
    # 进入界面先刷新文件列表
    refresh('cd!@same')

# 创建文件按钮
button_file = tkinter.Button(root, text='文件', command=file_client)
button_file.place(x=95, y=505, width=80, height=30)

################################################################# 图片发送功能
PORT_IMG = 50009
s_img = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s_img.connect((IP, PORT_IMG))
ch = ',<.>/?\\|;:\'"][}{=+-_) (*&^%$#@!`~'

# 将图片以比特串形式上传至服务器
def upload_img():
    global ch
    file_path = tkinter.filedialog.askopenfilename(title='选择发送图片')
    if file_path:
        # 获取图片后缀
        tail = file_path.split('.')[-1]
        with open(file_path, 'rb') as f:
            lines = f.read()
        # 获取二进制打开的图片中的十位组成上传到服务器的图片名，尽可能防止重名
        raw = ('').join(str(lines[-100:-90])[2:-1].split('\\'))
        # 去除名字中的乱七八糟符号
        for i in ch:
            raw = ('').join(raw.split(i))
        img_name = raw.strip() + '.' + tail
        request = 'upload!@' + img_name
        s_img.send(request.encode())
        s_img.settimeout(5)
        flag = s_img.recv(1024).decode()
        if flag == 'permit':
            s_img.sendall(lines)
            # 图片以EOF结尾
            s_img.send('EOF'.encode())
            # 接收同步消息
            x = s_img.recv(1024)
        # 上传完成后发送消息给聊天服务器
        message = '*^`' + img_name + '$&' + user + '$&' + chat
        s.send(message.encode())

# 从服务器下载图片到客户端缓存
def download_img(name):
    global pic_dic
    mes = 'download!@' + name
    s_img.send(mes.encode())
    img_path = client_cache + '\\' + name
    with open(img_path, 'wb') as f:
        while True:
            line = s_img.recv(1024)
            if 'EOF'.encode() in line:
                f.write(line[:-3])
                break
            f.write(line)
    # 发送同步消息
    s_img.send('ok'.encode())
    # 防止多次添加浪费时间
    if name not in pic_dic:
        pic_path = client_cache + '\\' + name
        img = ImageTk.PhotoImage(Image.open(pic_path))
        pic_dic[name] = img

# 创建图片按钮
button_img = tkinter.Button(root, text='图片', command=upload_img)
button_img.place(x=180, y=505, width=80, height=30)

################################################################# 练魔方功能
# 跳转计时器网页
def cubing(): 
    flag = tkinter.messagebox.askyesno(title='提示', message='要开始练魔方吗？')
    if flag:
        webbrowser.open("https://cstimer.net/", new=0)
        mes = user + '正在练魔方，一起来pk吧%^' + '$&' + user + '$&' + chat  # 添加聊天对象标记
        s.send(mes.encode())

# 创建练魔方按钮
button_cubing = tkinter.Button(root, text='练魔方', command=cubing)
button_cubing.place(x=265, y=505, width=80, height=30)

################################################################# 清除聊天记录功能
def clear(): 
    listbox.configure(state='normal')
    listbox.delete(2.0, tkinter.END)
    listbox.configure(state='disabled')

# 创建清除记录按钮
button_clear = tkinter.Button(root, text='清除记录', command=clear)
button_clear.place(x=350, y=505, width=80, height=30)

################################################################# 导出聊天记录功能
def export(): 
    text = listbox.get(2.0, tkinter.END)
    file_path = tkinter.filedialog.asksaveasfilename(title='聊天记录下载至..', initialfile='record.txt')
    with open(file_path, 'w') as f:
        f.write(text)

# 创建清除记录按钮
button_clear = tkinter.Button(root, text='导出记录', command=export)
button_clear.place(x=435, y=505, width=80, height=30)

#################################################################
root.mainloop()
s.close()  # 关闭图形界面后关闭连接