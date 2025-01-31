import remail.controller as controller

if not controller.controller.has_user():
    controller.controller.create_user("Milo", "thatchmilo35@gmail.com", protocol=controller.Protocol.IMAP, extra_information="imap.gmail.com", password = "oxomygwqzgdpislb")
    print("User created")
    controller.controller.create_user(
        "ReMail",
        "praxisprojekt-remail@uni-due.de",
        protocol=controller.Protocol.EXCHANGE,
        extra_information="ude-1729267167",
        password="V4otcHU^Tnr375R2H",
    )
# #controller.controller.refresh(False)

# emails = controller.controller.get_emails()
# email = controller.controller.get_emails(sender_email="apotrox@gmail.com")
# print(email)
# for mail in email:
#     print(controller.controller.get_attachments(mail))

#print(controller.controller.get_attachments(email))

#import os
#print(os.getcwd())
#_attach_folder = "./remail/database/attachments"
#If there are not attachments, do nothing
#if not (os.path.exists(_attach_folder) or os.listdir(_attach_folder)>0):
#    exit()

#attachments are stored in folders corresponding to their mail ids
#if there are multiple attachments per mail, they are still stored in one folder
#mail_ids=os.listdir(_attach_folder) #get list of all mail ids
#email_data=[]
#for mail in mail_ids:
   # print(mail)
    #email_data.append(controller.controller.get_mail_by_id(mail)) #append all mails to a list
    #email = controller.controller.get_mail_by_message_id("<"+mail+">")
   # print(email)