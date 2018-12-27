import sqlite3
import csv
import pandas as pd

stages = {
        -1: 'qual',
        1: 'stage1',
        2: 'stage2',
        3: 'stage3',
        0: 'finish',
        }

class Database:
	
    def __init__(self):
        # init results database
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS Results (
                  driver_id INTEGER,
                  race_id INTEGER,
                  qual INTEGER,
                  pole INTEGER,
                  stage1 INTEGER,
                  stage2 INTEGER,
                  stage3 INTEGER,
                  finish INTEGER,
                  laps_led INTEGER,
                  win INTEGER,
                  ineligible INTEGER,
                  encumbered INTEGER,
                  penalty INTEGER,
                  car_number INTEGER,
                  manufacturer TEXT,
                  sponsor TEXT
                  )""")
        # init race database
        c.execute("""CREATE TABLE IF NOT EXISTS Races (
		            race_id INTEGER NOT NULL UNIQUE,
		            series_id INTEGER,
		            year INTEGER,
                  start_time INTEGER,
		            track_id INTEGER,
                  race_name TEXT,
                  race_number INTEGER,
                  stage_length INTEGER,
                  total_laps INTEGER,
                  PRIMARY KEY(race_id)
		            )""")
        # init track database
        c.execute("""CREATE TABLE IF NOT EXISTS Tracks (
                  track_id INTEGER NOT NULL UNIQUE,
                  track_name TEXT,
                  length REAL,
                  nickname TEXT,
                  type TEXT,
                  PRIMARY KEY(track_id)
                  )""")
        # init drivers database
        c.execute("""CREATE TABLE IF NOT EXISTS Drivers (
                  driver_id INTEGER NOT NULL UNIQUE,
                  driver_name TEXT NOT NULL UNIQUE,
                  PRIMARY KEY(driver_id)
                  )""")
        conn.commit()
        c.close()
        conn.close()
        
    def web_query(self, WebData):
        self.qry = WebData
        self.qry.open_browser()
        self.qry.get_json()
        self.qry.close_browser()
        self.qry.get_driver_info()
        self.qry.clean_driver_names()
        self.qry.get_race_info()
        self.qry.get_race_status()
    
    def add_results(self):
        """
        Add rows to the 'Results' table
        This initalizes the rows with qual and other data
        Must be called before results can be updated with stages and finish
        """
        
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()
        for driver in self.qry.driver_list:
            # Check if row already exists. If not, create it.
            c.execute("""SELECT EXISTS(SELECT * FROM Results WHERE 
                                       driver_id=? AND 
                                       race_id=?)""", 
                      (driver['driver id'], 
                       self.qry.race_info['race id']))
            data = c.fetchone()
            if data[0] == 0:
                c.execute("""INSERT INTO Results(driver_id, 
                                                 race_id, 
                                                 qual,
                                                 pole, 
                                                 ineligible, 
                                                 car_number,
                                                 manufacturer, 
                                                 sponsor)
                                        VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                          (driver['driver id'], 
                           self.qry.race_info['race id'], 
                           driver['qual'], 
                           driver['pole'],
                           driver['ineligible'], 
                           driver['car number'], 
                           driver['manufacturer'], 
                           driver['sponsor'])
                          )
        conn.commit()
        print('\nResults DB initialized')
        c.close()
        conn.close()
        
    def update_results(self, stage):
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()     
        for driver in self.qry.driver_list:
            # Check for win
            if stage == 0 and driver['position'] == 1:
                c.execute('UPDATE Results SET win=1 WHERE driver_id=? AND race_id=?',
                          (driver['driver id'],
                           self.qry.race_info['race id']))
            if stage == -1:
                c.execute('UPDATE Results SET {}=? WHERE driver_id=? AND race_id=?'.format(stages[stage]),
                          (driver['qual'], 
                           driver['driver id'], 
                           self.qry.race_info['race id']))    
            else:
                c.execute('UPDATE Results SET {}=? WHERE driver_id=? AND race_id=?'.format(stages[stage]),
                          (driver['position'], 
                           driver['driver id'], 
                           self.qry.race_info['race id']))
        conn.commit()
        print('\nResults DB updated')
        c.close()
        conn.close()

    def update_laps(self):
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()
        # Reset everyone to NULL
        c.execute('UPDATE Results SET laps_led=? WHERE race_id=?', (None, self.qry.race_info['race id']))
        # Update laps led in DB
        for driver in self.qry.driver_list:
            if not driver['laps led'] == None:
                c.execute('UPDATE Results SET laps_led=? WHERE driver_id=? and race_id=?',
                          (driver['laps led'],
                           driver['driver id'],
                           self.qry.race_info['race id']))
        conn.commit()
        print('\nLaps Led updated\n')
        c.close()
        conn.close()         
        
    def update_drivers(self):
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()
        for driver in self.qry.driver_list:
            c.execute('SELECT EXISTS(SELECT driver_name FROM Drivers WHERE driver_id=?)',
                      (driver['driver id'],))
            data = c.fetchone()
            if data[0] == 0:
                c.execute('INSERT INTO Drivers VALUES(?, ?)',
                          (driver['driver id'], 
                           driver['driver name']))
                print(f"{driver['driver name']} (ID = {driver['driver id']}) was added to the database")
        conn.commit()
        print('\nDriver database update complete')
        c.close()
        conn.close()
        
    def update_tracks(self):
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()
        c.execute('SELECT EXISTS(SELECT track_id FROM TRACKS WHERE track_id=?)',
                  (self.qry.race_info['track id'],))
        data = c.fetchone()
        if data[0] == 0:
            c.execute('INSERT INTO Tracks(track_id, track_name, length) VALUES(?, ?, ?)',
                      (self.qry.race_info['track id'],
                       self.qry.race_info['track name'],
                       self.qry.race_info['track length'],))
            print(f"{self.qry.race_info['track name']} (ID = {self.qry.race_info['track id']}) was added to the database")
        conn.commit()
        print('\nTrack database update complete')
        c.close()
        conn.close()
        
    def add_race(self, year, race_number, stage_length):
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()
        c.execute('SELECT EXISTS(SELECT race_id FROM Races WHERE race_id=?)',
                  (self.qry.race_info['race id'],))
        data = c.fetchone()
        if data[0] == 0:
            c.execute('INSERT INTO Races(race_id, series_id, track_id, race_name, total_laps, year, race_number, stage_length) VALUES(?, ?, ?, ?, ?, ?, ?, ?)',
                      (self.qry.race_info['race id'], 
                       self.qry.race_info['series id'],
                       self.qry.race_info['track id'], 
                       self.qry.race_info['race name'],
                       self.qry.race_status['total laps'],
                       year,
                       race_number,
                       stage_length,))
        else:
            c.execute('UPDATE Races SET series_id = ? WHERE race_id=?',
                      (self.qry.race_info['series id'], 
                       self.qry.race_info['race id']))
            c.execute('UPDATE Races SET track_id = ? WHERE race_id=?',
                      (self.qry.race_info['track id'], 
                       self.qry.race_info['race id']))
            c.execute('UPDATE Races SET race_name = ? WHERE race_id=?',
                      (self.qry.race_info['race name'], 
                       self.qry.race_info['race id']))
            c.execute('UPDATE Races SET total_laps = ? WHERE race_id=?',
                      (self.qry.race_status['total laps'], 
                       self.qry.race_info['race id']))
            c.execute('UPDATE Races SET year = ? WHERE race_id=?',
                      (year, 
                       self.qry.race_info['race id']))
            c.execute('UPDATE Races SET race_number = ? WHERE race_id=?',
                      (race_number, 
                       self.qry.race_info['race id']))
            c.execute('UPDATE Races SET stage_length = ? WHERE race_id=?',
                      (stage_length, 
                       self.qry.race_info['race id']))
        conn.commit()
        c.close()
        conn.close()
        
        
class Fetch:
    
    def __init__(self):
        pass
        
    def results(self, race_id, stage_id):
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()
        stage = stages[stage_id]
        sql = f"""SELECT driver_name FROM Drivers JOIN Results ON 
                  Drivers.driver_id = Results.driver_id 
                  WHERE race_id={race_id} ORDER BY {stage}"""
        c.execute(sql)
        drivers = c.fetchall()
        driver_list = []
        for driver in drivers:
            print(driver[0])
            driver_list.append(driver[0])
        c.close()
        conn.close()
        return driver_list

    def results_to_csv(self, race_id, stage_id, col):  
        driver_list = self.results(race_id, stage_id)
        driver_list.insert(0, col)
        with open('results.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            for name in driver_list:
                writer.writerow([name])
        print('\ncsv. created')
        
    def laps_to_csv(self, series, year):
        conn = sqlite3.connect('NASCAR.db')
        df = pd.read_sql_query("""SELECT driver_name, SUM(laps_led) FROM Results 
                               JOIN Races ON Results.race_id = Races.race_id
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               WHERE series_id=? AND year=? 
                               GROUP BY Results.driver_id
                               ORDER BY SUM(laps_led) DESC""", 
                               params=(series, year), con=conn)
        df.to_csv('laps led.csv')
        conn.close()
    
    def all_drivers(self, series, year):
        conn = sqlite3.connect('NASCAR.db')
        df = pd.read_sql_query("""SELECT driver_name, car_number, manufacturer FROM Results
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               WHERE Races.series_id=? AND Races.year=?
                               GROUP BY Results.driver_id
                               ORDER BY driver_name""",
                               params=(series, year), con=conn)
        print('\nAll drivers:\n')
        for driver in df['driver_name']:
            print(driver)
        conn.close()
        df.to_csv('results.csv')
        
    def ineligible_drivers(self, series, year):
        conn = sqlite3.connect('NASCAR.db')
        df = pd.read_sql_query("""SELECT driver_name FROM Results
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               WHERE Races.series_id=? AND Races.year=? AND Results.ineligible = 1
                               GROUP BY Results.driver_id
                               ORDER BY driver_name""",
                               params=(series, year), con=conn)
        print('\nIneligible drivers:\n')
        for driver in df['driver_name']:
            print(driver)
        conn.close()


class LiveRace:
    
    def __init__(self):
        pass
        
    def drop_table(self):
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()
        c.execute('DROP TABLE IF EXISTS Live_Race')
        conn.commit()
        c.close()
        conn.close()
        
    def add_table(self, driver_list):
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS Live_Race(driver_id INTEGER, "0" INTEGER)')
        for driver in driver_list:
            c.execute('INSERT INTO Live_Race VALUES(?, ?)',
                      (driver['driver id'], driver['qual']))
        conn.commit()
        c.close()
        conn.close()
        
    def add_lap(self, driver_list, race_status):
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()
        c.execute('PRAGMA table_info(Live_Race)')
        col_list = c.fetchall()
        lap = race_status['lap number']
        lap_exists = False
        for col in col_list:
            if col[1] == str(lap):
                lap_exists = True
        if not lap_exists:
            c.execute(f'ALTER TABLE Live_Race ADD COLUMN "{lap}" INTEGER')
        for driver in driver_list:
            c.execute(f'UPDATE Live_Race SET "{lap}"=? WHERE driver_id=?', 
                      (driver['position'], driver['driver id']))
        conn.commit()
        c.close()
        conn.close()
        
    def get_results(self):
        conn = sqlite3.connect('NASCAR.db')        
        df = pd.read_sql_query("""SELECT * FROM Live_Race
                               JOIN Drivers ON Live_Race.driver_id = Drivers.driver_id
                               """, con=conn)
        # Removes driver_id's and rearrange columns so driver_name is first
        del df['driver_id']
        cols = df.columns.tolist()
        cols = cols[-1:] + cols[:-1]
        df = df[cols]
        df.to_csv('live race.csv')