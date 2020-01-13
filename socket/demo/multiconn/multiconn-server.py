import selectors
import socket
import types
import sys

sel = selectors.DefaultSelector()

# 获取新的 socket 对象并注册到 selector 上
def accept_wrapper(sock):
    conn, addr = sock.accept()
    print('accept connection from ', addr)
    conn.setblocking(False)
    # types.SimpleNamespace 类创建了一个对象用来保存我们想要的 socket 和数据
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    # 由于我们得知道客户端连接什么时候可以写入或者读取，下面两个事件都会被用到
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

# 当客户端 socket 就绪的时候连接请求是如何使用 service_connection() 来处理的
def service_connection(key, mask):
    # key 就是从调用 select() 方法返回的一个具名元组，它包含了 socket 对象「fileobj」和数据对象
    sock = key.fileobj
    data = key.data
    # 如果 socket 就绪而且可以被读取，mask & selectors.EVENT_READ 就为真
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        # 所有读取到的数据都会被追加到 data.outb 里面
        if recv_data:
            data.outb += recv_data
        # 如果没有收到任何数据,表示客户端关闭了它的 socket 连接，这时服务端也应该关闭自己的连接
        else:
            print('closing connection to ', data.addr)
            # 调用 sel.unregister() 来撤销 select() 的监控
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print('echoing ', repr(data.outb), ' to ', data.addr)
            # 任何接收并被 data.outb 存储的数据都将使用 sock.send() 方法打印出来
            sent = sock.send(data.outb)
            # 发送出去的字节随后就会被从缓冲中删除
            data.outb = data.outb[sent:] 

host, port = sys.argv[1], int(sys.argv[2])
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()
print('listening on ', (host, port))
# 配置 socket 为非阻塞模式
lsock.setblocking(False)
# sel.register() 使用 sel.select() 为你感兴趣的事件注册 socket 监控
# data 用来存储任何你 socket 中想存的数据,用来跟踪 socket 上发送或者接收的东西
sel.register(lsock, selectors.EVENT_READ, data=None)

while True:
    # sel.select(timeout=None) 调用会阻塞直到 socket I/O 就绪
    events = sel.select(timeout=None)
    # key 就是一个包含 fileobj 属性的具名元组。key.fileobj 是一个 socket 对象，mask 表示一个操作就绪的事件掩码
    for key, mask in events:
        # 如果 key.data 为空，我们就可以知道它来自于监听 socket
        if key.data is None:
            accept_wrapper(key.fileobj)
        else:
            # 如果 key.data 不为空，我们就可以知道它是一个被接受的客户端 socket
            service_connection(key, mask)