import WebQuery3
import sys
import time
import social
import timer


def query(year, series_id, race_id, practice_id, practice_type):
    practice_la_titles = {1: 'practice_1',
                          2: 'practice_2',
                          3: 'final_practice',
                       }
    practice_titles = {1: 'practice1',
                       2: 'practice2',
                       3: 'practice3',
                       }
    series = {1: 'mencs',
              2: 'nxs',
              3: 'ngots'}
    # Get web object and set url
    web = WebQuery3.WebData(1, 1, 1, 1)
    if practice_type == 1:
        web.url = f'https://www.nascar.com/cacher/{year}/{series_id}/{race_id}/{practice_titles[practice_id]}.json'
    elif practice_type == 2:
        web.url = f'https://www.nascar.com/cacher/{year}/{series_id}/{race_id}/lapAvg_{series[series_id]}_{practice_la_titles[practice_id]}.json'
    else:
        print('Practice type does not exist')
        sys.exit()
    # Wait for page to become active and pull json
    while True:
        try: 
            web.open_browser()
            web.get_json()
            print('\n')
            break
        except:
            print('pausing 60...')
            time.sleep(60)
    web.close_browser()
    web.driver_list = []
    if practice_type == 1:
        drivers = web.json_dict
        for driver in drivers:
            web.driver_list.append({'driver name': driver['driver_name']})
    else:
        drivers = web.json_dict['10-Lap-Average']
        for driver in drivers:
            web.driver_list.append({'driver name': driver['dName']})
    web.clean_driver_names()
    return web.driver_list

def comment(series, practice_type, drivers, practice_header):
    num_drivers = 10
    if len(drivers) < num_drivers:
        num_drivers = len(drivers)
        if num_drivers == 0:
            print('No drivers completed practice type')
            return
    tweet_headers = {1: '1st',
                     2: '2nd',
                     3: 'final',
                     }
    srs = {1: 'Cup',
           2: 'Xfinity',
           3: 'Truck',}
    if practice_type == 1:
        comment = f'Fastest single laps from {tweet_headers[practice_header]} {srs[series]} practice:\n'
    else:    
        comment = f'Fastest 10-lap runs from {tweet_headers[practice_header]} {srs[series]} practice:\n'
    count = 0
    while count < num_drivers:
        comment = f'{comment}\n{count + 1}) {drivers[count]["driver name"]}'
        count += 1
    return comment


if __name__ == '__main__':
    year = 2019
    series = 1
    race_id = 4789                  #4823            #4789 
    track = '@MISpeedway'
    hashtags = ['#FireKeepersCasino400', '#NASCAR',]       #LTiPrinting250    #FireKeepersCasino400
    timer.run(timer.delay_start2(2019,6,7,16,55))
    
    practice_id = 2
    practice_header = 3
    practice_type = 1 # 1 = fastest lap, 2 = 10 lap average  
    drivers = query(year, series, race_id, practice_id, practice_type)
    com = comment(series, practice_type, drivers, practice_header)
    twitter = social.twitter(series, track, hashtags)
    tweet_id = twitter.practice(com, reply_id=0)
    
    practice_id = 3
    practice_header = 3
    practice_type = 2
    drivers = query(year, series, race_id, practice_id, practice_type)
    com = comment(series, practice_type, drivers, practice_header)
    twitter = social.twitter(series, track, hashtags)
    tweet_id = twitter.practice(com, reply_id=tweet_id)   
    
    
    
 