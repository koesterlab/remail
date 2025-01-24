import remail.controller as controller



#controller.controller.create_user("Milo", "thatchmilo35@gmail.com", protocol=controller.Protocol.IMAP, extra_information="imap.gmail.com", password = "oxomygwqzgdpislb")


#emails = controller.controller.get_emails()
email = controller.controller.get_emails(recipient_email="robinhempel1@gmail.com")
print(controller.controller.get_full_email_data(email[1]))
print(controller.controller.get_attachments(email[1]))