import sys, os, time, socket, select


class ProxyServer:
    def __init__(self, addr):
        self.listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen.bind(addr)
        self.listen.listen(5)
        self.client = None

    def listening(self):
        self.client, addr = self.listen.accept()
        print('listening to {} with {}'.format(self.client, addr))

    def connect(self, forward):
        while True:
            try:
                request = self.client.recv(8192)
                if request != b'':
                    break
                else:
                    pass
            except:pass
        header, website = self.modify_request(request)
        if website == 'favicon.ico':
            forward.close()
            return False
        print('\n', request, '\n')
        print(header, '\n')
        print(website, '\n')
        forward.connect((website, 80))
        forward.sendall(header)
        data_rec = self.recvall(forward)
        self.client.sendall(data_rec)
        return True

    def disconnect_all(self):
        self.listen.close()

    def fwd(self):
        input = [self.listen]
        output = []
        socket_client = {}
        while True:
            print("hi")
            read, write, exce = select.select(input, output, [])
            print("bad")
            for connection in read:
                if connection is self.listen:
                    print("once")
                    self.listening()
                    self.client.setblocking(0)
                    input.append(self.client)
                    socket_client[self.client] = [socket.socket(socket.AF_INET, socket.SOCK_STREAM)]
                    if not self.connect(socket_client[self.client][0]):
                        input.remove(self.client)
                        del socket_client[self.client]
                else:
                    request = connection.recv(8192)
                    print(request)
                    header, website = self.modify_request(request)
                    socket_client[connection][0].sendall(header)
                    print("send")
                    data_rec = self.recvall(socket_client[connection][0])
                    socket_client[connection].append(data_rec)
                    output.append(connection)
                    input.remove(connection)
            for connection in write:
                connection.sendall(socket_client[connection][1])
                print("wat")
                output.remove(connection)
                socket_client[connection][0].close()
                del socket_client[connection]


    def recvall(self, socket):
        socket.setblocking(0)
        total_data = b'';
        begin = time.time()
        while True:
            try:
                if (time.time()-begin) >= 0.5:
                    break
                data = socket.recv(8192)
                if data and data != b'':
                    total_data += data
                    begin = time.time()
                begin = time.time()
                if data == b'':
                    break
            except:pass
        return total_data

    def modify_request(self, request):
        decode = request.decode()
        index = decode.find('HTTP')
        website = decode[5:index - 1]

        index_slash = website.find('/')
        if index_slash == -1:
            decode = decode[:5] + website + '/' + decode[index - 1:]
        else:
            path = website[index_slash + 1:]
            website = website[:index_slash]
            decode = decode[:5] + path + decode[index - 1:]

        index_head = decode.find('Host:')
        index_tail = decode.find('\r\nConnection')
        decode = decode[:index_head + 6] + website + decode[index_tail:]

        request = decode.encode()
        return request, website

    def test_get(self):
        self.client, addr = self.listen.accept()
        print('listening to {} with {}'.format(self.client, addr))
        self.get_header()
        while True:
            data_sent = self.client.recv(8192)
            #print(data_sent)
            if not data_sent:
                self.disconnect_all()


if __name__ == '__main__':
    ProxyServer(('localhost', 8888)).fwd()
