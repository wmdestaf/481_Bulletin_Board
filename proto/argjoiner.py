from proto9_constants import *
from proto9_util_extractor import *

def force_str_repr(x):
    if isinstance(x, str):
        return x
    elif isinstance(x, bool):
        return '1' if x else '0'
    elif isinstance(x, int):
        return str(x)
    elif isinstance(x, float):
        return str(int(x))
    raise ValueError
        
def argjoin(opcode, arg_list):
    string = ''
    
    def argjoin0(arg_list, sep):
        nonlocal string
        for idx, arg in enumerate(arg_list):
            if not isinstance(arg, list):
                string += force_str_repr(arg) + ('' if idx == len(arg_list) - 1 else ASCII_REPR(sep))
            else:
                argjoin0(arg, sep - 1)
                string += ('' if idx == len(arg_list) - 1 else ASCII_REPR(sep))
                
    argjoin0(arg_list,0xFE)
    return opcode + ASCII_REPR(0xFE) + string + ASCII_REPR(0xFF)

samples = [
[1],
[1,2,3,4,5],
[1,"2",3,"4",500],
[1,2,[3,4],[[5,6],[7,8],[True, False]],"hello"],
[1,2,[],4,5],
[],
[0x2],
[[1, 1, 1638982287.493978, 'subj1', 'msg1'], [2, 2, 1638982289.360206, 'subj2', 'msg2']]
]

for sample in samples:
    print(unzip_seperators(argjoin("TESTOPCD",sample)))