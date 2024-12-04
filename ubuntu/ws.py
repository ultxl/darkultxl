import socket
import select
import threading
import sys
from concurrent.futures import ThreadPoolExecutor
import signal

# Global variable to manage server state
shutdown_event = threading.Event()

def handle_client(client_socket, upstream_address):
    try:
        # Create connection to upstream server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.connect(upstream_address)
            
            # Log the connection
            client_address = client_socket.getpeername()
            print(f"[+] Connection established with {client_address}")

            # Send custom response (simplified)
            custom_response = 'HTTP/1.1 101 <b><font color=#FFA500>ULTXL SPIDEY</font></b>\r\n\r\n'
            client_socket.send(custom_response.encode())

            # Prepare sockets for forwarding
            sockets = [client_socket, server_socket]

            while not shutdown_event.is_set():
                readable, _, _ = select.select(sockets, [], [], 1)
                if not readable:
                    continue

                for sock in readable:
                    try:
                        data = sock.recv(4096)
                        if not data:
                            raise ConnectionError("Connection closed by peer")
                        (server_socket if sock is client_socket else client_socket).send(data)
                    except Exception as e:
                        print(f"[-] Error during data transfer: {e}")
                        return
    except Exception as e:
        print(f"[-] Connection handling error: {e}")
    finally:
        client_socket.close()

def handle_shutdown(signal_number, frame):
    print("\n[!] Shutting down proxy server...")
    shutdown_event.set()

def start_proxy(host='0.0.0.0', port=10015, upstream_address=('127.0.0.1', 143), max_workers=200):
    # Create proxy server socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as proxy_socket:
        proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        proxy_socket.bind((host, port))
        proxy_socket.listen(5)
        print(f"Proxy listening on {host}:{port}")

        # Thread pool for handling client connections
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Register signal handler for graceful shutdown
            signal.signal(signal.SIGINT, handle_shutdown)
            signal.signal(signal.SIGTERM, handle_shutdown)

            try:
                while not shutdown_event.is_set():
                    try:
                        client_socket, _ = proxy_socket.accept()
                        print("[+] Accepted connection from client")
                        executor.submit(handle_client, client_socket, upstream_address)
                    except socket.error as e:
                        if not shutdown_event.is_set():
                            print(f"[-] Error accepting connection: {e}")
            
            finally:
                print("Proxy server shutting down...")
                # Shutdown the executor and wait for all threads to complete
                executor.shutdown(wait=True)
                print("Proxy server shut down")

if __name__ == "__main__":
    start_proxy()
