import socket
import select
import pickle
from des_cipher import KEY_LENGTH, decode_text, encode_text
import random

from quantum_lib import Replicator, Gate


def receive_message(client: socket.socket):
    try:
        msg_header = client.recv(HEADER)
        if not len(msg_header):  # if len is 0
            return False

        message_length = int(msg_header.decode("UTF-8").strip())

        return {
            "header": msg_header.decode("UTF-8"),
            "data": client.recv(message_length).decode("UTF-8")
        }
    except:
        return False


HOST = ("localhost", 10000)
HEADER = 10
BUFFER_SIZE = 1024


def client_bb84(_socket):
    # ----------- QUANTUM PART ----------- #
    secret_key = [random.choice([0, 1]) for _ in range(3 * KEY_LENGTH)]
    server_bases = [Gate(random.choice([Gate.GateBases.RECTANGULAR, Gate.GateBases.DIAGONAL])) for _ in secret_key]
    key_qubits = Replicator.create_qubits(server_bases, secret_key)

    _socket.send(f"{len('QKD-BB84'.encode('UTF-8')):<{HEADER}}{'QKD-BB84'}".encode("UTF-8"))

    for key_qubit in key_qubits:
        qubit_data = pickle.dumps(key_qubit)
        qubit_msg = f"{len(qubit_data):<{HEADER}}".encode("UTF-8") + qubit_data
        _socket.send(qubit_msg)

    gates = "".join([str(base.gate_type.value) for base in server_bases]).encode("UTF-8")
    _socket.send(f"{len(gates):<{HEADER}}".encode("UTF-8") + gates)

    callback = receive_message(_socket)

    final_key = ""

    if callback["data"] == "QKD-BB84":
        callback = receive_message(_socket)
        for gate_type, server_base, key_bit in zip(callback["data"], server_bases, secret_key):
            if gate_type == str(server_base.gate_type.value):
                final_key += str(key_bit)

    # print(f"Final key: {final_key}\n\n\n\n\n")

    if len(final_key) < KEY_LENGTH:
        return False
    return final_key[:KEY_LENGTH]
    # ----------- ------------ ----------- #


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind(HOST)
    server.listen()
    print("!!!SERVER IS LISTENING!!!")
    socket_list = [server]
    clients_list = {}

    try:
        while "work":
            rs, _, xs = select.select(socket_list, [], socket_list)
            for _socket in rs:
                if _socket == server:
                    client, addr = server.accept()

                    user = receive_message(client)
                    if not user:
                        continue
                    # key = receive_message(client)
                    # if not key:
                    #     continue
                    socket_list.append(client)
                    clients_list[client] = user
                    print(f"New connection from {addr} - {user['data']}")
                else:
                    receiver = receive_message(_socket)  # type or length

                    if receiver is False:
                        print(f"Connection from {_socket} has been interrupted")
                        socket_list.remove(_socket)
                        del clients_list[_socket]
                        continue

                    if receiver["data"] == "GETCLIENTLIST":
                        type = "CLIENTLIST"
                        data = f"{len(type.encode('UTF-8')):<{HEADER}}{type}".encode("UTF-8")
                        user_list = [
                            {"addr": client.getpeername(),
                             "usr": clients_list[client]["data"]}
                            for client in clients_list if client != _socket]
                        client_list_pickled = pickle.dumps(user_list)
                        clients = f"{len(client_list_pickled):<{HEADER}}".encode("UTF-8") + client_list_pickled
                        _socket.send(data + clients)
                        continue

                    if receiver["data"] == "CONNECT":
                        usrport_to_connect = receive_message(_socket)["data"]
                        connect_client = list(filter(lambda client: client.getpeername()[1] == int(usrport_to_connect),
                                                     clients_list))[0]

                        type = "DIALOG"
                        # secret_key = create_random_key()

                        # ----------- QUANTUM PART ----------- #
                        final_key = client_bb84(_socket)
                        while not final_key:
                            final_key = client_bb84(_socket)

                        clients_list[_socket]["key"] = final_key

                        final_key = client_bb84(connect_client)
                        while not final_key:
                            final_key = client_bb84(connect_client)

                        clients_list[connect_client]["key"] = final_key
                        # ----------- ------------ ----------- #

                        msg = f"{len(type.encode('UTF-8')):<{HEADER}}{type}".encode(
                            "UTF-8")
                        rec_user = f"{len(clients_list[_socket]['data'].encode('UTF-8')):<{HEADER}}{clients_list[_socket]['data']}".encode(
                            "UTF-8")
                        connect_client.send(msg + rec_user)
                        _socket.send(msg)

                        clients_list[_socket]["dialog"] = connect_client
                        clients_list[connect_client]["dialog"] = _socket
                        continue

                    msg = receiver

                    user = clients_list[_socket]

                    for client in clients_list:
                        if client == user["dialog"]:
                            print(f"From {user['data']} received {msg['data']}")
                            decoded = decode_text(msg["data"], user["key"])
                            encoded = encode_text(decoded[0], clients_list[client]["key"])[0]

                            client.send(
                                f"{len(user['data']):<{HEADER}}{user['data']}{len(encoded.encode('UTF-8')):<{HEADER}}{encoded}".encode(
                                    "UTF-8"))

            for _socket in xs:
                socket_list.remove(_socket)
                del clients_list[_socket]
    except KeyboardInterrupt as exc:
        print("!!!SERVER STOPPED!!")


if __name__ == "__main__":
    start_server()