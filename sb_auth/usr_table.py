import os

# DEFAULT VARIABLES 
base_dir = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SB_USER_DIR = os.path.join(base_dir, "user_data")
os.makedirs(DEFAULT_SB_USER_DIR, exist_ok=True)

DEFAULT_SB_AUTH_USER_SSIDE_DIRECTORY_PATH = os.path.join(DEFAULT_SB_USER_DIR,"server_dir") 
DEFAULT_SB_AUTH_USER_CSIDE_DIRECTORY_PATH = os.path.join(DEFAULT_SB_USER_DIR,"client_dir") 
SB_AUTH_DIRECTORY_FILE_ROW_MAP = {"cl file":0,"g-name":1,"# iterations":2,"# times": 3} 

class UserTable: 

    def __init__(self,is_server_side:bool):  
        assert type(is_server_side) == bool 

        self.is_server_side = is_server_side

        # user idn -> (commond file,generator name,number of iterations,number of times used) 
        self.t0 = dict() 
        # file line -> user idn
        self.l0 = dict() 

        self.fobj = None 
        self.fpath = None 
        self.initial_read() 


    def fetch_dirfile_path(self): 
        self.fpath = DEFAULT_SB_AUTH_USER_SSIDE_DIRECTORY_PATH if self.is_server_side \
            else DEFAULT_SB_AUTH_USER_CSIDE_DIRECTORY_PATH

        if not os.path.isfile(self.fpath): 
            with open(self.fpath,"w") as f: pass 
        return self.fpath  

    """
    reads all users from user directory into maps  
    """
    def initial_read(self):

        self.fetch_dirfile_path() 
        f = open(self.fpath,"r")
        f.seek(0,os.SEEK_END) 
        file_end = f.tell()
        f.seek(0)

        while f.tell() != file_end: 
            p = f.tell() 
            q = f.readline() 
            q = q.strip() 
            if len(q) == 0: continue 

            q_ = q.split(",") 
            assert len(q_) == 5 
            
            user_idn,cl_file,gen_name,num_iter,num_times = q_[0],q_[1],q_[2],q_[3],q_[4]

            # make sure no duplicate users 
            assert user_idn not in self.t0 

            full_cl_filepath = os.path.join(DEFAULT_SB_USER_DIR,cl_file) 
            assert os.path.isfile(full_cl_filepath) 

            num_iter = int(num_iter) 
            num_times = int(num_times) 
            
            self.t0[user_idn] = (cl_file,gen_name,num_iter,num_times) 
            self.l0[len(self.l0)] = user_idn 

        f.close() 
        return

    def update_user(self,user_idn,iterations):  
        assert user_idn in self.t0 
        assert type(iterations) == int and iterations >= 0 

        if iterations == 0: return 

        fp = self.t0[user_idn][0]
        gen_name = self.t0[user_idn][1] 
        num_iter = self.t0[user_idn][2] + iterations
        num_times = self.t0[user_idn][3] + 1 
        self.t0[user_idn] = (fp,gen_name,num_iter,num_times) 
        self.rewrite_usr_file() 

    def add_user(self,user_idn,cl_file,gen_name): 
        assert not self.user_exists(user_idn)

        full_cl_filepath = os.path.join(DEFAULT_SB_USER_DIR,cl_file) 
        assert os.path.isfile(full_cl_filepath) 
        self.t0[user_idn] = (cl_file,gen_name,0,0)  
        self.l0[len(self.l0)] = user_idn 
        self.rewrite_usr_file() 
        return

    def delta_user(self,user_idn,cl_file,gen_name):
        assert self.user_exists(user_idn)

        full_cl_filepath = os.path.join(DEFAULT_SB_USER_DIR,cl_file) 
        assert os.path.isfile(full_cl_filepath) 

        self.t0[user_idn] = (cl_file,gen_name,0,0)   
        self.rewrite_usr_file() 
        return

    def user_to_str_info(self,user_idn): 
        assert user_idn in self.t0 
        x = [user_idn] + [str(x_) for x_ in self.t0[user_idn]] 
        return ",".join(x) + "\n"

    def user_to_X(self,user_idn,varname): 
        assert self.user_exists(user_idn) 
        assert varname in SB_AUTH_DIRECTORY_FILE_ROW_MAP

        index = SB_AUTH_DIRECTORY_FILE_ROW_MAP[varname] 
        return self.t0[user_idn][index]

    def user_exists(self,user_idn): 
        return user_idn in self.t0

    def rewrite_usr_file(self): 
        self.fobj = open(self.fpath,"w") 
        
        l = len(self.l0) 
        new_lines = [] 
        for i in range(l): 
            user_idn = self.l0[i] 
            s = self.user_to_str_info(user_idn) 
            new_lines.append(s) 
        self.fobj.writelines(new_lines) 
        self.fobj.flush() 
        self.fobj.close() 