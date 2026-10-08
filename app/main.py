import socket


def handle_requests(client_socket):
    try:
        data = client_socket.recv(1024)
        if not data:
            return
        response = parse_request(data)
        client_socket.sendall(response.encode())
    except Exception as e:
        print(f"Error handling request: {e}")
    finally:
        client_socket.close()


def parse_request(data):
    try:
        request_data = data.decode().split("\r\n")
        request_line = request_data[0]
        method, path, http_version = request_line.split()

        # Parse headers into a dictionary (case-insensitive for keys)
        headers = {}
        for line in request_data[1:]:
            if not line:
                break
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()

        if method == "GET":
            if path == "/":
                return "HTTP/1.1 200 OK\r\n\r\nHello, World!"
            elif path.startswith("/echo/"):
                echo_str = path[6:]
                return f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(echo_str)}\r\n\r\n{echo_str}"
            elif path == "/user-agent":
                user_agent = headers.get("user-agent", "")
                return f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(user_agent)}\r\n\r\n{user_agent}"
        
        return "HTTP/1.1 404 Not Found\r\n\r\nNot Found"
    except Exception as e:
        print(f"Error parsing request: {e}")
        return "HTTP/1.1 400 Bad Request\r\n\r\nBad Request"


def main():
    print("Server is starting...")
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    server_socket.listen()

    try:
        while True:
            client_socket, address = server_socket.accept()
            print(f"Connection from {address}")
            handle_requests(client_socket)
    except KeyboardInterrupt:
        print("Server is shutting down...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()