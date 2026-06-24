from .sb_local import * 
from .sb_client import * 
from .sb_serve import * 

while True: 
    s = input("(s) server (c) client (l) local[offline]: ") 
    s = s.strip().lower()  

    if s in {"s","c","l"}:
        break 

if s == "s": 
    sbs = SBAuthServer()
    asyncio.run(sbs.service())
    
elif s == "c": 
    sbc = SBAuthClient()
    asyncio.run(sbc.contact()) 
else:  
    while True: 
        s = input("(s) server OR (c) client side: ") 
        s = s.strip().lower()  

        if s in {"s","c"}:
            break

    stat = s == "s"      
    sls = SBLocalService(stat)  
    sls.run() 