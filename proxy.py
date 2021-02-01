import sys, os, time, socket, select

"""
Our code only runs on Google Chrome, Firefox keeps sending empty request for some reasons

Please test each website separately by either restart program or reopen browser
It can run many websites at the same time but if you run it one by one, the second pages will stuck sometimes
"""

class ProxyServer:
    def __init__(self, addr):
        """
        initialization function

        adr: Set the address and port of the proxy server
        """
        self.listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen.bind(addr)
        self.listen.listen(10)
        self.time_limit = float(sys.argv[1])

    def connect(self, client, forward):
        """
        Receive&modify GET request from the client(browser) socket
        and connect the forward socket to the destination server
        Pull the information from the destination server and send it back to
        the client

        client: the client socket from the browser
        forward: The socket created to send and receive response message from the web server
        """
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
        data_rec = self.cache(header, forward, website, path)
        client.sendall(data_rec)
        return True

    def fwd(self):
        """
        The main function to run the proxy server
        Create forward socket for each browser socket
        Using select.select to allow multiple website to run simultaneously
        """
        input = [self.listen]
        output = []
        socket_client = {}
        if not os.path.exists("./cache"):
            os.mkdir("cache")
        while True:
            read, write, exce = select.select(input, output, [])
            for connection in read:
                if connection is self.listen:
                    print("server accepting")
                    client, addr = self.listen.accept()
                    client.setblocking(0)
                    input.append(client)
                    socket_client[client] = [socket.socket(socket.AF_INET, socket.SOCK_STREAM), 0]
                else:
                    print("client processing")
                    if socket_client[connection][1] == 0:
                        socket_client[connection][1] = 1
                        print("connecting to website")
                        if not self.connect(connection, socket_client[connection][0]):
                            input.remove(connection)
                            del socket_client[connection]
                        continue
                    request = connection.recv(8192)
                    if request == 0 or request == b'':
                        input.remove(connection)
                        connection.close()
                        del socket_client[connection]
                        continue
                    header, website, path = self.modify_request(request)
                    if website == 'favicon.ico':
                        input.remove(connection)
                        connection.close()
                        del socket_client[connection]
                        continue
                    data_rec = self.cache(header, socket_client[connection][0], website, path)
                    socket_client[connection].append(data_rec)
                    output.append(connection)
                    input.remove(connection)
            for connection in write:
                connection.sendall(socket_client[connection][2])
                output.remove(connection)
                socket_client[connection][0].close()
                del socket_client[connection]

    def recvall(self, socket):
        """
            Read all the response message from the web server,
            concatenate them together and send it back to the browser

            socket: The socket created to receive response message from the web server
        """
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
        """
            Modify the request message so that the web server can read it correctly

            request: The request message received from the browser
        """
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
        return request, website, path

    def cache(self, header, sock, website, path):
        """
            Check if any caches exist and haven't expired for the request message
            If yes, read it directly and send it back to browser
            If no, get the response message and store it as cache

            header: The request message received from the browser
            sock: The socket created to send and receive response message from the web server
            website: the website that the forward socket needs to connect to
            path: the path of the file, used as the name for the cache file
        """
        file_path = "./cache/" + website + path.replace("/", "%")
        if os.path.exists(file_path) and time.time() - os.path.getmtime(file_path) < self.time_limit:
            cache_file = open(file_path, "rb")
            data = cache_file.read()
            if path[-5:] == '.html' or path[-1:] == '/':
                data = self.modify_html(data, os.path.getmtime(file_path))
            print("data loaded")
        else:
            print("cache not found")
            sock.sendall(header)
            data = self.recvall(sock)
            cache_file = open(file_path, "wb+")
            cache_file.write(data)
            if path[-5:] == '.html' or path[-1:] == '/':
                data = self.modify_html(data, -1)
            print("cache saved")
        cache_file.close()
        return data

    def modify_html(self, data, cachetime):
        """
            Modify the html file so that the yellow box can appear on the website

            data: the response message
            cachetime: the latest modified time of the file
        """
        index = data.find(b'<html')
        if index != -1:
            index = index + data[index:].find(b'>')
            if cachetime == -1:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                label = "FRESH VERSION AT" + str(timestamp)
            else:
                cachetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cachetime))
                label = "CACHED VERSION AS OF" + str(cachetime)
            label = "<p style=\"z-index:9999; position:fixed; top:20px; left:20px; width:200px; height:100px; " \
                    "background-color:yellow; padding:10px; font-weight:bold;\">" + label + "</p>"
            data = data[:index+1] + label.encode() + data[index+1:]
        return data


if __name__ == '__main__':
    ProxyServer(('localhost', 8888)).fwd()
