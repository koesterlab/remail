import remail.controller as controller



#controller.controller.create_user("Milo", "thatchmilo35@gmail.com", protocol=controller.Protocol.IMAP, extra_information="imap.gmail.com", password = "oxomygwqzgdpislb")


emails = controller.controller.get_emails()

print(emails)