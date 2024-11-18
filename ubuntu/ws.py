import socket
import select
import threading
import sys
from concurrent.futures import ThreadPoolExecutor
import signal

# Global variable to manage server state
shutdown_event = threading.Event()

def handle_client(client_socket):
    try:
        # Log the connection
        client_address = client_socket.getpeername()
        print(f"[+] Connection established with {client_address}")

        # Send custom response (properly formatted)
        custom_response = (
            'HTTP/1.1 200 OK\r\n'
            'Content-Type: text/html; charset=UTF-8\r\n'
            'Connection: close\r\n'
            '\r\n'
            '<html><body><b><font color="#FFA500">ULTXL</font></b></body></html>'
        )
        client_socket.sendall(custom_response.encode())
        
    except Exception as e:
        print(f"[-] Error during handling client: {e}")
    finally:
        client_socket.close()

def handle_shutdown(signal_number, frame):
    print("\n[!] Shutting down proxy server...")
    shutdown_event.set()

def start_proxy(host='0.0.0.0', port=10015, max_workers=200):
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
                        executor.submit(handle_client, client_socket)
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
