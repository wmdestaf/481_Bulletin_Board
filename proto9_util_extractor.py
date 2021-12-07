from socket import AF_INET, SOCK_STREAM
from threading import Thread, Semaphore
from proto8_constants import *
import re

def str_to_bytes(string):
    return b''.join([ord(c).to_bytes(1,'little') for c in string])

def bytes_to_str(raw):
    return "".join([chr(x) for x in raw])
    
def zip_seperators(unformatted):
    return re.sub(r'\[(F[C-F])\]', lambda hx: chr(int(hx.group(1),16)), unformatted)

def unzip_seperators(formatted):
    for i in range(FIELDSEP, END + 1): #Hardcoded for protocol, but could be easily changed.
        formatted = formatted.replace(chr(i), '[' + hex(i)[2:] + ']')
    return formatted

def SBBP_Frame_Extractor0(ref):
    buf = bytes(0)
    while True:
        frame = ref.sock.recv(ref.bf_size) #TODO: GUARD

        if not len(frame): #socket died
            print("socket died... :(")
            return

        if END in frame: #hit the terminator
            points = [0] + [idx + 1 for idx, val in enumerate(frame) if val == END] + [len(frame)]
            splits = [frame[points[idx]:points[idx+1]] for idx in range(len(points) - 1)]
            
            #finish the current message
            buf += splits[0]
            msg = bytes_to_str(buf)
            
            #TODO: handle the message
            ref.fun(ref.sock, msg)
            
            #and if there are any other messages...
            for other_msg in splits[1:]:
                if other_msg and END in other_msg:
                    other_msg = bytes_to_str(other_msg)
                    
                    #TODO: handle the message
                    ref.fun(ref.sock, other_msg)
                    
                else: #last message in list, potentially not terminated
                    buf = other_msg
        else:
            buf += frame

class SBBP_Frame_Extractor:
    def __init__(self, sock, bf_size, fun):
        self.sock    = sock
        self.fun     = fun
        self.bf_size = bf_size
        Thread(target=SBBP_Frame_Extractor0, args=(self,)).start() #recv thread