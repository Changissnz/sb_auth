import asyncio
import websockets
from .rw_comm_lang import * 

class SBAuthServer: 

    def __init__(self): 
        self.utable = UserTable(True)  
        self.current_user = None 

        self.action_queue = [] 

        self.socket2user = dict() 

        # user -> Comm Lang parser 
        self.user2clp = dict() 

        # user -> UserPermissions 
        self.user2permissions = dict() 

    async def service(self): 
        async with websockets.serve(self.one_step, "0.0.0.0", DEFAULT_PORT):
            print("Server listening on port 8765...")
            await asyncio.Future()  # run forever

    async def one_step(self,wsock): 
        while True: 
            quit_stat = await self.one_step_(wsock)  
            if quit_stat == -1: 
                del self.socket2user[wsock] 
                break 

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
            stat = await self.user_security_check(wsock,user_idn,is_new_user,is_login=True) 
            if not stat: 
                await wsock.send("u wrong, bruh. u ain't {}".format(user_idn)) 
                return -1 

            await self.verify_user(wsock,user_idn,is_new_user) 
            self.socket2user[wsock] = user_idn 

            # add permissions 
            if is_new_user: 
                UserPermissions.new_user_file(user_idn)

            fpath = user_idn_to_default_permissions_file_path(user_idn)
            self.user2permissions = UserPermissions(fpath) 

        else: 
            quit_stat = await self.ask(wsock) 
            if quit_stat: 
                return -1 

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

    async def user_security_check(self,wsock,user_idn,is_new_user,is_login:bool): 
        num_elements,gen_name,stat = self.user_login_subproc(user_idn,is_new_user) 
        if num_elements == 0: 
            return True 

        prev_elements = 0 
        
        # case: is login: have to iterate through the previous iterations first 
        if is_login: 
            prev_elements = self.utable.user_to_X(user_idn,"# iterations")

        total_elements = prev_elements + num_elements

        clp = self.user2clp[user_idn] 
        key = process_CommLang_generator(clp,gen_name,\
            num_iter=total_elements,output_last=num_elements) 
        key = vector_to_string(key,cr) 

        self.utable.update_user(user_idn,num_elements) 
        u_gud_bruh = await self.cmp_key(wsock,key,num_elements) 
        return u_gud_bruh 

    async def cmp_key(self,wsock,actual_key,num_elements):  

        await wsock.send("enter in your key of {} numbers: ".format(num_elements))
        key = await wsock.recv()

        print("\t\tactual key")
        print(actual_key)
        print("\t\tkey given")
        print(key)

        stat = actual_key == key 
        return stat 

    """
    accept or deny user login 

    return: 
    - next key size, generator name, ?login stat?
    """
    def user_login_subproc(self,user_idn,is_new_user): 
        

        # TODO: allow for other commonds 
        if is_new_user: 
            #x = "commond_two.txt"
            x = "commond_{}.txt".format(user_idn)  
            x_ = os.path.join(DEFAULT_SB_USER_DIR,x) 

            K = TimeBasedCommLangFileGenerator(x_,"rx",0.5,vector_files=[],\
                comm_lang_files=[],consistent_prng_output=True)  
            K.generate() 
            R = K.clp.single_output_generator_list()[-1] 
            stat = verify_CommLang_file(x_,R) 

            try: 
                self.utable.add_user(user_idn,x,R) 
            except: 
                print("user already exists!") 
                return 0,R,False 

            if not stat: 
                print("invalid Comm Lang file.") 

            self.load_CommLangParser_for_user(user_idn) 
            return 0,R,stat 
        
        clp = self.load_CommLangParser_for_user(user_idn) 
        R = self.utable.user_to_X(user_idn,"g-name")
        q = process_CommLang_generator(clp,R,1)[0]  
        q_ = modulo_in_range(int(q),DEFAULT_SB_AUTH_KEYSIZE_RANGE)
        print("user {} key: next {} values".format(user_idn,q_)) 
        return q_,R,True

    def load_CommLangParser_for_user(self,user_idn): 
        if user_idn in self.user2clp: 
            return self.user2clp[user_idn]

        fp = self.utable.user_to_X(user_idn,"cl file") 
        full_fp = os.path.join(DEFAULT_SB_USER_DIR,fp) 
        clp = CommLangParser(full_fp) 
        clp.process_file() 
        self.user2clp[user_idn] = clp 
        return self.user2clp[user_idn]

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
        try: 
            op = await self.ask_for_op(wsock) 
            stat = await self.conduct_op(wsock,op) 

            # case: security check failed 
            if stat == -1: 
                ip_addr,port = wsock.remote_address
                print("security check to client {}/{} failed.".format(\
                    ip_addr,port))
                return True 

            return False 
        except: 
            ip_addr,port = wsock.remote_address
            print("closed connection to {}/{}".format(\
                ip_addr,port)) 
            return True 
            
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
                
                if q in {"r","w"}:
                    S = "\tenter in filepath:"
                else: 
                    S = "."
                await wsock.send(S) 
                op = q
                break 
        return op 

    def check_for_usr_permission(self,user_idn,fpath,rw:str): 
        assert rw in {"r","w"} 
        usp = self.user2permissions[user_idn] 
        return usp.is_allowed(fpath,rw) 

    async def conduct_op(self,wsock,op): 
        assert op in {"r","w","q"} 
        if op == "r": 

            # user security check 
            user_idn = self.socket2user[wsock] 
            clp = self.user2clp[user_idn] 

            fpath = await wsock.recv() 
            stat = await self.user_security_check(\
                wsock,user_idn,is_new_user=False,is_login=False)

            #   case: wrong key 
            if not stat: 
                await wsock.send("u wrong, bruh. u ain't {}".format(user_idn)) 
                return -1  

            #   case: not permitted 
            stat = self.check_for_usr_permission(user_idn,fpath,"r") 
            if not stat: 
                await wsock.send("u wrong, bruh. u prohibited from this.") 
                return  

            with open(fpath,'r') as f: 
                content = f.read() 
            msg = ["True",content] 
            await wsock.send(json.dumps(msg))  
            return 

        elif op == "w": 
            #while True: 
            await wsock.send("source file for writing?") 
            q = await wsock.recv() 
            C = json.loads(q) 
            fpath,content = C 

            #   case: not permitted 
            stat = self.check_for_usr_permission(user_idn,fpath,"w") 
            if not stat: 
                await wsock.send("u wrong, bruh. u prohibited from this.") 
                return  

            try: 
                with open(fpath,"w") as f: 
                    f.write(content) 
                print("YESST.")
                await wsock.send("Wrote content.")
            except: 
                await wsock.send("Error writing content.") 
                ##continue 
            print("BREAKING")
            #    break
            return 
        else: 
            await wsock.close(code=1000, reason="Invalid")
              

#------------------------------------------------------------------------------------

sbs = SBAuthServer()
asyncio.run(sbs.service())