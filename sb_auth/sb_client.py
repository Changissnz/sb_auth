from .rw_comm_lang import * 

async def clientete():
    s = str(input("enter in IP address: ")) 
    s1 = str(input("enter in port number: ")) 
    server = "ws://" + s + ":" + s1
    async with websockets.connect(server) as wsock:
        print("Connected to server!")
        await asyncio.gather(receive_command_file(wsock), send_command_file(wsock)) 

asyncio.run(clientete())