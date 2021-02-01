import sys, os, time, socket, select

class ProxyServer:
    def __init__(self, addr):
        self.listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen.bind(addr)
        self.listen.listen(10)
        self.time_limit = float(sys.argv[1])
        self.addr = addr

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
            return
        forward.connect((website, 80))
        data_rec = self.cache(header, forward, website, path)
        client.sendall(data_rec)

    def fwd(self):
        input = [self.listen]
        output = []
        socket_client = {}
        if not os.path.exists("./cache"):
            os.mkdir("cache")
        while True:
            print("hi")
            print(input)
            read, write, exce = select.select(input, output, [], 5)
            if not (read or write or exce):
                self.listen.close()
                self.listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.listen.bind(self.addr)
                self.listen.listen(10)
                input = [self.listen]
                output = []
                socket_client = {}
                continue
            print(read)
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
                        self.connect(connection, socket_client[connection][0])
                        continue
                    request = connection.recv(8192)
                    if request == b'':
                        input.remove(connection)
                        connection.close()
                        del socket_client[connection]
                        continue
                    print(request)
                    header, website, path = self.modify_request(request)
                    data_rec = self.cache(header, socket_client[connection][0], website, path)
                    socket_client[connection].append(data_rec)
                    output.append(connection)
                    input.remove(connection)
            for connection in write:
                connection.sendall(socket_client[connection][2])
                output.remove(connection)
                input.append(connection)
                #socket_client[connection][0].close()
                #del socket_client[connection]

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
            decode = decode[:5] + decode[index - 1:]
        else:
            path = website[index_slash + 1:]
            website = website[:index_slash]
            decode = decode[:5] + path + decode[index - 1:]
        if not path:
            path = "/"

        index_head = decode.find('Host:')
        index_tail = decode.find('\r\nConnection')
        decode = decode[:index_head + 6] + website + decode[index_tail:]

        index_head = decode.find('Accept-Encoding: ')
        index_tail = decode.find('\r\nAccept-Language:')
        decode = decode[:index_head + 17] + decode[index_tail:]

        request = decode.encode()
        print("request:")
        print(request)
        return request, website, path

    def cache(self, header, sock, website, path):
        file_path = "./cache/" + website + path.replace("/", "%")
        print(("path is!!!!!!!!!", path))
        if os.path.exists(file_path) and time.time() - os.path.getmtime(file_path) < self.time_limit:
            cache_file = open(file_path, "rb")
            data = cache_file.read()
            if path[-5:] == '.html' or path[-1:] == '/':
                data = self.modify_html(data, os.path.getmtime(file_path))
            print("data loaded")
        else:
            print("cache not found")
            sock.sendall(header)
            print("send")
            data = self.recvall(sock)
            cache_file = open(file_path, "wb+")
            cache_file.write(data)
            if path[-5:] == '.html' or path[-1:] == '/':
                data = self.modify_html(data, -1)
            print("cache saved")
        cache_file.close()
        return data

    def modify_html(self, data, cachetime):
        index = data.find(b'<html>')
        if index != -1:
            if cachetime == -1:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                print("timestamp")
                print(timestamp)
                label = "FRESH VERSION AT" + str(timestamp)
            else:
                cachetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cachetime))
                print("timestamp")
                print(cachetime)
                label = "CACHED VERSION AS OF" + str(cachetime)
            label = "<p style=\"z-index:9999; position:fixed; top:20px; left:20px; width:200px; height:100px; " \
                    "background-color:yellow; padding:10px; font-weight:bold;\">" + label + "</p>"
            data = data[:index+6] + label.encode() + data[index+7:]
            print("data MOOOOOOOOOOOOOOO!")
        return data





if __name__ == '__main__':
    ProxyServer(('localhost', 8888)).fwd()
