from .rw_comm_lang import * 


CLIENT_LIST_TITLE = "\t\t USER LIST"
CLIENT_LIST_INPUT = "press (enter) for the next group of users OR\nenter in the name of a user: "

CLIENT_PERMISSIONS_INPUT0 = "(ro) read folder (ri) read file (wo) write folder (wi) write file (b) go back: "
CLIENT_PERMISSIONS_INPUT1 = "(a) add | (d) delete | (b) go back | press (enter) for the next group: "  

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
        self.user_list.append("default")

        # for server side 
        self.uperms = dict()  

        self.preprocess()
        return 

    def load_user_permissions(self): 
        
        default_fp = os.path.join(DEFAULT_SB_USER_DIR,"default_user_permissions.txt")

        for u in self.user_list:
            if u != "default":  
                fp_user = user_idn_to_default_permissions_file_path(u)
            else: 
                fp_user = default_fp 
                
            uperm = UserPermissions(fp_user)
            self.uperms[u] = uperm 

    def preprocess(self):

        if self.is_server_side: 
            self.load_user_permissions() 
        return 

    def run(self):
        mode = "user"
        user_idn = None 
        perm_op = None 

        while True: 
            if mode == "user": 
                user_idn,i = self.display_list(mode)
                mode = "perm view" 
            elif mode == "perm view": 
                perm_op = self.user_selection(user_idn)
                if perm_op == "b": 
                    mode = "user"
                    continue  
                mode = "perm op"
            else: 
                op,i = self.display_list(mode,user_idn,perm_op)

                if op == "b": 
                    mode = "user" 
                    continue 

                uperm = self.uperms[user_idn] 
                if op == "a": 
                    to_add = True 
                    S = CLIENT_PERMISSIONS_ADD_INPUT
                elif op == "d": 
                    to_add = False
                    S = CLIENT_PERMISSIONS_DELETE_INPUT
                else: 
                    continue 

                P = input(S)
                uperm.update(perm_op[0],P,to_add=to_add)
                mode = "perm view" 

        return

    def display_list(self,list_type,*args): 
        assert list_type in {"user","perm op"}
        
        F = self.display_user_list_ if list_type == \
            "user" else self.display_usr_perm_list
        i = 0 
        name = None 

        while True: 
            stat = F(i,*args)  
            stat = stat.strip() 
            if stat == "": 
                i = i + 50 
                if i >= len(self.user_list): 
                    i = 0 
            else: 
                name = stat 
                break 
        return name,i 
    
    def user_selection(self,user_idn): 
        if user_idn not in self.user_list: 
            print("* user does not exist!") 
            return None 

        while True: 
            s = input(CLIENT_PERMISSIONS_INPUT0) 
            s = s.strip().lower()

            if s in {"ro","ri","wo","wi","b"}: 
                break 
        return s 

    def user_op(self,user_idn,action): 
        assert action in {"ro","ri","wo","wi"}
        return self.display_list("perm view",user_idn,action)

    def display_usr_perm_list(self,ref_index,user_idn,action): 
        if user_idn not in self.uperms: 
            return "b" 
        uperm = self.uperms[user_idn]

        if action == "ro": 
            Q = uperm.read_folder_ex

        elif action == "ri": 
            Q = uperm.read_file_ex

        elif action == "wo": 
            Q = uperm.write_folder_ex 

        elif action == "wi": 
            Q = uperm.write_file_ex

        else: 
            return "" 

        return display_loop(Q,ref_index,title="\t\t* exclusion list",\
            input_str=CLIENT_PERMISSIONS_INPUT1)

    def display_user_list_(self,ref_index): 
        return display_loop(self.user_list,ref_index,title=CLIENT_LIST_TITLE,\
            input_str=CLIENT_LIST_INPUT) 

    def delete_client(self): 
        return -1 

    def delete_server(self): 
        return -1