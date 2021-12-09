from proto9_util_extractor import *
from proto9_util_argparse  import *
from proto9_data           import *
from proto9_input import get_client_input, set_user
import socket
from socket import AF_INET, SOCK_STREAM
from socket import error as GENERIC_SOCKET_ERROR
from threading import Thread, Semaphore
from _thread import interrupt_main
import re
import time
import signal

while True:
    serverName = input('Connect where? ')
    if not serverName:
        continue
    break

serverPort = 13037

try:
    clientSocket = socket.socket(AF_INET, SOCK_STREAM)
    clientSocket.settimeout(0.5)
except GENERIC_SOCKET_ERROR as e:
    print("Could not establish socket -",e)
    quit(1)
    
try:
    clientSocket.connect((serverName,serverPort))
except GENERIC_SOCKET_ERROR as e:
    print("Could not connect to server -",e)
    quit(1)

mutex = Semaphore(1)
#begin a recieving thread
def on_recieve_frame(*args):
    socket = args[0]
    frame  = args[1]
    if len(args) > 2:
        other = args[2:]

    parsed = CLIENT_ARGPARSER.parse_message(frame)
    
    if not isinstance(parsed, tuple): #Server returned something strange...very bad!
        print( ("#"*20) + "ERROR" + ("#"*20))
        print("Could not parse response from server! (parse returned {:d})".format(parsed))
        print("Dumping information...")
        print(frame)
    else:
        res = EXECUTE_ARGS_CLIENT(parsed[0], parsed[1])

    print(res)
    client_io_lock.release()

def on_exit(*args):
    extractor.mark_dead()
    extractor.t.join()
    quit(0)
signal.signal(signal.SIGINT, on_exit)

client_io_lock = Semaphore(1)

def on_extractor_die(*args):
    print("Server unexpectedly terminated...Press <Enter> to exit.")
    interrupt_main()

extractor = SBBP_Frame_Extractor(clientSocket, (serverName, serverPort), 
            RECV_SSIZE, on_recieve_frame, die_fun = on_extractor_die)

#main processing loop
set_user("What is your User ID?")
while True:

    client_io_lock.acquire()

    try:
        opcode, args = get_client_input()
    except TypeError: #returned 'None'
        break
        
    raw = str_to_bytes(argjoin(opcode, args))

    try:
        clientSocket.sendall(raw)
    except GENERIC_SOCKET_ERROR as e:
        print("Error sending message:",e)
        break
    
on_exit()   
    
'''
    TODO: 
    lock access to board with RWSEM
'''