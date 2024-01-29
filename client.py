import socket
import sys
import threading
import pickle
from des_cipher import encode_text, decode_text

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

            msg_header = server.recv(HEADER_LENGTH)
            msg_length = int(msg_header.decode("UTF-8").strip())

            if username == "CLIENTLIST":
                userlist = pickle.loads(server.recv(msg_length))
                print(userlist)
                continue

            if username == "DIALOG":
                secret_key = server.recv(msg_length).decode("UTF-8")
                if not dialog_user:
                    name_h = server.recv(HEADER_LENGTH)
                    name_length = int(name_h.decode("UTF-8").strip())
                    dialog_user = server.recv(name_length).decode("UTF-8")
                print("You-re chatting with", dialog_user)
                continue

            data = server.recv(msg_length).decode("UTF-8")

            data = decode_text(data, secret_key)
            print(f"{username}: {data[0]}")
        except Exception as e:
            print(f"EXITED {e}")
            sys.exit()


get_user_list()
receive = threading.Thread(target=receive_message)
receive.start()

while is_connected:
    try:
        if not dialog_user:
            print("Enter to update, or print id of user you want ot connect")
        msg = input("")
        if msg and dialog_user:
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
        server.close()
