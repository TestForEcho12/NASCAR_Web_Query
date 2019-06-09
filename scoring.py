import pandas as pd
import sqlite3
from jinja2 import Environment, FileSystemLoader
from selenium import webdriver

pd.options.display.html.border = 0
pd.options.mode.chained_assignment = None

class points():
    
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
        num_races = {1:36, 2:33, 3:23}
        self.total_num_races = num_races[self.series]
        self.num_races_left = num_races[self.series] - self.num_races
        
    def drivers(self, num_races):
        conn = sqlite3.connect('NASCAR.db')
        # Select all drivers that have run the given series and year
        df = pd.read_sql_query("""SELECT driver_name FROM Results
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               WHERE series_id = ? AND 
                                     year = ? AND 
                                     Races.race_number <= ?""", 
                               params=(self.series, self.year, num_races,),
                               con=conn)
        self.all_drivers = df['driver_name'].unique()
        self.eligible_drivers = []
        for driver in self.all_drivers:
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
                                     Races.race_number BETWEEN 1 AND ? AND
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
            if df['COUNT(Results.race_id)'][0] == num_races:
                self.eligible_winners.append(winner)
        conn.close()
        self.num_eligible_winners = len(self.eligible_winners)

    def calc_points(self, num_races):
        conn = sqlite3.connect('NASCAR.db')    
        df = pd.read_sql_query("""SELECT driver_name, 
                                   Results.race_id, 
                                   Races.race_number, 
                                   Tracks.nickname,
                                   (ifnull(s1.stage, 0) + 
                                    ifnull(s2.stage, 0) + 
                                    ifnull(s3.stage, 0) + 
                                    (CASE
                                        WHEN Races.race_number = 0 THEN
                                            ifnull(f.stage, 0)
                                        ELSE
                                            ifnull(f.finish, 0)
                                    END) -
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
        self.points = df.groupby('driver_name', as_index=False).sum() 
        del self.points['race_id']
        del self.points['race_number']
        self.points = self.points.sort_values('pts', ascending=False)
        self.points = self.points.reset_index(drop=True)
        
        # Add empty column for each race
        self.race_dict = {}
        races = df['race_id'].unique()
        self.points['Points Behind Leader'] = ''
        self.points['+/- Cutoff'] = ''
        for race in races:
            # return data of first row where race_id = race
            name = df.loc[df['race_id'] == race].iloc[0]['nickname']
            race_num = df.loc[df['race_id'] == race].iloc[0]['race_number']
            self.race_dict[race] = name
            # Add column if not a Duel
            if race_num > 0:
                self.points[race] = 0
            # Store Daytona race number as 'Daytona'
            if race_num == 1:
                Daytona = race
            
        # Add point values for each race
        for index, row in df.iterrows():
            # If one of the Duels, replace race_number with Daytona race number
            if row['race_number'] == 0:
                row['race_id'] = Daytona
            self.points.loc[self.points['driver_name'] == row['driver_name'], row['race_id']] += row['pts'] 
        
        # Rename column headers. Races are renamed from id to track name after 
        # ties() to avoid errors resulting from duplicate column names
        self.points = self.points.rename(columns = {'pts': 'Total Points',
                                        'driver_name': 'Drivers'})
        self.points = self.points.replace(to_replace=0, value='')
        
        # Points Behind Leader
        self.points.loc[0, 'Points Behind Leader'] = '-'
        leader_pts = self.points.loc[0, 'Total Points']
        for index, row in self.points.iterrows():
            if index > 0:
                self.points.loc[index, 'Points Behind Leader'] = row['Total Points'] - leader_pts
    
        # Add position and delta columns
        cols = self.points.columns.tolist()
        cols = ['Pos', 'delta'] + cols
        self.points['Pos'] = 0
        self.points['delta'] = ''
        self.points = self.points[cols]
        for index, row in self.points.iterrows():
            self.points.loc[index, 'Pos'] = index + 1
      
    def ties(self):
        tied_points = self.points[self.points.duplicated(subset='Total Points', keep=False)]
        tied_points = tied_points['Total Points'].unique()
        total_copy = self.points.copy()
        for points in tied_points:
            tied_total = self.points.loc[self.points['Total Points'] == points]
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
                self.points.loc[index] = total_copy.loc[total_copy['Drivers'] == name].iloc[0]
                self.points.loc[index, 'Pos'] = 'T-'+str(pos)
            conn.close()
        # Rename race_ids with track names. Errors occur if this is done before
        # ties since there will be columns with duplicate names
        self.points = self.points.rename(columns = self.race_dict)
        
    def playoff_drivers(self):
        drivers = self.points['Drivers'].tolist()
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
        self.cut_line = i
            
    def cutoff(self):
        if not self.num_races > 26:
            for index, row in self.points.iterrows():
                driver = row['Drivers']
                if driver not in self.playoff_drivers:
                    self.points.loc[index, '+/- Cutoff'] = row['Total Points'] - int(self.points.loc[self.points['Drivers'] == self.last_in]['Total Points'])
                elif driver not in self.eligible_winners:
                    self.points.loc[index, '+/- Cutoff'] = row['Total Points'] - int(self.points.loc[self.points['Drivers'] == self.first_out]['Total Points'])
                else:
                    self.points.loc[index, '+/- Cutoff'] = '-'
        else:
            self.points.loc[:, '+/- Cutoff'] = '-'
                
    def last_race_order(self):
        s = points(series=self.series, year=self.year)
        race_num = self.num_races
        last_race_num = race_num - 1
        
        s.calc_points(last_race_num)
        s.ties()
        last_race_order = s.points['Drivers'].tolist()
        self.last_race_dict = {k:v for v,k in enumerate(last_race_order)}
        
    def points_delta(self):
        race_order = self.points['Drivers'].tolist()
        race_dict = {k:v for v,k in enumerate(race_order)}
        
        for key in race_dict:
            if key in self.last_race_dict:
                delta = self.last_race_dict[key] - race_dict[key]
                if delta > 0:
                    delta = f'+{delta}'
                elif delta < 0:
                    delta = f'{delta}'
                else:
                    delta = ''
                self.points.loc[self.points['Drivers'] == key, 'delta'] = delta
                
    def penalties(self, num_races):
        conn = sqlite3.connect('NASCAR.db')
        # Select all drivers that have run the given series and year with a penalty
        df = pd.read_sql_query("""SELECT driver_name, Results.race_id FROM Results
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               WHERE series_id = ? AND 
                                     year = ? AND 
                                     Races.race_number <= ? AND
                                     penalty IS NOT NULL""", 
                               params=(self.series, self.year, num_races,),
                               con=conn)
        conn.close()
        self.penalty = self.points
        self.penalty = self.penalty.drop(['Pos', 'delta', 'Total Points', 'Points Behind Leader', '+/- Cutoff'], axis=1)
        self.penalty.loc[:, self.penalty.columns != 'Drivers'] = 0
        for index, row in df.iterrows():
            self.penalty.loc[self.penalty['Drivers'] == row['driver_name'], row['race_id']] = 1

    def calc_playoff_points(self, num_races):
        conn = sqlite3.connect('NASCAR.db')    
        df = pd.read_sql_query("""SELECT driver_name, 
                                   Results.race_id, 
                                   Races.race_number, 
                                   Tracks.nickname,
                                   (ifnull(s1.playoff_stage, 0) + 
                                    ifnull(s2.playoff_stage, 0) + 
                                    ifnull(s3.playoff_stage, 0) + 
                                    ifnull(f.playoff_finish, 0)) AS pts
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


if __name__ == '__main__':
    
    year = 2019
    series = 1
    
    p = points(series=series, year=year)
    p.number_of_races()
    p.calc_points(p.num_races)
    p.drivers(p.num_races)
    p.winners(p.num_races)
    p.ties()
    p.playoff_drivers()
    p.cutoff()
    p.last_race_order()
    p.points_delta()
    p.penalties(p.num_races)
    
    a = p.points
    p.points.to_csv('tables/test.csv')
    
    
    
#    env = Environment(loader=FileSystemLoader('HTML'))
#    template = env.get_template('Points.html')
#    f = open('HTML/Points_Output.html','w')
#    f.write(template.render(drivers=p.total[['Pos', 'delta', 'Drivers']].head(40),
#                            sums=p.total[['Total Points', 'Points Behind Leader', '+/- Cutoff']].head(40),
#                            points=p.total.drop(columns=['Pos', 'delta', 'Drivers', 'Total Points', 'Points Behind Leader', '+/- Cutoff']).head(40),
#                            total_num_races=p.total_num_races,
#                            num_races_left=p.num_races_left,
#                            winners=p.eligible_winners,
#                            penalties=p.penalty,
#                            cut_line=p.cut_line - 1,))
#    f.close()
#
#    a = p.penalty
#
#    
#    chrome_ops = webdriver.ChromeOptions()
##    chrome_ops.add_argument('headless')
#    
#    browser = webdriver.Chrome(chrome_options=chrome_ops)
#    browser.get('file:///G:/Greg/Python/NASCAR/HTML/Points_Output.html')
#    
#    browser.set_window_size(1950, 997) #width, height
#    browser.save_screenshot('HTML/test2.png')
##    browser.quit()





    
    
