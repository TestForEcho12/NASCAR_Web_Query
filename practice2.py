import WebQuery3
import time
import social
import timer
import pandas as pd
import numpy as np

class Practice():
    
    def __init__(self, year, series_id, race_id):
        self.year = year
        self.series_id = series_id
        self.race_id = race_id

    def query(self, practice_id):
        practice_title = {1: 'practice_1',
                          2: 'practice_2',
                          3: 'final_practice'}[practice_id]
        series = {1: 'mencs',
                  2: 'nxs',
                  3: 'ngots'}[self.series_id]
        
        # Get web object and set url
        web = WebQuery3.WebData(1, 1, 1, 1)
        web.url = f'https://www.nascar.com/cacher/{self.year}/{self.series_id}/{race_id}/lapAvg_{series}_{practice_title}.json'
    
        # Wait for page to become active and pull json
        while True:
            try: 
                web.open_browser()
                web.get_json()
                print('\n')
                break
            except:
                print('pausing 60...')
                time.sleep(60)
        web.close_browser()
        
        df = pd.DataFrame(web.json_dict)
        df.sort_values('BestLapRank', inplace=True)
        df.reset_index(inplace=True)
        
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

    def comment(self, practice_header, track, hashtags):
        num_drivers = 10
        if len(self.top) < num_drivers:
            num_drivers = len(self.top)
            if num_drivers == 0:
                print('No drivers completed practice type')
                return
        
        tweet_header = {1: '1st',
                         2: '2nd',
                         3: 'final'}[practice_header]
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
        self.df.to_csv('tables/practice.csv',
                        header=False,
                        index=False)

if __name__ == '__main__':
    year = 2019
    series = 3
    race_id = 4856
    track = '@EldoraSpeedway'
    hashtags = ['#EldoraDirtDerby', '#NASCAR',]
    timer.run(timer.delay_start2(2019,7,31,20,0))
    
    practice_id = 3
    practice_header = 3
    p = Practice(year, series, race_id)
    p.query(practice_id)
    p.comment(practice_header, track, hashtags)
    p.excel()
    
    a = p.df
    print(p.com)
    
    

#    com = comment(series, practice_type, drivers, practice_header)
#    print(com)
#    twitter = social.twitter(series, track, hashtags)
#    tweet_id = twitter.practice(com, reply_id=tweet_id)   
    
    
    
 