import socket  # noqa: F401


def main():
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    
    # Run in a loop so the server stays up for multiple requests/tests
    while True:
        try:
            conn, address = server_socket.accept()
            
            # Read the request data
            request = conn.recv(1024)
            if not request:
                conn.close()
                continue
                
            # Parse the request line
            request_lines = request.decode("utf-8").split("\r\n")
            request_line = request_lines[0]
            parts = request_line.split(" ")
            path = parts[1] if len(parts) > 1 else "/"
            
            # Handle routing
            if path == "/":
                response = b"HTTP/1.1 200 OK\r\n\r\n"
            elif path.startswith("/echo/"):
                echo_str = path[len("/echo/"):]
                body = echo_str.encode("utf-8")
                
                # Fixed: Use bytes for the Content-Length header string too
                response = (
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: text/plain\r\n"
                    f"Content-Length: {len(body)}\r\n".encode("utf-8") +
                    b"\r\n" + body
                )
            else:
                response = b"HTTP/1.1 404 Not Found\r\n\r\n"
                
            conn.sendall(response)
            conn.close()
        except Exception as e:
            print(f"Error handling connection: {e}")


if __name__ == "__main__":
    main()