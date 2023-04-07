# Simple Upload Server

## Description

A client/server app which can be used to upload files from the client to the server. The server is multi-threaded and can allow mutliple clients to upload to it at once. The server tries to validate that the file transfer was successfully completed by comparing a md5 checksum of the file with one sent from the client. The client prints a status bar to the terminal during the uploading of the file. 


## Getting Started

Download all the dependecies, then start the server from a terminal by running e.g.: ```python server.py```, once the server is ready to allow connections start the client from a terminal by running e.g.: ```python client.py```. The client default connection is "localhost:45678" so if you want to connect to another ip run the client with e.g.: ```python client.py -r <IP.ADDRESS.GOES.HERE>``` and to connect to another port ```python client.py -r <IP.ADDRESS.GOES.HERE> -p <port-number-here>```

### Dependencies

* Python (developed with v. 3.10.5)
