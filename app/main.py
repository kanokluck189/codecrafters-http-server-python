import socket
from threading import Thread
import sys
from pathlib import Path


class server_side:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.running = True
        self.files_dir = self.parse_directory()
        self.start_server()

    def parse_directory(self):
        for i in range(len(sys.argv) - 1):
            if sys.argv[i] == "--directory":
                return sys.argv[i + 1]
        return "."

    def start_server(self):
        with socket.create_server((self.host, self.port), reuse_port=True) as server:
            print(f"Server is open on port {self.port}")
            while self.running:
                connection, address = server.accept()
                thread = Thread(target=self.handle_client, args=(connection,))
                thread.daemon = True
                thread.start()

    def handle_client(self, connection):
        # Removed the 'with connection:' block so it doesn't auto-close after one request
        try:
            while self.running:
                recv = connection.recv(4096)
                if not recv:
                    break  # Client closed connection or no more data
                
                respond = self.user_request(recv)
                connection.sendall(respond)
                
                # Optional: Check if request explicitly specified connection: close
                if b"connection: close" in recv.lower():
                    break
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
                        connection.close()

    def user_request(self, recv):
        try:
            header_data, body_data = recv.split(b"\r\n\r\n", 1)
        except ValueError:
            header_data = recv
            body_data = b""

        request_lines = header_data.decode("utf-8", errors="ignore").split("\r\n")
        if not request_lines or not request_lines[0]:
            return b"HTTP/1.1 400 Bad Request\r\n\r\n"

        request_line = request_lines[0].split(" ")
        if len(request_line) < 2:
            return b"HTTP/1.1 400 Bad Request\r\n\r\n"
            
        method = request_line[0]
        path = request_line[1]
        paths = path.split("/")

        headers = {}
        for line in request_lines[1:]:
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()

        user_agent = headers.get("user-agent", "")

        if method == "GET":
            if path == "/":
                return b"HTTP/1.1 200 OK\r\n\r\n"
            elif len(paths) > 1 and paths[1] == "echo":
                echo = paths[2] if len(paths) > 2 else ""
                data = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(echo)}\r\n\r\n{echo}"
                return data.encode()
            elif len(paths) > 1 and paths[1] == "user-agent":
                data = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(user_agent)}\r\n\r\n{user_agent}"
                return data.encode()
            elif len(paths) > 1 and paths[1] == "files":
                filename = paths[2] if len(paths) > 2 else ""
                file_path = Path(self.files_dir) / filename
                if file_path.exists() and file_path.is_file():
                    content = file_path.read_bytes()
                    return (
                        b"HTTP/1.1 200 OK\r\n"
                        b"Content-Type: application/octet-stream\r\n"
                        f"Content-Length: {len(content)}\r\n\r\n".encode() + content
                    )
                else:
                    return b"HTTP/1.1 404 Not Found\r\n\r\n"
            elif len(paths) > 1 and paths[1] == "quit":
                self.running = False
                return b"HTTP/1.1 200 OK\r\n\r\n"
            else:
                return b"HTTP/1.1 404 Not Found\r\n\r\n"

        elif method == "POST":
            if len(paths) > 1 and paths[1] == "files":
                filename = paths[2] if len(paths) > 2 else ""
                file_path = Path(self.files_dir) / filename
                content_length = int(headers.get("content-length", 0))
                file_path.write_bytes(body_data[:content_length])
                return b"HTTP/1.1 201 Created\r\n\r\n"
            else:
                return b"HTTP/1.1 404 Not Found\r\n\r\n"

        return b"HTTP/1.1 404 Not Found\r\n\r\n"


def main():
    server_side("localhost", 4221)


if __name__ == "__main__":
    main()