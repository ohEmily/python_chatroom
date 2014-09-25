Client-Server Messaging App (Python)
------------------------------------
An exercise in socket programming and multithreading in Python.

A simple app that creates a chat room for logged in users. User authentication reads from a pre-defined list of usernames and allows or disallows a login. Logged in users can private message and broadcast.

How to run
==========
Server:
```
'python Server.py <server_port_no>'
```

Client(s):
```
'python Client.py <server_IP_address> <server_port_no>'
```