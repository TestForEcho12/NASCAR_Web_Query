import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime as dt

pd.options.mode.chained_assignment = None

class Points():
    
    def __init__(self, series, year):
        self.series = series
        self.year = year
        self.database = 'NASCAR.db'
        
    def get_races(self):
        conn = sqlite3.connect(self.database)
        df = pd.read_sql_query("""SELECT race_id, Races.track_id, race_number, Tracks.nickname FROM Races
                                       JOIN Tracks ON Races.track_id = Tracks.track_id
                                       WHERE series_id = ? AND
                                           year = ? AND
                                           race_number IS NOT NULL""",
                               params=(self.series, self.year),
                               con=conn)
        conn.close()
        self.races = df.set_index('race_id')
        self.num_races = int(self.races['race_number'].max())

    def calc_points(self, num_races=None, races=None):
        if num_races is None:
            num_races = self.num_races
        if races is None:
            races = self.races
        conn = sqlite3.connect(self.database)    
        df = pd.read_sql_query("""SELECT driver_name, 
                                   Results.race_id, 
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
                               LEFT OUTER JOIN Points AS s1 ON Results.stage1 = s1.position
                               LEFT OUTER JOIN Points AS s2 ON Results.stage2 = s2.position
                               LEFT OUTER JOIN Points AS s3 ON Results.stage3 = s3.position
                               LEFT OUTER JOIN Points AS f ON Results.finish = f.position
                               WHERE series_id = ? AND 
                                     year = ? AND 
                                     Races.race_number <= ? AND
                                     ineligible IS NULL""",
                               params=(self.series, self.year, num_races),
                               con=conn)
        conn.close()

        # Group by driver
        self.points = df.pivot(index='driver_name', columns='race_id', values='pts')
        
        # Sum points
        self.points['Total Points'] = self.points.sum(axis=1)
        self.points = self.points.sort_values('Total Points', ascending=False)
        
        # Combine Daytona races
        if self.series == 1:
            daytona = races[races['race_number'] == 1].index.item()
            r = races[races['race_number'] < 2].index
            self.points[daytona] = self.points[r].sum(axis=1)
            delete = races[races['race_number'] < 1].index
            self.points.drop(delete, axis=1, inplace=True)
            
        # Replace any zero values with nan
        self.points.replace(to_replace=0, value=np.NaN, inplace=True)
        
        # Change index from driver to int
        self.points.reset_index(inplace=True)
        self.points.rename(columns={'driver_name': 'Drivers'}, inplace=True)
        
        # Add 'points behind leader' and '+/- cutoff'
        self.points['Points Behind Leader'] = np.NaN
        self.points['+/- Cutoff'] = np.NaN
        leader_pts = self.points.loc[0, 'Total Points']
        self.points['Points Behind Leader'] = self.points['Total Points'] - leader_pts
        self.points.loc[0, 'Points Behind Leader'] = '-'
        
        # Add position and delta columns
        self.points['pos'] = self.points.index + 1
        self.points['delta'] = np.NaN
        
        # Update column order
        cols = races[races['race_number'] > 0].sort_values('race_number').index.tolist()
        cols = ['pos', 'delta', 'Drivers', 'Total Points', 'Points Behind Leader', '+/- Cutoff'] + cols
        self.points = self.points[cols]
      
    def ties(self):
        tied_points = self.points[self.points.duplicated(subset='Total Points', keep=False)]
        tied_points = tied_points['Total Points'].unique()
        points_copy = self.points.copy()
        for points in tied_points:
            tied_total = self.points.loc[self.points['Total Points'] == points]
            drivers = tied_total['Drivers'].tolist()
            indices = tied_total.index.tolist()
            positions = tied_total['pos'].tolist()
            pos = min(positions)
            conn = sqlite3.connect(self.database)
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
                self.points.loc[index] = points_copy.loc[points_copy['Drivers'] == name].iloc[0]
                self.points.loc[index, 'pos'] = 'T-'+str(pos)
            conn.close()
            
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
        s = Points(series=self.series, year=self.year)
        last_race_num = self.num_races - 1
        races = self.races.drop(self.races[self.races['race_number'] == self.num_races].index)
        s.calc_points(last_race_num, races)
        s.ties()       
        self.last_race = s.points
    
    def points_delta(self):
        points = self.points.copy()        
        last_race = self.last_race.copy()
        
        last_race = last_race.merge(points, how='outer', on='Drivers')

        points['pos'] = points.index + 1
        points = points.set_index('Drivers')
        last_race['pos'] = last_race.index + 1
        last_race = last_race.set_index('Drivers')        
        
        last_race['delta'] = last_race['pos'] - points['pos']
        last_race['delta'].replace(to_replace=0, value=np.NaN, inplace=True)
        last_race = last_race.reindex(self.points['Drivers'])
        self.points['delta'] = np.array(last_race['delta'])

    def drivers(self):
        conn = sqlite3.connect(self.database)
        # Select all drivers that have run the given series and year
        df = pd.read_sql_query("""SELECT driver_name FROM Results
                                       JOIN Drivers ON Results.driver_id = Drivers.driver_id
                                       JOIN Races ON Results.race_id = Races.race_id
                                       WHERE series_id = ? AND 
                                           year = ? AND 
                                           Races.race_number <= ?""", 
                               params=(self.series, self.year, self.num_races,),
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
                                    params=(driver, self.series, self.year, self.num_races,),
                                    con=conn)                                           
            if df['COUNT(Results.race_id)'][0] == self.num_races:
                self.eligible_drivers.append(driver)
        conn.close()
        
    def winners(self):
        conn = sqlite3.connect(self.database)
        df = pd.read_sql_query("""SELECT driver_name, encumbered FROM Results 
                                       JOIN Drivers ON Results.driver_id = Drivers.driver_id
                                       JOIN Races ON Results.race_id = Races.race_id
                                           WHERE series_id = ? AND 
                                           year = ? AND 
                                           Races.race_number BETWEEN 1 AND ? AND
                                           win = 1 """,
                               params=(self.series, self.year, self.num_races,),
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
                                    params=(winner, self.series, self.year, self.num_races,),
                                    con=conn)
            if df['COUNT(Results.race_id)'][0] == self.num_races:
                self.eligible_winners.append(winner)
        conn.close()
        self.num_eligible_winners = len(self.eligible_winners)
        
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

    def playoff_drivers2(self, num_races=None):
        if num_races is None:
            num_races = self.num_races
        if num_races > 26:
            num_races = 26
        top = self.points.iloc[0:30]['Drivers']
        conn = sqlite3.connect(self.database)    
        df = pd.read_sql_query("""SELECT driver_name
                               FROM Results
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               WHERE series_id = ? AND 
                                     year = ? AND 
                                     Races.race_number BETWEEN 1 AND ?""",
                               params=(self.series, self.year, num_races),
                               con=conn)
        df = df.groupby('driver_name').size()
        run_all = df.where(df==num_races).dropna().index.tolist()
        playoff_eligible = top.where(top.isin(run_all)).dropna()
        
        df = pd.read_sql_query("""SELECT driver_name
                               FROM Results
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               WHERE series_id = ? AND 
                                     year = ? AND 
                                     Races.race_number BETWEEN 1 AND ? AND
                                     win = 1""",
                               params=(self.series, self.year, num_races),
                               con=conn)
        conn.close()
        winners = pd.Series(df['driver_name'].unique())
        winners = winners.where(winners.isin(playoff_eligible).dropna())
        return winners
    '''
    * playoff eligible drivers
        - not labled ineligible
        - run every race
        - in top 30
        
        - make 2 lists, top 30 from self.points and run_every_race
        - have to be in both lists
            
    * regular season winners that are eligible
        - Find all winners
        - Are winners playoff_eligible
        
    * playoff drivers
    '''

            
    def penalties(self):
        '''This method is currently building a dataframe self.penalty that copies
        self.points but makes every value a bool for if the driver has a penalty
        in that race. 
        
        Simply returning a list of the penalties seems easier'''
        
        conn = sqlite3.connect('NASCAR.db')
        # Select all drivers that have run the given series and year with a penalty
        df = pd.read_sql_query("""SELECT driver_name, Results.race_id FROM Results
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               WHERE series_id = ? AND 
                                     year = ? AND 
                                     Races.race_number <= ? AND
                                     penalty IS NOT NULL""", 
                               params=(self.series, self.year, self.num_races,),
                               con=conn)
        conn.close()
        self.penalty = self.points
        self.penalty = self.penalty.drop(['pos', 'delta', 'Total Points', 'Points Behind Leader', '+/- Cutoff'], axis=1)
        self.penalty.loc[:, self.penalty.columns != 'Drivers'] = 0
        for index, row in df.iterrows():
            self.penalty.loc[self.penalty['Drivers'] == row['driver_name'], row['race_id']] = 1
            
    def export_points(self):
        self.points.to_csv('tables/points.csv')
        with open('tables/data.txt', 'w') as writer:
            for driver in self.eligible_winners:
                writer.write(driver + ',')

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
        return df


if __name__ == '__main__':

    year = 2019
    series = 1
    
    p = Points(series=series, year=year)
    p.get_races()
    p.calc_points()
    p.drivers()
    p.winners()
    p.ties()
    p.playoff_drivers()
    p.cutoff()
    p.last_race_order()
    p.points_delta()
#    p.penalties()
    
    now = dt.now()
    b = p.playoff_drivers2()
    print(dt.now() - now)

    a = p.points

    

#    p.export_points()



