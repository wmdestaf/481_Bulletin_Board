import re
import signal 

SEP = 0xFE.to_bytes(1, 'big')
END = 0xFF.to_bytes(1, 'big')
OK  = 'OK'.encode(encoding='ASCII')
NO  = 'NO'.encode(encoding='ASCII')

def parse(msg):
    if len(msg) < 10: #No 9 digit code + FF
        return NO + END
    

signal.signal(signal.SIGINT, lambda *a: quit())
while True:
    msg = input("MSG: ")
    msg = re.sub(r'\[(F[C-F])\]', lambda hx: chr(int(hx.group(1),16)), msg)
    ret = ''.join([chr(c) for c in parse(msg)])
    for i in range(0xFC, 0x100):
        ret = ret.replace(chr(i), '[' + hex(i)[2:] + ']')
    print(ret)