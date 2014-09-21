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
    aFile = open("../user_pass.txt")
    
    for line in aFile:
        (key, val) = line.split()
        user_logins[key] = val

    aFile.close()
    return user_logins

def prompt_login(client):
    login_attempt_count = 0 
    
    while login_attempt_count < 3:
        client.send('Please enter your username.')
        username = client.recv(BUFF_SIZE) # e.g. 'google'
    
        client.send('Please enter your password.')
        password = client.rev(BUFF_SIZE) # e.g. 'hasglasses' 
        
        if (logins[username] == False) or (logins[username] != password):
            client.send('Login incorrect. Please try again.')
        
        elif (logins[username]) and (logins[username] == password):
            client.send('Login successful. Welcome!')
            return True
        
        login_attempt_count += 1
        
    client.send('Login failed too many times. Closing connection.')
    return False

def start(argv):
    server_port = '55555' #int(argv[1])
    print 'server started on ' + server_port
    
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind((IP_ADDR,server_port))
    sock.listen(BACKLOG)
    
    while(1):
      client_connection, addr = sock.accept()
      prompt_login(client_connection)
      
      client_connection.close()
      
    sock.close()

# main
logins = get_logins()
start(argv)