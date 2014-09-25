Client-Server Messaging App (Python)
====================================
An exercise in socket programming and multithreading in Python.

A simple app that creates a chat room for users. Users can log in and out, send private messages, broadcast messages to the whole room, check who else is online, and check who was logged in over the past 60 minutes. User authentication reads from a pre-defined text file containing username and password combinations and allows or disallows a login.

How to run
----------
Server:
```
'python Server.py <server_port_no>'
```

Client(s):
```
'python Client.py <server_IP_address> <server_port_no>'
```