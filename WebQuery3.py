import sys
import time
import json
import sqlite3
import csv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException


class WebQuery:
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
                self.driver_list.append([car['running_position'],
                                    car['vehicle_number'],
                                    car['driver']['driver_id'],
                                    car['driver']['full_name'],
                                    car['delta'],
                                    car['sponsor_name'],
                                    car['starting_position'],
                                    car['vehicle_manufacturer']])
        #This works for qualifying results
        elif 'driver_name' in self.json_dict[0]:
            for i, car in enumerate(self.json_dict):
                self.driver_list.append([car['finishing_position'],
                                    car['car_number'],
                                    car['driver_id'],
                                    car['driver_name'],
                                    car['delta_leader'],
                                    car['sponsor'],
                                    car['finishing_position'],
                                    car['manufacturer']])
        #And this works for race results
        elif 'driver_fullname' in self.json_dict[0]:
            for i, car in enumerate(self.json_dict):
                self.driver_list.append([car['finishing_position'],
                                    car['car_number'],
                                    car['driver_id'],
                                    car['driver_fullname'],
                                    car['points_delta'],
                                    car['sponsor'],
                                    car['qualifying_position'],
                                    car['car_make']])  
        else:
            sys.exit('An unknown set of JSON dictionary keys are used... Exiting')
        self.driver_list.sort(key=lambda driver: driver[0])
    
    
    def clean_driver_list(self):
        self.cln_driver_list = []
        for driver in self.driver_list:
            driver[3] = driver[3].replace(' #', '')
            driver[3] = driver[3].replace('(i)', '')
            driver[3] = driver[3].replace('* ', '')
            driver[3] = driver[3].replace(' (P)', '')
            self.cln_driver_list.append(driver)
    
    
    def update_driver_DB(self):
        self.open_browser()
        self.get_json()
        self.close_browser()
        self.get_driver_info()
        self.clean_driver_list()
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS Drivers ('
                    'driver_id INTEGER NOT NULL UNIQUE, '
                    'driver_name TEXT NOT NULL UNIQUE, '
                    'PRIMARY KEY(driver_id))')
        for driver in self.cln_driver_list:
            c.execute('SELECT driver_name FROM Drivers WHERE driver_id=?',
                      (driver[2],))
            data = c.fetchone()
            if data == None:
                c.execute('INSERT INTO Drivers VALUES(?, ?)',
                          (driver[2], driver[3]))
                conn.commit()
                print('{} (ID = {}) was added to the database'
                      .format(driver[3], driver[2]))
        print('\nDatabase update complete')
        c.close()
        conn.close()
        
        
    def fetch_names_from_DB(self):
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()
        self.name_list = []
        for driver in self.driver_list:
            c.execute('SELECT driver_name FROM Drivers WHERE driver_id=?',
                      (driver[2],))
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
    
    
    def print_results(self):
        print('')
        if 'run_name' in self.json_dict: print(self.json_dict['run_name'])
        if 'track_name' in self.json_dict: print(self.json_dict['track_name'])
        if 'flag_state' in self.json_dict:
            flag_state = self.json_dict['flag_state']
            if flag_state in self.flag_dict:
                print('Flag:', self.flag_dict[flag_state])
            else:
                print('Flag', flag_state, 'not defined')
        if 'lap_number' and 'laps_in_race' in self.json_dict:
            print('Lap:', self.json_dict['lap_number'], '/',
                  self.json_dict['laps_in_race'], '\n')
        print('{:^4}{:^8}{:22}{:^7}'.format('Pos', '#', 'Driver', 'Delta'))
        print('------------------------------------------')
        for driver, name in zip(self.driver_list, self.name_list):
            print('{:^4}{:^8}{:22}{:^7}'.format(driver[0], driver[1], name[0], driver[4]))
    
    
    def query(self):
        self.open_browser()
        self.get_json()
        self.close_browser()
        self.get_driver_info()
        self.fetch_names_from_DB()
        self.print_results()
        
    
    def live_race(self, stage_lap=0, refresh=3, results_pause=10, csv_col=(0,)):
        self.open_browser()
        prev_lap = -1
        prev_flag = -1
        while True:
            self.refresh_browser()
            self.get_json()
            flag_state = self.json_dict['flag_state']
            lap = self.json_dict['lap_number']
            total_laps = self.json_dict['laps_in_race']
            if stage_lap == 0:
                crit_lap = total_laps
            else:
                crit_lap = stage_lap
            if flag_state != 1 and lap >= crit_lap:
                print('\n' + self.flag_dict[flag_state])
                print('Laps: {}/{}'.format(lap, total_laps))
                print('Getting Running Order...')
                time.sleep(results_pause)
                self.refresh_browser()
                self.get_json()
                self.close_browser()
                self.get_driver_info()
                self.fetch_names_from_DB()
                self.print_results()
                self.name_list_to_csv(col=csv_col)
                break
            else:
                if lap != prev_lap or flag_state != prev_flag:
                    print('\n' + self.flag_dict[flag_state])
                    print('Laps: {}/{}'.format(lap, total_laps))
                    print('{} laps to go'.format(crit_lap - lap))
                prev_lap = lap
                prev_flag = flag_state
                time.sleep(refresh)

    
    
    
    
    