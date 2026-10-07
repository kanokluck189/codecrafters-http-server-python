import socket  # noqa: F401


def main():
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    
    conn, address = server_socket.accept()
    
    # Read the request data
    request = conn.recv(1024)
    
    # Parse the request line (e.g., "GET /index.html HTTP/1.1")
    request_lines = request.decode("utf-8").split("\r\n")
    request_line = request_lines[0]
    
    # Extract the method and the path
    parts = request_line.split(" ")
    path = parts[1] if len(parts) > 1 else "/"
    
    # Respond based on the path
    if path == "/":
        response = b"HTTP/1.1 200 OK\r\n\r\n"
    else:
        response = b"HTTP/1.1 404 Not Found\r\n\r\n"
        
    conn.sendall(response)
    conn.close()


if __name__ == "__main__":
    main()