import asyncio
import traceback
import os, sys
import streamlit.web.cli as stcli

try:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    sys.argv = [    
        'streamlit'
        , 'run'
        , os.path.join(sys._MEIPASS, "src", "model.py")
        , "--global.developmentMode=false"
    ]
    stcli.main()
except Exception:
    print(traceback.format_exc())
