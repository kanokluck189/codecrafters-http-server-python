import socket
import threading
import argparse
import os
import gzip


files_dir = "."


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


def parse_request(request_data):
    """
    Parse one complete HTTP request.
    Returns:
        method, path, version, headers, body
    """

    header_part, body = request_data.split("\r\n\r\n", 1)

    lines = header_part.split("\r\n")

    request_line = lines[0]

    method, path, version = request_line.split(" ", 2)

    headers = {}

    for line in lines[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.lower().strip()] = value.strip()

    return method, path, version, headers, body


def create_response(method, path, version, headers, body):
    """
    Create an HTTP response without sending it.
    Returns bytes.
    """

    # -------------------------
    # GET /
    # -------------------------
    if method == "GET" and path == "/":

        return (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Length: 0\r\n"
            b"\r\n"
        )


    # -------------------------
    # GET /echo/{str}
    # -------------------------
    elif method == "GET" and path.startswith("/echo/"):

        content = path[len("/echo/"):]

        content_bytes = content.encode()

        accept_encoding = headers.get("accept-encoding", "")

        supports_gzip = "gzip" in [
            encoding.strip().lower()
            for encoding in accept_encoding.split(",")
        ]

        if supports_gzip:

            compressed_body = gzip.compress(content_bytes)

            response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/plain\r\n"
                b"Content-Encoding: gzip\r\n"
                + f"Content-Length: {len(compressed_body)}\r\n"
                b"\r\n"
            )

            return response + compressed_body

        else:

            response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/plain\r\n"
                + f"Content-Length: {len(content_bytes)}\r\n"
                b"\r\n"
            )

            return response + content_bytes


    # -------------------------
    # GET /user-agent
    # -------------------------
    elif method == "GET" and path.startswith("/user-agent"):

        user_agent = headers.get("user-agent", "")

        user_agent_bytes = user_agent.encode()

        response = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/plain\r\n"
            + f"Content-Length: {len(user_agent_bytes)}\r\n"
            b"\r\n"
        )

        return response + user_agent_bytes


    # -------------------------
    # GET /files/{filename}
    # -------------------------
    elif method == "GET" and path.startswith("/files/"):

        filename = path[len("/files/"):]

        content = handle_file_get_request(filename)

        if content is not None:

            content_bytes = content.encode()

            response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: application/octet-stream\r\n"
                + f"Content-Length: {len(content_bytes)}\r\n"
                b"\r\n"
            )

            return response + content_bytes

        else:

            return (
                b"HTTP/1.1 404 Not Found\r\n"
                b"Content-Length: 0\r\n"
                b"\r\n"
            )


    # -------------------------
    # POST /files/{filename}
    # -------------------------
    elif method == "POST" and path.startswith("/files/"):

        filename = path[len("/files/"):]

        if handle_file_post_request(filename, body):

            return (
                b"HTTP/1.1 201 Created\r\n"
                b"Content-Length: 0\r\n"
                b"\r\n"
            )

        else:

            return (
                b"HTTP/1.1 404 Not Found\r\n"
                b"Content-Length: 0\r\n"
                b"\r\n"
            )


    # -------------------------
    # 404
    # -------------------------
    else:

        return (
            b"HTTP/1.1 404 Not Found\r\n"
            b"Content-Length: 0\r\n"
            b"\r\n"
        )


def handle_request(client_conn, client_addr):

    print(f"Received connection from: {client_addr}")

    buffer = b""

    try:

        while True:

            # Receive more data
            data = client_conn.recv(1024)

            # Client closed the connection
            if not data:
                break

            buffer += data

            # Process every complete request currently in buffer
            while b"\r\n\r\n" in buffer:

                header_end = buffer.find(b"\r\n\r\n")

                header_part = buffer[:header_end]

                header_lines = header_part.decode().split("\r\n")

                # Parse Content-Length
                content_length = 0

                for line in header_lines[1:]:

                    if ":" in line:

                        key, value = line.split(":", 1)

                        if key.lower().strip() == "content-length":
                            content_length = int(value.strip())

                # Position where body starts
                body_start = header_end + 4

                # Check whether entire body has arrived
                if len(buffer) - body_start < content_length:
                    break

                # Complete request size
                request_length = body_start + content_length

                request_data = buffer[:request_length]

                # Remove processed request from buffer
                buffer = buffer[request_length:]

                # Decode request
                request_text = request_data.decode()

                method, path, version, headers, body = parse_request(
                    request_text
                )

                print(f"{method} {path}")

                # Create response
                response = create_response(
                    method,
                    path,
                    version,
                    headers,
                    body
                )

                # Send response
                client_conn.sendall(response)

                # HTTP/1.1 is persistent by default
                connection_header = headers.get(
                    "connection",
                    ""
                ).lower()

                if connection_header == "close":

                    client_conn.close()
                    return

    except Exception as e:

        print(f"Error handling client: {e}")

    finally:

        client_conn.close()
        print(f"Connection closed: {client_addr}")


def main():

    parser = argparse.ArgumentParser(
        prog="http-server"
    )

    parser.add_argument("--directory")

    args = parser.parse_args()

    global files_dir

    if args.directory:

        files_dir = args.directory

        print(
            f"Directory given: {files_dir}"
        )

    port = 4221

    server_socket = socket.create_server(
        ("localhost", port),
        reuse_port=True
    )

    print(
        f"Server listening on port: {port}"
    )

    while True:

        conn, addr = server_socket.accept()

        thread = threading.Thread(
            target=handle_request,
            args=(conn, addr)
        )

        thread.start()


if __name__ == "__main__":
    main()