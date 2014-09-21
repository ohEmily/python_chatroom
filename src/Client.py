'''
Client. Should manage authentication, protection against consecutive failed 
logins, and multiple clients.

Run using 'python Client.py <server_IP_address> <server_port_no>'.

@author: Emily Pakulski
'''

from socket import *
from sys import argv

BUFF_SIZE = 4096

def start(argv):
    server_IP_addr = int(argv[1])
    server_port = int(argv[2])
    
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((server_IP_addr,server_port))
    
     
    # sock.close()

# main
start(argv)