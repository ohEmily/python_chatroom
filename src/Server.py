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
BACKLOG = 5 # max number of queued connections
BLOCK_TIME = 6000 # time period IP is blocked after 3 failed logins

# commands supported by the server
WHO_ELSE_CONNECTED = 'whoelse' # sends names of currently connected users
WHO_LAST_HOUR = 'wholasthr' # sends names of users connected in last hour
BROADCAST = 'broadcast' # send message to all connected users
MESSAGE = 'message' # private message to a user (run 'message <user> <message>')
LOGOUT = 'logout' # logout this user

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
        password = client.recv(BUFF_SIZE) # e.g. 'hasglasses' 
        
        if (not logins[username]) or (logins[username] != password):
            client.send('Login incorrect. Please try again.')
        
        elif (logins[username]) and (logins[username] == password):
            client.send('Login successful. Welcome!')
            return True
        
        login_attempt_count += 1
        
    client.send('Login failed too many times. Closing connection.')
    return False

def start(argv):
    server_port = int(argv[1])
    
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind((IP_ADDR,server_port))
    sock.listen(BACKLOG)
    print 'Server Listening on port ' + str(server_port) + '...'
    
    while(1):
      client_connection, addr = sock.accept()
      client_connection.recv(BUFF_SIZE)
      prompt_login(client_connection)
      
      print('Client connected from IP ' + str(addr) + '.')
      
      # client_connection.close()
      
    sock.close()

# main
logins = get_logins()
start(argv)