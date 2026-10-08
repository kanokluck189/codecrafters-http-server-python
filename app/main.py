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

        if method == "GET" and path == "/":
            return "HTTP/1.1 200 OK\r\n\r\nHello, World!"
        elif path.startswith("/echo/"):
            return f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(path[6:])}\r\n\r\n{path[6:]}"
        else:
            return "HTTP/1.1 404 Not Found\r\n\r\nNot Found"
    except Exception as e:
        print(f"Error parsing request: {e}")
        return "HTTP/1.1 400 Bad Request\r\n\r\nBad Request"


def main():
    print("Server is starting...")
    server_socket = socket.create_server(("localhost", 4221))
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