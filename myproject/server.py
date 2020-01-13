import socket
import threading
import queue
import json  
import os

IP = ''
PORT_CHAT = 50007
PORT_FILE = 50008
PORT_IMG = 50009
que = queue.Queue()  # 用于存放客户端发送的信息的队列
user_list = []  # 用于存放在线用户的信息  [conn, user, addr]
lock = threading.Lock()  # 创建锁, 防止多个线程写入数据的顺序打乱
# 获取服务端图片缓存文件夹的绝对路径
p = os.getcwd().split('\\')
for i in range(len(p)):
    if p[i] == 'myproject':
        break
server_cache = ('\\'.join(p[:i+1])) + '\\imgcache_server'
# 如果文件夹不存在则创建一个
if not os.path.exists(server_cache):
    os.mkdir(server_cache)
# print(server_cache)

################################################################################################################################
class Chat_Server(threading.Thread):
    global user_list, lock, que

    def __init__(self, ip, port):
        threading.Thread.__init__(self)
        self.ADDR = (ip, port)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        self.s.bind(self.ADDR)
        self.s.listen(5)
        print('聊天服务器运行中...')
        q = threading.Thread(target=self.send_message)
        q.start()
        while True:
            conn, addr = self.s.accept()
            t = threading.Thread(target=self.chat_connect, args=(conn, addr))
            t.start()
        self.s.close()
        
    # 将接收到的信息存入que
    def enter_que(self, addr, data):
        lock.acquire()
        try:
            que.put((addr, data))
        finally:
            lock.release()

    # 将离线用户移出user_list
    def del_user(self, conn, addr):
        for i in range(len(user_list)):
            if user_list[i][0] == conn:
                user_list.pop(i)
                # 显示当前在线用户
                online_user_list = [user_list[i][1] for i in range(len(user_list))]
                self.enter_que(addr, online_user_list)
                print('剩余在线用户：', online_user_list)
                break

    # 用于接收所有客户端发送信息的函数
    def chat_connect(self, conn, addr):
        print('*****聊天服务器已连接: ', addr)
        # 连接后将用户信息添加到user_list
        user = conn.recv(1024).decode()  # 接收用户名
        if user == 'no':
            user = addr[0] + ':' + str(addr[1])
        else:
            # 防止重名
            user = user + '[' + str(addr[1]) + ']'
        user_list.append((conn, user, addr))
        # print(user_list)
        online_user_list = [user_list[i][1] for i in range(len(user_list))]
        self.enter_que(addr, online_user_list)
        try:
            while True:
                data = conn.recv(1024)
                data = data.decode()
                self.enter_que(addr, data)  # 保存信息到队列
            conn.close()
        except:
            print('*****聊天服务器断开连接: ', addr)
            self.del_user(conn, addr)  # 将断开用户移出users
            conn.close()

    # 将队列que中的消息发送给所有连接到的用户
    def send_message(self):
        while True:
            if not que.empty():
                data = ''
                message = que.get()  # 取出队列第一个元素
                # print('-------------', message)
                # 如果是字符串，说明是消息
                if isinstance(message[1], str): 
                    for i in range(len(user_list)):
                        for j in range(len(user_list)):
                            if message[0] == user_list[j][2]:                            
                                data = message[1]
                                # print(message[1])
                                break      
                        user_list[i][0].send(data.encode())
                # print(data)
                data = data.split('$&')[0]
                # print(data)
                # 如果是列表，说明是用户列表
                if isinstance(message[1], list):    
                    data = json.dumps(message[1])
                    for i in range(len(user_list)):
                        user_list[i][0].send(data.encode())      

 ################################################################################################################################
class File_Server(threading.Thread):
    def __init__(self, ip, port):
        threading.Thread.__init__(self)
        self.ADDR = (ip, port)
        self.upload = './filerecv'
        if not os.path.exists(self.upload):
            os.mkdir(self.upload)
        os.chdir(self.upload)  # 将filerecv作为文件上传默认路径
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def run(self):
        self.s.bind(self.ADDR)
        self.s.listen(5)
        print('文件服务器运行中...')
        while True:
            conn, addr = self.s.accept()
            t = threading.Thread(target=self.file_connect, args=(conn, addr))
            t.start()
        self.s.close()
    
    # 传输当前目录列表
    def send_current_dirlist(self, conn):
        current_dir = os.listdir(os.getcwd())
        current_dir = json.dumps(current_dir)
        conn.sendall(current_dir.encode())

    # 客户端上传文件
    def upload_file(self, path, conn):
        file_path = './' + path
        with open(file_path, 'wb') as f:
            while True:
                line = conn.recv(1024)
                if 'EOF'.encode() in line:
                    f.write(line[:-3])
                    break
                f.write(line)
            # 发送同步消息
            conn.send('ok'.encode())
            print('文件上传完成', file_path)

    # 客户端下载文件
    def download_file(self, path, conn):
        file_path = './' + path
        with open(file_path, 'rb') as f:
            lines = f.read()
            conn.sendall(lines)
        conn.send('EOF'.encode())
        # 接收同步消息
        y = conn.recv(1024).decode()
        if y == 'ok':
            print('文件下载完成', file_path)

    # 切换目录
    def cd(self, item, conn):
        # 如果是新连接或者下载上传文件后的发送则不切换,只发送当前工作目录
        if item != 'same':
            f = './' + item
            os.chdir(f)
        path_list = os.getcwd().split('\\')  # 当前工作目录 
        # print('===============', path_list)
        for i in range(len(path_list)):
            if path_list[i] == 'filerecv':
                break
        path = ''
        for j in range(i, len(path_list)):
            path = path + path_list[j] + ' '
        path = '\\'.join(path.split())
        # print('+++++++++', path)
        # 如果切换目录超出范围则退回切换根目录
        if not 'filerecv' in path_list:
            f = './filerecv'
            os.chdir(f)
            path = 'filerecv'
        conn.send(path.encode())

    def file_connect(self, conn, addr):
        print('*****文件服务器已连接: ', addr)
        while True:
            # 获取客户端请求
            request = conn.recv(1024).decode()
            # 打印客户端请求
            print('客户端请求：', ' '.join(request.split('!@')))
            # if request == 'quit':
            #     print('*****文件服务器断开连接: ', addr)
            #     break
            # 获取客户端传来的操作命令
            command = request.split('!@')[0]
            # 获取客户端传来的目标路径
            path = request.split('!@')[1]
            if command == 'quit':
                print('*****文件服务器断开连接: ', addr)
                break
            elif command == 'upload':
                self.upload_file(path, conn)
            elif command == 'download':
                self.download_file(path, conn)
            elif command == 'show':
                self.send_current_dirlist(conn)
            elif command == 'cd':
                self.cd(path, conn)
        conn.close()

################################################################################################################################
class Img_Server(threading.Thread):
    global server_cache
    def __init__(self, ip, port):
        threading.Thread.__init__(self)
        self.ADDR = (ip, port)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        self.s.bind(self.ADDR)
        self.s.listen(5)
        print('图片服务器运行中...')
        while True:
            conn, addr = self.s.accept()
            t = threading.Thread(target=self.img_connect, args=(conn, addr))
            t.start()
        self.s.close()
    
    def upload_img(self, name, conn):
        img_path = server_cache + '\\' + name
        self.server_img = []
        for _, _, namelist in os.walk(server_cache):
            for n in namelist:
                self.server_img.append(n)
        # print(self.server_img)
        if name not in self.server_img:
            self.server_img.append(name)
            conn.send('permit'.encode())
            with open(img_path, 'wb') as f:
                while True:
                    line = conn.recv(1024)
                    if 'EOF'.encode() in line:
                        f.write(line[:-3])
                        break
                    f.write(line)
            # 发送同步消息
            conn.send('ok'.encode())
            print('图片上传完成', img_path)
        else:
            conn.send('deny'.encode())
            print('图片已存在')

    def download_img(self, name, conn):
        img_path = server_cache + '\\' + name
        with open(img_path, 'rb') as f:
            lines = f.read()
            conn.sendall(lines)
        conn.send('EOF'.encode())
        # 接收同步消息
        x = conn.recv(1024).decode()
        if x == 'ok':
            print('图片下载完成', img_path)

    def img_connect(self, conn, addr):
        print('*****图片服务器已连接: ', addr)
        while True:
            # 接收客户端传来的请求
            request = conn.recv(1024).decode()
            # 打印客户端请求
            print('客户端请求：', ' '.join(request.split('!@')))
            # 获取客户端传来的操作命令
            command = request.split('!@')[0]
            # 获取客户端传来的图片名
            name = request.split('!@')[1]
            # 将图片上传至服务器缓存文件夹
            if command == 'upload':
                self.upload_img(name, conn)
            # 下载图片到客户端缓存文件夹
            elif command == 'download':
                self.download_img(name, conn)      
        conn.close()

################################################################################################################################
if __name__ == '__main__':
    chat_server = Chat_Server(IP, PORT_CHAT)
    chat_server.start()
    file_server = File_Server(IP, PORT_FILE)
    file_server.start()
    img_server = Img_Server(IP, PORT_IMG)
    img_server.start()