'''
Client. Should manage authentication, protection against consecutive failed 
logins, and multiple clients.

Run using 'python Client.py <server_IP_address> <server_port_no>'.

@author: Emily Pakulski
'''

from socket import socket, AF_INET, SOCK_STREAM
from sys import argv
from sys import stdout
from threading import Thread

BUFF_SIZE = 4096

# handles sending text typed in stdin to server. 
# Runs on its own thread.
def send_to_server(sock, server_IP):
    while 1:
        try:
            message = raw_input()
            sock.sendall(message)
        except EOFError: # listens for exiting with ctrl + C
            print '\nClosing connection to server.'
    
# handles outputting messages from server to stdout. 
# Runs on its own thread.
def recv_from_server(sock, server_IP):
    while 1:
        message = sock.recv(BUFF_SIZE)
        if len(message) > 0:
            print message
        stdout.flush()

def start(argv):
    server_IP_addr = argv[1]
    server_port = int(argv[2])
    
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((server_IP_addr,server_port))
    
    # start threads for sending and receiving
    send_thread = Thread(target=send_to_server, args=(sock, server_IP_addr))
    send_thread.start()
    recv_thread = Thread(target=recv_from_server, args=(sock, server_IP_addr))
    recv_thread.start()

# main
start(argv)