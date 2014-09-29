Client-Server Messaging App (Python)
====================================
An exercise in socket programming and multithreading in Python.

A simple app that creates a chat room for 	users. Users can log in and out, send private messages, broadcast messages to the whole room, check who else is online, and check who was logged in over the past 60 minutes. User authentication reads from a pre-defined text file containing username and password combinations and allows or disallows a login -- after 3 failed logins on the same IP on the same username, that username is blocked from that IP for 60 seconds (BLOCK_TIME). Users will be logged out after 30 min (TIME_OUT) of inactivity.

How to run
----------
Server:
```
python Server.py <server_port_no>
```

Client(s):
```
python Client.py <server_IP_address> <server_port_no>
```