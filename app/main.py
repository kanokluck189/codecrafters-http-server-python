import socket  # noqa: F401


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    
    # Accept the incoming client connection
    conn, address = server_socket.accept()
    
    # Read the request from the client (we don't need to parse it yet, but we should read it)
    request = conn.recv(1024)
    
    # Send the HTTP 200 OK response with proper CRLF termination
    response = b"HTTP/1.1 200 OK\r\n\r\n"
    conn.sendall(response)
    
    # Close the connection
    conn.close()


if __name__ == "__main__":
    main()