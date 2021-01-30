import sys, os, time, socket, select

class ProxyServer:
    def __init__(self, addr):
        self.listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen.bind(addr)
        self.listen.listen(5)
        self.time_limit = float(sys.argv[1])

    def connect(self, client, forward):
        while True:
            try:
                request = client.recv(8192)
                if request != b'':
                    break
                else:
                    pass
            except:pass
        header, website, path = self.modify_request(request)
        if website == 'favicon.ico':
            forward.close()
            return False
        forward.connect((website, 80))
        data_rec = self.cache(header, forward, path)
        client.sendall(data_rec)
        return True

    def fwd(self):
        input = [self.listen]
        output = []
        socket_client = {}
        if not os.path.exists("./cache"):
            os.mkdir("cache")
        while True:
            print("hi")
            read, write, exce = select.select(input, output, [])
            for connection in read:
                if connection is self.listen:
                    print("server")
                    client, addr = self.listen.accept()
                    client.setblocking(0)
                    input.append(client)
                    socket_client[client] = [socket.socket(socket.AF_INET, socket.SOCK_STREAM), 0]
                else:
                    print("client")
                    if socket_client[connection][1] == 0:
                        socket_client[connection][1] = 1
                        print("connecting")
                        if not self.connect(connection, socket_client[connection][0]):
                            input.remove(connection)
                            del socket_client[connection]
                        continue
                    request = connection.recv(8192)
                    if request == b'':
                        input.remove(connection)
                        connection.close()
                        del socket_client[connection]
                        continue
                    print(request)
                    header, website, path = self.modify_request(request)
                    if website == 'favicon.ico':
                        input.remove(connection)
                        connection.close()
                        del socket_client[connection]
                        continue
                    data_rec = self.cache(header, socket_client[connection][0], path)
                    socket_client[connection].append(data_rec)
                    output.append(connection)
                    input.remove(connection)
            for connection in write:
                connection.sendall(socket_client[connection][2])
                output.remove(connection)
                socket_client[connection][0].close()
                del socket_client[connection]


    def recvall(self, socket):
        socket.setblocking(0)
        total_data = b''
        begin = time.time()
        while True:
            try:
                if (time.time()-begin) >= 0.5:
                    break
                data = socket.recv(8192)
                if data and data != b'':
                    total_data += data
                begin = time.time()
                if data == b'':
                    break
            except:pass
        return total_data

    def modify_request(self, request):
        path = None
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
        return request, website, path

    def cache(self, header, sock, path):
        print(path)
        file_path = "./cache/" + path.replace("/", "%")
        if os.path.exists(file_path) and time.time() - os.path.getmtime(file_path) < self.time_limit:
            cache_file = open(file_path, "rb")
            data = cache_file.read()
            print("data loaded")
        else:
            print("cache not found")
            sock.sendall(header)
            print("send")
            data = self.recvall(sock)
            cache_file = open(file_path, "wb+")
            cache_file.write(data)
            print("cache saved")
        cache_file.close()
        return data

if __name__ == '__main__':
    ProxyServer(('localhost', 8888)).fwd()
