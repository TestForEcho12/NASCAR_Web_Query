import pandas as pd
import sqlite3

    
def sum_points():
    conn = sqlite3.connect('NASCAR.db')    
    df = pd.read_sql_query("""SELECT driver_name, Results.race_id, Races.race_number, Tracks.nickname,
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

    # Group by Driver and sum points
    total = df.groupby('driver_name', as_index=False).sum()
    del total['race_id']
    del total['race_number']
    total = total.sort_values('pts', ascending=False)
    total = total.reset_index(drop=True)
    
    # Add empty column for each race
    race_dict = {}
    races = df['race_id'].unique()
    total['Points Behind Leader'] = ''
    total['+/- Cutoff'] = ''
    for race in races:
        # return data of first row where race_id = race
        name = df.loc[df['race_id'] == race].iloc[0]['nickname']
        race_num = df.loc[df['race_id'] == race].iloc[0]['race_number']
        race_dict[race] = name
        # Add column if not a Duel
        if race_num > 0:
            total[race] = 0
        # Store Daytona race number
        if race_num == 1:
            Daytona = race
        
    # Add point values for each race
    for index, row in df.iterrows():
        # If one of the Duels, replace race_number with Daytona race number
        if row['race_number'] == 0:
            row['race_id'] = Daytona
        total.loc[total['driver_name'] == row['driver_name'], row['race_id']] += row['pts'] 
    
    # Change column headers from race_id to track name
    total = total.rename(columns = race_dict)
    total = total.rename(columns = {'pts': 'Total Points',
                                    'driver_name': 'Drivers'})
    total = total.replace(to_replace=0, value='')
    
    # Points Behind Leader
    total.loc[0, 'Points Behind Leader'] = '-'
    leader_pts = total.loc[0, 'Total Points']
    for index, row in total.iterrows():
        if index > 0:
            total.loc[index, 'Points Behind Leader'] = row['Total Points'] - leader_pts


    
    print(total)
    total.to_html('HTML\points.html', index=False, border=0)


def winners():
    conn = sqlite3.connect('NASCAR.db')
    c = conn.cursor()    
    c.execute("""SELECT driver_name FROM Results 
                 JOIN Drivers ON Results.driver_id = Drivers.driver_id
                 JOIN Races ON Results.race_id = Races.race_id
                 WHERE series_id = 1 AND year = 2018 AND win = 1 AND ineligible IS NULL""")
    data = c.fetchall()
    conn.commit()
    print(data)
    c.close()
    conn.close()   



    
if __name__ == '__main__':
    
    sum_points()
    winners()

    
    
