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
    




        
        
class delay_start2:
    
    def __init__(self, year, month, day, hour, second):
        self.future = datetime.datetime(year, month, day, hour, second)
        
    def get_time_left(self):
        now = datetime.datetime.now()
        delta = self.future - now
        self.time_left = delta.total_seconds() 
    
    def sleep(self, length):
        while self.time_left > length:
            print(f'Pausing {length} seconds... {int(self.time_left)} seconds remaining')
            time.sleep(length)
            self.time_left -= length
            

    
def run(ds2):
    
    # 1 hour
    ds2.get_time_left()
    ds2.sleep(3600)
    
    # 10 minutes
    ds2.get_time_left()
    ds2.sleep(600)
    
    # 3 minutes
    ds2.get_time_left()
    ds2.sleep(180)
    
    # 30 seconds
    ds2.get_time_left()
    ds2.sleep(30)
    
    # 5 seconds
    ds2.get_time_left()
    ds2.sleep(5)

    # 1 second
    ds2.get_time_left()
    ds2.sleep(1)
    
    print('Pause Complete')

        
    
        
        