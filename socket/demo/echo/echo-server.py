import socket

HOST = '127.0.0.1'   # 标准的回环地址 (localhost)
PORT = 65432   # 监听的端口 (非系统级的端口: 大于 1023)

"""socket.socket() 创建了一个 socket 对象
socket 地址族参数 socket.AF_INET 表示因特网 IPv4 地址族
SOCK_STREAM 表示使用 TCP 的 socket 类型"""
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # bind() 用来关联 socket 到指定的网络接口（IP 地址）和端口号
    s.bind((HOST, PORT))
    # listen() 方法调用使服务器可以接受连接请求
    s.listen()
    # accept() 方法阻塞并等待传入连接
    conn, addr = s.accept()
    with conn:
        print('Connected by ', addr)
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(data)