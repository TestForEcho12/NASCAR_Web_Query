import pandas as pd
import sqlite3
    
def sum_points():
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
    
    sum_points()
