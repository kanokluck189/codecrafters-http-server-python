import socket
import threading
import argparse
import os
import gzip

def handle_file_get_request(filename: str):
    path = os.path.join(files_dir, filename)
    if os.path.isfile(path):
        with open(path, "r") as file:
            content = file.read()
        return content
    return None

def handle_file_post_request(filename: str, response_body: str):
    if os.path.exists(files_dir):
        with open(os.path.join(files_dir, filename), "w") as file:
            file.write(response_body)
        return True
    return False

def handle_request(client_conn, client_addr):
    print(f"Recieved connection from: {client_addr}")
    
    try:
        while True:
            request_data = client_conn.recv(1024)
            if not request_data:
                break  # Client closed connection
                
            request = request_data.decode().split("\r\n")
            if len(request) < 1 or not request[0]:
                break
                
            request_line = request[0]
            headers = request[1:-1]
            response_body = request[-1] if len(request) > 1 else ""
            
            try:
                method, path, version = request_line.split(" ")
            except ValueError:
                break

            # Check if client requested connection close
            connection_close = False
            for header in headers:
                if header.lower().startswith("connection:") and "close" in header.lower():
                    connection_close = True
                    break

            if method == "GET":
                if path == "/":
                    response = "HTTP/1.1 200 OK\r\n\r\n"
                    client_conn.sendall(response.encode())
                elif path.startswith("/echo/"):
                    content = path.split("/")[2]
                    content_len = len(content)
                    
                    # Check Accept-Encoding for gzip
                    gzipped = False
                    for header in headers:
                        if header.startswith("Accept-Encoding") and "gzip" in header:
                            gzipped = True
                            break
                    
                    if gzipped:
                        compressed_body = gzip.compress(content.encode())
                        response = (
                            f"HTTP/1.1 200 OK\r\n"
                            f"Content-Type: text/plain\r\n"
                            f"Content-Encoding: gzip\r\n"
                            f"Content-Length: {len(compressed_body)}\r\n\r\n"
                        )
                        client_conn.sendall(response.encode() + compressed_body)
                    else:
                        response = (
                            f"HTTP/1.1 200 OK\r\n"
                            f"Content-Type: text/plain\r\n"
                            f"Content-Length: {content_len}\r\n\r\n"
                            f"{content}"
                        )
                        client_conn.sendall(response.encode())
                        
                elif path.startswith("/user-agent"):
                    user_agent = None
                    for header in headers:
                        if header.startswith("User-Agent"):
                            # Safer header value extraction
                            parts = header.split(":", 1)
                            if len(parts) > 1:
                                user_agent = parts[1].strip()
                    if user_agent:
                        print(f"Parsed User-Agent: {user_agent}")
                        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(user_agent)}\r\n\r\n{user_agent}"
                        client_conn.sendall(response.encode())
                    else:
                        response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 0\r\n\r\n"
                        client_conn.sendall(response.encode())
                elif path.startswith("/files/"):
                    filename = path.split("/")[2]
                    content = handle_file_get_request(filename)
                    if content:
                        response = f"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {len(content)}\r\n\r\n{content}"
                        client_conn.sendall(response.encode())
                    else:
                        response = "HTTP/1.1 404 Not Found\r\n\r\n"
                        client_conn.sendall(response.encode())
                else:
                    response = "HTTP/1.1 404 Not Found\r\n\r\n"
                    client_conn.sendall(response.encode())

            elif method == "POST":
                if path.startswith("/files/"):
                    filename = path.split("/")[2]
                    if handle_file_post_request(filename, response_body):
                        response = "HTTP/1.1 201 Created\r\n\r\n"
                        client_conn.sendall(response.encode())
                    else:
                        response = "HTTP/1.1 500 Internal Server Error\r\n\r\n"
                        client_conn.sendall(response.encode())

            if connection_close:
                break
    finally:
        client_conn.close()

def main():
    parser = argparse.ArgumentParser(prog="http-server")
    parser.add_argument("--directory")
    args = parser.parse_args()
    directory = args.directory
    if directory:
        print(f"Directory given: {directory}")
        global files_dir
        files_dir = directory
    port = 4221
    server_socket = socket.create_server(("localhost", port), reuse_port=True)
    print(f"Server listening on port: {port}")

    while True:
        conn, addr = server_socket.accept()
        thread = threading.Thread(target=handle_request, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    main()