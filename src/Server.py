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
from threading import Thread, current_thread, Timer
import datetime # to recall when a user logged in
from collections import defaultdict # for keys mapped to lists

BUFF_SIZE = 4096
IP_ADDR = '127.0.0.1'
BACKLOG = 5 # max number of queued connections
BLOCK_TIME = 60 # time period IP is blocked after 3 failed logins

# commands supported by the server
WHO_ELSE_CONNECTED = 'whoelse'
WHO_LAST_HOUR = 'wholasthr'
BROADCAST = 'broadcast' 
MESSAGE = 'message'
LOGOUT = 'logout' 

# global variables
logged_in_users = [] # list of tuples (username, client_port)
past_connections = {} # dictionary (key = connection_time, val = client_port)
blocked_connections = {} # dictionary (key = IP_addr, val = blocked_usernames)

# COMMAND FUNCTIONS
# sends names of currently connected users
def cmd_who_else(client, sender_username):
    other_users_list = 'Other users currently logged in: ' 
    
    for user in logged_in_users:
        if (user[0] != sender_username):
            other_users_list += user[0] + ' '
    
    # if nobody else besides this client is logged in, let the client know
    if (len(logged_in_users) < 2): 
        other_users_list += '[none]'
    
    client.sendall(other_users_list)

# sends names of users connected in last hour
def cmd_who_last_hour(client):
    # remove all usernames from over an hour ago
    for time in past_connections:
        if datetime.datetime.now() - time > datetime.timedelta(hours = 1):
            past_connections.remove(time)
    
    # send back remaining users
    other_users_list = 'Users who connected in the past hour: \n' 
    
    for key in past_connections:
        other_users_list += '\t' + past_connections[key] + ' connected at ' + str(key) + '\n'
    
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
    for user in logged_in_users:
        if user[1] == client:
            stdout.flush()
            print 'Client ' + user[0] + ' disconnected. '
            logged_in_users.remove(user)
    client.sendall('Good bye!' )
    client.close()

# loop that accepts the defined commands.
def prompt_commands(client, username):    
    while 1:
        try:
            client.sendall('Please type a command. ')
            command = client.recv(BUFF_SIZE).split()
        except: # catch  errno 9 bad file descriptor if client disconnects  
            cmd_logout(client)
            client.close()
        
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
            client.sendall('Command not found. ')

def login(client, username):
    client.sendall('Login successful. Welcome! ')
    logged_in_users.append((username, client))
    past_connections[datetime.datetime.now()] = username 

# add the username to the list of blocked usernames for this IP
def block(ip_addr, username):    
    list_of_blocked_usernames = blocked_connections[ip_addr]
    list_of_blocked_usernames.append(username)
    blocked_connections[ip_addr] = list_of_blocked_usernames

# remove the username from thel ist of blocked usernames from this IP
def unblock(ip_addr, username):
    list_of_blocked_usernames = blocked_connections[ip_addr]
    list_of_blocked_usernames.remove(username)
    blocked_connections[ip_addr] = list_of_blocked_usernames

# returns true if username is blocked for this IP; false if not
def is_blocked(ip_addr, username):
    list_of_blocked_usernames = blocked_connections[ip_addr]
    if (username in list_of_blocked_usernames):
        return True
    return False

# Return true or false depending on whether the user logs in or not.
# If user fails password 3 times for same username, block them for 60 seconds.
def prompt_login(client_port, client_ip):
    username = 'default'
    
    # loop until user inputs a username that exists before continuing
    while (not username in logins):
        client_port.sendall('Please enter a valid username. ')
        username = client_port.recv(BUFF_SIZE) # e.g. 'google'
    
        if (is_blocked(client_ip, username)):
            client_port.sendall('Your access to this account is temporarily blocked. ')
            username = 'default'
    
    # suspend connection if 3 failed attempts. Otherwise login
    login_attempt_count = 0
    while login_attempt_count < 3:
        client_port.sendall('Please enter your password.')
        password = client_port.recv(BUFF_SIZE) # e.g. 'hasglasses' 
        
        if (logins[username] != password):
            login_attempt_count += 1
            client_port.sendall('Login incorrect. Please try again. ')
        
        elif (logins[username]) and (logins[username] == password):
            login(client_port, username)
            return (True, username)
    
    return (False, username)

# Logs that there is a new client and prompts for user credentials.
# If login is successful, allows user to run commands.
def handle_client(client_sock, client_ip):
    # initialize list of usernames that may need to be blocked from this IP
    blocked_connections[client_ip] = []
    
    try:
        while 1:
            user_login = prompt_login(client_sock, client_ip)
            if (user_login[0]):
                client_sock.sendall('Welcome! ')
                prompt_commands(client_sock, user_login[1])
                
            else:
                # suspend connection and notify user  
                client_sock.sendall('Login failed too many times. ' +
                            'Temporarily suspending. ')
                block(client_ip, user_login[1])
                # set callback to unblock this username after BLOCK_TIME elapses
                Timer(BLOCK_TIME, unblock, (client_ip, user_login[1])).start()
                #cmd_logout(client_sock)
    except:
        stdout.flush()
        print "Client on IP and port " + str(client_ip) + " forced disconnect."

# Reads from text file to create dictionary of username-password combinations.
def populate_logins_dictionary():
    user_logins = {}
    aFile = open("../user_pass.txt")
    
    for line in aFile:
        (key, val) = line.split()
        user_logins[key] = val

    aFile.close()
    return user_logins

# Prepares server socket to accept clients, with each client running on a 
# separate thread.
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