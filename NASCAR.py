import WebQuery3
import Database
import excel
import social
import timer

year = 2019
series_id = 1
race_id = 4789
race_number = 15
stage_length = 60
col = 60
track = '@MISpeedway'
hashtags = ['#FireKeepersCasino400', '#NASCAR']

# pause until racetime
timer.run(timer.delay_start2(2019,6,9,14,0))
pause = 25


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
exl = excel.Excel(year=year, series=series_id)
csv_col = str(col)
fetch.all_drivers(series=series_id, year=year)
exl.all_drivers()
fetch.ineligible_drivers(series=series_id, year=year)
exl.ineligible_drivers()
fetch.results_to_csv(race_id=race_id, stage_id=-1, col=csv_col)
exl.results_from_csv()
exl.calculate_points()
exl.full_run()
fetch.laps_to_csv(series=series_id, year=year)
exl.laps_led()

# Set up live race position tracking
live = Database.LiveRace()
live.drop_table()
live.add_table(qry.qry.driver_list)

# get reddit thread id
reddit = social.reddit()
reddit_id = reddit.get_id(thread=1, series=series_id)


# Stage 1
stage = 1
stage_lap = stage_length
csv_col = str(col + stage)

qry.live_race(stage_lap=stage_lap, refresh=3, results_pause=pause)
db.web_query(web)
db.update_results(stage=stage)
db.update_laps()
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
fetch.laps_to_csv(series=series_id, year=year)
live.get_results()
exl.results_from_csv()

exl.calculate_points()
exl.laps_led()
exl.export_pictures()

twitter = social.twitter(series=series_id, track=track, hashtags=hashtags)
twitter.top_10_standings(name_list=qry.qry.name_list, stg=stage)
reddit = social.reddit()
comment = social.imgur_upload(stage=stage, name_list=qry.qry.name_list)
reddit.comment(url_id=reddit_id, comment=comment)


# Stage 2
stage = 2
stage_lap = stage_length*stage
csv_col = str(col + stage)

qry.live_race(stage_lap=stage_lap, refresh=3, results_pause=pause)
db.web_query(web)
db.update_results(stage=stage)
db.update_laps()
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
fetch.laps_to_csv(series=series_id, year=year)
live.get_results()
exl.results_from_csv()

print('Double checking Stage 1')
stage = 1
csv_col = str(col + stage)
web = WebQuery3.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=stage)
db.web_query(web)
db.update_results(stage=stage)
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
exl.results_from_csv()
web = WebQuery3.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=0)
stage = 2

exl.calculate_points()
exl.laps_led()
exl.export_pictures()

twitter = social.twitter(series=series_id, track=track, hashtags=hashtags)
twitter.top_10_standings(name_list=qry.qry.name_list, stg=stage)
reddit = social.reddit()
comment = social.imgur_upload(stage=stage, name_list=qry.qry.name_list)
reddit.comment(url_id=reddit_id, comment=comment)


# Finish
stage = 0
stage_lap = 0
csv_col = str(col + 3)

qry.live_race(stage_lap=stage_lap, refresh=3, results_pause=pause*4)
db.web_query(web)
db.update_results(stage=stage)
db.update_laps()
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
fetch.laps_to_csv(series=series_id, year=year)
live.get_results()
exl.results_from_csv()

print('Double checking Stage 2')
stage = 2
csv_col = str(col + stage)
web = WebQuery3.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=stage)
db.web_query(web)
db.update_results(stage=stage)
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
exl.results_from_csv()
web = WebQuery3.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=0)
stage = 0

exl.calculate_points()
exl.laps_led()
exl.export_pictures()

twitter = social.twitter(series=series_id, track=track, hashtags=hashtags)
twitter.top_10_standings(name_list=qry.qry.name_list, stg=stage)
reddit = social.reddit()
comment = social.imgur_upload(stage=stage, name_list=qry.qry.name_list)
reddit.comment(url_id=reddit_id, comment=comment)


# Post Race
reddit_id = reddit.get_id(thread=2, series=series_id)
reddit.comment(url_id=reddit_id, comment=comment)
if series_id == 1:
    twitter.manufacturer()

