from SBBP_util_extractor import *
from SBBP_util_argparse  import *
from SBBP_data           import *
import socket
from socket import AF_INET, SOCK_STREAM
from socket import error as GENERIC_SOCKET_ERROR
from threading import Thread
import signal
import sys
from os.path import exists
serverPort = 13037

#load in the data
argc = len(sys.argv)
out_f = None
if argc > 2:
    print("usage: SBBP_serv [msgs_file]")
    quit(1)
elif argc == 2:
    if not exists(sys.argv[1]):
        print("File not found:",sys.argv[1])
        quit(1)
    out_f = sys.argv[1]
    deserialize(out_f)
else:
    loc = input("File: (Empty to ignore) ")
    if loc and not exists(loc):
        print("File not found:",loc)
        quit(1)
    elif loc:
        out_f = loc
        deserialize(out_f)

#attempt to create the socket
try:
    serverSocket = socket.socket(AF_INET,SOCK_STREAM)
    serverSocket.settimeout(0.5)
    serverSocket.bind(('',serverPort))
    serverSocket.listen(1)
except GENERIC_SOCKET_ERROR as e:
    print("Could not create socket:",e)
    quit(1)

#Keep the Kurose & Ross message for good luck
print('The server is ready to receive\n(Ctrl-C twice to exit)')
ip = socket.gethostbyname(socket.gethostname())
print('Running on',ip)

'''
    Decode, execute, encode, and send back information on receipt of a message
    @param args The list of arguments
'''
def on_recieve_frame(*args): 
    socket = args[0]
    frame  = args[1]
    if len(args) > 2:
        other = args[2:]
        
    #PARSE ARGS => OPCODE, ARGS
    parsed = SERVER_ARGPARSER.parse_message(frame)
    
    if not isinstance(parsed, tuple): #Parser has returned an error code instead of arguments
        raw = str_to_bytes("ERRORENC") + BYTE_REPR(SEP) + BYTE_REPR(parsed) + BYTE_REPR(END)
    else:
        opcode = parsed[0]
        arguments = parsed[1]
        
        #EXECUTE_ARGS => SUCCESS, RESPONSE_ARGUMENTS
        response = EXECUTE_ARGS_SERVER(opcode, arguments)
        if not response[0]:     #Execute returned 'False'
            opcode = "ERRORENC" #Instead of echoing the opcode, return the 'Error' opcode
            response[1][0] = ASCII_REPR(response[1][0])  #Convert the error code to ASCII
        raw = str_to_bytes(argjoin(opcode, response[1])) #Convert the message to bytes
        
    try:  
        socket.sendall(raw) #Send!
    except GENERIC_SOCKET_ERROR as e:
        print(e)

server_shutdown_lk  = Semaphore(1) #Ensure all extractors are shutdown before exit
shutdown_after_done = 0            #'Atomic'

'''
    On exit, attempt to shutdown ALL extractors
    @param args unused
'''
def on_exit(*args):
    global shutdown_after_done, out_f
    
    #did we interrupt something?
    if not server_shutdown_lk.acquire(blocking=False):
        shutdown_after_done = 1 #Tell main to handle us once it finishes another timeout
        return
        
    print("\nStopping server...")
    kill_ct = 0
    for extractor in extractors:
        extractor.close()
        kill_ct += 1
    server_shutdown_lk.release()
    
    #TODO: Serialize
    if out_f: #a file already provided
        while out_f and not serialize(out_f):
            out_f = input("Failed to write to" + out_f + ": try another file? (empty to ignore) ")
    else:
        out_f = input("Location to save: (empty to ignore) ")
        out_f = out_f if out_f.endswith(".sdb") else (out_f + ".sdb")
        while out_f and not serialize(out_f):
            out_f = input("Failed to write to" + out_f + ": try another file? (empty to ignore) ")
     
    if out_f:
        print(out_f + ": saved successfully.")
    
    print("Ended {:d} active connection(s).".format(kill_ct))
    quit(0)
   
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
        cur_anim = (cur_anim + 1) % ( (len(anims)) * 5 ) #Poll every '5' animation cycles
        print("\rWaiting for connection... " + anims[cur_anim % len(anims)], end='')
        
        for extractor in extractors: 
            if not extractor.alive():
                extractors.remove(extractor)         
    except GENERIC_SOCKET_ERROR as e:
        print("Failed to accept connection:",e)
    finally: #In the event that the except failed
        server_shutdown_lk.release()
        
    if shutdown_after_done:
        on_exit()   