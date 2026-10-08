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
                # Spawn a thread for each client to handle requests concurrently
                thread = Thread(target=self.handle_client, args=(connection,))
                thread.daemon = True
                thread.start()

    def handle_client(self, connection):
        # Kept connection open across multiple requests for HTTP/1.1 persistence
        try:
            while self.running:
                recv = connection.recv(1024)
                if not recv:
                    break  # Client closed the connection
                
                respond = self.user_request(recv)
                connection.sendall(respond)
                
                # Check if the client explicitly requested to close the connection
                if b"connection: close" in recv.lower():
                    break
        except Exception as e:
            print(e)
        finally:
            connection.close()

    def user_request(self, recv):
        request = recv.decode(errors="ignore").split("\r\n")
        # Parsing safety
        if not request or not request[0]:
            return b"HTTP/1.1 400 Bad Request\r\n\r\n"

        request_line = request[0].split(" ")
        if len(request_line) < 2:
            return b"HTTP/1.1 400 Bad Request\r\n\r\n"

        method = request_line[0]
        path = request_line[1]
        paths = path.split("/")
        user_agent = ""
        
        for line in request:
            if line.lower().startswith("user-agent:"):
                user_agent = line.split(":", 1)[1].strip()

        if method == "GET":
            if len(paths) > 1 and paths[1] == "echo":
                echo = paths[2] if len(paths) > 2 else ""
                data = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(echo)}\r\n\r\n{echo}"
                return data.encode()
            elif len(paths) > 1 and paths[1] == "user-agent":
                data = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(user_agent)}\r\n\r\n{user_agent}"
                return data.encode()
            elif path == "/":
                return b"HTTP/1.1 200 OK\r\n\r\n"
            elif len(paths) > 1 and paths[1] == "quit":
                self.running = False
                return b"HTTP/1.1 200 OK\r\n\r\n"
            elif len(paths) > 1 and paths[1] == "files" and len(paths) > 2:
                if "--directory" in sys.argv:
                    dir_index = sys.argv.index("--directory") + 1
                    file_path = Path(f"/{sys.argv[dir_index]}/{paths[2]}")
                else:
                    file_path = Path(f"./{paths[2]}")

                if file_path.exists() and file_path.is_file():
                    with open(file_path, "rb") as file:
                        content = file.read()
                        data = b"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: " + str(len(content)).encode() + b"\r\n\r\n" + content
                        return data
                else:
                    return b"HTTP/1.1 404 Not Found\r\n\r\n"
            else:
                return b"HTTP/1.1 404 Not Found\r\n\r\n"

        elif method == "POST":
            if len(paths) > 1 and paths[1] == "files" and len(paths) > 2:
                if "--directory" in sys.argv:
                    dir_index = sys.argv.index("--directory") + 1
                    file_path = Path(f"/{sys.argv[dir_index]}/{paths[2]}")
                else:
                    file_path = Path(f"./{paths[2]}")

                # Split header and body to get POST payload
                try:
                    header_data, body_data = recv.split(b"\r\n\r\n", 1)
                except ValueError:
                    body_data = b""

                file_path.write_bytes(body_data)
                return b"HTTP/1.1 201 Created\r\n\r\n"
            else:
                return b"HTTP/1.1 404 Not Found\r\n\r\n"

        return b"HTTP/1.1 404 Not Found\r\n\r\n"


def main():
    server_side("localhost", 4221)


if __name__ == "__main__":
    main()