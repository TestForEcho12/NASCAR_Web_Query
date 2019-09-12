import WebQuery3
import time
import csv
import pandas as pd
import numpy as np

class Practice():
    
    def __init__(self, year, series_id, race_id, practice_id):
        self.year = year
        self.series_id = series_id
        self.race_id = race_id
        self.practice_id = practice_id

    def query(self):
        practice_title = {1: 'practice_1',
                          2: 'practice_2',
                          3: 'final_practice'}[self.practice_id]
        series = {1: 'mencs',
                  2: 'nxs',
                  3: 'ngots'}[self.series_id]
        # Get web object and set url
        web = WebQuery3.WebData(1, 1, 1, 1)
        web.url = f'https://www.nascar.com/cacher/{self.year}/{self.series_id}/{self.race_id}/lapAvg_{series}_{practice_title}.json'
        # Wait for page to become active and pull json
        while True:
            try: 
                web.open_browser()
                web.get_json()
                df = pd.DataFrame(web.json_dict)
                df.sort_values('BestLapRank', inplace=True)
                df.reset_index(inplace=True)
                web.close_browser()
                print('\n')
                break
            except:
                web.close_browser()
                print('pausing 60...')
                time.sleep(60)
        # Clean driver names
        # Future work: Update database to accept practice results and clean names
        #              So that driver id can be used
        for index, row in df.iterrows():
            name = str(row['FullName']).replace(' #', '')
            name = name.replace('(i)', '')
            name = name.replace('* ', '')
            name = name.replace(' (P)', '')
            df.at[index, 'FullName'] = name
        self.top = df['FullName'].head(10).to_list()
        df['pos'] = df.index + 1
        df = pd.DataFrame(df[['pos', 'FullName', 'BestLapTime', 'Con5Lap', 'Con10Lap', 'Con15Lap', 'Con20Lap', 'Con25Lap', 'Con30Lap']])
        df.replace(999, np.NaN, inplace=True)
        self.df = df

    def comment(self, track, hashtags):
        num_drivers = 10
        if len(self.top) < num_drivers:
            num_drivers = len(self.top)
            if num_drivers == 0:
                print('No drivers completed practice type')
                return
        tweet_header = {1: '1st',
                         2: '2nd',
                         3: 'final'}[self.practice_id]
        srs = {1: '@NASCAR',
               2: '@NASCAR_XFINITY',
               3: '@NASCAR_Trucks'}[self.series_id]

        comment = f'Fastest from {tweet_header} {srs} practice at {track}:\n'
        count = 0
        while count < num_drivers:
            comment = f'{comment}\n{count + 1}) {self.top[count]}'
            count += 1
        tags = ''
        for tag in hashtags:
            tags += f'\n{tag}'      
        comment += f'\n{tags}'
        self.com = comment

    def excel(self):
        title = {1: '1st',
                 2: '2nd',
                 3: 'Final'}[self.practice_id]
        
        with open('tables/practice.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([f'{title} Practice Results'])
        with open('tables/practice.csv', 'a', newline='') as f:
            self.df.to_csv(f,
                           header=False,
                           index=False)

