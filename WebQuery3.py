import sys
import time
import json
import sqlite3
import csv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from operator import itemgetter


class _WebData:
    
    def __init__(self, url):
        self.url = url
        
    chrome_ops = webdriver.ChromeOptions()
    chrome_ops.add_argument('headless')
    flag_dict = {
        1: 'Green',
        2: 'Yellow',
        3: 'Red',
        4: 'Checkered',
        8: 'Warm Up',
        9: 'Not Active'
        }

    def open_browser(self):
        self.browser = webdriver.Chrome(chrome_options=self.chrome_ops)
        self.browser.get(self.url)

    def close_browser(self):
        self.browser.quit()

    def refresh_browser(self):
        self.browser.refresh()

    def get_json(self):
        try: table = self.browser.find_element_by_xpath('/html/body/pre')
        #Exit if there is no table
        except NoSuchElementException:  
            self.close_browser()
            sys.exit('json page is not active')  
        try:    
            self.json_dict = json.loads(table.text)
        #If page doesn't load, close browser
        except json.decoder.JSONDecodeError:    
            self.close_browser()
            sys.exit('Fucking NASCAR.com wont load again')

    def get_driver_info(self):
        self.driver_list = []
        #This works for all 'feeds'
        if 'vehicles' in self.json_dict:
            for i, car in enumerate(self.json_dict['vehicles']):
                self.driver_list.append({
                    'position'      :car['running_position'],
                    'car number'    :car['vehicle_number'],
                    'driver id'     :car['driver']['driver_id'],
                    'driver name'   :car['driver']['full_name'],
                    'delta'         :car['delta'],
                    'laps led'      :'N/A',
                    'team'          :'N/A',
                    'sponsor'       :car['sponsor_name'],
                    'qual'          :car['starting_position'],
                    'manufacturer'  :car['vehicle_manufacturer']})
        #This works for qualifying results
        elif 'driver_name' in self.json_dict[0]:
            for i, car in enumerate(self.json_dict):
                self.driver_list.append({
                    'position'      :car['finishing_position'],
                    'car number'    :car['car_number'],
                    'driver id'     :car['driver_id'],
                    'driver name'   :car['driver_name'],
                    'delta'         :car['delta_leader'],
                    'laps led'      :'N/A',
                    'team'          :'N/A',
                    'sponsor'       :car['sponsor'],
                    'qual'          :car['finishing_position'],
                    'manufacturer'  :car['manufacturer']})
        #And this works for race results
        elif 'driver_fullname' in self.json_dict[0]:
            for i, car in enumerate(self.json_dict):
                self.driver_list.append({
                    'position'      :car['finishing_position'],
                    'car number'    :car['car_number'],
                    'driver id'     :car['driver_id'],
                    'driver name'   :car['driver_fullname'],
                    'delta'         :'N/A',
                    'laps led'      :car['laps_led'],
                    'team'          :car['team_name'],
                    'sponsor'       :car['sponsor'],
                    'qual'          :car['qualifying_position'],
                    'manufacturer'  :car['car_make']})  
        else:
            sys.exit('An unknown set of JSON dictionary keys are used... Exiting')
            
        # Check eligibility, pole, and format 'delta'
        for driver in self.driver_list:
            if '(i)' in driver['driver name']:
                driver['eligible'] = 0
            else:
                driver['eligible'] = 1
            if driver['delta'] < 0:
                driver['delta'] = int(driver['delta'])
            else:
                driver['delta'] = format(driver['delta'], '.3f')
            if driver['qual'] == 1:
                driver['pole'] = 1
            else:
                driver['pole'] = 0
                
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
                self.name_list.append(('ID not in database. Run "populate_DB"',))
            else:
                self.name_list.append(name) 
        c.close()
        conn.close()
    
    def name_list_to_csv(self, col=(0,)):
        self.name_list.insert(0, col)
        with open('results.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(self.name_list)
        print('\ncsv. created')

    def print_results(self, driver_only=False):
        print('')
        print(self.race_info['race name'])
        print(self.race_info['track name'])
        flag_state = self.race_status['flag state']
        if flag_state in self.flag_dict:
            print('Flag:', self.flag_dict[flag_state])
        else:
            print('Flag', flag_state, 'not defined')
        print('Lap:', self.race_status['lap number'], '/',
              self.race_status['total laps'], '\n')
        if driver_only == False:
            print('{:^4}{:^8}{:22}{:^7}'.format('Pos', '#', 'Driver', 'Delta'))
            print('------------------------------------------')
            for driver, name in zip(self.driver_list, self.name_list):
                print('{:^4}{:^8}{:22}{:^7}'.format(driver['position'], 
                      driver['car number'], name[0], driver['delta']))
        else:
            for name in self.name_list:
                print (name[0])    

class Database:
    
    def __init__(self, url):
        self.qry = _WebData(url)
        self.qry.open_browser()
        self.qry.get_json()
        self.qry.close_browser()
        self.qry.get_driver_info()
        self.qry.clean_driver_names()
        self.qry.get_race_info()
        self.qry.get_race_status()
        
    def update_driver_DB(self):
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS Drivers ('
                    'driver_id INTEGER NOT NULL UNIQUE, '
                    'driver_name TEXT NOT NULL UNIQUE, '
                    'PRIMARY KEY(driver_id)'
                    ')')
        for driver in self.qry.driver_list:
            c.execute('SELECT EXISTS(SELECT driver_name FROM Drivers WHERE driver_id=?)',
                      (driver['driver id'],))
            data = c.fetchone()
            if data[0] == 0:
                c.execute('INSERT INTO Drivers VALUES(?, ?)',
                          (driver['driver id'], driver['driver name']))
                conn.commit()
                print('{} (ID = {}) was added to the database'
                      .format(driver['driver name'], driver['driver id']))
        print('\nDatabase update complete')
        c.close()
        conn.close()

# other defs will then populate everything else
# Other stats that need to be added?
        
# DNF?

    def init_race_results_DB(self):
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS Race_Results ('
                  'driver_id INTEGER,'
                  'series_id INTEGER,'
                  'race_id INTEGER,'
                  'qual INTEGER,'
                  'pole INTEGER,'       # 0, 1
                  'stage1 INTEGER,'
                  'stage2 INTEGER,'
                  'stage3 INTEGER,'
                  'finish INTEGER,'
                  'laps_led INTEGER,'
                  'win INTEGER,'        # 0, 1
                  'eligible INTEGER,'   # 0, 1
                  'encumbered INTEGER,' # 0, 1
                  'car_number INTEGER,'
                  'manufacturer TEXT,'
                  'team TEXT,'
                  'sponsor TEXT'
                  ')')
        for driver in self.qry.driver_list:
            c.execute('SELECT EXISTS(SELECT * FROM Race_Results WHERE driver_id=? AND race_id=?)', 
                      (driver['driver id'], self.qry.race_info['race id']))
            data = c.fetchone()
            if data[0] == 0:
                c.execute('INSERT INTO Race_Results(driver_id, series_id, race_id, qual,'
                                                    'pole, eligible, encumbered, car_number,'
                                                    'manufacturer, sponsor)'
                                                    'VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                          (driver['driver id'], self.qry.race_info['series id'], 
                           self.qry.race_info['race id'], driver['qual'], driver['pole'],
                           driver['eligible'], 0, driver['car number'], 
                           driver['manufacturer'], driver['sponsor'])
                          )
                conn.commit()
        print('Results saved to DB')
        c.close()
        conn.close()
        
    def update_results_DB(self, stage):
        
        stages = {
                0: 'finish',
                1: 'stage1',
                2: 'stage2',
                3: 'stage3'
                }
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()     
        for driver in self.qry.driver_list:
            c.execute('UPDATE Race_Results SET {}=? WHERE driver_id=? AND race_id=?'.format(stages[stage]),
                      (driver['position'], driver['driver id'], self.qry.race_info['race id']))
        
            conn.commit()
        print('Results updated in DB')
        c.close()
        conn.close()


class Query:
    
    def __init__(self, url):
        self.qry = _WebData(url)

    def results(self, driver_only=False):
        self.qry.open_browser()
        self.qry.get_json()
        self.qry.close_browser()
        self.qry.get_driver_info()
        self.qry.get_race_info()
        self.qry.get_race_status()
        self.qry.fetch_names_from_DB()
        self.qry.print_results(driver_only)

    def live_race(self, stage_lap=0, refresh=3, results_pause=10, csv_col=(0,)):
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
            laps_to_go = self.qry.race_status['laps to go']
            if stage_lap == 0:
                crit_lap = total_laps
            else:
                crit_lap = stage_lap
            if flag_state != 1 and lap >= crit_lap:
                print('\n' + self.qry.flag_dict[flag_state])
                print('Laps: {}/{}'.format(lap, total_laps))
                print('Getting Running Order...')
                time.sleep(results_pause)
                self.qry.refresh_browser()
                self.qry.get_json()
                self.qry.close_browser()
                self.qry.get_driver_info()
                self.qry.get_race_info()
                self.qry.get_race_status()
                self.qry.fetch_names_from_DB()
                self.qry.print_results(driver_only=False)
                self.qry.name_list_to_csv(col=csv_col)
                break
            else:
                if lap != prev_lap or flag_state != prev_flag:
                    print('\n' + self.qry.flag_dict[flag_state])
                    print('Laps: {}/{}'.format(lap, total_laps))
                    print('{} laps to go'.format(laps_to_go))
                    self.qry.get_driver_info()
                    self.qry.fetch_names_from_DB()
                    self.qry.print_results(driver_only=False)
                prev_lap = lap
                prev_flag = flag_state
                time.sleep(refresh)
