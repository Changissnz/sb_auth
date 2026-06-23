from .rw_comm_lang import * 

class SBAuthClient: 

    def __init__(self): 
        self.addr = None 
        self.user_idn = None 
        self.utable = UserTable(False) 
        self.is_new_user = False 

        self.finstat = False 
        self.active_clp = None 
        return

    async def contact(self): 
        s = await asyncio.get_running_loop().run_in_executor(None, \
            input, "enter in IP address: ")
        s1 = await asyncio.get_running_loop().run_in_executor(None, \
            input, "enter in port number: ")

        self.addr = s + ":" + s1 
        server = "ws://" + self.addr 
        await self.act(server)  

    async def act(self,server):  
        async with websockets.connect(server) as wsock:
            print("Connected to server!")
            while not self.finstat:  
                await self.recv(wsock)

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
                    stat = self.write_key_to_file(cl_string,gen_name,False)
                    if not stat: 
                        self.finstat = True 
                        return 
                    continue 

            # case: initial login 
            elif message.strip() == "username. leave blank if you are new:": 
                response = await self.login(wsock)
                continue 

            elif message.strip() == "read (r) or write (w) or quit (q)?":
                stat = await self.rw_ops(wsock) 
                if stat == -1: 
                    self.finstat = True 
                    return 
                continue 

    async def login(self,wsock): 
        s = await asyncio.get_running_loop().run_in_executor(None, input, "[x] ")

        await wsock.send(s) 
        self.user_idn = s 
        response = await wsock.recv()
        print(response) 
        response = response.strip() 
        q = response.split(" ") 

        # case: new user 
        if response == "new username:": 
            s2 = await asyncio.get_running_loop().run_in_executor(None, input, "[x] ")
            await wsock.send(s2) 
            self.user_idn = s2 
            response = wsock.recv()
            self.is_new_user = True
        # case: username does not exist. 
        elif q[-2] == ["try","again!"]:
            print("Username does not exist. Please try again.")
            s2 = await asyncio.get_running_loop().run_in_executor(None, input, "[x] ")
            response = await wsock.send(s2) 
        # case: provide the key 
        elif q[:4] == ["enter","in","your","key"]:  
            num_iter = int(q[5])
            await self.send_passwd(wsock,num_iter,is_login=True)

        return response

    def write_key_to_file(self,cl_string,gen_name,is_update:bool):   
        user_str = filename_for_CL(self.addr,False) 
        fp = os.path.join(DEFAULT_SB_USER_DIR, user_str)  

        fobj = open(fp, "w") 
        fobj.write(cl_string) 
        fobj.close() 

        try: 
            if not is_update: 
                self.utable.add_user(self.addr,user_str,gen_name) 
            else: 
                self.utable.delta_user(self.addr,user_str,gen_name) 
        except: 
            print("key already present for server/port OR could not be updated") 
            return False 
        return True 

    async def send_passwd(self,wsock,num_iter,is_login:bool):  

        user_str = filename_for_CL(self.addr,False) 

        if type(self.active_clp) == type(None): 
            fp = filename_for_CL(self.addr,False)  
            full_fp = os.path.join(DEFAULT_SB_USER_DIR,fp) 
            self.active_clp = CommLangParser(full_fp) 
            self.active_clp.process_file() 

        gen_name = self.utable.user_to_X(self.addr,"g-name")

        prev_elements = 0 
        if is_login: 
            prev_elements = self.utable.user_to_X(self.addr,"# iterations")

        total_elements = prev_elements + num_iter 
        q = process_CommLang_generator(self.active_clp,gen_name,\
            total_elements+1,num_iter)

        self.utable.update_user(self.addr,num_iter)
        s = vector_to_string(q,cr)
        await wsock.send(s) 

    #------------------------------- post login 

    async def rw_ops(self,wsock): 
        # read/write
        rw_stat = None
        fpath = None  
        while True: 
            q = await asyncio.get_running_loop().run_in_executor(None, input, "[x] ")
            await wsock.send(q)  
            s = await wsock.recv()
            print(s) 
            if s.strip() == "enter in filepath:": 
                rw_stat = q  
                break 

            if q == "q": 
                rw_stat = "q" 
                break 

        if rw_stat == "q": 
            return -1  

        F = self.r_ops if rw_stat == "r" else self.w_ops 
        stat = await F(wsock) 
        return stat 

    async def r_ops(self,wsock): 
        fpath = await asyncio.get_running_loop().run_in_executor(None, input, "[x] ")
        await wsock.send(fpath) 

        #while True: 
        sec_check_prompt = await wsock.recv() 
        sec_check_prompt = sec_check_prompt.strip().split(" ") 
        assert sec_check_prompt[:4] == ["enter","in","your","key"]
            #break  

        num_iter = int(sec_check_prompt[5])
        await self.send_passwd(wsock,num_iter,is_login=False) 

        sec_check_two = await wsock.recv()
        print(sec_check_two)
        try: 
            sec_check_two_ = json.loads(sec_check_two)
            sec_check_two = sec_check_two_
        except: 
            return False 

        # case: correct key     
        if type(sec_check_two) == list: 
            ##fpath2 = await asyncio.get_running_loop().run_in_executor(None, input, "[x] write out path? ") 
            stat = await self.record_read_file(sec_check_two[1])
            if not stat: 
                print("could not write out contents to file.") 
                return False
        else: 
            print("Security check failed.")
            return False 

        x = await wsock.recv()
        self.update_key_proc(x) 
        return True 

    async def record_read_file(self,contents):

        fpath2 = await asyncio.get_running_loop().run_in_executor(None, input, "[x] write out path? ") 
        
        try: 
            with open(fpath2,"w") as f: 
                f.write(contents) 
        except: 
            return False 
        return True 

    async def w_ops(self,wsock): 
        q = await wsock.recv() 
        print(q) 
        fpath = await asyncio.get_running_loop().run_in_executor(None, input, "[x]: ") 

        contents = None 
        try: 
            with open(fpath,"r") as f: 
                contents_ = f.read() 
                contents = contents_ 
        except: 
            pass 
        
        if type(contents) == type(None): 
            print("invalid path.") 
            return False 

        fpath2 = await asyncio.get_running_loop().run_in_executor(None, input, "[x] server side path: ") 
        C = json.dumps([fpath2,contents]) 
        await wsock.send(C)  
        s = await wsock.recv() 
        print(s)

        if s == "Wrote content.": 
            x = await wsock.recv() 
            self.update_key_proc() 

        return True 

    def update_key_proc(self,x): 

        # check for update to key here 
        try: 
            x_ = json.loads(x) 

            # 
            if type(x_) == list: 
                print("updating key")
                #q = ["COMM LANG",gen_name,content]
                gen_name = x_[1] 
                cl_string = x_[2] 
                self.write_key_to_file(cl_string,gen_name,is_update=True)
        except: 
            print(x) 


sbc = SBAuthClient()
asyncio.run(sbc.contact()) 