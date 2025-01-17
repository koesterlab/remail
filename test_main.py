import remail.controller as controller



#controller.controller.create_user("Milo", "thatchmilo35@gmail.com", protocol=controller.Protocol.IMAP, extra_information="imap.gmail.com", password = "oxomygwqzgdpislb")


#emails = controller.controller.get_emails()
recipients = controller.controller.get_recipients(1306)
print(recipients)