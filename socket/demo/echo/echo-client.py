import socket

HOST = '127.0.0.1'   # 服务器的主机名或者 IP 地址
PORT = 65432   # 服务器使用的端口

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b'Hello, world')
    # 1024 是缓冲区数据大小限制最大值参数 bufsize
    data = s.recv(1024)

print('Received ', repr(data))