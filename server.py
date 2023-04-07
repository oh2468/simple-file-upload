import sys
import socket
import signal
import os
import shutil
import time
from socket_handler import SocketHandler


CLIENT_SERVER_SECRET = "SECRETACCESSKEY0"
SRV_HOST, SRV_PORT = "", 45678

SRV_TIMEOUT = 30
SRV_DEFAULT_FILE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "USER_UPLOADED_FILES"))
SRV_ALLOWED_CONNECTIONS = 0
SRV_MAX_DAILY_CONNECTIONS = 3
SRV_MAX_LOG_LENGTH = 2500

SRV_MEGABYTE = 10 ** 6
SRV_MINIMUM_FREE_SPACE = 20 * (10 ** 3) * SRV_MEGABYTE
SRV_MAX_FILE_SIZE = 150 * SRV_MEGABYTE
SRV_MAX_RAM_SIZE = 0 * SRV_MEGABYTE

server_should_still_run = True


def signal_stop_server(signal, frame):
    global server_should_still_run
    server_should_still_run = False
    print("\n\tuser interruption made. shutting down!\t\n")
    sys.exit(1)

signal.signal(signal.SIGINT, signal_stop_server)


def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(SRV_ALLOWED_CONNECTIONS)
    server_socket.settimeout(SRV_TIMEOUT)

    local_name = socket.gethostname()
    local_ip = socket.gethostbyname(local_name)
    print(f"The server is now listening as ({local_name}) on (local ip, port): ({local_ip}, {SRV_PORT})")

    return server_socket


def stop_server(server_socket):
    server_socket.close()


def send_ok_msg(client):
    client.send_text("ok")


def raise_assertion_error(message):
    raise AssertionError(f" -- ERROR: {message} Aborting.")


def raise_server_issue(message):
    print(f" -- ERROR: {message} Aborting.")
    print("\n  -*-*-*-  THE SERVER HAS AN CRITICAL ISSUE, SHUTTING DOWN THE SERVER NOW  -*-*-*-  \n")
    sys.exit(1)


def assert_server_resources():
    if not os.path.isdir(SRV_DEFAULT_FILE_DIR):
        raise_server_issue(f"Upload folder missing... Verify the existence of the upload folder: {SRV_DEFAULT_FILE_DIR} !")
    
    if getattr(shutil.disk_usage("/"), "free") < SRV_MINIMUM_FREE_SPACE:
        raise_server_issue("Running on empty... There is not enough free space on the server!")


def assert_file_name_available(file_name):
    file_name = os.path.basename(file_name)
    srv_file = os.path.join(SRV_DEFAULT_FILE_DIR, file_name)
    
    if os.path.isfile(srv_file):
        raise_assertion_error(f"A file with name {file_name} already exists!")
   
    return srv_file


def assert_file_size_available(file_size):
    if file_size == 0:
        raise_assertion_error("You are trying to upload an empty file.")

    if file_size > SRV_MAX_FILE_SIZE:
        raise_assertion_error(f"The size of the incoming file is too large! Size: {file_size}.")



if __name__ == "__main__":
    print("Starting server!")
    total_connections_made = 0

    server_mode = "logging" if "-l" in sys.argv else "upload"
    print(f"SERVER NOW RUNNING IN MODE: {server_mode}")

    if server_mode == "upload": assert_server_resources()

    server_socket = start_server(SRV_HOST, SRV_PORT)

    while total_connections_made < SRV_MAX_DAILY_CONNECTIONS and server_should_still_run:
        try:
            print("Now waiting for a connection.")
            client_socket, addr = server_socket.accept()
            print(f"New connection established from: {addr}")
        except TimeoutError:
            print("Nobody seems to connect today.... BYE!")
            break

        total_connections_made += 1

        with SocketHandler(client_socket, SRV_MAX_RAM_SIZE) as client:
            client_secret = client.receive_text()
            if client_secret != CLIENT_SERVER_SECRET:
                print(" -- WARNING: RANDO TRYING TO ACCESS THE SERVER!! -- ")
                print(f"Somebody tried to access the server with the wrong creds: {client_secret}")
                total_connections_made -= 1
                client.send_text("I don't know who you are, but you don't have persmission to enter....")
                continue

            client.send_text(server_mode)
            client.set_delay(False)
            client.set_delay(True)
            try:
                if server_mode == "logging":
                    client.send_text(str(SRV_MAX_LOG_LENGTH))
                    
                    log_length = int(client.receive_text())
                    log_length = log_length if log_length <= SRV_MAX_LOG_LENGTH else SRV_MAX_LOG_LENGTH
                    send_ok_msg(client)

                    log_this = client.receive_text(log_length)
                    print(f"SIZE OF LOG MESSAGE: {len(log_this)}")
                    send_ok_msg(client)
                    
                    print(f"\nINCOMING LOG MESSAGE FROM: {addr}, AT: {time.time()}")
                    print(f"LOG: {log_this}\n")
                else:
                    file_name = client.receive_text()
                    srv_file = assert_file_name_available(file_name)
                    send_ok_msg(client)

                    file_size = int(client.receive_text())
                    assert_file_size_available(file_size)
                    send_ok_msg(client)

                    success = client.receive_file(srv_file, file_size)
                    if success:
                        client.send_file_md5_sum(srv_file)
                    else:
                        print(" -- WARNING: The connection terminated before all the data could be recevied!!!")
            except AssertionError as err:
                print(" -- CATCHING ERROR -- ")
                print(err)
                client.send_text(str(err))
            except ValueError as err:
                print(err)
                client.send_text(f"YOU ARE NOT SENDING THE CORRECT DATA FORMAT WHEN EXPECTED...\n{str(err)}")

    stop_server(server_socket)
    print("Closing server!")


