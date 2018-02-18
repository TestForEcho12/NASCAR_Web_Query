import sqlite3
import csv
import pandas as pd

stages = {
        0: 'finish',
        1: 'stage1',
        2: 'stage2',
        3: 'stage3'
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
                  tv TEXT,
                  PRIMARY KEY(race_id)
		            )""")
        # init track database
        c.execute("""CREATE TABLE IF NOT EXISTS Tracks (
                  track_id INTEGER NOT NULL UNIQUE,
                  track_name TEXT,
                  length REAL,
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
#        date_stamp = int(datetime.datetime(2018,2,11,12).timestamp())  
#        c.execute('INSERT INTO Races(race_id, start_time) VALUES(?, ?)', (10, date_stamp))
#        conn.commit()
#        c.execute('SELECT start_time FROM Races WHERE race_id=10')
#        dt = c.fetchone()
#        print(dt[0])
#        print(datetime.datetime.fromtimestamp(dt[0]).date())
#        print(datetime.datetime.fromtimestamp(dt[0]).time())
        print('\nResults DB initialized')
        c.close()
        conn.close()
        
    def update_results(self, stage):
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()     
        for driver in self.qry.driver_list:
            # Check for win
            if stage == 0 and driver['position'] == 1:
                win = 1
            else:
                win = None
            c.execute('UPDATE Results SET {}=?, laps_led=?, win=? WHERE driver_id=? AND race_id=?'.format(stages[stage]),
                      (driver['position'], 
                       driver['laps led'], 
                       win, 
                       driver['driver id'], 
                       self.qry.race_info['race id']))
        conn.commit()
        print('\nResults DB updated')
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
                
        print('\nDatabase update complete')
        c.close()
        conn.close()
        
    def add_race(self):
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()
        c.execute('SELECT EXISTS(SELECT race_id FROM Races WHERE race_id=?)',
                  (self.qry.race_info['race id'],))
        data = c.fetchone()
        if data[0] == 0:
            c.execute('INSERT INTO Races(race_id, series_id, track_id, race_name, total_laps) VALUES(?, ?, ?, ?, ?)',
                      (self.qry.race_info['race id'], 
                       self.qry.race_info['series id'],
                       self.qry.race_info['track id'], 
                       self.qry.race_info['race name'],
                       self.qry.race_status['total laps']))
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
#            c.execute("""UPDATE Races 
#                      SET (series_id, track_id, race_name, total_laps) = (?, ?, ?, ?) 
#                      WHERE race_id=?""", 
#                      (self.qry.race_info['series id'], 
#                       self.qry.race_info['track id'], 
#                       self.qry.race_info['race name'], 
#                       self.qry.race_status['total laps'],
#                       self.qry.race_info['race id']))
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

    def results_to_csv(self, race_id, stage_id, col='0'):  
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
        self.drop_table()
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
            if col[1][0] == lap:
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
        df.to_csv('live race.csv')
