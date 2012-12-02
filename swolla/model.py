from candle import *
import re

def normalize_phone_number(inphone):
    return re.sub("[^0-9]", "", inphone)

class User(Candle):
    _id_column = "user_id"
    table_name = "user_credentials"


class Contact(Candle):
    _id_column = "contact_id"
    table_name = "contacts"
