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
        self.num_regular_season_races = {1:26, 2:26, 3:16}[series]
        self.num_playoff_drivers = {1:16, 2:12, 3:8}[series]
        
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
        self.points.sort_values('Total Points', ascending=False, inplace=True)
        
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
                                       params=(driver, self.series, self.year),
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

    def playoff_drivers(self, num_races=None):
        if num_races is None:
            num_races = self.num_races
        if num_races > self.num_regular_season_races:
            num_races = self.num_regular_season_races
        
        # Find eligible drivers that have run every race
        points_to_qual = {1:30, 2:30, 3:20}
        top = self.points.iloc[0:points_to_qual[self.series]]['Drivers']
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
        
        # Find winners
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
        
        # Isolate winners who are also playoff eligible
        self.eligible_winners = winners.where(winners.isin(playoff_eligible)).dropna()
        
        remaining = self.num_playoff_drivers - self.eligible_winners.size
        others = playoff_eligible.where(~playoff_eligible.isin(winners)).dropna().reset_index(drop=True)
        self.playoff_drivers = pd.concat([self.eligible_winners, others[:remaining]], ignore_index=True)
        
        self.last_in = others[remaining - 1]
        self.first_out = others[remaining]
        self.cut_line = int(self.points.loc[self.points['Drivers'] == self.last_in].index[0]) + 1
        
    def cutoff(self):
        if not self.num_races > self.num_regular_season_races:
            playoff_drivers = self.playoff_drivers.tolist()
            eligible_winners = self.eligible_winners.tolist()
            for index, row in self.points.iterrows():
                driver = row['Drivers']
                if driver not in playoff_drivers:
                    self.points.loc[index, '+/- Cutoff'] = row['Total Points'] - int(self.points.loc[self.points['Drivers'] == self.last_in]['Total Points'])
                elif driver not in eligible_winners:
                    self.points.loc[index, '+/- Cutoff'] = row['Total Points'] - int(self.points.loc[self.points['Drivers'] == self.first_out]['Total Points'])
                else:
                    self.points.loc[index, '+/- Cutoff'] = '-'
        else:
            self.points.loc[:, '+/- Cutoff'] = '-'

    def calc_playoff_points(self, num_races=None):#, races=None):
        if num_races is None:
            num_races = self.num_races

        conn = sqlite3.connect(self.database)    
        df = pd.read_sql_query("""SELECT driver_name, 
                                   Races.race_number,
                                   (ifnull(s1.playoff_stage, 0) + 
                                    ifnull(s2.playoff_stage, 0) + 
                                    ifnull(s3.playoff_stage, 0) + 
                                    ifnull(f.playoff_finish, 0)) AS pts
                               FROM Results
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               LEFT OUTER JOIN Points AS s1 ON Results.stage1 = s1.position
                               LEFT OUTER JOIN Points AS s2 ON Results.stage2 = s2.position
                               LEFT OUTER JOIN Points AS s3 ON Results.stage3 = s3.position
                               LEFT OUTER JOIN Points AS f ON Results.finish = f.position
                               WHERE series_id = ? AND 
                                     year = ? AND 
                                     Races.race_number BETWEEN 1 AND ? AND
                                     ineligible IS NULL""",
                               params=(self.series, self.year, num_races,),
                               con=conn)
        conn.close()
        
        # Group by driver
        self.playoff_points = df.pivot(index='driver_name', columns='race_number', values='pts')
        cols = self.playoff_points.columns.values.tolist()
    
        # Sum points
        self.playoff_points['Playoff Points'] = self.playoff_points.sum(axis=1)
        
        # Add regular season bonus
        add_bonus = False
        if num_races > self.num_regular_season_races:
            add_bonus = True
        elif num_races == self.num_regular_season_races:
            if self.finish_exists(self.num_regular_season_races):
                add_bonus = True
        if add_bonus:
            bonus = pd.DataFrame({'bonus': [15, 10, 8, 7, 6, 5, 4, 3, 2, 1]}, index=self.points['Drivers'][:10])
            self.playoff_points['Regular Season Bonus'] = 0
            self.playoff_points.loc[bonus.index, 'Regular Season Bonus'] = bonus['bonus']
        else:
            self.playoff_points['Regular Season Bonus'] = 0
        self.playoff_points['Total Playoff Points'] = self.playoff_points['Playoff Points'] + self.playoff_points['Regular Season Bonus']

        # Sort
        self.playoff_points = self.playoff_points.reindex(self.points['Drivers'])
        self.playoff_points.replace(to_replace=0, value=np.NaN, inplace=True)
        self.playoff_points = self.playoff_points.sort_values('Total Playoff Points', ascending=False)
        self.playoff_points.reset_index(inplace=True)
        
        # Update column order
        self.playoff_points['pos'] = self.playoff_points.index + 1
        self.playoff_points['delta'] = np.NaN
        cols = ['pos', 'delta', 'Drivers', 'Total Playoff Points', 'Playoff Points', 'Regular Season Bonus'] + cols
        self.playoff_points = self.playoff_points[cols]
    
    def calc_stats(self, num_races=None, races=None):
        if num_races is None:
            num_races = self.num_races
        if races is None:
            races = self.races
        conn = sqlite3.connect(self.database)    
        df = pd.read_sql_query("""SELECT driver_name, 
                                  Results.race_id,
                                  Results.finish
                               FROM Results
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               WHERE series_id = ? AND 
                                     year = ? AND 
                                     Races.race_number BETWEEN 1 AND ? AND
                                     ineligible IS NULL""",
                               params=(self.series, self.year, num_races,),
                               con=conn)
        # Group by driver
        self.stats = df.pivot(index='driver_name', columns='race_id', values='finish')
        
        # Sort
        self.stats = self.stats.reindex(self.points['Drivers'])
        
        # Stats
        # Playoff Points
        self.stats['playoff points'] = 0
        pp = self.playoff_points[['Drivers', 'Total Playoff Points']].dropna().set_index('Drivers')
        self.stats.loc[pp.index, 'playoff points'] = pp['Total Playoff Points']
        # Wins
        df = pd.read_sql_query("""SELECT driver_name, 
                                  Results.finish
                               FROM Results
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               WHERE series_id = ? AND
                                     year = ? AND
                                     Races.race_number BETWEEN 1 AND ? AND
                                     ineligible IS NULL AND
                                     Results.finish = 1""",
                               params=(self.series, self.year, num_races,),
                               con=conn)                               
        wins = df.groupby('driver_name').sum()
        self.stats['wins'] = 0
        self.stats.loc[wins.index, 'wins'] = wins['finish']
        # Stage Wins
        df = pd.read_sql_query("""SELECT driver_name, 
                                   Results.race_id,
                                   (ifnull(s1.playoff_stage, 0) + 
                                    ifnull(s2.playoff_stage, 0) + 
                                    ifnull(s3.playoff_stage, 0)) AS pts
                               FROM Results
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               LEFT OUTER JOIN Points AS s1 ON Results.stage1 = s1.position
                               LEFT OUTER JOIN Points AS s2 ON Results.stage2 = s2.position
                               LEFT OUTER JOIN Points AS s3 ON Results.stage3 = s3.position
                               WHERE series_id = ? AND 
                                     year = ? AND 
                                     Races.race_number BETWEEN 1 AND ? AND
                                     ineligible IS NULL""",
                               params=(self.series, self.year, num_races,),
                               con=conn)
        stages = df.groupby('driver_name').sum()
        self.stats['stage wins'] = 0
        self.stats.loc[stages.index, 'stage wins'] = stages['pts']
        # Poles
        df = pd.read_sql_query("""SELECT driver_name, 
                                  Results.qual
                               FROM Results
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               WHERE series_id = ? AND
                                     year = ? AND
                                     Races.race_number BETWEEN 1 AND ? AND
                                     ineligible IS NULL AND
                                     Results.qual = 1""",
                               params=(self.series, self.year, num_races,),
                               con=conn)                               
        poles = df.groupby('driver_name').sum()
        self.stats['poles'] = 0
        self.stats.loc[poles.index, 'poles'] = poles['qual']
        # Average Finish
        df = pd.read_sql_query("""SELECT driver_name, 
                                  Results.finish
                               FROM Results
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               WHERE series_id = ? AND
                                     year = ? AND
                                     Races.race_number BETWEEN 1 AND ? AND
                                     ineligible IS NULL""",
                               params=(self.series, self.year, num_races,),
                               con=conn)     
        avg = df.groupby('driver_name').mean().round(1)
        self.stats['average'] = 0
        self.stats.loc[avg.index, 'average'] = avg['finish']
        # Top5
        df = pd.read_sql_query("""SELECT driver_name, 
                                  Results.finish
                               FROM Results
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               WHERE series_id = ? AND
                                     year = ? AND
                                     Races.race_number BETWEEN 1 AND ? AND
                                     ineligible IS NULL AND
                                     Results.finish <= 5""",
                               params=(self.series, self.year, num_races,),
                               con=conn)                               
        top5 = df.groupby('driver_name').count()
        self.stats['top 5'] = 0
        self.stats.loc[top5.index, 'top 5'] = top5['finish']
        # Laps Lead
        df = pd.read_sql_query("""SELECT driver_name, 
                                  Results.laps_led
                               FROM Results
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               WHERE series_id = ? AND
                                     year = ? AND
                                     Races.race_number BETWEEN 1 AND ? AND
                                     ineligible IS NULL""",
                               params=(self.series, self.year, num_races,),
                               con=conn)     
        laps = df.groupby('driver_name').sum()
        self.stats['laps'] = 0
        self.stats.loc[laps.index, 'laps'] = laps['laps_led']
        conn.close()
        
        # Points
        self.stats.reset_index(inplace=True)
        self.stats['pos'] = self.points['pos']
        self.stats['delta'] = self.points['delta']
        self.stats['points'] = self.points['Total Points']
        self.stats.replace(to_replace=0, value=np.NaN, inplace=True)

        # Update column order
        cols = races[races['race_number'] > 0].sort_values('race_number').index.tolist()
        cols = ['pos', 'delta', 'Drivers', 'points', 'playoff points', 'wins', 'stage wins', 'poles', 'average', 'top 5', 'laps'] + cols
        self.stats = self.stats[cols]

    def calc_playoffs(self):
        rounds = {1:3, 2:2, 3:2}[self.series]
        drivers_eliminated = {1:4, 2:4, 3:2}[self.series]
        races_per_round = 3
        
        if self.num_races < self.num_regular_season_races:
            return

        conn = sqlite3.connect(self.database)   
        df = pd.read_sql_query("""SELECT driver_name, 
                                   Races.race_number, 
                                   (ifnull(s1.stage, 0) + 
                                    ifnull(s2.stage, 0) + 
                                    ifnull(f.finish, 0) -
                                    ifnull(penalty, 0)) AS pts
                               FROM Results
                               JOIN Drivers ON Results.driver_id = Drivers.driver_id
                               JOIN Races ON Results.race_id = Races.race_id
                               LEFT OUTER JOIN Points AS s1 ON Results.stage1 = s1.position
                               LEFT OUTER JOIN Points AS s2 ON Results.stage2 = s2.position
                               LEFT OUTER JOIN Points AS f ON Results.finish = f.position
                               WHERE series_id = ? AND 
                                     year = ? AND 
                                     Races.race_number > ? AND
                                     ineligible IS NULL""",
                               params=(self.series, self.year, self.num_regular_season_races),
                               con=conn)
        conn.close()
        # Group by driver
        self.playoffs = df.pivot(index='driver_name', columns='race_number', values='pts')
        self.playoffs = self.playoffs[self.playoffs.index.isin(self.playoff_drivers)]

        self.num_races = 32
        # Find where we are in the playoffs
        current_round = 0
        for i in range(1, rounds + 1):
            last_race_of_round = self.num_regular_season_races + i*races_per_round
            if self.num_races < last_race_of_round + 1:
                current_round = i
                if self.num_races == last_race_of_round:
                    end_of_round = self.finish_exists(self.num_races)
                else:
                    end_of_round = False
                break
        if current_round == 0:
            end_of_round = self.finish_exists(self.num_races)
            current_round = rounds
            finale = True
        else:
            finale = False
        
        self.playoffs['playoff points'] = 0
        for i in range(current_round):
            remaining_drivers = self.playoffs.head(self.num_playoff_drivers - i*drivers_eliminated).index
            pp = self.playoff_points[self.playoff_points['Drivers'].isin(remaining_drivers)]
            pp.set_index('Drivers', inplace=True)
            pp.drop(['pos', 'delta', 'Total Playoff Points', 'Playoff Points'], axis=1, inplace=True)
            races = self.num_regular_season_races + i*races_per_round + 1 # +1 for reg season bonus
            pp = pp.iloc[:, :races]
            pp['Total Playoff Points'] = pp.sum(axis=1)
            
            self.playoffs['playoff points'] = pp.loc[remaining_drivers]['Total Playoff Points']
            start = i*races_per_round
            end = (i+1)*races_per_round
            points = self.playoffs.iloc[:, start:end]
            self.playoffs['points'] = 2000 + i*1000 + points.sum(axis=1)
            self.playoffs['total points'] = self.playoffs['points'] + self.playoffs['playoff points']
            self.playoffs.sort_values('total points', ascending=False, inplace=True)

                
        return self.playoffs




    def finish_exists(self, race_num):
            conn = sqlite3.connect(self.database)
            c = conn.cursor()
            c.execute("""SELECT EXISTS(SELECT finish FROM Results 
                         JOIN Races ON Results.race_id = Races.race_id
                         WHERE series_id = ? AND
                         year = ? AND
                         race_number = ?)""",
                        (self.series, self.year, race_num))
            exists = bool(c.fetchone()[0])
            c.close()
            conn.close()
            return exists

    def export_points(self):
        self.points.to_csv('tables/points.csv',
                           header=False,
                           index=False)
        self.playoff_points.to_csv('tables/playoff points.csv',
                                   header=False,
                                   index=False)
        self.stats.to_csv('tables/stats.csv',
                          header=False,
                          index=False)
        # Points Data
        with open('tables/data.txt', 'w') as writer:
            winners = self.eligible_winners.tolist()
            if winners:
                s = ''
                for driver in winners:
                    s += driver + ','
                s = s[:-1] + '\n'
                writer.write(s)
            else:
                writer.write('None\n')
            writer.write(str(self.cut_line))











if __name__ == '__main__':
    now = dt.now()
    
    year = 2018
    series = 1
    
    p = Points(series=series, year=year)
    p.get_races()   
    p.calc_points()
    p.ties()
    p.last_race_order()
    p.points_delta()
    p.playoff_drivers()
    p.cutoff()
    p.calc_playoff_points()
    p.calc_stats()
    
    a = p.calc_playoffs()

    
    p.export_points()
    print(dt.now() - now)



