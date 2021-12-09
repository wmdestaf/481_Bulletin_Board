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

#Request useer for server IP
while True:
    serverName = input('Connect where? ')
    if not serverName:
        continue
    break

serverPort = 13037 #per assignment specification

#Establish a socket
try:
    clientSocket = socket.socket(AF_INET, SOCK_STREAM)
    clientSocket.settimeout(0.5)
except GENERIC_SOCKET_ERROR as e:
    print("Could not establish socket -",e)
    quit(1)
    
#Connect the socket to the server
try:
    clientSocket.connect((serverName,serverPort))
except GENERIC_SOCKET_ERROR as e:
    print("Could not connect to server -",e)
    quit(1)

'''
    Called by the client's Frame Extractor upon reception of a complete frame.
    Note: This function's calling context is from a daemon.
    @param args Variable number of arguments
'''
def on_recieve_frame(*args):
    socket = args[0]
    frame  = args[1]
    if len(args) > 2:
        other = args[2:]

    parsed = CLIENT_ARGPARSER.parse_message(frame)
    
    if not isinstance(parsed, tuple): #Server returned something strange...very bad!
        print(("#"*20) + "ERROR" + ("#"*20))
        print("Could not parse response from server! (parse returned {:d})".format(parsed))
        print("Dumping information...")
        print(frame)
    else:
        res = EXECUTE_ARGS_CLIENT(parsed[0], parsed[1])

    print(res)
    client_io_lock.release()

'''
    Cleans up on keyboard interrupt. This is additionally fired if
    the client's frame extractor encounters a socket error.
    Because of signal hackery, this can be called from the client's context
    by a thread.
    @param args unused
'''
def on_exit(*args):
    client_io_lock.release() #Just in case we're still holding the lock
    extractor.mark_dead()
    extractor.t.join()
    quit(0)
signal.signal(signal.SIGINT, on_exit) #register the handler

client_io_lock = Semaphore(1) #Ensure that recieved messages appear prettily.
                              #Absolutely not necessary as SBBP_Frame_Extractor handles
                              #incomplete messages split across multiple recv calls, but...

'''
    Called upon recieving socket error in the extractor. Will notify
    main through a KeyboardInterrupt signal, the equivalent of
    calling on_exit from main's context.
    @param args unused
'''
def on_extractor_die(*args):
    print("Server unexpectedly terminated...Press <Enter> to exit.")
    interrupt_main()

#Client's frame extractor
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