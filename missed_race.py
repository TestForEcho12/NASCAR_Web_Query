import WebQuery3
import Database
import excel
import social


year = 2018
series_id = 2
race_id = 4725
race_number = 12
stage_length = 25
col = 46

track = '@poconoraceway'
hashtags = ['#PoconoGreen250',]


# set up live feed web object
web = WebQuery3.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=0)

# query object and return inital results
qry = WebQuery3.Query(web)
qry.results()

# Database object, load web object, add race and results to DB
db = Database.Database()
fetch = Database.Fetch()
db.web_query(web)
db.update_drivers()
db.update_tracks()
db.add_race(year=year, race_number=race_number, stage_length=stage_length)
db.add_results()

# Qual results to Excel
csv_col = str(col)
fetch.results_to_csv(race_id=race_id, stage_id=-1, col=csv_col)
fetch.laps_to_csv(series=series_id, year=year)
excel.results_from_csv(series=series_id)
excel.full_run(series=series_id)
excel.laps_led(series=series_id)

print('Double checking Stage 1')
stage = 1
csv_col = str(col + 1)
web = WebQuery3.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=stage)
db.web_query(web)
db.update_results(stage=stage)
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
excel.results_from_csv(series=series_id)
web = WebQuery3.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=0)

print('Double checking Stage 2')
stage = 2
csv_col = str(col + 2)
web = WebQuery3.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=stage)
db.web_query(web)
db.update_results(stage=stage)
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
excel.results_from_csv(series=series_id)
web = WebQuery3.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=0)

# Finish
stage = 0
stage_lap = 0
csv_col = str(col + 3)

db.web_query(web)
db.update_results(stage=stage)
db.update_laps()
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
fetch.laps_to_csv(series=series_id, year=year)
excel.results_from_csv(series=series_id)

excel.calculate_points(series=series_id)
excel.laps_led(series=series_id)
excel.export_pictures(series=series_id)


twitter = social.twitter(hashtags=hashtags)
twitter.top_10(name_list=qry.qry.name_list, series_id=series_id, stage=stage)
twitter.standings(srs=series_id, stg=stage, track=track)