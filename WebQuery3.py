import sys
import time
import json
import sqlite3
import datetime
import Database
from selenium import webdriver
import selenium.common.exceptions as selenium_exceptions
from operator import itemgetter


class WebData:
    
    def __init__(self, year, series_id, race_id, feed_type):
        #'https://www.nascar.com/live/feeds/series_2/4627/live-feed.json'
        #'https://www.nascar.com/live/feeds/series_2/4636/stage1-feed.json'
        #'https://www.nascar.com/cacher/2017/2/4636/qualification.json'
        #'https://www.nascar.com/cacher/2017/2/4636/raceResults.json'
        feeds = {
                0: 'live-feed',
                1: 'stage1-feed',
                2: 'stage2-feed',
                3: 'stage3-feed',
                }
        self.feed = feeds[feed_type]
        url = f'https://www.nascar.com/live/feeds/series_{series_id}/{race_id}/{self.feed}.json'
        self.url = url
        self.chrome_ops = webdriver.ChromeOptions()
        self.chrome_ops.add_argument('headless')
        self.chrome_ops.add_argument('--no-sandbox')  # fixes page crash issues
        self.flag_dict = {
            1: 'Green',
            2: 'Yellow',
            3: 'Red',
            4: 'Checkered',
            8: 'Warm Up',
            9: 'Not Active',
			}

    def open_browser(self):
        self.browser = webdriver.Chrome(chrome_options=self.chrome_ops)
        self.browser.get(self.url)

    def close_browser(self):
        self.browser.quit()

    def refresh_browser(self):
        self.browser.refresh()

    def get_json(self):
        try: 
            table = self.browser.find_element_by_xpath('/html/body/pre')
        #Exit if there is no table
        except selenium_exceptions.NoSuchElementException:  
            self.close_browser()
            sys.exit('json page is not active')
        try:    
            self.json_dict = json.loads(table.text)
        #If page doesn't load, close browser
        except json.decoder.JSONDecodeError:    
            sys.exit('NASCAR.com will not load')

    def get_driver_info(self):
        self.driver_list = []
        for i, car in enumerate(self.json_dict['vehicles']):
            laps_led = 0
            for led in car['laps_led']:
                if not led['end_lap'] == 0:       # Eliminates situation where pole winner doesn't lead first lap
                    laps_led += led['end_lap'] - led['start_lap'] + 1
            if laps_led == 0:
                laps_led = None
            self.driver_list.append({
                'position'      :car['running_position'],
                'laps led'      :laps_led,
                'car number'    :car['vehicle_number'],
                'driver id'     :car['driver']['driver_id'],
                'driver name'   :car['driver']['full_name'],
                'delta'         :car['delta'],
                'lap time'      :car['last_lap_time'],
                'sponsor'       :car['sponsor_name'],
                'qual'          :car['starting_position'],
                'manufacturer'  :car['vehicle_manufacturer']})
        for driver in self.driver_list:
            # Check eligibility
            if '(i)' in driver['driver name']:
                driver['ineligible'] = 1
            else:
                driver['ineligible'] = None #NULL
            # Check pole
            if driver['qual'] == 1:
                driver['pole'] = 1
            else:
                driver['pole'] = None
            # Format 'delta'
            if driver['delta'] < 0:
                driver['delta'] = int(driver['delta'])
            elif driver['position'] == 1:
                driver['delta'] = format(driver['lap time'], '.3f')
            else:
                driver['delta'] = format(driver['delta'], '.3f')
        self.driver_list.sort(key=itemgetter('position'))

    def get_race_info(self): 
        
        self.race_info = {
            'race id'      :self.json_dict['race_id'],
            'series id'    :self.json_dict['series_id'],
            'track id'     :self.json_dict['track_id'],
            'race name'    :self.json_dict['run_name'],
            'track name'   :self.json_dict['track_name'],
            'track length' :self.json_dict['track_length']  
            }

    def get_race_status(self):
        self.race_status = {
            'lap number'   :self.json_dict['lap_number'],
            'total laps'   :self.json_dict['laps_in_race'],
            'laps to go'   :self.json_dict['laps_to_go'],
            'flag state'   :self.json_dict['flag_state'],
            'elapsed time' :self.json_dict['elapsed_time'],
            'time of day'  :self.json_dict['time_of_day'],
            'cautions'     :self.json_dict['number_of_caution_segments'],
            'caution laps' :self.json_dict['number_of_caution_laps'],
            'lead changes' :self.json_dict['number_of_lead_changes'],
            'leaders'      :self.json_dict['number_of_leaders']
            }
    
    def clean_driver_names(self):
        for driver in self.driver_list:
            driver['driver name'] = driver['driver name'].replace(' #', '')
            driver['driver name'] = driver['driver name'].replace('(i)', '')
            driver['driver name'] = driver['driver name'].replace('* ', '')
            driver['driver name'] = driver['driver name'].replace(' (P)', '')
        
    def fetch_names_from_DB(self):
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()
        self.name_list = []
        for driver in self.driver_list:
            c.execute('SELECT driver_name FROM Drivers WHERE driver_id=?',
                      (driver['driver id'],))
            name = c.fetchone()
            if name == None:
                self.name_list.append((f'ID {driver["driver id"]} not in database. Run "Database.update_drivers"',))
            else:
                self.name_list.append(name) 
        c.close()
        conn.close()


class Query:
    
    def __init__(self, WebData):
        self.qry = WebData

    def results(self, driver_only=False):
        self.qry.open_browser()
        self.qry.get_json()
        self.qry.close_browser()
        self.qry.get_driver_info()
        self.qry.get_race_info()
        self.qry.get_race_status()
        self.qry.fetch_names_from_DB()
        self._print_header()
        self._print_results(driver_only)
        
    def _print_header(self, stage_lap=0):
        print('')
        print(f"\n{self.qry.race_info['race name']}")
        print(f"{self.qry.race_info['track name']}\n")
        flag_state = self.qry.race_status['flag state']
        if flag_state in self.qry.flag_dict:
            print(f'Flag: {self.qry.flag_dict[flag_state]}')
        else:
            print(f'Flag {flag_state} not defined')
        current_lap = self.qry.race_status['lap number']
        if not stage_lap == 0:
            total_laps = stage_lap
            to_go = total_laps - current_lap
        else:
            total_laps = self.qry.race_status['total laps']
            to_go = self.qry.race_status['laps to go']
        print(f'Lap: {current_lap}/{total_laps}')
        print(f'{to_go} laps to go')
        print(f"Elapsed: {datetime.timedelta(seconds=self.qry.race_status['elapsed time'])}\n")
    
    def _print_results(self, driver_only=False):
        if driver_only == False:
            print('{:^4}{:^8}{:22}{:^7}'.format('Pos', '#', 'Driver', 'Delta'))
            print('------------------------------------------')
            for driver, name in zip(self.qry.driver_list, self.qry.name_list):
                print(f"{driver['position']:^4}"
                      f"{driver['car number']:^8}"
                      f"{name[0]:22}"
                      f"{driver['delta']:^7}")
        else:
            for name in self.qry.name_list:
                print (name[0])

    def live_race(self, stage_lap=0, refresh=3, results_pause=10):
        live = Database.LiveRace()
        self.qry.open_browser()
        prev_lap = -1
        prev_flag = -1
        while True:
            self.qry.refresh_browser()
            self.qry.get_json()
            self.qry.get_race_status()
            
            flag_state = self.qry.race_status['flag state']
            lap = self.qry.race_status['lap number']
            total_laps = self.qry.race_status['total laps']
            if stage_lap == 0:
                crit_lap = total_laps
            else:
                crit_lap = stage_lap
            # Yellow flag and stage end
            if flag_state != 1 and lap >= crit_lap: 
                print('\nGetting Running Order...')
                print(f'Pausing {results_pause} seconds...')
                time.sleep(results_pause)
                self.qry.refresh_browser()
                self.qry.get_json()
                self.qry.close_browser()
                self.qry.get_driver_info()
                self.qry.get_race_info()
                self.qry.get_race_status()
                self.qry.fetch_names_from_DB()
                self._print_header(stage_lap=stage_lap)
                self._print_results()
                live.add_lap(self.qry.driver_list, self.qry.race_status)
                break
            else:
                # new lap or new flag
                if lap != prev_lap or flag_state != prev_flag: 
                    self.qry.get_driver_info()
                    self.qry.fetch_names_from_DB()
                    self._print_header(stage_lap=stage_lap)
                    self._print_results()
                    live.add_lap(self.qry.driver_list, self.qry.race_status)
                prev_lap = lap
                prev_flag = flag_state
                time.sleep(refresh)