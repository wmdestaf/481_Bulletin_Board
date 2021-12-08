from proto9_util_extractor import *
from proto9_util_argparse  import *
from proto9_data           import *
import socket
from socket import AF_INET, SOCK_STREAM
from socket import error as GENERIC_SOCKET_ERROR
from threading import Thread
import signal
serverPort = 13037

try:
    serverSocket = socket.socket(AF_INET,SOCK_STREAM)
    serverSocket.settimeout(0.5)
    serverSocket.bind(('',serverPort))
    serverSocket.listen(1)
except GENERIC_SOCKET_ERROR as e:
    print("Could not create socket:",e)
    quit(1)

print('The server is ready to receive')

def on_recieve_frame(*args): 
    socket = args[0]
    frame  = args[1]
    if len(args) > 2:
        other = args[2:]
        
    #PARSE ARGS => OPCODE, ARGS
    parsed = SERVER_ARGPARSER.parse_message(frame)
    
    if not isinstance(parsed, tuple): #Has returned an error code instead of arguments
        raw = str_to_bytes("ERRORENC") + BYTE_REPR(SEP) + BYTE_REPR(parsed) + BYTE_REPR(END)
    else:
        opcode = parsed[0]
        arguments = parsed[1]
        
        #EXECUTE_ARGS => SUCCESS, RESPONSE_ARGUMENTS
        response = EXECUTE_ARGS_SERVER(opcode, arguments)
        if not response[0]:     #Execute returned 'False'
            opcode = "ERRORENC" #Instead of echoing the opcode, return the 'Error' opcode
            response[1][0] = ASCII_REPR(response[1][0]) #Convert the error code
        raw = str_to_bytes(argjoin(opcode, response[1]))
        
    try:  
        socket.sendall(raw)
    except GENERIC_SOCKET_ERROR as e:
        print(e)

server_shutdown_lk  = Semaphore(1)
shutdown_after_done = 0

def on_exit(*args):
    global shutdown_after_done
    
    #did we interrupt something?
    if not server_shutdown_lk.acquire(blocking=False):
        shutdown_after_done = 1
        return
        
    print("\nStopping server...")
    kill_ct = 0
    for extractor in extractors:
        extractor.close()
        kill_ct += 1
    server_shutdown_lk.release()
    
    print("Killed {:d} connection(s).".format(kill_ct))
    quit()
   
signal.signal(signal.SIGINT, on_exit)

cur_anim = 0 #for a pretty animation. Doubles as a polling timer
anims = ('|','/','—','\\')
extractors = []

while True:
    server_shutdown_lk.acquire()
    try:
        connectionSocket, addr = serverSocket.accept()
        print("\rConnection on:", addr)
        extractors.append(SBBP_Frame_Extractor(connectionSocket, addr, RECV_SSIZE, on_recieve_frame))
    except socket.timeout: #don't block permanently, allow other things to happen on main server thread
        cur_anim = (cur_anim + 1) % (len(anims))
        print("\rWaiting for connection... " + anims[cur_anim % len(anims)], end='')
        
        if not cur_anim: #this could probably be a one-liner
            for extractor in extractors: 
                if not extractor.alive():
                    extractors.remove(extractor)         
        
    except GENERIC_SOCKET_ERROR as e:
        print("Failed to accept connection:",e)
    finally: #In the event that the except failed
        server_shutdown_lk.release()
        
    if shutdown_after_done:
        on_exit()   