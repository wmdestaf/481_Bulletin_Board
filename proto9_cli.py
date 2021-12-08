from proto9_util_extractor import *
from proto9_util_argparse  import *
from proto9_data           import *
import socket
from socket import AF_INET, SOCK_STREAM, error
from threading import Thread, Semaphore
import re
import time
import signal

serverName = 'localhost'
serverPort = 12000
clientSocket = socket.socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName,serverPort))

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

extractor = SBBP_Frame_Extractor(clientSocket, (serverName, serverPort), RECV_SSIZE, on_recieve_frame)

def on_exit(*args):
    extractor.close()
    quit()
signal.signal(signal.SIGINT, on_exit)

while True:
    msg = input("MSG: ")
    if not msg:
        extractor.close()
    clientSocket.sendall(str_to_bytes(zip_seperators(msg)))
    time.sleep(0.5)
    
'''
    TODO:
    client send like a human being
    semaphore on client input recieve
    lock access to board with RWSEM
'''