import WebQuery3
import sys
import time
import social
import timer
import pandas as pd


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
        drivers = web.json_dict
        df = pd.DataFrame(web.json_dict)
        df.sort_values('Con10LapRank', inplace=True)
        for index, driver in df.head(10).iterrows():
            web.driver_list.append({'driver name': driver['FullName']})
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
    srs = {1: '@NASCAR',
           2: '@NASCAR_XFINITY',
           3: '@NASCAR_Trucks',}
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
    series = 2
    race_id = 4830
    track = '@WGI'
    hashtags = ['#Zippo200', '#NASCAR',]
    timer.run(timer.delay_start2(2019,8,2,13,30))
    
    practice_id = 1
    practice_header = 1
    practice_type = 1 # 1 = fastest lap, 2 = 10 lap average  
    drivers = query(year, series, race_id, practice_id, practice_type)
    com = comment(series, practice_type, drivers, practice_header)
    twitter = social.twitter(series, track, hashtags)
    tweet_id = twitter.practice(com, reply_id=0)
    
    practice_id = 1
    practice_header = 1
    practice_type = 2
    drivers = query(year, series, race_id, practice_id, practice_type)
    com = comment(series, practice_type, drivers, practice_header)
    print(com)
    twitter = social.twitter(series, track, hashtags)
    tweet_id = twitter.practice(com, reply_id=tweet_id)   
    
    
    
 