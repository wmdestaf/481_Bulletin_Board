from socket import AF_INET, SOCK_STREAM, SHUT_RDWR, timeout
from socket import error as GENERIC_SOCKET_ERROR
from threading import Thread, Semaphore
from proto9_constants import *
import re

'''
    Converts a string of characters to their pythonic representation as bytes
    @param string The string of characters
    @return The string's byte representation
'''
def str_to_bytes(string):
    return b''.join([ord(c).to_bytes(1,'little') for c in string])

'''
    Converts a series of bytes to their pythonic representation as a string
    @param bytes The bytes
    @return The associated string
'''
def bytes_to_str(raw):
    return "".join([chr(x) for x in raw])
    
'''
    Converts any 'escaped' seperators of the form '[YZ]' to their character literal
    specified by the hex ordinal 0xYZ. Hardcoded for this protocol to only accept
    0xFC to 0xFF, inclusive.
    @param unformatted The unescaped string
    @return The escaped string
'''
def zip_seperators(unformatted):
    return re.sub(r'\[(F[C-F])\]', lambda hx: chr(int(hx.group(1),16)), unformatted)

'''
    Converts any unescaped seperators to their escaped counterpart: 
    e.g. 'ab[0xYZ literal]cd' = 'ab[YZ]cd'. Hardcoded for this protocol to only
    accept character literals FC to FF, inclusive.
    @param formatted The escaped string
    @return The unescaped string
'''
def unzip_seperators(formatted):
    for i in range(FIELDSEP, END + 1): #Hardcoded for protocol, but could be easily changed.
        formatted = formatted.replace(chr(i), '[' + hex(i)[2:] + ']')
    return formatted

'''
    The internal frame extractor, to be run on a seperate thread.
    @param ref The reference to the parent extractor.
'''
def SBBP_Frame_Extractor0(ref):
    buf = bytes(0)
    while True:
    
        try: 
            frame = ref.sock.recv(ref.bf_size)
        except timeout: #periodically timeout to check if we were killed from the outside
            if not ref.alive():
                ref.sock.shutdown(SHUT_RDWR)
                ref.sock.close()
                return
            else:
                continue
        except ConnectionResetError:
            print("The connection was reset. {}".format(ref.addr))
            ref.close()
            return
        except ConnectionAbortedError:
            print("You have forcibly closed the connection.")
            ref.close()
            return
        except GENERIC_SOCKET_ERROR:
            ref.mark_dead()
            ref.on_death()
            return

        if not len(frame): #got a FIN/ACK in the correct way
            ref.mark_dead()
            ref.on_death()
            print("The connection has been properly closed! {}".format(ref.addr))
            return

        if END in frame: #hit the terminator
            points = [0] + [idx + 1 for idx, val in enumerate(frame) if val == END] + [len(frame)]
            splits = [frame[points[idx]:points[idx+1]] for idx in range(len(points) - 1)]
            
            #finish the current message
            buf += splits[0]
            msg = bytes_to_str(buf)
            
            #handle the message
            ref.fun(ref.sock, msg)
            
            #and if there are any other messages...
            for other_msg in splits[1:]:
                if other_msg and END in other_msg:
                    other_msg = bytes_to_str(other_msg)
                    
                    #handle the message
                    ref.fun(ref.sock, other_msg)
                    
                else: #last message in list, potentially not terminated
                    buf = other_msg
        else:
            buf += frame

class SBBP_Frame_Extractor:
    '''
        Creates a new Extractor
        @param sock The socket to recieve from
        @param addr The address represented at the other end of the socket
        @param bf_size The buffer-size for each recv call
        @param fun The function to execute each time a frame is recieved
        @param die_fun The function to execute on death
    '''
    def __init__(self, sock, addr, bf_size, fun, die_fun=None):
        self.sock    = sock
        self.addr    = addr
        self.fun     = fun
        self.bf_size = bf_size
        self.die_fun = die_fun
        self.die_lk  = Semaphore(1)
        self.dead    = False
        t = Thread(target=SBBP_Frame_Extractor0, args=(self,))
        t.daemon = True
        t.start() #recv thread
        self.t = t
       
    #Is the extractor 'alive'?       
    def alive(self):
        return not self.dead
        
    #Mark the extractor as dead
    def mark_dead(self):
        self.dead = True
        
    #Executes a 'death' function, if given
    def on_death(self):
        if self.die_fun:
            self.die_fun()
        
    #Kill the extractor and attempt to FIN/ACK the socket
    def close(self):
        if not self.die_lk.acquire(blocking=False):
            return
        elif not self.alive():
            self.die_lk.release()
            return
            
        self.mark_dead()
        self.on_death()
        self.die_lk.release()