import pandas as pd
import sqlite3



class scoring():
    
    def __init__(self, series, year):
        self.series = series
        self.year = year

    def points(self):
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
                               WHERE series_id = ? AND year = ? AND ineligible IS NULL""",
                               params=(self.series, self.year),
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
            # Store Daytona race number
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
    
#        print(self.total)
        self.total.to_html('HTML\points.html', index=False, border=0)
    
    def number_of_races(self):
        conn = sqlite3.connect('NASCAR.db')
        df = pd.read_sql_query("""SELECT MAX(race_number) AS races FROM Races 
                               WHERE series_id = ? AND year = ?""",
                               params=(self.series, self.year),
                               con=conn)
        conn.close()
        self.num_races = df['races'][0]
        print(f'{self.num_races} races have been run this year.\n')
        
    def get_all_drivers(self):
        conn = sqlite3.connect('NASCAR.db')
        df = pd.read_sql_query("""SELECT driver_name FROM Results
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               WHERE series_id = ? AND year = ?""", 
                               params=(self.series, self.year),
                               con=conn)
        self.all_drivers = df['driver_name'].unique()
        print(self.all_drivers)
        conn.close()
    
    def winners(self):
        conn = sqlite3.connect('NASCAR.db')
        df = pd.read_sql_query("""SELECT driver_name FROM Results 
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               WHERE series_id = ? AND year = ? AND win = 1 
                               """,
                               params=(self.series, self.year),
                               con=conn)
        self.winners = df['driver_name'].unique()
        self.num_winners = len(self.winners)
        self.eligible_winnners = []
        for winner in self.winners:
            #Check that driver has run every race
            df = pd.read_sql_query("""SELECT COUNT(Results.race_id) FROM Results
                                                  JOIN Drivers ON Results.driver_id = Drivers.driver_id
                                                  JOIN Races ON Results.race_id = Races.race_id
                                                  WHERE Drivers.driver_name = ? AND 
                                                  Races.series_id = ? AND
                                                  Races.year = ? AND
                                                  ineligible IS NULL AND
                                                  Races.race_number > 0""",
                                    params=(winner, self.series, self.year,),
                                    con=conn)
            if df['COUNT(Results.race_id)'][0] == self.num_races:
                self.eligible_winnners.append(winner)
        self.num_eligible_winners = len(self.eligible_winnners)
        print(self.num_winners)   
        print(self.winners)
        print(self.num_eligible_winners)
        print(self.eligible_winnners)
        conn.close()
      
    def ties(self):
        tied_points = self.total[self.total.duplicated(subset='Total Points', keep=False)]
        tied_points = tied_points['Total Points'].unique()
        tied_drivers = []
        for points in tied_points:
            tied = self.total.loc[self.total['Total Points'] == points]
            drivers = tied['Drivers'].tolist()
            
            tie = {}
            tie_list = []
            conn = sqlite3.connect('NASCAR.db')
            for driver in drivers:
                df = pd.read_sql_query("""SELECT driver_name, Races.race_number, finish FROM RESULTS 
                                       JOIN Drivers ON Results.driver_id = Drivers.driver_id
                                       JOIN Races ON Results.race_id = Races.race_id
                                       WHERE Drivers.driver_name = ? AND
                                       Races.series_id = ? AND
                                       Races.year = ? AND
                                       Races.race_number > 0""",
                                       params=(driver, self.series, self.year),
                                       con=conn)
                finish = df['finish'].tolist()
                finish.sort()
                tie[driver] = finish
                tie_list.append(finish)

            conn.close()
            #print(tie)
            print(tie_list)
            test = list(zip(*tie_list))
            print(test)
            
            
            
            tied_drivers.append(drivers)
        print(tied_drivers)
    
if __name__ == '__main__':
    
    year = 2018
    series = 2
    
    s = scoring(series=series, year=year)
    s.points()
    s.ties()
#    s.number_of_races()
#    s.winners()

    
    
