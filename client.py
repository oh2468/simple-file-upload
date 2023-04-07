import socket
import os
import argparse
from socket_handler import SocketHandler



parser = argparse.ArgumentParser()
parser.add_argument("-r", metavar="remote host", default=None, type=str, help="connect to this host")
parser.add_argument("-p", metavar="port", default=None, type=int, help="connect to this port")
parser.add_argument("-s", metavar="server secret", default=None, type=str, help="connect to server with this secret")
args = parser.parse_args()


CLIENT_SERVER_SECRET =  args.s or "SECRETACCESSKEY0"
SRV_HOST = args.r or "localhost"
SRV_PORT = args.p or 45678
SRV_OK_RESPONSE = "ok"
MAX_CHAR_BYTE_SIZE = 4


def connect_to_server(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    return sock


def get_file_name_and_path(file_path):
    if '"' in file_path[1:-1]: raise ValueError(" -- ERROR: Place do NOT use the char \" in the file name!!")
    file_path = file_path.replace('"', '')

    cwd = os.path.abspath(os.path.dirname(__file__))
    abs_path = os.path.abspath(os.path.join(cwd, file_path))
    file_name = os.path.basename(abs_path)
    return (file_name, abs_path)


def assert_server_status(status):
    #print(f"Incoming status: {status}")
    if status and status != SRV_OK_RESPONSE:
        raise AssertionError(status)


def run_logging_mode(client):
    max_chars = int(client.receive_text())

    print(f"The server accpets at most < {max_chars} > characters in the text!\n")
    print(" -- INPUT NEEDED, MAKE A CHOICE! -- ")
    print("0: System shutdown.")
    print("1: Send text to logger from file.")
    print("2: Send text to logger from console.")
    
    while (opt := input("Enter an option: ")) not in ["0", "1", "2"]: pass
    match opt:
        case "0":
            print("Shutting down")
            raise SystemExit
        case "1":
            inp_file = input(f"Enter file path: ")
            _, data_source = get_file_name_and_path(inp_file)
            with open(data_source, "r") as file: data = file.read(max_chars * MAX_CHAR_BYTE_SIZE)
        case "2":
            data_source = "console input"
            data = input("Enter text: ")
    
    print(f"Trying to log data on the server from source: {data_source}")

    client.send_text(str(len(data)))
    assert_server_status(client.receive_text())

    client.send_text(data[:max_chars])
    assert_server_status(client.receive_text())

    print("Now sent the message to the server log!")


def run_upload_mode(client):
    inp_file =  input("Enter a file path: ")
    file_name, file_path = get_file_name_and_path(inp_file)
    file_size = os.path.getsize(file_path)    
    
    client.send_text(file_name)
    assert_server_status(client.receive_text())

    client.send_text(str(file_size))
    assert_server_status(client.receive_text())

    client.upload_file(file_path)
    server_file_md5_sum = client.receive_text()
    print(f"Servers file hash: {server_file_md5_sum}")
    
    my_file_md5 = client.md5sum(file_path)
    print(f"The uploaded file apperas to be {'complete' if server_file_md5_sum == my_file_md5 else 'corrupted'}!")


if __name__ == "__main__":
    print("Starting Client!")
    
    try:
        client_socket = connect_to_server(SRV_HOST, SRV_PORT)
        print(f"Now connected to: {client_socket.getpeername()}")
    except ConnectionRefusedError:
        print("Server refused the connection.... It might be down, busy with another client or something?!")
        raise SystemExit(0)
        
    with SocketHandler(client_socket) as client:
        print("Now waiting for the server. to talk with me. I'm probably in a queue..")
        client.send_text(CLIENT_SERVER_SECRET)

        server_mode = client.receive_text()
        print(f"SERVER MODE: {server_mode}")

        try:
            match server_mode:
                case "logging":
                    run_logging_mode(client)
                case "upload":
                    run_upload_mode(client)
                case _:
                    print(" -- Server is returning an unhandled mode..... --")
                    print(f" -- THE SERVER SAYS: {server_mode}")
                    print(" -- SHUTTING DOWN! -- ")
        except AssertionError as err:
            print(err)
        except FileNotFoundError as err:
            print(" -- ERROR: The file your trying to upload doesn't exist...")
            print(f" -- ERROR: {err}")

    print("Ending Client!")


