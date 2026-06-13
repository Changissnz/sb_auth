"""
read/write operations for Seqbuild's Comm Lang language. 
"""
import re
import websockets
import asyncio
from .sb_op import * 
import json 
from morebs2.matrix_methods import vector_to_string,cr 

DEFAULT_PORT = 8765 

def is_alphanumeric(s):
    pattern = "^[a-zA-Z0-9]*$"
    return bool(re.match(pattern, s))

"""
outputs the program's conventional filename 
for `info` (client name or server address). 
"""
def filename_for_CL(info,is_server_side:bool): 
    assert type(is_server_side) == bool

    if is_server_side: 
        return "client__" + info + ".txt" 
    
    q = info.split(".")
    assert len(q) == 4 

    q1 = q[-1].split(":") 
    assert len(q1) == 2 

    q[-1] = q1[0] 
    q1 = q1[1] 

    s = "_".join(q) 
    return "server__" + s + "-" + q1 + ".txt" 