import sys, os, time, socket, select


class ProxyServer:
    def __init__(self, addr):
        self.listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen.bind(addr)
        self.listen.listen(3)
        self.client = self.forward = self.url =None
        self.time_limit = float(sys.argv[1])

    def listening(self):
        self.client, addr = self.listen.accept()
        print('listening to {} with {}'.format(self.client, addr))

    def connect(self):
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.forward.connect((self.url, 80))

    def disconnect_all(self):
        self.listen.close()
        self.forward.close()

    def fwd(self):
        try:
            self.listening()
            os.mkdir("tem")
        except:pass
        header, path = self.get_header()
        self.connect()
        print('connection created')
        self.forward.sendall(header.encode())
        data_rec = self.recvall(self.forward)
        print(data_rec)
        self.client.sendall(data_rec)
        cache_file = None
        while True:
            self.listening()
            ready2 = select.select([self.client], [], [], 0.1)
            if ready2[0]:
                header, path = self.get_header()
                ###################
                if (not self.exists(path)) or \
                        (self.exists(path) and time.time() - os.path.getmtime("./tem/" + path.replace("/", "%")) > self.time_limit):
                    print("cache not found")
                    self.forward.sendall(header.encode())
                    print("datasent:")
                else:
                    print(os.path.getmtime("./tem/" + path.replace("/", "%")) - time.time())
                    print(self.time_limit)
                    cache_file = open("./tem/" + path.replace("/", "%"), "rb")
                    self.client.sendall(self.pull(cache_file))
                    print("cache loaded")

                #######################
            ready1 = select.select([self.forward], [], [], 0.1)
            if ready1[0]:
                data_rec = self.recvall(self.forward)
                if data_rec:
                    self.client.sendall(data_rec)
                    print("datarec:")
                    ################
                    if not self.exists(path) or \
                            (self.exists(path) and time.time() - os.path.getmtime("./tem/" + path.replace("/", "%")) > self.time_limit):
                        cache_file = open("./tem/" + path.replace("/", "%"), "wb+")
                        self.cache(cache_file, data_rec)
                        print("cache Saved")
                    #############
                else:
                    self.disconnect_all()

    def recvall(self, socket):
        socket.setblocking(0)
        total_data = b'';
        begin = time.time()
        while True:
            try:
                if (time.time()-begin) >= 0.5:
                    break
                data = socket.recv(8192)
                if data:
                    total_data += data
                begin = time.time()
            except:pass
        return total_data

    def get_header(self):
        header = ''
        while True:
            header += self.client.recv(8192).decode()
            i_0 = header.find('HTTP')
            if i_0 > 0: break
        path = header[4:i_0-1]
        if not self.url:
            url = path.split('/', 2)[1]
            self.url = url
        else:
            url = self.url

        path = path.replace("/" + url, "")
        if path == "":
            path = "/"
        header = header.replace(header[4:i_0-1], path)
        print(path)
        print(url)
        i_1 = header.find('Host: ')
        i_2 = header.find('\r\nConnection:')
        header = header.replace(header[i_1+6:i_2], url)
        return header, path

    def test_get(self):
        self.client, addr = self.listen.accept()
        print('listening to {} with {}'.format(self.client, addr))
        self.get_header()
        while True:
            data_sent = self.client.recv(8192)
            #print(data_sent)
            if not data_sent:
                self.disconnect_all()

    def cache(self, file, content):
        file.write(content)
        file.close()

    def exists(self, path):
        return os.path.exists("./tem/" + path.replace("/", "%"))

    def pull(self, file):
        content = file.read()
        file.close()
        return content


if __name__ == '__main__':
    ProxyServer(('localhost', 8888)).fwd()
