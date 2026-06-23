from .rw_comm_lang import * 


CLIENT_LIST_TITLE = "\t\t USER LIST"
CLIENT_LIST_INPUT = "press (enter) for the next group of users OR\nenter in the name of a user: "

CLIENT_PERMISSIONS_INPUT0 = "(ro) read folder (ri) read file (wo) write folder (wi) write file: "
CLIENT_PERMISSIONS_INPUT1 = "(a) add | (d) delete | (b) go back | press (enter) for the next group"  

CLIENT_PERMISSIONS_TITLE = "\t\t USER EXCLUSION: "
CLIENT_PERMISSIONS_ADD_INPUT = "add exclusion: " 
CLIENT_PERMISSIONS_DELETE_INPUT = "delete exclusion: " 

def display_loop(L,ref_index,title,input_str):  

    print(title) 
    end = min(len(L),ref_index + 50)
    for i in range(ref_index,end): 
        print(L[i] + "\n") 
    print("\n\n") 
    x = input(input_str) 
    return x  

"""
server side 
"""
class SBLocalService: 

    def __init__(self,is_server_side:bool): 
        self.is_server_side = is_server_side
        self.utable = UserTable(self.is_server_side)
        self.user_list = sorted(self.utable.t0.keys())

        # for server side 
        self.uperms = dict()  
        return 

    def load_user_permissions(self): 
        
        for u in self.user_list: 
            fp_user = user_idn_to_default_permissions_file_path(u)
            uperm = UserPermissions(fp_user)
            self.uperms[u] = uperm 

    def preprocess(self):

        if self.is_server_side: 
            self.load_user_permissions() 
        return 

    def run(self): 
        return -1 

    def display_list(self,list_type,*args): 
        assert list_type in {"user","user op"}
        
        F = self.display_user_list_ if list_type == \
            "user" else self.display
        i = 0 
        name = None 

        while True: 
            stat = self.display_user_list_(i,**args)  
            if stat.strip() == "": 
                i = i + 50 
                if i >= len(self.user_list): 
                    i = 0 
            else: 
                name = stat 
                break 
        return name,i 
    
    def user_selection(self,user_idn): 
        if name not in self.user_list: 
            print("* user does not exist!") 
            return None 

        while True: 
            s = input(CLIENT_PERMISSIONS_INPUT0) 
            s = s.strip().lower()

            if s in {"ro","ri","wo","wi"}: 
                break 
        return s 

    def user_op(self,user_idn,action): 
        assert action in {"ro","ri","wo","wi"}
        uperm = self.uperms[user_idn]

        Q = None 
        return self.display_list("user op",action)

    def display_usr_perm_list(self,ref_index,action): 

        if action == "ro": 
            Q = uperm.read_folder_ex

        elif action == "ri": 
            Q = uperm.read_file_ex

        elif action == "wo": 
            Q = uperm.write_folder_ex 

        else: 
            Q = uperm.write_file_ex

        return display_loop(Q,ref_index,title="",\
            input_str=CLIENT_PERMISSIONS_INPUT1)

    # REFACTOR THIS. 
    def display_user_list_(self,ref_index): 
        return display_loop(self.user_list,ref_index,title=CLIENT_LIST_TITLE,\
            input_str=CLIENT_LIST_INPUT) 

    def delete_client(self): 
        return -1 

    def delete_server(self): 
        return -1 

    def add_rw_permission(self): 
        return -1 

    def remove_rw_permission(self): 
        return -1 