import pandas as pd
import sqlite3

    
def sum_points():
    conn = sqlite3.connect('NASCAR.db')    
    df = pd.read_sql_query("""SELECT driver_name, Results.race_id, Tracks.nickname,
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
                           WHERE series_id = 1 AND year = 2018 AND ineligible IS NULL
                           """, con=conn)
    conn.close()                          
    
    
    print(df)
    races = df['race_id'].unique()

    # Group by Driver and sum points
    total = df.groupby('driver_name', as_index=False).sum()
    del total['race_id']
    total = total.sort_values('pts', ascending=False)
    total = total.reset_index(drop=True)
    
    # Add empty column for each race
    race_dict = {}
    for race in races:
        # return nickname of first row where race_id = race
        name = df.loc[df['race_id'] == race].iloc[0]['nickname']
        race_dict[race] = name
        total[race] = ''
        
    # Add point values for each race
    for index, row in df.iterrows():
        if not row['pts'] == 0:
            total.loc[total['driver_name'] == row['driver_name'], row['race_id']] = row['pts']
    
    # Change column headers from race_id to track name
    total = total.rename(columns = race_dict)
    
    print(total)
    total.to_html('points table.html')




    
if __name__ == '__main__':
    
    sum_points()

    
    
