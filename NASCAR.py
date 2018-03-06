import WebQuery3
import Database
import excel
import social
import time

year = 2018
series_id = 1
race_id = 4678
track = '@LVMotorSpeedway'
hashtags = ['#Pennzoil400',]


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
db.add_race(year=year)
db.add_results()

# Qual results to Excel
csv_col = '12'
fetch.results_to_csv(race_id=race_id, stage_id=-1, col=csv_col)
fetch.laps_to_csv(series=series_id, year=year)
excel.results_from_csv(series=series_id)
excel.full_run(series=series_id)
excel.laps_led(series=series_id)

# Set up live race position tracking
live = Database.LiveRace()
live.add_table(qry.qry.driver_list)

# get reddit thread id
reddit = social.reddit()
reddit_id = reddit.get_id('Race Thread')


# Stage 1
stage = 1
stage_lap = 80
csv_col = '13'

qry.live_race(stage_lap=stage_lap, refresh=3, results_pause=10)
db.web_query(web)
db.update_results(stage=stage)
db.update_laps()
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
fetch.laps_to_csv(series=series_id, year=year)
live.get_results()

excel.results_from_csv(series=series_id)
excel.calculate_points(series=series_id)
excel.laps_led(series=series_id)
excel.export_pictures(series=series_id)

reddit = social.reddit()
twitter = social.twitter(hashtags=hashtags)
comment = social.imgur_upload(stage=stage)
twitter.top_10(name_list=qry.qry.name_list, stage=stage)
reddit.comment(url_id=reddit_id, comment=comment)
twitter.standings(srs=series_id, stg=stage, track=track)


# Stage 2
stage = 2
stage_lap = 160
csv_col = '14'

qry.live_race(stage_lap=stage_lap, refresh=3, results_pause=10)
db.web_query(web)
db.update_results(stage=stage)
db.update_laps()
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
fetch.laps_to_csv(series=series_id, year=year)
live.get_results()

excel.results_from_csv(series=series_id)
excel.calculate_points(series=series_id)
excel.laps_led(series=series_id)
excel.export_pictures(series=series_id)

reddit = social.reddit()
twitter = social.twitter(hashtags=hashtags)
comment = social.imgur_upload(stage=stage)
twitter.top_10(name_list=qry.qry.name_list, stage=stage)
reddit.comment(url_id=reddit_id, comment=comment)
twitter.standings(srs=series_id, stg=stage, track=track)



# Finish
stage = 0
stage_lap = 0
csv_col = '15'

qry.live_race(stage_lap=stage_lap, refresh=3, results_pause=30)
db.web_query(web)
db.update_results(stage=stage)
db.update_laps()
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
fetch.laps_to_csv(series=series_id, year=year)
live.get_results()

excel.results_from_csv(series=series_id)
excel.calculate_points(series=series_id)
excel.laps_led(series=series_id)
excel.export_pictures(series=series_id)

reddit = social.reddit()
twitter = social.twitter(hashtags=hashtags)
comment = social.imgur_upload(stage=stage)
twitter.top_10(name_list=qry.qry.name_list, stage=stage)
reddit.comment(url_id=reddit_id, comment=comment)
twitter.standings(srs=series_id, stg=stage, track=track)


# Post Race
reddit_id = reddit.get_id('Post-Race')
reddit.comment(url_id=reddit_id, comment=comment)
time.sleep(60)
reddit_id = reddit.get_id('Scorecard')
reddit.comment(url_id=reddit_id, comment=comment)
