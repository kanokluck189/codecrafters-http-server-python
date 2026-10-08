import socket
from threading import Thread
import sys
from pathlib import Path


class server_side:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.running = True
        self.start_server()

    def start_server(self):
        with socket.create_server((self.host, self.port), reuse_port=True) as server:
            print(f"Server is open on port {self.port}")
            while self.running:
                connection, address = server.accept()
                # To make it concurrent, we spawn a thread for each client
                thread = Thread(target=self.handle_client, args=(connection,))
                thread.start()

    def handle_client(self, connection):
        with connection:
            try:
                recv = connection.recv(1024)
                if not recv:
                    return
                respond = self.user_request(recv)
                connection.sendall(respond)
                connection.settimeout(10.0)

            except Exception as e:
                print(e)

    def user_request(self, recv):
        request = recv.decode().split("\r\n")
        # parsing safety
        if not request:
            return b"HTTP/1.1 400 Bad Request\r\n\r\n"

        path = request[0].split(" ")[1]
        paths = path.split("/")
        for line in request:
            if line.startswith("User-Agent: "):
                user_agent = line.split("User-Agent: ")[1]

        if paths[1] == "echo":
            echo = paths[2]
            data = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(echo)}\r\n\r\n{echo}"
            return data.encode()
        elif paths[1] == "user-agent":
            data = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(user_agent)}\r\n\r\n{user_agent}"
            return data.encode()
        elif path == "/":
            return b"HTTP/1.1 200 OK\r\n\r\n"
        elif paths[1] == "quit":
            self.running = False
            return b"HTTP/1.1 200 OK\r\n\r\n"
        elif paths[1] == "files" and Path(f"/{sys.argv[2]}/{paths[2]}").exists():
            with open(f"/{sys.argv[2]}/{paths[2]}", "r") as file:
                content = file.read()
                data = f"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {len(content)}\r\n\r\n{content}"
                return data.encode()
        else:
            return b"HTTP/1.1 404 Not Found\r\n\r\n"


def main():
    server_side("localhost", 4221)


if __name__ == "__main__":
    main()