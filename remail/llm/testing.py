import sys,os
# Add the Remail directory (parent folder) to sys.path
remail_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(remail_path)

import RAG_Backend
import controller

ec = controller.EmailController()
ec.create_email(1,"abc",["123","def"],"test","Hello World!",[None], None, None)
print(ec.get_emails())

#llm= RAG_Backend.LLM()
#llm._connectToDb()