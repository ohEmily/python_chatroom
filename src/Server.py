'''
Server. Should manage authentication, protection against consecutive failed 
logins, and multiple clients. 

Run using 'python Server.py <server_port_no>'.

@author: Emily Pakulski
'''

from socket import socket, AF_INET, SOCK_STREAM
from sys import argv
from sys import stdout
from threading import Thread, Timer
import datetime # to recall when a user logged in

BUFF_SIZE = 4096
OFFLINE_MSG_SIZE = 256
IP_ADDR = '127.0.0.1'
BACKLOG = 5 # max number of queued connections
BLOCK_TIME = 60 # time period in seconds for IP blocking after 3 failed logins
TIME_OUT = 30 * 60 # time in seconds after user is logged out due to inactivity

# commands supported by the server
HELP = 'help'
WHO_ELSE_CONNECTED = 'whoelse'
WHO_LAST_HOUR = 'wholasthr'
BROADCAST = 'broadcast' 
MESSAGE = 'message'
SET_OFFLINE_MSG = 'setawaymsg'
CHECK_OFFLINE_MSG = 'seeawaymsg'
LOGOUT = 'logout' 

commands_dict = {
    WHO_ELSE_CONNECTED : 'Display all users currently logged in. ',
    WHO_LAST_HOUR : 'Display the usernames of all users active within the past hour. ',
    BROADCAST : 'Send a message to the entire chat room. Type \'broadcast <content>\'',
    MESSAGE : 'Send a private message to someone. Type \'message <username> <content>\' ',
    SET_OFFLINE_MSG : 'Set your away message that other users see when you\'re logged off. ',
    CHECK_OFFLINE_MSG : 'View your away message, if any. ',             
    LOGOUT : 'Disconnect this session. '
}

# global variables
logged_in_users = [] # list of tuples (username, client_sock)
past_connections = {} # dictionary (key = connection_time, val = client_port)
blocked_connections = {} # dictionary (key = IP_addr, val = blocked_usernames)
offline_messages = {} # dictionary (key = username, val = away message)

# COMMAND FUNCTIONS
# sends all the possible commands a user can enter
def cmd_help(client):
    text = 'The following commands are available: \n'
    for key in commands_dict:
        text += key + ': ' + commands_dict[key] + '\n'

    client.sendall(text)

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
    for key in past_connections:
        if datetime.datetime.now() - past_connections[key] > datetime.timedelta(hours = 1):
            past_connections.remove(key)
    
    # send back remaining users
    other_users_list = 'Users who connected in the past hour: \n' 

    for key in past_connections:
        if (key != username):
            other_users_list += '\t' + str(key) + '\n'
    
    client.sendall(other_users_list)

# send message to all users currently logged in
def cmd_broadcast(user, command):
    message = 'Message to all users from ' + user + ': '
    
    for word in command[1:]:
        message += word + ' '

    for user_tuple in logged_in_users:
        user_tuple[1].sendall(message)

# private message to a single user (run 'message <user> <message>')
def cmd_private_message(sender_username, client, command):
    message = 'Private message from ' + sender_username + ': '
    
    receiver = command[1]
    
    for word in command[2:]:
        message += word + ' '
    
    receiver_is_logged_in = False
    for user_tuple in logged_in_users:
        if user_tuple[0] == receiver:
            user_tuple[1].sendall(message)
            receiver_is_logged_in = True
    
    if (not receiver_is_logged_in):
        client.sendall(receiver + ' is not logged in. ')

        if (offline_messages.has_key(sender_username)):
            client.sendall('Away message: ' + offline_messages[sender_username])   

# allows user to set an offline message that is shown when another user 
# PMs them but they're not online
def cmd_set_offline_message(client, username):
    client.sendall('Please enter your away message (max 256 characters).')
    offline_msg = client.recv(OFFLINE_MSG_SIZE)
    
    offline_messages[username] = offline_msg

def cmd_see_offline_message(client, username):
    text = 'Your away message: '
    
    if (offline_messages.has_key(username)):
        client.sendall(text + offline_messages[username])
    else:
        client.sendall(text + '[no message set]')

# notifies users of logout and closes socket
def cmd_logout(client):
    client.sendall('Good bye! ')
    client.close() # triggers exception that calls client_exit() call in handle_client()

# logs server for client disconnect and performs cleanup operations
def client_exit(client, client_ip, client_port):
    for user in logged_in_users:
        if user[1] == client:
            logged_in_users.remove(user)
    print 'Client on ' + client_ip + ':' + client_port + ' disconnected. '
    stdout.flush()
    client.close()

# called when TIME_OUT elapses while waiting for a user command
def client_timeout(client, client_identifier):
    client.sendall('Your session has been timed out due to inactivity. ')
    client.close()

# loop that accepts the defined commands.
def prompt_commands(client, client_ip_and_port, username):    
    while 1:
        try:
            client.sendall('Please type a command. ')
            
            # set timer to logout if user is inactive for 30 min
            timeout_countdown = Timer(TIME_OUT, client_timeout, (client, client_ip_and_port))
            timeout_countdown.start()
            
            command = client.recv(BUFF_SIZE).split()
            timeout_countdown.cancel() # cancel timeout when we pass blocking recv call
            past_connections[username] = datetime.datetime.now() # log the user's latest activity
        
        except: # catch  er89 rno 9 bad file descriptor if client disconnects  
            cmd_logout(client)
            client.close()
        
        if (command[0] == HELP):
            cmd_help(client)
        
        elif (command[0] == WHO_ELSE_CONNECTED):
            cmd_who_else(client, username)
            
        elif (command[0] == WHO_LAST_HOUR):
            cmd_who_last_hour(client, username)
            
        elif (command[0] == BROADCAST):
            cmd_broadcast(username, command)

        elif (command[0] == MESSAGE):
            cmd_private_message(username, client, command)
        
        elif(command[0] == CHECK_OFFLINE_MSG):
            cmd_see_offline_message(client, username)
        
        elif (command[0] == SET_OFFLINE_MSG):
            cmd_set_offline_message(client, username)
             
        elif (command[0] == LOGOUT):
            cmd_logout(client)
            
        else:
            client.sendall('Command not found. ')

# welcomes user and stores user login
def login(client, username):
    client.sendall('Login successful. Welcome! ')
    logged_in_users.append((username, client))
    past_connections[username] = datetime.datetime.now() 

# add the username to the list of blocked usernames for this IP
# and drops the connection
def block(ip_addr, client_sock, username):    
    list_of_blocked_usernames = blocked_connections[ip_addr]
    list_of_blocked_usernames.append(username)
    blocked_connections[ip_addr] = list_of_blocked_usernames
    client_sock.close()

# remove the username from the list of blocked usernames from this IP
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
def prompt_login(client_sock, client_ip, client_port):
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
        client_sock.sendall('Please enter your password. ')
        password = client_sock.recv(BUFF_SIZE) # e.g. 'hasglasses' 
        
        if (logins[username] != password):
            login_attempt_count += 1
            client_sock.sendall('Login incorrect. Please try again. ')
        
        elif (logins[username]) and (logins[username] == password):
            login(client_sock, username)
            return (True, username)
    
    return (False, username)

# prompts user to see if they'd like to create a new account
def prompt_create_username(client_sock):
    client_sock.sendall('Hello! Would you like to create a new user? [Y/n]')
    response = client_sock.recv(BUFF_SIZE)
    
    if (response == 'Y'):
        created_username = False
        new_user = ""
        while (not created_username):
            client_sock.sendall('Great. Please choose a username. ')
            new_user = client_sock.recv(BUFF_SIZE)
            
            if (len(new_user) < 5 or len(new_user) > 10):
                client_sock.sendall('Usernames must be between 5 and 10 characters long. ')    
            
            elif (new_user in logins):
                client_sock.sendall('This username already exists!')
            else:
                created_username = True
        
        new_pass = ""
        created_password = False
        while (not created_password):
            client_sock.sendall('Please type in a secure password. ')
            new_pass = client_sock.recv(BUFF_SIZE)
            
            if (len(new_pass) < 6 or len(new_pass) > 16):
                client_sock.sendall('Passwords must be between 6 and 16 characters long.')
            else:
                created_password = True
        
        # write new username and password to file
        with open('../user_pass.txt', 'a') as aFile:
            aFile.write('\n' + new_user + ' ' + new_pass)
        
        # make new username and password available in current session
        logins[new_user] = new_pass
        
        client_sock.sendall('New user created. Redirecting to login menu...')

# Logs that there is a new client and prompts for user credentials.
# If login is successful, allows user to run commands.
def handle_client(client_sock, client_ip_and_port):
    client_ip = client_ip_and_port[0]
    client_port = client_ip_and_port[1]
    
    # initialize list of usernames that may need to be blocked from this IP
    if (not blocked_connections.has_key(client_ip)):
        blocked_connections[client_ip] = []
    
    prompt_create_username(client_sock)
    
    try:
        while 1:
            user_login = prompt_login(client_sock, client_ip, client_port)

            if (user_login[0]): # login succeeded
                prompt_commands(client_sock, client_ip_and_port, user_login[1])
                
            else: # login failed
                # suspend connection and notify user  
                client_sock.sendall('Login failed too many times. ' +
                            'Temporarily suspending. ')
                block(client_ip, client_sock, user_login[1])
                # set callback to unblock this username after BLOCK_TIME elapses
                Timer(BLOCK_TIME, unblock, (client_ip, user_login[1])).start()
    except:
        client_exit(client_sock, client_ip, client_port)

# Reads from text file to create dictionary of username-password combinations
def populate_logins_dictionaries():
    user_logins = {}

    with open('../user_pass.txt') as aFile:
        for line in aFile:
            (key, val) = line.split()
            user_logins[key] = val

    return user_logins

# Prepares server socket to accept clients, with each client running on a 
# separate thread.
def main(argv):
    server_port = int(argv[1])
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind((IP_ADDR,server_port))
    sock.listen(BACKLOG)
    print 'Server Listening on port ' + str(server_port) + '...\n'
    stdout.flush()
    
    try:
        while 1:
            client_connection, addr = sock.accept()
            print 'Client connected on '  + str(addr[0]) + ':' + str(addr[1]) + '. '
            stdout.flush()
            thread = Thread(target=handle_client, args=(client_connection, addr))
            thread.start()
    except (KeyboardInterrupt, SystemExit):
        stdout.flush()
        print '\nServer shut down. '
        
logins = populate_logins_dictionaries()
main(argv)