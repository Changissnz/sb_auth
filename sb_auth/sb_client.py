from .rw_comm_lang import * 

class SBAuthClient: 

    def __init__(self): 
        self.addr = None 
        self.user_idn = None 
        self.utable = UserTable(False) 
        self.is_new_user = False 
        return

    async def contact(self): 
        s = str(input("enter in IP address: ")) 
        s1 = str(input("enter in port number: ")) 
        self.addr = s + ":" + s1 
        server = "ws://" + self.addr 
        await self.act(server)  

    async def act(self,server):  
        async with websockets.connect(server) as wsock:
            print("Connected to server!")
            await asyncio.gather(self.recv(wsock), self.send(wsock)) 

    async def recv(self,wsock): 
        async for message in wsock:
            print(message) 

            try: 
                message2 = json.loads(message)
                message = message2
            except: pass 

            # case: data input, CL key or data 
            if type(message) == list: 
                #q = message.split("\n") 
                # case: receive COMM LANG key 
                if message[0].strip() == "COMM LANG": 
                    gen_name = message[1] 
                    cl_string = message[2] 
                    self.write_key_to_file(cl_string,gen_name)
                    continue 

            # case: initial login 
            elif message.strip() == "username. leave blank if you are new:": 
                response = await self.login(wsock)
                continue 



    async def login(self,wsock): 
        s = input("[x] ") 
        await wsock.send(s) 
        self.user_idn = s 
        response = await wsock.recv()
        print(response) 
        response = response.strip() 
        q = response.split(" ") 

        # case: new user 
        if response == "new username:": 
            s2 = input("[x] ")
            await wsock.send(s2) 
            self.user_idn = s2 
            response = wsock.recv()
            self.is_new_user = True
        # case: username does not exist. 
        elif q[-2] == ["try","again!"]:
            print("Username does not exist. Please try again.")
            s2 = input("[x] ")
            response = await wsock.send(s2) 
        # case: provide the key 
        elif q[:4] == ["enter","in","your","key"]:  
            num_iter = int(q[5])
            print("QX: ",num_iter) 
            await self.send_passwd(wsock,num_iter)

        return response

    async def send(self,wsock):
        return

    def write_key_to_file(self,cl_string,gen_name):   
        user_str = filename_for_CL(self.addr,False) 
        fp = os.path.join(DEFAULT_SB_USER_DIR, user_str)  

        fobj = open(fp, "w") 
        fobj.write(cl_string) 
        fobj.close() 

        self.utable.add_user(self.addr,user_str,gen_name) 
        return 

    async def send_passwd(self,wsock,num_iter):  
        fp = filename_for_CL(self.addr,False)  
        full_fp = os.path.join(DEFAULT_SB_USER_DIR,fp) 
        gen_name = self.utable.user_to_X(self.addr,"g-name")  
        q = process_CommLang_generator(full_fp,gen_name,num_iter)
        self.utable.update_user(self.addr,num_iter)
        s = vector_to_string(q,cr)
        await wsock.send(s) 

sbc = SBAuthClient()
asyncio.run(sbc.contact()) 