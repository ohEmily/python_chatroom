'''
Client. Supports 2 threads -- one for sending, one for receiving.
Intentionally kept as simple as possible in order to push computationally
expensive operations to the server.

Run using 'python Client.py <server_IP_address> <server_port_no>'.

@author: Emily Pakulski
'''

from socket import socket, AF_INET, SOCK_STREAM
from sys import argv, stdout, exit
from threading import Thread

BUFF_SIZE = 4096
connected = False
# Handles sending text from stdin to server. Runs on its own thread.
def send_to_server(sock, server_IP):
    try:
        while 1:
            message = raw_input()
            sock.sendall(message)
    except: # listens for exiting with ctrl + C
        connected = False
        exit(1)
    
# Handles outputting messages from server to stdout. Runs on its own thread.
def recv_from_server(sock, server_IP):
    try: 
        while 1:
            message = sock.recv(BUFF_SIZE)
            if len(message) > 0:
                stdout.flush()
                print message
    except: # listens for exiting with ctrl + C
        connected = False
        exit(1)
        

# Connects to server socket and starts send and receive threads.
def main(argv):
    server_IP_addr = argv[1]
    server_port = int(argv[2])
    
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((server_IP_addr,server_port))
    connected = True
    
    # start threads for sending and receiving
    send_thread = Thread(target=send_to_server, args=(sock, server_IP_addr))
    send_thread.start()
    recv_thread = Thread(target=recv_from_server, args=(sock, server_IP_addr))
    recv_thread.start()
    
    # graceful exit when user hits Ctrl + C
    try:
        while True:
            if (not connected):
                exit(1)
    except (KeyboardInterrupt, SystemExit):
        stdout.flush()
        print '\nConnection to server closed. '
    
main(argv)