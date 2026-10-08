import socket
import threading
import sys
import os
from pathlib import Path


def parse_args():
    """Extracts the directory path from command-line arguments like --directory /tmp/"""
    directory = "."
    for i in range(len(sys.argv) - 1):
        if sys.argv[i] == "--directory":
            directory = sys.argv[i + 1]
            break
    return directory


def handle_requests(client_socket, files_dir):
    try:
        data = client_socket.recv(1024)
        if not data:
            return
        response = parse_request(data, files_dir)
        client_socket.sendall(response)
    except Exception as e:
        print(f"Error handling request: {e}")
    finally:
        client_socket.close()


def parse_request(data, files_dir):
    try:
        request_data = data.decode("utf-8", errors="ignore").split("\r\n")
        request_line = request_data[0]
        parts = request_line.split()
        if len(parts) < 2:
            return b"HTTP/1.1 400 Bad Request\r\n\r\nBad Request"
            
        method, path, http_version = parts[0], parts[1], parts[2]

        # Parse headers into a dictionary
        headers = {}
        for line in request_data[1:]:
            if not line:
                break
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()

        if method == "GET":
            if path == "/":
                return b"HTTP/1.1 200 OK\r\n\r\n"
            elif path.startswith("/echo/"):
                echo_str = path[6:]
                body = echo_str.encode("utf-8")
                return (
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: text/plain\r\n"
                    f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8") + body
                )
            elif path == "/user-agent":
                user_agent = headers.get("user-agent", "")
                body = user_agent.encode("utf-8")
                return (
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: text/plain\r\n"
                    f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8") + body
                )
            elif path.startswith("/files/"):
                filename = path[len("/files/"):]
                file_path = Path(files_dir) / filename
                
                # Check if file exists and is a file
                if file_path.exists() and file_path.is_file():
                    file_content = file_path.read_bytes()
                    return (
                        b"HTTP/1.1 200 OK\r\n"
                        b"Content-Type: application/octet-stream\r\n"
                        f"Content-Length: {len(file_content)}\r\n\r\n".encode("utf-8") + file_content
                    )
                else:
                    return b"HTTP/1.1 404 Not Found\r\n\r\n"
        
        return b"HTTP/1.1 404 Not Found\r\n\r\n"
    except Exception as e:
        print(f"Error parsing request: {e}")
        return b"HTTP/1.1 400 Bad Request\r\n\r\nBad Request"


def main():
    # Read the directory flag from command-line arguments
    files_dir = parse_args()
    print(f"Server starting, serving files from: {files_dir}")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    server_socket.listen()

    try:
        while True:
            client_socket, address = server_socket.accept()
            client_thread = threading.Thread(target=handle_requests, args=(client_socket, files_dir))
            client_thread.daemon = True
            client_thread.start()
            
    except KeyboardInterrupt:
        print("Server is shutting down...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()