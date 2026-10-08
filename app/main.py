import socket
from threading import Thread
import sys
from pathlib import Path
import gzip


class server_side:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.running = True
        self.start_server()

    def start_server(self):
        with socket.create_server(
            (self.host, self.port),
            reuse_port=True
        ) as server:

            print(f"Server is open on port {self.port}")

            while self.running:
                connection, address = server.accept()

                thread = Thread(
                    target=self.handle_client,
                    args=(connection,)
                )
                thread.start()

    def handle_client(self, connection):
        with connection:
            try:
                recv = connection.recv(1024)

                if not recv:
                    return

                # Receive the complete POST request body
                if recv.startswith(b"POST"):
                    while b"\r\n\r\n" not in recv:
                        recv += connection.recv(1024)

                    header_part, body = recv.split(b"\r\n\r\n", 1)

                    headers = header_part.decode().split("\r\n")

                    content_length = 0

                    for line in headers:
                        if line.lower().startswith("content-length:"):
                            content_length = int(
                                line.split(":", 1)[1].strip()
                            )

                    while len(body) < content_length:
                        body += connection.recv(1024)

                    recv = header_part + b"\r\n\r\n" + body

                respond = self.user_request(recv)
                connection.sendall(respond)

            except Exception as e:
                print(e)

    def user_request(self, recv):
        parts = recv.split(b"\r\n\r\n", 1)

        header_bytes = parts[0]
        body = parts[1] if len(parts) > 1 else b""

        request = header_bytes.decode().split("\r\n")

        if not request:
            return b"HTTP/1.1 400 Bad Request\r\n\r\n"

        request_line = request[0].split(" ")

        if len(request_line) < 3:
            return b"HTTP/1.1 400 Bad Request\r\n\r\n"

        method = request_line[0]
        path = request_line[1]

        paths = path.split("/")

        user_agent = ""
        accept_encoding = ""

        for line in request[1:]:
            if line.lower().startswith("user-agent:"):
                user_agent = line.split(":", 1)[1].strip()

            elif line.lower().startswith("accept-encoding:"):
                accept_encoding = line.split(":", 1)[1].strip()

        # Check whether the client supports gzip
        supports_gzip = "gzip" in [
            encoding.strip().lower()
            for encoding in accept_encoding.split(",")
        ]

        # GET /echo/{str}
        if (
            method == "GET"
            and len(paths) >= 3
            and paths[1] == "echo"
        ):
            echo = paths[2]
            echo_bytes = echo.encode()

            # Compress the response body if gzip is supported
            if supports_gzip:
                echo_bytes = gzip.compress(echo_bytes)

            response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/plain\r\n"
            )

            if supports_gzip:
                response += b"Content-Encoding: gzip\r\n"

            response += (
                f"Content-Length: {len(echo_bytes)}\r\n"
                f"\r\n"
            ).encode()

            response += echo_bytes

            return response

        # GET /user-agent
        elif method == "GET" and len(paths) >= 2 and paths[1] == "user-agent":
            user_agent_bytes = user_agent.encode()

            data = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/plain\r\n"
                + f"Content-Length: {len(user_agent_bytes)}\r\n"
                f"\r\n".encode()
                + user_agent_bytes
            )

            return data

        # GET /
        elif method == "GET" and path == "/":
            return b"HTTP/1.1 200 OK\r\n\r\n"

        # GET /quit
        elif method == "GET" and len(paths) >= 2 and paths[1] == "quit":
            self.running = False

            return b"HTTP/1.1 200 OK\r\n\r\n"

        # GET /files/{filename}
        elif (
            method == "GET"
            and len(paths) >= 3
            and paths[1] == "files"
            and Path(sys.argv[2], paths[2]).exists()
        ):
            file_path = Path(sys.argv[2], paths[2])

            with open(file_path, "rb") as file:
                content = file.read()

            data = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: application/octet-stream\r\n"
                + f"Content-Length: {len(content)}\r\n\r\n".encode()
                + content
            )

            return data

        # POST /files/{filename}
        elif (
            method == "POST"
            and len(paths) >= 3
            and paths[1] == "files"
        ):
            file_path = Path(sys.argv[2], paths[2])

            with open(file_path, "wb") as file:
                file.write(body)

            return b"HTTP/1.1 201 Created\r\n\r\n"

        # Unknown route
        else:
            return b"HTTP/1.1 404 Not Found\r\n\r\n"


def main():
    server_side("localhost", 4221)


if __name__ == "__main__":
    main()