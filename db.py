import sqlite3

class Database:
	
    def __init__(self, WebData):
        self.qry = WebData
        self.qry.open_browser()
        self.qry.get_json()
        self.qry.close_browser()
        self.qry.get_driver_info()
        self.qry.clean_driver_names()
        self.qry.get_race_info()
        self.qry.get_race_status()
		
        # init results database
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS Race_Results ('
                  'driver_id INTEGER,'			# __init__
                  'race_id INTEGER,'				# __init__
                  'qual INTEGER,'					# __init__
                  'pole INTEGER,'       		   # __init__	
                  'stage1 INTEGER,'           # update_results_DB
                  'stage2 INTEGER,'           # update_results_DB
                  'stage3 INTEGER,'           # update_results_DB
                  'finish INTEGER,'           # update_results_DB
                  'laps_led INTEGER,'			   # update_results_DB
                  'win INTEGER,'              # update_results_DB
                  'ineligible INTEGER,'   		# __init__
                  'encumbered INTEGER,' 			# N/A
                  'car_number INTEGER,'			# __init__
                  'manufacturer TEXT,'			# __init__
                  'sponsor TEXT'					# __init__
                  ')')
        # init race database
        c.execute('CREATE TABLE IF NOT EXISTS Races ('
		            'race_id INTEGER NOT NULL UNIQUE,'
		            'series_id INTEGER,'
		            'year INTEGER,'      # Do I need this if 'start_time' has the full date?
                  'start_time INTEGER,'
		            'track_id INTEGER,'
                  'race_name TEXT,'
                  'race_number INTEGER,'
                  'stage_length INTEGER,'
                  'total_laps INTEGER,'
                  'tv TEXT'
		            ')')
        # init track database
        c.execute('CREATE TABLE IF NOT EXISTS Tracks ('
                  'track_id INTEGER NOT NULL UNIQUE,'
                  'track_name TEXT,'
                  'length REAL,'
                  'type TEXT'
                  ')')
        conn.commit()
        
        
        
# Now that this is in its own module, I think this should be its own method
        
        for driver in self.qry.driver_list:
            # Check if row already exists. If not, create it.
            c.execute('SELECT EXISTS(SELECT * FROM Race_Results WHERE driver_id=? AND race_id=?)', 
                      (driver['driver id'], self.qry.race_info['race id']))
            data = c.fetchone()
            if data[0] == 0:
                c.execute('INSERT INTO Race_Results(driver_id, race_id, qual,'
                                                    'pole, ineligible, car_number,'
                                                    'manufacturer, sponsor)'
                                                    'VALUES(?, ?, ?, ?, ?, ?, ?, ?)',
                          (driver['driver id'], self.qry.race_info['race id'], 
                           driver['qual'], driver['pole'],
                           driver['ineligible'], driver['car number'], 
                           driver['manufacturer'], driver['sponsor'])
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
                
        print('Results DB initialized')
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
            # Check for win
            if stage == 0 and driver['position'] == 1:
                win = 1
            else:
                win = None
            c.execute('UPDATE Race_Results SET {}=?, laps_led=?, win=? WHERE driver_id=? AND race_id=?'.format(stages[stage]),
                      (driver['position'], driver['laps led'], win, driver['driver id'], self.qry.race_info['race id']))
            conn.commit()
        print('Results DB updated')
        c.close()
        conn.close()
        
        
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
                print(f"{driver['driver name']} (ID = {driver['driver id']}) was added to the database")
        print('\nDatabase update complete')
        c.close()
        conn.close()
