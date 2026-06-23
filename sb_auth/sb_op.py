from .usr_table import * 
from seqbuild.face.easy_gen_struct import *  
from morebs2.matrix_methods import is_number 

# DEFAULT VARIABLES  
PROHIBITED_COMMLANG_COMMANDS = {"load","show","chaintest","qualtest","open"} 
PROHIBITED_SB_AUTH_NAMES = {"server_dir","client_dir","default",""} 
DEFAULT_SB_AUTH_KEYSIZE_RANGE = [24,58]  
DEFAULT_SB_AUTH_INDEX_RANGE = [0,5] # [627,1450]
DEFAULT_SB_SKIPSIZE_RANGE = [0,3]  

"""
checks if file abides by constrained Comm Lang rules. 
"""
def verify_CommLang_file(f,gen_name):
    if not os.path.isfile(f): return False 

    clp = CommLangParser(f)

    while not clp.finstat: 
        clp.load_next_command()

        if len(clp.cmdlines) > 0: 
            q = clp.cmdlines[0] 
            c = q.split(" ")
            if c[0] in PROHIBITED_COMMLANG_COMMANDS: 
                return False 
            if c[0] == "set": 
                if "open" in c: return False 

        clp.process_command() 
        clp.check_finstat() 

    if type(gen_name) == type(None): 
        gen_name = clp.single_output_generator_list()[-1]

    clp.close() 

    try: 
        stat = process_CommLang_generator(f,gen_name,0)
        return stat  
    except: 
        return False

# TODO:
'''
if num_iter = 0: checks generator first 50 outputs are real numbers. 
otherwise: outputs `num_iter` values 
'''  
def process_CommLang_generator(f,generator_name,num_iter=0,output_last=0):
    if type(f) == str: 
        assert os.path.isfile(f) 
        clp = CommLangParser(f) 
        clp.process_file() 
    else: 
        assert type(f) == CommLangParser
        clp = f 

    assert num_iter >= 0 

    excluded_types = {complex,np.complex64,np.complex128}
    def vfunc(): 
        for _ in range(50): 
            try: 
                x = G() 
                stat = is_number(x,excluded_types)
                if not stat: return False 
            except: 
                return False 
        return True 

    def nfunc():
        X = [] 
        for _ in range(num_iter): 
            r = G()
            X.append(float(round(r,5))) 
        return X[-output_last:]

    F = vfunc if num_iter == 0 else nfunc 

    assert generator_name in clp.vartable, "got {}, available {}".format(generator_name,\
        set(clp.vartable.keys()))

    G = clp.vartable[generator_name]
    G = MAIN_method_for_object(G) 
    assert type(G) in {FunctionType,MethodType} 
    return F()