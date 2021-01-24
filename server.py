import socket

server = socket.socket() # 1. 新建socket
server.bind(('127.0.0.1', 8999)) # 2. 绑定IP和端口（其中127.0.0.1为本机回环IP）
server.listen(5) # 3. 监听连接
s, addr = server.accept() # 4. 接受连接
while True:
    content =s.recv(1024)
    if len(content) == 0:
        break
    s.send(content)
    print(str(content, encoding='utf-8')) # 接受来自客户端的消息，并打印出来

s.close()