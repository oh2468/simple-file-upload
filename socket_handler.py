import socket
import random
import os
import time
import hashlib


class SocketHandler:
    MY_DEFAULT_SOCK_TIMEOUT = 30
    MY_DEFAULT_BUFFER_SIZE = 4096
    MY_DEFAULT_TEXT_ENC = "UTF-8"


    def __init__(self, client_socket, max_ram_size=0):
        self.sock = client_socket
        self.max_ram_size = max_ram_size
        self.rand_id = random.randint(10, 99)
        self.sock.settimeout(self.MY_DEFAULT_SOCK_TIMEOUT)
    

    def __del__(self):
        self.sock.close()
        #print(f"Client {self.rand_id} socket now closed from DEL properly!")


    def __enter__(self):
        print(f"Now entering {self.rand_id} context manager.")
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        self.sock.close()
        print(f"Client {self.rand_id} socket now closed from EXIT properly!")
        
        if exc_type:
            if exc_type.__name__ == "TimeoutError":
                print(f"\n -- ERROR: The client {self.rand_id} socket timed out.... -- \n")
                return True
            if exc_type.__name__ == "ConnectionAbortedError" or exc_type.__name__ == "ConnectionResetError":
                print(f"\n -- ERROR: The connection between the client {self.rand_id} and server has been lost... -- \n")
                return True
            if exc_type.__name__ == "AssertionError":
                print("\nCatching error in SocketHandler!!\n")
                # incase I want to handle assertion errors here since I throw them...
                pass
                #print(exc_value)
                #return True


    def connect(self, host, port):
        self.sock.connect((host, port))


    def set_delay(self, delay):
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 0 if delay else 1)


    def md5sum(self, file_path):
        hash = hashlib.md5()
        with open(file_path, "rb") as file:
            while (data := file.read(self.MY_DEFAULT_BUFFER_SIZE)):
                hash.update(data)
        
        return hash.hexdigest()


    def send_all_data(self, data):
        self.sock.sendall(data)


    def receive_buff_size_data(self):
        return self.sock.recv(self.MY_DEFAULT_BUFFER_SIZE)


    def receive_data(self, data_size):
        data = b""
        
        while len(data) < data_size:
            data_part = self.receive_buff_size_data()
            if not data_part: break
            data += data_part

        return data


    def __upload_file_in_ram(self, file_path, file_size, printer):
        with open(file_path, "rb") as file:
            self.send_all_data(file.read())
            printer.print_progress(file_size)
            return True


    def upload_file(self, file_path):
        file_size = os.path.getsize(file_path)
        total_sent = 0
        printer = PrintHandler(file_path, file_size, True)

        if file_size <= self.max_ram_size: return self.__upload_file_in_ram(file_path, printer)

        with open(file_path, "rb", self.MY_DEFAULT_BUFFER_SIZE) as file:
            while (data := file.read(self.MY_DEFAULT_BUFFER_SIZE)):
                self.send_all_data(data)
                total_sent += len(data)
                printer.print_progress(total_sent)
            return True


    def download_file(self, file_name):
        pass
    
    
    def delete_corrupt_file(self, file_name):
        pass
    

    def __receive_file_in_ram(self, file_path, file_size, printer):
        with open(file_path, "wb") as file:
            file.write(self.receive_data(file_size))
            printer.print_progress(file_size)
            return True


    def receive_file(self, file_path, file_size):
        received_data = 0
        printer = PrintHandler(file_path, file_size, False)

        if file_size <= self.max_ram_size: return self.__receive_file_in_ram(file_path, printer)

        with open(file_path, "wb", self.MY_DEFAULT_BUFFER_SIZE) as file:
            while received_data < file_size:
                data = self.receive_buff_size_data()
                if not data: 
                    print()
                    return False
                file.write(data)     
                received_data += len(data)
                
                printer.print_progress(received_data)
                # toggle these to slow down localhost transfers
                #if random.randint(0, 20) == 5: time.sleep(0.01)
                #time.sleep(0.01)
            return True


    def convert_text_to_bytes(self, text):
        return text.encode(self.MY_DEFAULT_TEXT_ENC)

    
    def convert_bytes_to_text(self, data):
        return data.decoce(self.MY_DEFAULT_TEXT_ENC)
    

    def send_text(self, text):
        # toggle this so inspect text transfers
        #print(f"NOW SENDING TEXT: {text}")
        self.send_all_data(text.encode(self.MY_DEFAULT_TEXT_ENC))


    def receive_text(self, text_length=0):
        if not text_length:
            return self.receive_buff_size_data().decode(self.MY_DEFAULT_TEXT_ENC)
        else:
            text_msg = ""
            while len(text_msg) < text_length:
                data = self.receive_buff_size_data()
                if not data: break
                text_msg += data.decode(self.MY_DEFAULT_TEXT_ENC)
            return text_msg[:text_length]


    def send_file_md5_sum(self, file_path):
        self.send_text(self.md5sum(file_path))



class PrintHandler():
    PROGRESS_UPDATE_COUNT = 10
    UPDATE_PRINT_INTERVAL = 2
    PROG_BAR = 20
    PROG_BOX = 100 / PROG_BAR

    
    def __init__(self, file_path, file_size, sending_file):
        self.file_name = os.path.basename(file_path)
        self.file_size = file_size
        self.sending_file = sending_file
        self.hum_re_size = self.convert_bytes_to_print(self.file_size)
        self.prev_print = 0
        self.print_start()
        self.start_time = time.time()


    def print_start(self):
        direction = "OUTGOING" if self.sending_file else "INCOMING"
        print(f"\n\t{direction} FILE: {self.file_name}, SIZE: {self.convert_bytes_to_print(self.file_size)}")


    def convert_bytes_to_print(self, bts):
        sizes = ["B", "KB", "MB", "GB"]
        index = 0
        while bts / 1000 > 1:
            index += 1
            bts /= 1000
        
        #print(f"Size: {bts:.2f} {sizes[index]}")
        return f"{bts:.2f} {sizes[index]}"


    def print_progress(self, curr_size):
        now = time.time()
        if now - self.prev_print < self.UPDATE_PRINT_INTERVAL and curr_size != self.file_size: return

        self.prev_print = now
        progress = (curr_size / self.file_size) * 100

        prog_dash = int(progress / self.PROG_BOX)
        prog_dot = self.PROG_BAR - prog_dash

        print(f"\tPROGRESS: [{'#' * prog_dash}{'.' * prog_dot}] {(progress):.2f} %, TIME ELSAPSED: {(now - self.start_time):.2f} s", end="\r")
        if progress == 100:
            print("\n")


