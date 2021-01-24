import socket

client = socket.socket() # 1. 新建socket
client.connect(('127.0.0.1', 8888)) # 2. 连接服务端（注意，IP和端口要和服务端一致）
while True:
    content = input('>>> ')
    client.send(bytes(content, 'utf-8')) # 发送内容，注意发送的是字节字符串。
    content = client.recv(1024)
    print(str(content, encoding='utf-8'))

client.close()
