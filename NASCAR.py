import WebQuery3
import Database
import excel
import social
import time
import timer

year = 2018
series_id = 1
race_id = 4690
race_number = 11
stage_length = 120
track = '@MonsterMile'
hashtags = ['#AAA400',]

# pause until racetime
timer.delay_start(2018,5,6,13,45)

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
csv_col = '44'
fetch.results_to_csv(race_id=race_id, stage_id=-1, col=csv_col)
fetch.laps_to_csv(series=series_id, year=year)
excel.results_from_csv(series=series_id)
excel.full_run(series=series_id)
excel.laps_led(series=series_id)

# Set up live race position tracking
live = Database.LiveRace()
live.drop_table()
live.add_table(qry.qry.driver_list)

# get reddit thread id
reddit = social.reddit()
reddit_id = reddit.get_id('Race Thread')


# Stage 1
stage = 1
stage_lap = stage_length
csv_col = '45'

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
twitter.top_10(name_list=qry.qry.name_list, series_id=series_id, stage=stage)
reddit.comment(url_id=reddit_id, comment=comment)
twitter.standings(srs=series_id, stg=stage, track=track)


# Stage 2
stage = 2
stage_lap = stage_length*2
csv_col = '46'

qry.live_race(stage_lap=stage_lap, refresh=3, results_pause=10)
db.web_query(web)
db.update_results(stage=stage)
db.update_laps()
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
fetch.laps_to_csv(series=series_id, year=year)
live.get_results()
excel.results_from_csv(series=series_id)

print('Double checking Stage 1')
stage = 1
csv_col = '45'
web = WebQuery3.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=stage)
db.web_query(web)
db.update_results(stage=stage)
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
excel.results_from_csv(series=series_id)
web = WebQuery3.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=0)
stage = 2

excel.calculate_points(series=series_id)
excel.laps_led(series=series_id)
excel.export_pictures(series=series_id)

reddit = social.reddit()
twitter = social.twitter(hashtags=hashtags)
comment = social.imgur_upload(stage=stage)
twitter.top_10(name_list=qry.qry.name_list, series_id=series_id, stage=stage)
reddit.comment(url_id=reddit_id, comment=comment)
twitter.standings(srs=series_id, stg=stage, track=track)



# Finish
stage = 0
stage_lap = 0
csv_col = '47'

qry.live_race(stage_lap=stage_lap, refresh=3, results_pause=30)
db.web_query(web)
db.update_results(stage=stage)
db.update_laps()
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
fetch.laps_to_csv(series=series_id, year=year)
live.get_results()
excel.results_from_csv(series=series_id)

print('Double checking Stage 2')
stage = 2
csv_col = '46'
web = WebQuery3.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=stage)
db.web_query(web)
db.update_results(stage=stage)
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
excel.results_from_csv(series=series_id)
web = WebQuery3.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=0)
stage = 0

excel.calculate_points(series=series_id)
excel.laps_led(series=series_id)
excel.export_pictures(series=series_id)

reddit = social.reddit()
twitter = social.twitter(hashtags=hashtags)
comment = social.imgur_upload(stage=stage)
twitter.top_10(name_list=qry.qry.name_list, series_id=series_id, stage=stage)
reddit.comment(url_id=reddit_id, comment=comment)
twitter.standings(srs=series_id, stg=stage, track=track)


# Post Race
reddit_id = reddit.get_id('Post-Race')
reddit.comment(url_id=reddit_id, comment=comment)
time.sleep(90)
reddit_id = reddit.get_id('Scorecard')
reddit.comment(url_id=reddit_id, comment=comment)
