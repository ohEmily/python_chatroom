'''
Server. Should manage authentication, protection against consecutive failed 
logins, and multiple clients.

Run using 'python Server.py <server_port_no>'.

@author: Emily Pakulski
'''

from socket import *
from sys import argv

BUFF_SIZE = 4096
IP_ADDR = '127.0.0.1' # localhost
BACKLOG = 5 

def get_logins():
    user_logins = {}
    file = open("../user_pass.txt")
    
    for line in file:
        (key, val) = line.split()
        user_logins[int(key)] = val

    file.close()
    
    return user_logins

def prompt_login(client):
    client.send('Please enter your username.')
    username = client.recv(BUFF_SIZE)
    client.send('Please enter your password.')
    password = client.rev(BUFF_SIZE)

def start(argv):
    server_port = int(argv[1])
    print server_port
    
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind((IP_ADDR,server_port))
    sock.listen(BACKLOG)
    
    while(1):
      client_connection, addr = sock.accept()
      client_input = client_connection.recv(BUFF_SIZE)
      
      # do things
      
      client_connection.close()
      
    sock.close()

# main

start(argv)