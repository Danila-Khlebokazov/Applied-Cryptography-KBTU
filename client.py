import socket
import sys
import threading
import pickle
from des_cipher import encode_text, decode_text, KEY_LENGTH
import tkinter as tk
from tkinter import filedialog
import base64

import random
from quantum_lib import Gate

HEADER_LENGTH = 10
SERVER_HOST = ("localhost", 10000)

username = input("Please input your name: ").encode("UTF-8")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.connect(SERVER_HOST)
# server.setblocking(False)

header = f"{len(username):<{HEADER_LENGTH}}".encode("UTF-8")

server.send(header + username)

is_connected = True

secret_key = None

dialog_user = None

# server.send(f"{len(secret_key.encode('UTF-8')):<{HEADER_LENGTH}}{secret_key}".encode("UTF-8"))

userlist = []


def get_save_path():
    save_path = filedialog.askopenfilename(title="Выберите файл")
    return save_path


def send_connect_request(id):
    request = f"{len('CONNECT'.encode('UTF-8')):<{HEADER_LENGTH}}CONNECT".encode("UTF-8")
    usr_data = f"{len(str(id).encode('UTF-8')):<{HEADER_LENGTH}}{id}".encode("UTF-8")
    server.send(request + usr_data)
    print("Waiting...")


def get_user_list():
    get_list = f"{len('GETCLIENTLIST'):<{HEADER_LENGTH}}GETCLIENTLIST"
    server.send(get_list.encode("UTF-8"))


def receive_message():
    global dialog_user
    global userlist
    global secret_key
    while is_connected:
        try:
            user_header = server.recv(HEADER_LENGTH)
            if not len(user_header):
                sys.exit()

            user_length = int(user_header.decode("UTF-8").strip())
            username = server.recv(user_length).decode("UTF-8")

            if username == "QKD-BB84":

                # ----------- QUANTUM PART ----------- #
                client_bases = [Gate(random.choice([Gate.GateBases.RECTANGULAR, Gate.GateBases.DIAGONAL])) for _ in
                                range(3 * KEY_LENGTH)]

                key = []

                for gate in client_bases:
                    header = server.recv(HEADER_LENGTH)
                    q_length = int(header.decode("UTF-8").strip())
                    data = server.recv(q_length)
                    try:
                        qubit = pickle.loads(data)
                        result = gate.calculate(qubit)
                        key.append(result)
                    except:
                        if data.decode("UTF-8") == "END":
                            break
                header = server.recv(HEADER_LENGTH)
                gates_length = int(header.decode("UTF-8").strip())
                gates = server.recv(gates_length).decode("UTF-8")

                server.send(f"{len('QKD-BB84'.encode('UTF-8')):<{HEADER_LENGTH}}{'QKD-BB84'}".encode("UTF-8"))
                client_gates = "".join([str(base.gate_type.value) for base in client_bases])
                server.send(f"{len(client_gates.encode('UTF-8')):<{HEADER_LENGTH}}{client_gates}".encode("UTF-8"))

                final_key = ""
                for server_gate, client_gate, key_bit in zip(gates, client_gates, key):
                    if server_gate == client_gate:
                        final_key += str(key_bit)

                print("Final key:", final_key)
                secret_key = final_key[:KEY_LENGTH]

                continue
                # ----------- ------------ ----------- #

            if username == "CLIENTLIST":
                msg_header = server.recv(HEADER_LENGTH)
                msg_length = int(msg_header.decode("UTF-8").strip())
                userlist = pickle.loads(server.recv(msg_length))
                print(userlist)
                continue

            if username == "DIALOG":
                # secret_key = server.recv(msg_length).decode("UTF-8")
                if not dialog_user:
                    name_h = server.recv(HEADER_LENGTH)
                    name_length = int(name_h.decode("UTF-8").strip())
                    dialog_user = server.recv(name_length).decode("UTF-8")
                print("You-re chatting with", dialog_user)
                continue

            msg_header = server.recv(HEADER_LENGTH)
            msg_length = int(msg_header.decode("UTF-8").strip())

            data = server.recv(msg_length).decode("UTF-8")

            data = decode_text(data, secret_key)

            if data[0].startswith("imagefile::"):

                dir = f"d{server.getsockname()[1]}"
                import os
                if not os.path.exists(dir):
                    # Создаем новую директорию
                    os.makedirs(dir)

                image = data[0].replace("imagefile::", "")
                ext, image = image.split("EXTENSION")
                from datetime import datetime
                path = f"{dir}/{datetime.now()}.{ext}"
                with open(path, "wb") as file:
                    file.write(base64.decodebytes(image.encode("UTF-8")))

                print(f"{username}: 'file:///{os.path.abspath(path).replace(' ', '%20')}'")
                continue

            print(f"{username}: {data[0]}")
        except Exception as e:
            print(f"EXITED {e}")
            sys.exit()


get_user_list()
receive = threading.Thread(target=receive_message)
receive.start()

root = tk.Tk()
root.withdraw()  # Скрываем основное окно

while is_connected:
    try:
        if not dialog_user:
            print("Enter to update, or print id of user you want ot connect")
        msg = input("")

        if msg == "IMAGE" and dialog_user:
            image_path = get_save_path()
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read())
                msg = "imagefile::" + image_path.split(".")[-1] + "EXTENSION" + encoded_string.decode("UTF-8")

        if msg and dialog_user:
            if msg.startswith("imagefile::"):
                print(f"Me: 'file:///{image_path.replace(' ', '%20')}'")
            else:
                print("Me: " + msg)
            msg = encode_text(msg, secret_key)[0]

            msg_header = f"{len(msg.encode('UTF-8')):<{HEADER_LENGTH}}".encode("UTF-8")
            server.send(msg_header + msg.encode('UTF-8'))
        elif msg != "":
            for usr in userlist:
                if int(msg) == int(usr["addr"][1]):
                    print("Trying to connect to " + usr["usr"])
                    send_connect_request(msg)
                    dialog_user = usr["usr"]
            else:
                if dialog_user:
                    print("Connected")
                else:
                    print("Wrong id")
        elif not dialog_user:
            get_user_list()

    except KeyboardInterrupt:
        is_connected = False
        import os

        dir = "d" + str(server.getsockname()[1])
        if os.path.exists(dir):
            import shutil
            shutil.rmtree(dir)
        server.close()
        root.destroy()
