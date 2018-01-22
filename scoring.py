import pandas as pd
import sqlite3

series = 1
year = 2017

stage_points = {
        1:  10,
        2:  9,
        3:  8,
        4:  7,
        5:  6,
        6:  5,
        7:  4,
        8:  3,
        9:  2,
        10: 1,
        11: 0,
        12: 0,
        13: 0,
        14: 0,
        15: 0,
        16: 0,
        17: 0,
        18: 0,
        19: 0,
        20: 0,
        21: 0,
        22: 0,
        23: 0,
        24: 0,
        25: 0,
        26: 0,
        27: 0,
        28: 0,
        29: 0,
        30: 0,
        31: 0,
        32: 0,
        33: 0,
        34: 0,
        35: 0,
        36: 0,
        37: 0,
        38: 0,
        39: 0,
        40: 0,
        None: 0
        }

finish_points = {
        1:  40,
        2:  35,
        3:  34,
        4:  33,
        5:  32,
        6:  31,
        7:  30,
        8:  29,
        9:  28,
        10: 27,
        11: 26,
        12: 25,
        13: 24,
        14: 23,
        15: 22,
        16: 21,
        17: 20,
        18: 19,
        19: 18,
        20: 17,
        21: 16,
        22: 15,
        23: 14,
        24: 13,
        25: 12,
        26: 11,
        27: 10,
        28: 9,
        29: 8,
        30: 7,
        31: 6,
        32: 5,
        33: 4,
        34: 3,
        35: 2,
        36: 1,
        37: 1,
        38: 1,
        39: 1,
        40: 1,
        None: 0
        }

def get_driver_id_list():
    conn = sqlite3.connect('NASCAR.db')
    df = pd.read_sql_query("""SELECT driver_id FROM Results JOIN 
                           Races ON Results.race_id = Races.race_id 
                           WHERE series_id=? AND year=? 
                           """, params=(series, year), con=conn)
    df = df.drop_duplicates(subset='driver_id')
    driver_id_list = df['driver_id'].tolist()
    conn.close()
    return driver_id_list


def sum_points(driver_id_list):
    conn = sqlite3.connect('NASCAR.db')
    for driver_id in driver_id_list:
        stage_pts = 0
        finish_pts = 0
        df = pd.read_sql_query("""SELECT * FROM Results JOIN
                               Races ON Results.race_id = Races.race_id
                               WHERE series_id=? AND year=? AND driver_id=?
                               """, params=(series, year, driver_id), con=conn)
        for index, row in df.iterrows():
            if row['ineligible'] != 1:
                stage_pts += stage_points[row['stage1']] + stage_points[row['stage2']] + stage_points[row['stage3']]
                finish_pts += finish_points[row['finish']]
            pts = stage_pts + finish_pts 
        print(df['driver_id'][0], '\t', pts)
    conn.close()
    
def sum_points_2():
    conn = sqlite3.connect('NASCAR.db')    
    df = pd.read_sql_query("""SELECT driver_name, (ifnull(s1.stage, 0) + 
                                                   ifnull(s2.stage, 0) + 
                                                   ifnull(s3.stage, 0) + 
                                                   ifnull(f.finish, 0)) AS pts
                           FROM Results
                           JOIN Drivers ON Results.driver_id = Drivers.driver_id
                           LEFT OUTER JOIN Points AS s1 ON Results.stage1 = s1.position
                           LEFT OUTER JOIN Points AS s2 ON Results.stage2 = s2.position
                           LEFT OUTER JOIN Points AS s3 ON Results.stage3 = s3.position
                           LEFT OUTER JOIN Points AS f ON Results.finish = f.position
                           ORDER BY Results.driver_id
                           """, con=conn)
    print(df)
    total = df.groupby('driver_name').sum()
    print(total.sort_values('pts', ascending=False))

    conn.close()

    
    
if __name__ == '__main__':
    
    
    driver_id_list = get_driver_id_list()
    sum_points(driver_id_list)
    
    
