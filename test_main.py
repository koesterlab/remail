import remail.controller as controller
from remail.email_api.service import ExchangeProtocol, ImapProtocol
import remail.email_api.credentials_helper as ch
import datetime
from tzlocal import get_localzone

# ch.protocol = ch.Protocol.EXCHANGE
# #ex = ExchangeProtocol(ch.get_email(), "None", ch.get_username(), controller.controller)

# #ex.login()

# #print(ex.get_emails(date=datetime.datetime(2025,1,17,8,0, tzinfo=get_localzone())))

# ch.protocol = ch.Protocol.IMAP
# im = ImapProtocol(ch.get_email(), None, ch.get_host(), controller.controller)
# im.login()
# print(im.get_emails(date=datetime.datetime(2025,1,17,8,0, tzinfo=get_localzone())))
# im.logout()
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