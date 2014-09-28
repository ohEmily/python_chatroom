'''
Server. Should manage authentication, protection against consecutive failed 
logins, and multiple clients.

Run using 'python Server.py <server_port_no>'.

@author: Emily Pakulski
'''

from socket import socket, AF_INET, SOCK_STREAM
from sys import argv
from sys import stdout
from threading import Thread, current_thread, Timer
import datetime # to recall when a user logged in

BUFF_SIZE = 4096
IP_ADDR = '127.0.0.1'
BACKLOG = 5 # max number of queued connections
BLOCK_TIME = 60 # time period in seconds for IP blocking after 3 failed logins
TIME_OUT = 30 * 60 # time in seconds after user is logged out due to inactivity

# commands supported by the server
WHO_ELSE_CONNECTED = 'whoelse'
WHO_LAST_HOUR = 'wholasthr'
BROADCAST = 'broadcast' 
MESSAGE = 'message'
LOGOUT = 'logout' 

# global variables
logged_in_users = [] # list of tuples (username, client_sock)
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
        other_users_list += '[none] '
    
    client.sendall(other_users_list)

# sends names of users connected in last hour
def cmd_who_last_hour(client, username):
    # remove all usernames from over an hour ago
    for time in past_connections:
        if datetime.datetime.now() - time > datetime.timedelta(hours = 1):
            past_connections.remove(time)
    
    # send back remaining users
    other_users_list = 'Users who connected in the past hour: \n' 
    
    for key in past_connections:
        if (key != username):
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
def cmd_logout(client, username):
    client.sendall('Good bye!' )
    client_exit(client, username)

# logs server for client disconnect and performs cleanup operations
def client_exit(client, client_identifier):
    for user in logged_in_users:
        if user[1] == client:
            stdout.flush()
            print "Client " + str(client_identifier) + " disconnected. "
            logged_in_users.remove(user)
    client.close()

# called when TIME_OUT elapses while waiting for a user command
def client_timeout(client, client_identifier):
    client.sendall('Your session has been timed out due to inactivity.')
    client_exit(client, client_identifier)

# loop that accepts the defined commands.
def prompt_commands(client, username):    
    while 1:
        try:
            client.sendall('Please type a command. ')
            
            # set timer to logout if user is inactive for 30 min
            Timer(TIME_OUT, client_timeout, (client, username)).start()
            
            command = client.recv(BUFF_SIZE).split()
        except: # catch  errno 9 bad file descriptor if client disconnects  
            cmd_logout(client, username)
            client.close()
        
        if (command[0] == WHO_ELSE_CONNECTED):
            cmd_who_else(client, username)
            
        elif (command[0] == WHO_LAST_HOUR):
            cmd_who_last_hour(client, username)
            
        elif (command[0] == BROADCAST):
            cmd_broadcast(username, command)

        elif (command[0] == MESSAGE):
            cmd_private_message(username, command)
            
        elif (command[0] == LOGOUT):
            cmd_logout(client, username)
            
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

def is_already_logged_in(username):
    for user in logged_in_users:
        if user[0] == username:
            return True
    return False

# Return true or false depending on whether the user logs in or not.
# If user fails password 3 times for same username, block them for 60 seconds.
def prompt_login(client_sock, client_ip):
    username = 'default'
    
    # loop until user inputs a valid username
    while (not username in logins):
        client_sock.sendall('Please enter a valid username. ')
        username = client_sock.recv(BUFF_SIZE) # e.g. 'google'
    
        if (is_blocked(client_ip, username)):
            client_sock.sendall('Your access to this account is temporarily blocked. ')
            username = 'default'
        
        if (is_already_logged_in(username)):
            client_sock.sendall('This username is already in use. ')
            username = 'default'
    
    # suspend connection if 3 failed attempts. Otherwise login
    login_attempt_count = 0
    while login_attempt_count < 3:
        client_sock.sendall('Please enter your password.')
        password = client_sock.recv(BUFF_SIZE) # e.g. 'hasglasses' 
        
        if (logins[username] != password):
            login_attempt_count += 1
            client_sock.sendall('Login incorrect. Please try again. ')
        
        elif (logins[username]) and (logins[username] == password):
            login(client_sock, username)
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
    except:
        stdout.flush()
        client_exit(client_sock, client_ip)

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
    print "Server Listening on port " + str(server_port) + "...\n"
    stdout.flush()
    
    while 1:
        client_connection, addr = sock.accept()
        print "Client connected from IP "  + str(addr) + "."
        
        thread = Thread(target=handle_client, args=(client_connection, addr))
        thread.start()

logins = populate_logins_dictionary()
main(argv)