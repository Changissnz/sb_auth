import asyncio
import websockets
from .rw_comm_lang import * 

class SBAuthServer: 

    def __init__(self): 
        self.utable = UserTable(True)  
        self.current_user = None 

        self.action_queue = [] 

        self.socket2user = dict() 

    async def service(self): 
        async with websockets.serve(self.one_step, "0.0.0.0", DEFAULT_PORT):
            print("Server listening on port 8765...")
            await asyncio.Future()  # run forever

    async def one_step(self,wsock): 
        while True: 
            await self.one_step_(wsock)  

    async def one_step_(self,wsock): 
        # case: new user 
        if wsock not in self.socket2user: 
            # get user name from client 
            user_idn,valid,is_new_user = await self.user_login(wsock,False) 
            print("login from {},valid {},new user {}".format(user_idn,valid,is_new_user)) 

            while not valid or user_idn == "": 
                user_idn,valid,is_new_user = await self.user_login(wsock,is_new_user) 
                # case: invalid input, user already exists. Quit this iteration.
                if not valid and not is_new_user: 
                    return 

            # verify user has correct passkey 
            stat = await self.user_login_key(wsock,user_idn,is_new_user)
            if not stat: 
                await wsock.send("u wrong, bruh. u ain't {}".format(user_idn)) 
                return 

            await self.verify_user(wsock,user_idn,is_new_user) 
            self.socket2user[wsock] = user_idn 
        else: 
            await self.ask(wsock) 

    #--------------------------------- for client logging in 

    """
    return: 
    - [0] user idn 
    - [1] valid user idn 
    - [2] is new user 
    """
    async def user_login(self,wsock,is_new_user:bool): 

        if not is_new_user: 
            await wsock.send("username. leave blank if you are new: ")
        else: 
            await wsock.send("new username: ")

        user_idn = await wsock.recv()
        user_idn = user_idn.strip() 

        # case: new user 
        if user_idn == "": 
            return "",True,True 
        
        # case: not new user, check for existence in user directory 
        else: 
            if user_idn in PROHIBITED_SB_AUTH_NAMES: 
                await wsock.send("[!] name {} is prohibited".format(user_idn)) 
                return "",False,False 

            if not is_alphanumeric(user_idn): 
                return "",False,False 

            if self.utable.user_exists(user_idn) and is_new_user:  
                print("USER {} DOES NOT EXIST.")
                await wsock.send("[!] username already exists. try again.") 
                return "", False,False 
            elif not self.utable.user_exists(user_idn) and not is_new_user: 
                q = await wsock.send("[!] username does not exist. try again.") 
                return "",False,False 

        return user_idn, True, is_new_user

    async def verify_user(self,wsock,user_idn,is_new_user): 

        if not is_new_user: 
            cl_file,gen_name,num_iter,num_times = self.utable.t0[user_idn]
            print("user {},generator {},iteration {},times used {}".format(user_idn,gen_name,num_iter,num_times)) 
        else: 
            print("issuing key to new user {}".format(user_idn)) 
            await self.send_new_key(wsock,user_idn) 

    async def user_login_key(self,wsock,user_idn,is_new_user): 
        num_elements,gen_name,stat = self.user_login_subproc(user_idn,is_new_user) 
        if num_elements == 0: 
            return True 

        fp = self.utable.user_to_X(user_idn,"cl file") 
        full_fp = os.path.join(DEFAULT_SB_USER_DIR,fp) 
        key = process_CommLang_generator(full_fp,gen_name,num_iter=num_elements)   
        key = vector_to_string(key,cr) 
        self.utable.update_user(user_idn,num_elements) 
        u_gud_bruh = await self.cmp_key(wsock,key,num_elements) 
        return u_gud_bruh 

    async def cmp_key(self,wsock,actual_key,num_elements):  

        await wsock.send("enter in your key of {} numbers: ".format(num_elements))
        key = await wsock.recv()

        stat = actual_key == key 
        return stat 

    """
    accept or deny user login 
    """
    def user_login_subproc(self,user_idn,is_new_user): 
        

        # TODO: allow for other commonds 
        if is_new_user: 
            #x = "commond_two.txt"
            x = "commond_{}.txt".format(user_idn)  
            x_ = os.path.join(DEFAULT_SB_USER_DIR,x) 

            K = TimeBasedCommLangFileGenerator(x_,"rx",0.5,vector_files=[],\
                comm_lang_files=[])
            K.generate() 
            R = K.clp.single_output_generator_list()[-1] 
            stat = verify_CommLang_file(x_,R) 

            try: self.utable.add_user(user_idn,x,R) 
            except: 
                print("user already exists!") 
                return 0,R,False 

            if not stat: 
                print("invalid Comm Lang file.") 
            return 0,R,stat 
        
        fp = self.utable.user_to_X(user_idn,"cl file") 
        R = self.utable.user_to_X(user_idn,"g-name")
        full_fp = os.path.join(DEFAULT_SB_USER_DIR,fp) 
        q = process_CommLang_generator(full_fp,R,1)[0]  
        q_ = modulo_in_range(int(q),DEFAULT_SB_AUTH_KEYSIZE_RANGE)
        print("user {} key: next {} values".format(user_idn,q_)) 
        return q_,R,True

    async def send_new_key(self,wsock,user_idn): 
        fp = self.utable.user_to_X(user_idn,"cl file")
        gen_name = self.utable.user_to_X(user_idn,"g-name")
        full_fp = os.path.join(DEFAULT_SB_USER_DIR,fp) 
        with open(full_fp, "r") as f:
            content = f.read()
        q = ["COMM LANG",gen_name,content]
        await wsock.send(json.dumps(q))  
        return

    #------------------------------- for post-login  
    # NOTE: rough draft 

    async def ask(self,wsock): 
        op = await self.ask_for_op(wsock) 
        await self.conduct_op(wsock,op) 

    async def ask_for_op(self,wsock): 
        op = None 
        while type(op) == type(None): 
            await wsock.send("read (r) or write (w) or quit (q)? ") 
            q = await wsock.recv() 
            q = q.lower() 
            if q not in {"r","w","q"}: 
                await wsock.send("[!] wrong input. try again.") 
            else: 
                print("gotem") 
                await wsock.send(".") 
                op = q 
        return op 

    async def conduct_op(self,wsock,op): 
        assert op in {"r","w","q"} 
        if op == "r": 
            while True: 
                q = await wsock.recv() 
                ##await wsock.send("filepath for reading?") 
                
                if not os.path.isfile(q): 
                    await wsock.send("file {} does not exist".format(q)) 
                    continue   

                #await wsock.send("file {} does exist".format(q)) 

                with open(q,'r') as f: 
                    content = f.read() 
                msg = ["True",content] 
                await wsock.send(json.dumps(msg))  
                break 
        elif op == "w": 
            while True: 
                await wsock.send("source file for writing?") 
                q = await wsock.recv() 
                C = json.loads(q) 
                fpath,content = C 

                try: 
                    with open(fpath,"w") as f: 
                        f.write(content) 
                except: 
                    await wsock.send("Error writing content.") 
                    continue 
                break
        else: 
            await wsock.close(code=4001, reason="Invalid")
            return  

#------------------------------------------------------------------------------------

sbs = SBAuthServer()
asyncio.run(sbs.service())