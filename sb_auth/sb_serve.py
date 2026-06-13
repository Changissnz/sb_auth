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
            print("VUN") 

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
                print("USER IDN: ",user_idn) 
                print("VA: ",valid,is_new_user) 
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
            async for message in wsock:                
                fipath,msg = message.split(":") 
                fp0 = os.path.join(DEFAULT_SB_USER_DIR,fipath)
                with open(fp0,"w") as f: 
                    sf.write(msg)

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
            print("issuing key to new user {}")
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
        
        R = "G"

        # TODO: allow for other commonds 
        if is_new_user: 
            x = "commond_two.txt" 
            x_ = os.path.join(DEFAULT_SB_USER_DIR,x) 
            stat = verify_CommLang_file(x_,R) 

            try: self.utable.add_user(user_idn,x,R) 
            except: 
                print("user already exists!") 
                return 0,R,False 


            if not stat: 
                print("invalid Comm Lang file.") 
            return 0,R,stat 
        
        fp = self.utable.user_to_X(user_idn,"cl file") 
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

    def new_user(self): 
        x = input("new user! Choose your name: ") 

        if not is_alphanumeric(x): 
            print("[!] username must contain only letters or numbers.")  
            return self.new_user() 

        # TODO: add 
        if x in self.utable.t0: 
            print("[!] username already taken") 
            return self.new_user() 

        return x,True   

#------------------------------------------------------------------------------------

sbs = SBAuthServer()
asyncio.run(sbs.service())