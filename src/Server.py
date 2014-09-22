'''
Server. Should manage authentication, protection against consecutive failed 
logins, and multiple clients.

Run using 'python Server.py <server_port_no>'.

@author: Emily Pakulski
'''

from socket import *
import time # for e.g. time.sleep(1)
from sys import argv
from sys import stdout
from threading import Thread, current_thread

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

# global variabless
logged_in_users = []

# Return true or false depending on whether the user logs in or not.
# If user fails password 3 times for same username, block them for 60 seconds.
def prompt_login(client):
    login_attempt_count = 0 
    
    while login_attempt_count < 3:
        client.sendall('Please enter your username.')
        username = client.recv(BUFF_SIZE) # e.g. 'google'
    
        client.sendall('Please enter your password.')
        password = client.recv(BUFF_SIZE) # e.g. 'hasglasses' 
        
        if (not logins[username]) or (logins[username] != password):
            client.sendall('Login incorrect. Please try again.')
        
        elif (logins[username]) and (logins[username] == password):
            client.sendall('Login successful. Welcome!')
            return True
        
        login_attempt_count += 1
        
    client.sendall('Login failed too many times. Closing connection.')
    return False

def prompt_commands(client):
    while 1:
        client.sendall('Please type a command.')
        command = client.recv(BUFF_SIZE)
        
        if (command == WHO_ELSE_CONNECTED):
            client.sendall("Command: " + WHO_ELSE_CONNECTED)
        elif (command == WHO_LAST_HOUR):
            client.sendall("Command: " + WHO_LAST_HOUR)
        elif (command == BROADCAST):
            client.sendall("Command: " + BROADCAST)
        elif (command == MESSAGE):
            client.sendall("Command: " + MESSAGE)
        elif (command == LOGOUT):
            client.sendall("Command: " + LOGOUT)
        else:
            client.sendall('Command not found.')

def handle_client(client_sock, addr):
    print "New thread: " + str(current_thread())
    stdout.flush()
    if (prompt_login(client_sock)):
        stdout.flush()
        print 'Successfully logged in user'
        prompt_commands(client_sock)
    else:
        print 'User failed login.'
        client_sock.close()

def start(argv):
    server_port = int(argv[1])
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind((IP_ADDR,server_port))
    sock.listen(BACKLOG)
    print 'Server main thread: ' + str(current_thread())
    print "Server Listening on port " + str(server_port) + "...\n"
    stdout.flush()
    
    while 1:
        client_connection, addr = sock.accept()
        print "Client connected from IP "  + str(addr) + "."
        
        thread = Thread(target=handle_client, args=(client_connection, addr))
        thread.start()

def populate_logins_dictionary():
    user_logins = {}
    aFile = open("../user_pass.txt")
    
    for line in aFile:
        (key, val) = line.split()
        user_logins[key] = val

    aFile.close()
    return user_logins

# main
logins = populate_logins_dictionary()
start(argv)