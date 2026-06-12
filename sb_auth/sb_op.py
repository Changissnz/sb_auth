from .usr_table import * 
from seqbuild.face import comm_lang 

# DEFAULT VARIABLES  
PROHIBITED_COMMLANG_COMMANDS = {"load","show","chaintest","qualtest","open"} 
DEFAULT_SB_AUTH_KEYSIZE_RANGE = [24,58]  
DEFAULT_SB_AUTH_INDEX_RANGE = [327,450]
DEFAULT_SB_SKIPSIZE_RANGE = [0,3]  

"""
checks if file abides by constrained Comm Lang rules. 
"""
def verify_CommLang_file(f):
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

    return True 

# TODO: 
def process_CommLang_generator(f,generator_name):  
    assert os.path.isfile(f) 

    clp = CommLangParser(f) 

    clp.process_file() 
    assert generator_name in clp.vartable
    assert False 