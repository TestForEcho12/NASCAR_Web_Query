import WebQuery3
import Database
import excel
import social

year = 2018
series_id = 1
race_id = xxxx
track = '@DISupdates'
hashtag = '#DAYTONA500'

# set up live feed web object
web = WebQuery3.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=0)

# query object and return inital results
qry = WebQuery3.Query(web)
qry.results()

# Database object, load web object, add race and results to DB
db = Database.Database()
db.web_query(web)
db.add_race()
db.add_results()

# Set up live race position tracking
Database.LiveRace.drop_table()
Database.LiveRace.add_table(qry.name_list)

# initalize social accounts
reddit = social.reddit()
twitter = social.twitter()

# Stage 1
stage = 1
stage_lap = 60
csv_col = 'xxxx'

qry.live_race(stage_lap=stage_lap)
db.web_query(web)
db.update_results(stage=stage)
Database.Fetch.results_to_csv(col=csv_col)
Database.Fetch.laps_to_csv(series=series_id, year=year)
excel.run_macros(series=series_id)

comment = social.imgur_upload(stage=1)
reddit.comment(url_id='xxxx', comment=comment)
twitter.standings(srs=series_id, stg=stage, track=track, hashtag=hashtag)

