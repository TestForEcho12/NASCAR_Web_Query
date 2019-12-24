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
        self.total_num_races = {1:36, 2:33, 3:23}[series]
        
    def get_races(self, race_num=100):
        conn = sqlite3.connect(self.database)
        df = pd.read_sql_query("""SELECT race_id, Races.track_id, race_number, Tracks.nickname FROM Races
                                   JOIN Tracks ON Races.track_id = Tracks.track_id
                                   WHERE series_id = ? AND
                                       year = ? AND
                                       race_number BETWEEN 0 AND ?""",
                           params=(self.series, self.year, race_num),
                           con=conn)
        conn.close()
        if race_num < 1:
            self.races = None
            self.num_races = 0
        else:
            self.races = df.set_index('race_id')
            self.num_races = int(self.races['race_number'].max())

    def calc_points(self, num_races=None):
        if num_races is None:
            num_races = self.num_races
        if num_races == 0:
            self.points = None
            return
        
        conn = sqlite3.connect(self.database)    
        df = pd.read_sql_query("""SELECT driver_name, 
                                   Races.race_number, 
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
        self.points = df.pivot(index='driver_name', columns='race_number', values='pts')
        
        # Combine Daytona races
        if self.series == 1:
            self.points[1] = self.points[[0, 1]].sum(axis=1)
            self.points.drop(0, axis=1, inplace=True)
            
        # Sum points
        cols = self.points.columns.values.tolist()
        self.points['Total Points'] = self.points.sum(axis=1)
        self.points.sort_values('Total Points', ascending=False, inplace=True)
            
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
        cols = ['pos', 'delta', 'Drivers', 'Total Points', 'Points Behind Leader', '+/- Cutoff'] + cols
        self.points = self.points[cols]
      
    def ties(self):
        if self.points is None:
            return
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
    
    def points_delta(self, last=None):
        if last is None:
            self.points['delta'] = np.NaN
        else:
            points = self.points.copy()        
            last_race = last.points.copy()
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
        # Set num_races = to num regular season races
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

    def calc_playoff_points(self, reg_season=None, num_races=None):
        if num_races is None:
            num_races = self.num_races
            pts = self.points
        elif num_races == self.num_races - 1:
            pts = self.last_race_points
        else:
            s = Points(series=self.series, year=self.year)
            s.calc_points(num_races)
            s.ties()
            pts = s.points
        if num_races == 0:
            return

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
        if not reg_season:
            add_bonus = False
                
        if add_bonus:
            bonus = pd.DataFrame({'bonus': [15, 10, 8, 7, 6, 5, 4, 3, 2, 1]}, index=reg_season.points['Drivers'][:10])
            self.playoff_points['Regular Season Bonus'] = 0
            self.playoff_points.loc[bonus.index, 'Regular Season Bonus'] = bonus['bonus']
        else:
            self.playoff_points['Regular Season Bonus'] = 0
        self.playoff_points['Total Playoff Points'] = self.playoff_points['Playoff Points'] + self.playoff_points['Regular Season Bonus']
        
        # Sort
        self.playoff_points = self.playoff_points.reindex(pts['Drivers'])
        self.playoff_points.replace(to_replace=0, value=np.NaN, inplace=True)
        self.playoff_points = self.playoff_points.sort_values('Total Playoff Points', ascending=False)
        self.playoff_points.reset_index(inplace=True)
        
        # Drop all drivers with zero playoff points
        self.playoff_points = self.playoff_points.loc[self.playoff_points['Total Playoff Points'] > 0]

        # Update column order
        self.playoff_points['pos'] = self.playoff_points.index + 1
        self.playoff_points['delta'] = np.NaN
        cols = ['pos', 'delta', 'Drivers', 'Total Playoff Points', 'Playoff Points', 'Regular Season Bonus'] + cols
        self.playoff_points = self.playoff_points[cols]
        
    def playoff_points_ties(self):
        tied_points = self.playoff_points[self.playoff_points.duplicated(subset='Total Playoff Points', keep=False)]
        tied_points = tied_points['Total Playoff Points'].unique()
        pp_copy = self.playoff_points.copy()
        for points in tied_points:
            tied_total = self.playoff_points.loc[self.playoff_points['Total Playoff Points'] == points]
            drivers = tied_total['Drivers'].tolist()
            indices = tied_total.index.tolist()
            positions = tied_total['pos'].tolist()
            pos = min(positions)
            tie_dict = {}
            for driver in drivers:
                pts_pos = self.points[self.points['Drivers'] == driver].index[0]
                tie_dict[driver] = pts_pos
            tiebreaker = list(sorted(tie_dict.items(), key=lambda x:x[1]))
            tiebreaker = [i[0] for i in tiebreaker]
            for index, name in zip(indices, tiebreaker):
                self.playoff_points.loc[index] = pp_copy.loc[pp_copy['Drivers'] == name].iloc[0]
                self.playoff_points.loc[index, 'pos'] = 'T-'+str(pos)   
        
    def playoff_points_delta(self, last=None):
        if last is None:
            self.playoff_points['delta'] = np.NaN
        else:
            playoff_points = self.playoff_points.copy()        
            last_race = last.playoff_points.copy()
            new_drivers = np.setdiff1d(playoff_points['Drivers'], last_race['Drivers'])
            last_race = last_race.merge(playoff_points, how='outer', on='Drivers')
    
            playoff_points['pos'] = playoff_points.index + 1
            playoff_points = playoff_points.set_index('Drivers')
            last_race['pos'] = last_race.index + 1
            last_race = last_race.set_index('Drivers')        
            
            last_race['delta'] = last_race['pos'] - playoff_points['pos']
            last_race['delta'].replace(to_replace=0, value=np.NaN, inplace=True)
            last_race = last_race.reindex(self.playoff_points['Drivers'])
            self.playoff_points['delta'] = np.array(last_race['delta'])
            self.playoff_points.loc[self.playoff_points['Drivers'].isin(new_drivers), 'delta'] = 'New'
    
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
        cols = self.playoffs.columns.tolist()

        # Find where we are in the playoffs
        current_round = 0
        for i in range(1, rounds + 1):
            last_race_of_round = self.num_regular_season_races + i*races_per_round
            if self.num_races < last_race_of_round + 1:
                current_round = i
                race_in_round = races_per_round - (last_race_of_round - self.num_races)
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
            remaining_drivers = self.playoffs.head(self.num_playoff_drivers - i*drivers_eliminated).index.to_series().rename('Drivers')
            num_remaining_drivers = remaining_drivers.size

            # Get remaining drivers's playoff points
            pp = self.playoff_points[self.playoff_points['Drivers'].isin(remaining_drivers)]
            pp = pp.merge(remaining_drivers, how='outer', on='Drivers')
            pp.set_index('Drivers', inplace=True)
            # Drop everything except regular season, previous rounds, and bonus
            pp.drop(['pos', 'delta', 'Total Playoff Points', 'Playoff Points'], axis=1, inplace=True)
            races = self.num_regular_season_races + i*races_per_round + 1 # +1 for reg season bonus
            pp = pp.iloc[:, :races]
            # Calculate playoff points for this round
            pp['Total Playoff Points'] = pp.sum(axis=1)
            # Update playoff points for remaining drivers
            self.playoffs['playoff points'].iloc[:num_remaining_drivers] = pp.loc[remaining_drivers]['Total Playoff Points']
            # Sum points for round
            start = i*races_per_round
            end = race_in_round
            points = self.playoffs.iloc[:num_remaining_drivers, start:end]
            if 'points' not in self.playoffs.columns:
                self.playoffs['points'] = np.NaN
            self.playoffs['points'].iloc[:num_remaining_drivers] = 2000 + i*1000 + points.sum(axis=1)
            # Sum total points
            self.playoffs['total points'] = self.playoffs['points'] + self.playoffs['playoff points']
            self.playoffs.sort_values('total points', ascending=False, inplace=True)

            if end_of_round and i+1 == current_round:
                # Reset points to X000
                num_remaining_drivers -= drivers_eliminated
                self.playoffs['points'].iloc[:num_remaining_drivers] = 2000 + (i+1)*1000
                
                # Update playoff points to include last round
                remaining_drivers = self.playoffs.head(self.num_playoff_drivers - (i+1)*drivers_eliminated).index
                num_remaining_drivers = remaining_drivers.size
                # Get remaining drivers's playoff points
                pp = self.playoff_points[self.playoff_points['Drivers'].isin(remaining_drivers)]
                pp.set_index('Drivers', inplace=True)
                # Drop everything except regular season, previous rounds, and bonus
                pp.drop(['pos', 'delta', 'Total Playoff Points', 'Playoff Points'], axis=1, inplace=True)
                races = self.num_regular_season_races + (i+1)*races_per_round + 1 # +1 for reg season bonus
                pp = pp.iloc[:, :races]
                # Calculate playoff points for this round
                pp['Total Playoff Points'] = pp.sum(axis=1)
                # Update playoff points for remaining drivers
                self.playoffs['playoff points'].iloc[:num_remaining_drivers] = pp.loc[remaining_drivers]['Total Playoff Points']
                
                if current_round != rounds:
                    # Sum total points
                    self.playoffs['total points'] = self.playoffs['points'] + self.playoffs['playoff points']
                    self.playoffs.sort_values('total points', ascending=False, inplace=True)
                else:
                    self.playoffs['total points'].iloc[:num_remaining_drivers] = self.playoffs['points'].iloc[:num_remaining_drivers]
        # Finale
        if finale and end_of_round:
            conn = sqlite3.connect(self.database)   
            df = pd.read_sql_query("""SELECT driver_name, 
                                       Races.race_number, 
                                        ifnull(f.finish, 0) AS pts
                                   FROM Results
                                   JOIN Drivers ON Results.driver_id = Drivers.driver_id
                                   JOIN Races ON Results.race_id = Races.race_id
                                   LEFT OUTER JOIN Points AS f ON Results.finish = f.position
                                   WHERE series_id = ? AND 
                                         year = ? AND 
                                         Races.race_number = ? AND
                                         ineligible IS NULL""",
                                   params=(self.series, self.year, self.total_num_races),
                                   con=conn)
            conn.close()
            final = df[df['driver_name'].isin(remaining_drivers)]
            final.set_index('driver_name', inplace=True)
            self.playoffs['total points'].loc[remaining_drivers] = self.playoffs['points'].loc[remaining_drivers] + final['pts']
            self.playoffs['points'].loc[remaining_drivers] = self.playoffs['total points'].loc[remaining_drivers]
            self.playoffs.sort_values('total points', ascending=False, inplace=True)
            
        # Formatting 
        self.playoffs.reset_index(inplace=True)
        self.playoffs['pos'] = self.playoffs.index + 1
        self.playoffs['delta'] = np.NaN
        self.playoffs['cutoff'] = np.NaN
        cols = ['pos', 'delta', 'driver_name', 'total points', 'cutoff', 'points', 'playoff points'] + cols
        self.playoffs = self.playoffs[cols]
        self.playoffs.replace(to_replace=0, value=np.NaN, inplace=True)
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
        self.playoffs.to_csv('tables/playoffs.csv',
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
    
    year = 2019
    series = 1
    
    reg = Points(series=series, year=year)
    reg.get_races(26)
    reg.calc_points()
    reg.ties()
    
    last = Points(series=series, year=year)
    last.get_races(35)      # this will need to take (p.num_races - 1)
    last.calc_points()
    last.ties()
    last.calc_playoff_points(reg_season=reg)
    last.playoff_points_ties()
    
    p = Points(series=series, year=year)
    p.get_races()   
    p.calc_points()
    p.ties()
    p.points_delta(last=last)
    p.playoff_drivers()
    p.cutoff()
    p.calc_playoff_points(reg_season=reg)
    p.playoff_points_ties()
    p.playoff_points_delta(last=last)
    p.calc_stats()
    
    # a = p.calc_playoffs()s


    
    # p.export_points()
    print(dt.now() - now)


# To Do:
    
     # calc_playoff_points().
        # Remove if/else at beginning for num races?

