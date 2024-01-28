import socket
import threading
import sys

HOST = '127.0.0.1'
PORT = 5555

connections = {}
usernames = {}
server_running = False


def check_server_running():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, PORT)) == 0


def broadcast(message, sender_addr):
    for client_addr, client_conn in connections.copy().items():
        try:
            client_conn.send(message.encode())
        except (BrokenPipeError, ConnectionError):
            del connections[client_addr]
            del usernames[client_addr]


def handle_client(conn, addr):
    try:
        username = conn.recv(1024).decode()

        while not username:
            conn.send("Введите непустое имя пользователя: ".encode())
            username = conn.recv(1024).decode()

        welcome_message = f"Добро пожаловать, {username}! Для выхода напишите /exit."
        conn.send(welcome_message.encode())

        connections[addr] = conn
        usernames[addr] = username

        online_users = ", ".join(usernames.values())
        broadcast(f"{username} присоединился. Онлайн: {online_users}", addr)

        while True:
            message = conn.recv(1024).decode()
            if message.lower() == "/exit":
                conn.send("exit".encode())
                break

            broadcast(f"{username}: {message}", addr)

        online_users = ", ".join(usernames.values())
        broadcast(f"{username} покинул. Онлайн: {online_users}", addr)
    except:
        pass
    finally:
        del connections[addr]
        del usernames[addr]

        if len(connections) == 0:
            print("Все пользователи отключились. Сервер остановлен.")
            sys.exit()

        conn.close()


def server_maintenance():
    global server_running
    while True:
        if len(connections) == 0 and server_running:
            print("Все пользователи отключились. Сервер остановлен.")
            sys.exit()


def start_server():
    global server_running
    server_running = True

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server.bind((HOST, PORT))
    except socket.error as e:
        print(f"Ошибка при привязке адреса: {e}")
        sys.exit()

    server.listen()

    print(f"Сервер слушает на {HOST}:{PORT}")

    maintenance_thread = threading.Thread(target=server_maintenance)
    maintenance_thread.start()

    try:
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
    except KeyboardInterrupt:
        print("Сервер остановлен.")
    finally:
        server_running = False
        maintenance_thread.join()
        server.close()


def start_client():
    username = input("Введите ваше имя: ")
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    if check_server_running():
        client_socket.connect((HOST, PORT))
    else:
        print("Сервер не запущен. Пожалуйста, запустите сервер.")
        sys.exit()

    client_socket.send(username.encode())

    welcome_message = client_socket.recv(1024).decode()
    print(welcome_message)

    def receive_messages():
        try:
            while True:
                message = client_socket.recv(1024).decode()
                if message.lower() == "exit":
                    print("Сервер закрыл соединение.")
                    break
                print(message)
        except ConnectionResetError:
            print("Сервер закрыл соединение.")
        finally:
            client_socket.close()

    receive_thread = threading.Thread(target=receive_messages)
    receive_thread.start()

    while True:
        message = input()
        client_socket.send(message.encode())
        if message.lower() == "/exit":
            break

    receive_thread.join()
    client_socket.close()


if __name__ == "__main__":
    if not check_server_running():
        server_thread = threading.Thread(target=start_server)
        server_thread.start()

    start_client()
