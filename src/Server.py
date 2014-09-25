'''
Server. Should manage authentication, protection against consecutive failed 
logins, and multiple clients.

Run using 'python Server.py <server_port_no>'.

@author: Emily Pakulski
'''

# TODO: update logged in users when user disconnects
# TODO: fix login to match assignment exactly
# TODO: check that user is not already logged in when logging in

from socket import socket, AF_INET, SOCK_STREAM
import time # for e.g. time.sleep(1)
from sys import argv
from sys import stdout
from threading import Thread, current_thread
import datetime # to recall when a user logged in

BUFF_SIZE = 4096
IP_ADDR = '127.0.0.1'
BACKLOG = 5 # max number of queued connections
BLOCK_TIME = 6000 # time period IP is blocked after 3 failed logins

# commands supported by the server
WHO_ELSE_CONNECTED = 'whoelse'
WHO_LAST_HOUR = 'wholasthr'
BROADCAST = 'broadcast' 
MESSAGE = 'message'
LOGOUT = 'logout' 

# global variables
logged_in_users = [] # list of tuples (username, client_port)
past_connections = {} # dictionary (key = connection_time, val = client_port)

# COMMAND FUNCTIONS
# sends names of currently connected users
def cmd_who_else(client, sender_username):
    other_users_list = 'Other users currently logged in: ' 
    
    for user in logged_in_users:
        if (user[0] != sender_username):
            other_users_list += user[0] + ' '
    
    client.sendall(other_users_list)

# sends names of users connected in last hour
def cmd_who_last_hour(client):
    # remove all usernames from over an hour ago
    for time in past_connections:
        if datetime.datetime.now() - time > datetime.timedelta(hours = 1):
            past_connections.remove(time)
    
    # send back remaining users
    other_users_list = 'Users who connected in the past hour: ' 
    
    for user in past_connections:
            other_users_list += user[0] + ' '
    
    client.sendall(other_users_list)

# send message to all users currently logged in
def cmd_broadcast(user, command):
    message = 'Message to all users from ' + user + ': '
    
    for word in command[1:]:
        message += word + ' '

    for user_tuple in logged_in_users:
        user_tuple[1].sendall(message)

# private message to a single user (run 'message <user> <message>')
def cmd_private_message(sender_username, command):
    message = 'Private message from ' + sender_username + ': '
    
    receiver = command[1]
    
    for word in command[2:]:
        message += word + ' '
    
    for user_tuple in logged_in_users:
        if user_tuple[0] == receiver:
            user_tuple[1].sendall(message)

# notifies users of logout and updates array for logged out users 
def cmd_logout(client):
    client.sendall('Good bye!')
    for user in logged_in_users:
        if user[1] == client:
            stdout.flush()
            print 'Client ' + user + ' disconnected.'
            logged_in_users.remove(user)
    client.close()

# loop that accepts the defined commands.
def prompt_commands(client, username):    
    while 1:
        client.sendall('Please type a command.')
        command = client.recv(BUFF_SIZE).split()
        
        if (command[0] == WHO_ELSE_CONNECTED):
            cmd_who_else(client, username)
            
        elif (command[0] == WHO_LAST_HOUR):
            cmd_who_last_hour(client)
            
        elif (command[0] == BROADCAST):
            cmd_broadcast(username, command)

        elif (command[0] == MESSAGE):
            cmd_private_message(username, command)
            
        elif (command[0] == LOGOUT):
            cmd_logout(client)
            
        else:
            client.sendall('Command not found.')

def login(client, username):
    client.sendall('Login successful. Welcome!')
    logged_in_users.append((username, client))
    past_connections[datetime.datetime.now()] = username 

# Return true or false depending on whether the user logs in or not.
# If user fails password 3 times for same username, block them for 60 seconds.
def prompt_login(client_port):
    login_attempt_count = 0
    
    while login_attempt_count < 3:
        stdout.flush()
        
        client_port.sendall('Please enter your username.')
        username = client_port.recv(BUFF_SIZE) # e.g. 'google'
    
        client_port.sendall('Please enter your password.')
        password = client_port.recv(BUFF_SIZE) # e.g. 'hasglasses' 
        
        if (not logins[username]) or (logins[username] != password):
            client_port.sendall('Login incorrect. Please try again.')
        
        elif (logins[username]) and (logins[username] == password):
            login(client_port, username) # CHANGE MADE HERE
            return username
        
        login_attempt_count += 1
        
    client_port.sendall('Login failed too many times. Closing connection.')
    return False

def handle_client(client_sock, addr):
    stdout.flush()
    print "New thread: " + str(current_thread()) # log new threads on server
    
    user_login = prompt_login(client_sock)
    if (user_login):
        prompt_commands(client_sock, user_login)
    else:
        client_sock.close()

def populate_logins_dictionary():
    user_logins = {}
    aFile = open("../user_pass.txt")
    
    for line in aFile:
        (key, val) = line.split()
        user_logins[key] = val

    aFile.close()
    return user_logins

def main(argv):
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

logins = populate_logins_dictionary()
main(argv)