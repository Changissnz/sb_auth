"""
read/write operations for Seqbuild's Comm Lang language. 
"""
import re
import websockets
import asyncio
from .sb_op import * 

DEFAULT_PORT = 8765 

def is_alphanumeric(s):
    pattern = "^[a-zA-Z0-9]*$"
    return bool(re.match(pattern, s))

async def send_command_file(wsock): 
    while True:
        fipath = await asyncio.get_event_loop().run_in_executor(None, input, "Send command file: ")
        outsource,insource = fipath.split(":") 
        insource = os.path.join(USER_DIR,insource) 
        if os.path.isfile(fipath):
            with open(fipath, "r") as f:
                content = f.read()
            await wsock.send(f"{fipath}:{content}")
            print(f"Sent file: {fipath}") 
        else:
            await wsock.send(fipath)

async def receive_command_file(wsock):
    async for message in wsock:
        fipath,msg = message.split(":") 
        fp0 = os.path.join(USER_DIR,fipath)
        with open(fp0,"w") as f: 
            f.write(msg)