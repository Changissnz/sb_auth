# sb_auth (seqbuild Authenticator) 

*Work in progress* 

A WebSocket authentication schematic for a client-server model, using the `seqbuild` library. 

Simple client-server layout. Authentication allows for file read/write operations to take 
place between the two devices. 

*NOTE*  
The current websocket implementation uses the unsecured `ws://` protocol instead of the 
secured `wss://` one. The development of this authenticator has not advanced into 
production-level mode.  

This codebase works for local WiFi networks but otherwise, more code with third-party 
services must be used for secured communication. 

## Description 

There are three perspectives for use: 
- local (server or client side): offline mode, used to modify read/write settings and delete bunk 
Comm Lang key files.  
- server: can serve an unspecified number of clients. Every authenticated client has read/write access to permitted files/folders.  
- client: can access one server at a time to read/write permitted files.  

The procedure in which a client interacts with a server goes so:  
1. Client sends IP address and port number (default is 8765, variable<DEFAULT_PORT>), and 
connects to the server.  
2. Client inputs username. If server has no registered username, it sends client a new 
Comm Lang file key. This is a script that loads up a primary pseudo-random number generator 
G, and can be executed by `seqbuild`'s Comm Lang interpreter. Client stores this Comm Lang 
file key and sets the number of past iterations `i_p` to 0.  
3. Client is required to output `q_x` integers from generator G, `q_x` specified by the server and 
in the range of `DEFAULT_SB_AUTH_KEYSIZE_RANGE`, default set to `[24,58]`, every time client 
prompts to read/write a file; `q_x` is variable. These `q_x` integers are sent to the server, 
and the server terminates connection if those integers do not match the ones it calculated, given 
the same Comm Lang file key. 
4. When the number of past iterations `i_p` of G passes a number `q2`, specified by the server 
and in the range of `DEFAULT_SB_AUTH_INDEX_RANGE`, default set to `[627,1450)`, server sends 
client a new Comm Lang file key. Integer `q2` is set by the server when client connects to it, 
and remains constant throughout the session. 

Server does not require any user input. Client requires user to input IP address/port, as well 
as for read/write operations to permitted files.  

On the server side, every username it has stored in its client directory is associated with a 
file for file+folder exclusions. These exclusions prohibit the client from read/write operations 
concerning them.  

## Default File Naming 

- Server Side:  
    - username directory file is @ `user_data/server_dir`.  
    - directory file stores Comm Lang key file names and generator index (number of past iterations) 
    for every username. 
    - directory file column layout is 
        - username  
        - Comm Lang key filepath  
        - primary generator name  
        - generator index  
        - number of sessions key has been used 
    - every username `U` has a Comm Lang file key @ `user_data/commond_U.txt`.  
    - default permissions file is @ `user_data/default_user_permissions.txt`.  
    - every username `U` has an exclusion file @ `user_data/permissions_U.txt`.

- Client Side: 
    - username directory file is @ `user_data/client_dir`.  
    - column layout is virtually identical to that of server side.  
    - every server of IP address `I` and port `Q` is assigned a Comm Lang key file @ 
    `user_data/server__I-Q.txt`. 

## The Identity Aspect 

Websocket has the problem of authentication. If a username's Comm Lang file key for a  
server is shared between `> 1` devices, those devices can all access the server under  
the same username.  

For a server with a fixed IP address and port combination, a device can access it through 
only one username, given how the file naming convention goes.  

## Technicals Behind the Generator Key  

The program used to generate Comm Lang key files is `seqbuild` @  
[seqbuild](https://www.github.com/changissnz/seqbuild). Specifically, the Comm Lang file 
generator is @ the file `face/easy_gen_struct.py`. There may be instances where the key 
may be a generator such that two different devices output different sequences of integers. 
So the Comm Lang key file generator is not guaranteed to be stable. 

## Usage 

Go into this directory, and run this script: 

```
from sb_auth.exec import * 
```