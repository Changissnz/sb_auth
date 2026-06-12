import asyncio
import websockets
from .rw_comm_lang import * 


async def server_handler(wsock): 
    await asyncio.gather(receive_command_file(wsock), send_command_file(wsock)) 


async def servetete(): 
    async with websockets.serve(server_handler, "0.0.0.0", DEFAULT_PORT):
        print("Server listening on port 8765...")
        await asyncio.Future()  # run forever

asyncio.run(servetete())