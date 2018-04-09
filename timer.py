import time
import datetime


def delay_start(year, month, day, hour, second):
    now = datetime.datetime.now()
    future = datetime.datetime(year,month,day,hour,second)
    delta = future - now
    time_left = delta.total_seconds()
    while time_left > 0:
        hours = delta.seconds//3600
        minutes = (delta.seconds//60)%60
        seconds = delta.seconds - 3600*hours - 60*minutes
        print(f'Program will start in {hours}:{minutes}:{seconds}')
        if time_left > 120:
            time.sleep(60)
        elif time_left > 60:
            time.sleep(5)
        else:
            time.sleep(1)
        now = datetime.datetime.now()
        delta = future - now
        time_left = delta.total_seconds()
    print('\nPause complete. Starting program now!')