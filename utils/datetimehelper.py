import datetime

def get_current_unix_time():
    current_datetime = datetime.datetime.now()
    unix_time = int(current_datetime.timestamp())
    return unix_time
