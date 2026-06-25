import os

# DEFAULT VARIABLES 
base_dir = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SB_USER_DIR = os.path.join(base_dir, "user_data")
os.makedirs(DEFAULT_SB_USER_DIR, exist_ok=True)

DEFAULT_SB_AUTH_USER_SSIDE_DIRECTORY_PATH = os.path.join(DEFAULT_SB_USER_DIR,"server_dir") 
DEFAULT_SB_AUTH_USER_CSIDE_DIRECTORY_PATH = os.path.join(DEFAULT_SB_USER_DIR,"client_dir") 
SB_AUTH_DIRECTORY_FILE_ROW_MAP = {"cl file":0,"g-name":1,"# iterations":2,"# times": 3} 

def user_idn_to_default_permissions_file_path(user_idn): 
    s = "permissions__{}.txt".format(user_idn) 
    return os.path.join(DEFAULT_SB_USER_DIR,s) 

"""
contains information from a structured file for one client 
"""
class UserPermissions: 

    S0 = "\t\t R E A D    F I L E    E X C L U S I O N"
    S1 = "\t\t R E A D    F O L D E R    E X C L U S I O N"
    S2 = "\t\t W R I T E   F I L E    E X C L U S I O N"
    S3 = "\t\t W R I T E   F O L D E R    E X C L U S I O N"

    def __init__(self,fp): 
        stat = os.path.isfile(fp)

        # file does not exist 
        if not stat: 
            UserPermissions.new_user_file_(fp) 

        self.fp = fp
        self.file_obj = open(self.fp,"r")

        self.process_phase = -1  
        self.read_file_ex = [] 
        self.read_folder_ex = [] 
        self.write_file_ex = [] 
        self.write_folder_ex = [] 

        self.S = [UserPermissions.S0,UserPermissions.S1,\
            UserPermissions.S2,UserPermissions.S3]
        self.Q = [self.read_file_ex,self.read_folder_ex,\
            self.write_file_ex,self.write_folder_ex]  

        self.process() 
        return 

    def process(self):
        end = self.file_obj.seek(0,os.SEEK_END) 
        self.file_obj.seek(0)
        stat = True 
        
        ref_line = self.S[self.process_phase + 1] 
        while self.file_obj.tell() != end: 
            line = self.file_obj.readline().rstrip() 
            if line == ref_line: 
                self.process_phase += 1 
                ref_line = self.S[(self.process_phase + 1) % 4]
            else: 
                if line.strip() != "": 
                    Q = self.Q[self.process_phase] 
                    Q.append(line) 
        self.file_obj.close() 
        return 

    def update(self,rw:str,P,to_add:bool=True):
        assert rw in {"r","w"}, "got {}".format(rw)

        is_folder = os.path.isdir(P) 
        q = None 
 
        # case: folder  
        if is_folder: 
            q = self.read_folder_ex if rw == "r" else \
                self.write_folder_ex 
        else: 
            if not os.path.isfile(P): 
                print("invalid path @ {}".format(P))
                return False 
            q = self.read_file_ex if rw == "r" else \
                self.write_file_ex 

        if to_add: 
            q.append(P) 
        else: 
            if P not in q: 
                print("exclusion does not exist for: {}".format(P)) 
            i = q.index(P)
            q.pop(i) 

        self.rewrite_to_file() 
        return 

    def rewrite_to_file(self): 
        with open(self.fp,"w") as self.file_obj: 
            for i in range(4): 
                s = self.S[i] 
                q = self.Q[i] 

                self.file_obj.write(s + "\n\n") 
                for q_ in q: 
                    self.file_obj.write(q_ + "\n") 
            return

    def is_allowed(self,fpath,rw): 
        assert rw in {"r","w"}

        dpath = os.path.dirname(fpath) 

        if rw == "r": 
            Q = self.Q[:2] 
        else: 
            Q = self.Q[2:] 

        if dpath in Q[1]: 
            return False 

        if fpath in Q[0]: 
            return False 

        return True 

    @staticmethod 
    def new_user_file(user_idn): 
        fpath = user_idn_to_default_permissions_file_path(user_idn)
        UserPermissions.new_user_file_(fpath) 

    @staticmethod 
    def new_user_file_(fpath): 
        default_uperm = os.path.join(DEFAULT_SB_USER_DIR,"default_user_permissions.txt") 
        contents = None 
        with open(default_uperm,"r") as f: 
            contents = f.readlines() 

        with open(fpath,"w") as f: 
            f.writelines(contents)
        return

    @staticmethod 
    def clear_default_user_permissions():
        fpath = os.path.join(DEFAULT_SB_USER_DIR,"default_user_permissions.txt") 

        S = [UserPermissions.S0,UserPermissions.S1,\
            UserPermissions.S2,UserPermissions.S3]

        with open(fpath,"w") as f: 
            for s in S: 
                f.write(s + "\n\n") 
        return

#-------------------------------------------------------------------------------------------

"""
loads up either the server or client directory 
"""
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
        default_uperm = os.path.join(DEFAULT_SB_USER_DIR,"default_user_permissions.txt") 

        # check for default user permissions 
        if not os.path.isfile(default_uperm): 
            UserPermissions.clear_default_user_permissions() 

        self.fetch_dirfile_path() 
        f = open(self.fpath,"r")
        f.seek(0,os.SEEK_END) 
        file_end = f.tell()
        f.seek(0)

        missing_keys = False 
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

            if not os.path.isfile(full_cl_filepath):
                print("user {} is missing key".format(user_idn))
                missing_keys = True 
                continue 
            num_iter = int(num_iter) 
            num_times = int(num_times) 
            
            self.t0[user_idn] = (cl_file,gen_name,num_iter,num_times) 
            self.l0[len(self.l0)] = user_idn 
        f.close() 

        if missing_keys: 
            self.rewrite_usr_file() 
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

    def delete_user(self,user_idn): 
        if user_idn in self.t0: 
            del self.t0[user_idn] 

        k_ = None 
        for k,v in self.l0.items(): 
            if v == user_idn: 
                k_ = k
                break 

        if type(k_) != type(None):
            del self.l0[k_]

            l0 = dict()  
            for k,v in self.l0.items(): 
                if k > k_:
                    l0[k - 1] = v 
                else:  
                    l0[k] = v 
            self.l0 = l0 

        self.rewrite_usr_file()

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