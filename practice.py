import WebQuery3
import sys
import time
import social


def query(year, race_id, practice_id, practice_type):
    practice_la_titles = {1: 'practice_1',
                          2: 'practice_2',
                          3: 'final_practice',
                       }
    practice_titles = {1: 'practice1',
                       2: 'practice2',
                       3: 'practice3',
                       }
    # Get web object and set url
    web = WebQuery3.WebData(1, 1, 1, 1)
    if practice_type == 1:
        web.url = f'https://www.nascar.com/cacher/{year}/1/{race_id}/{practice_titles[practice_id]}.json'
    elif practice_type == 2:
        web.url = f'https://www.nascar.com/cacher/{year}/1/{race_id}/lapAvg_mencs_{practice_la_titles[practice_id]}.json'
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

def comment(practice_type, drivers):
    num_drivers = 10
    if len(drivers) < num_drivers:
        num_drivers = len(drivers)
    tweet_headers = {1: '1st',
                     2: '2nd',
                     3: 'final',
                     }
    if practice_type == 1:
        comment = f'Fastest single lap times from {tweet_headers[practice_id]} Cup practice:\n'
    else:    
        comment = f'Fastest 10 lap averages from {tweet_headers[practice_id]} Cup practice:\n'
    count = 0
    while count < num_drivers:
        comment = f'{comment}\n{count + 1}) {drivers[count]["driver name"]}'
        count += 1
    return comment


if __name__ == '__main__':
    year = 2019
    series = 1
    race_id = 4777
    practice_id = 3
    practice_type = 2 # 1 = fastest lap, 2 = 10 lap average
    track = '@ACSupdates'
    hashtags = ['#NASCAR',]
    
    drivers = query(year, race_id, practice_id, practice_type)
    com = comment(practice_type, drivers)
    
    twitter = social.twitter(series, track, hashtags)
    twitter.practice(com)
