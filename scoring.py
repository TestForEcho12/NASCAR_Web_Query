import pandas as pd
import sqlite3

class scoring():
    
    def __init__(self, series, year):
        self.series = series
        self.year = year

    def number_of_races(self):
        conn = sqlite3.connect('NASCAR.db')
        df = pd.read_sql_query("""SELECT MAX(race_number) AS races FROM Races 
                               WHERE series_id = ? AND year = ?""",
                               params=(self.series, self.year,),
                               con=conn)
        conn.close()
        self.num_races = int(df['races'][0])

    def points(self, num_races):
        conn = sqlite3.connect('NASCAR.db')    
        df = pd.read_sql_query("""SELECT driver_name, 
                                   Results.race_id, 
                                   Races.race_number, 
                                   Tracks.nickname,
                                   (ifnull(s1.stage, 0) + 
                                    ifnull(s2.stage, 0) + 
                                    ifnull(s3.stage, 0) + 
                                    ifnull(f.finish, 0) -
                                    ifnull(penalty, 0)) AS pts
                               FROM Results
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               JOIN Tracks ON Races.track_id = Tracks.track_id
                               LEFT OUTER JOIN Points AS s1 ON Results.stage1 = s1.position
                               LEFT OUTER JOIN Points AS s2 ON Results.stage2 = s2.position
                               LEFT OUTER JOIN Points AS s3 ON Results.stage3 = s3.position
                               LEFT OUTER JOIN Points AS f ON Results.finish = f.position
                               WHERE series_id = ? AND 
                                     year = ? AND 
                                     Races.race_number <= ? AND
                                     ineligible IS NULL""",
                               params=(self.series, self.year, num_races,),
                               con=conn)
        conn.close()                          

        # Group by Driver and sum points
        self.total = df.groupby('driver_name', as_index=False).sum()
        del self.total['race_id']
        del self.total['race_number']
        self.total = self.total.sort_values('pts', ascending=False)
        self.total = self.total.reset_index(drop=True)
        
        # Add empty column for each race
        race_dict = {}
        races = df['race_id'].unique()
        self.total['Points Behind Leader'] = ''
        self.total['+/- Cutoff'] = ''
        for race in races:
            # return data of first row where race_id = race
            name = df.loc[df['race_id'] == race].iloc[0]['nickname']
            race_num = df.loc[df['race_id'] == race].iloc[0]['race_number']
            race_dict[race] = name
            # Add column if not a Duel
            if race_num > 0:
                self.total[race] = 0
            # Store Daytona race number as 'Daytona'
            if race_num == 1:
                Daytona = race
            
        # Add point values for each race
        for index, row in df.iterrows():
            # If one of the Duels, replace race_number with Daytona race number
            if row['race_number'] == 0:
                row['race_id'] = Daytona
            self.total.loc[self.total['driver_name'] == row['driver_name'], row['race_id']] += row['pts'] 
        
        # Change column headers from race_id to track name
        self.total = self.total.rename(columns = race_dict)
        self.total = self.total.rename(columns = {'pts': 'Total Points',
                                        'driver_name': 'Drivers'})
        self.total = self.total.replace(to_replace=0, value='')
        
        # Points Behind Leader
        self.total.loc[0, 'Points Behind Leader'] = '-'
        leader_pts = self.total.loc[0, 'Total Points']
        for index, row in self.total.iterrows():
            if index > 0:
                self.total.loc[index, 'Points Behind Leader'] = row['Total Points'] - leader_pts
    
        # Add position and delta columns
        cols = self.total.columns.tolist()
        cols = ['Pos', 'delta'] + cols
        self.total['Pos'] = 0
        self.total['delta'] = ''
        self.total = self.total[cols]
        for index, row in self.total.iterrows():
            self.total.loc[index, 'Pos'] = index + 1     
        
    def drivers(self, num_races):
        conn = sqlite3.connect('NASCAR.db')
        df = pd.read_sql_query("""SELECT driver_name FROM Results
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               WHERE series_id = ? AND 
                                     year = ? AND 
                                     Races.race_number <= ?""", 
                               params=(self.series, self.year, num_races,),
                               con=conn)
        self.drivers = df['driver_name'].unique()
        self.eligible_drivers = []
        for driver in self.drivers:
            df = pd.read_sql_query("""SELECT COUNT(Results.race_id) FROM Results
                                           JOIN Drivers ON Results.driver_id = Drivers.driver_id
                                           JOIN Races ON Results.race_id = Races.race_id
                                           WHERE Drivers.driver_name = ? AND 
                                                 Races.series_id = ? AND
                                                 Races.year = ? AND
                                                 ineligible IS NULL AND
                                                 Races.race_number > 0 AND
                                                 Races.race_number <= ?""",
                                    params=(driver, self.series, self.year, num_races,),
                                    con=conn)                                           
            if df['COUNT(Results.race_id)'][0] == num_races:
                self.eligible_drivers.append(driver)
        conn.close()
        
    def winners(self, num_races):
        conn = sqlite3.connect('NASCAR.db')
        df = pd.read_sql_query("""SELECT driver_name, encumbered FROM Results 
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               WHERE series_id = ? AND 
                                     year = ? AND 
                                     Races.race_number <= ? AND
                                     win = 1 
                               """,
                               params=(self.series, self.year, num_races,),
                               con=conn)
        self.winners = df['driver_name'].unique()
        self.num_winners = len(self.winners)
        # Drop encumbered
        unencumbered = df[df.encumbered != 1]['driver_name'].unique()
        
        self.eligible_winners = []
        for winner in unencumbered:
            #Check that driver has run every race
            df = pd.read_sql_query("""SELECT COUNT(Results.race_id) FROM Results
                                           JOIN Drivers ON Results.driver_id = Drivers.driver_id
                                           JOIN Races ON Results.race_id = Races.race_id
                                           WHERE Drivers.driver_name = ? AND 
                                                 Races.series_id = ? AND
                                                 Races.year = ? AND
                                                 Races.race_number <= ? AND
                                                 ineligible IS NULL AND
                                                 Races.race_number > 0""",
                                    params=(winner, self.series, self.year, num_races,),
                                    con=conn)
            print(df['COUNT(Results.race_id)'][0])
            if df['COUNT(Results.race_id)'][0] == num_races:
                self.eligible_winners.append(winner)
        conn.close()
        self.num_eligible_winners = len(self.eligible_winners)
      
    def ties(self):
        tied_points = self.total[self.total.duplicated(subset='Total Points', keep=False)]
        tied_points = tied_points['Total Points'].unique()
        total_copy = self.total.copy()
        for points in tied_points:
            tied_total = self.total.loc[self.total['Total Points'] == points]
            drivers = tied_total['Drivers'].tolist()
            indices = tied_total.index.tolist()
            positions = tied_total['Pos'].tolist()
            pos = min(positions)
            conn = sqlite3.connect('NASCAR.db')
            tie_dict = {}
            for driver in drivers:
                df = pd.read_sql_query("""SELECT driver_name, Races.race_number, finish FROM RESULTS 
                                       JOIN Drivers ON Results.driver_id = Drivers.driver_id
                                       JOIN Races ON Results.race_id = Races.race_id
                                       WHERE Drivers.driver_name = ? AND
                                       Races.series_id = ? AND
                                       Races.year = ? AND
                                       Races.race_number > 0""",
                                       params=(driver, self.series, self.year,),
                                       con=conn)
                finish = df['finish'].tolist()
                finish.sort()
                tie_dict[driver] = finish
            tiebreaker = list(sorted(tie_dict.items(), key=lambda x:x[1]))
            tiebreaker = [i[0] for i in tiebreaker]
            for index, name in zip(indices, tiebreaker):
                self.total.loc[index] = total_copy.loc[total_copy['Drivers'] == name].iloc[0]
                self.total.loc[index, 'Pos'] = 'T-'+str(pos)
            conn.close()

    def playoff_drivers(self):
        drivers = self.total['Drivers'].tolist()
        count = self.num_eligible_winners
        self.playoff_drivers = self.eligible_winners.copy()
        i = 0
        while count < 16:
            driver = drivers[i]
            if driver not in self.eligible_winners and driver in self.eligible_drivers:
                self.playoff_drivers.append(driver)
                count += 1
            i += 1
        while True:
            driver = drivers[i]
            if driver not in self.eligible_winners:
                self.first_out = driver
                self.last_in = drivers[i-1]
                break
            i += 1
            
    def cutoff(self):
        print(self.eligible_winners)
        for index, row in self.total.iterrows():
            driver = row['Drivers']
            if driver not in self.playoff_drivers:
                self.total.loc[index, '+/- Cutoff'] = row['Total Points'] - int(self.total.loc[self.total['Drivers'] == self.last_in]['Total Points'])
            elif driver not in self.eligible_winners:
                self.total.loc[index, '+/- Cutoff'] = row['Total Points'] - int(self.total.loc[self.total['Drivers'] == self.first_out]['Total Points'])
            else:
                self.total.loc[index, '+/- Cutoff'] = '-'
                
    def standings_delta(self, num_races):
        s = scoring(series=self.series, year=self.year)
        race_num = num_races
        last_race_num = race_num - 1
        
        s.points(last_race_num)
        s.ties()
        last_race_order = s.total['Drivers'].tolist()
        last_race_dict = {k:v for v,k in enumerate(last_race_order)}
        
        s.points(race_num)
        s.ties()
        race_order = s.total['Drivers'].tolist()
        race_dict = {k:v for v,k in enumerate(race_order)}
        
        delta_standings = {}
        for key in race_dict:
            if key in last_race_order:
                delta = last_race_dict[key] - race_dict[key]
                if delta > 0:
                    delta = f'+{delta}'
            else:
                delta = ''
            delta_standings[key] = delta


    
    
if __name__ == '__main__':
    
    year = 2018
    series = 2
    
    s = scoring(series=series, year=year)
    s.number_of_races()
    s.standings_delta(s.num_races)
    s.points(s.num_races)
    print(s.total)
    
#    s.points(last_race_num)
#    s.ties()
#    print(s.total)
    
    
#    s.drivers(race_num)
#    s.winners(race_num)
#    s.playoff_drivers()
#    s.cutoff()
#    print(s.total)
    

#    s.total.to_html('HTML\points.html', index=False, border=0)



    
    
