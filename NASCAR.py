import WebQuery3
import Database
import excel
import social
import timer
import practice2


def race():
    year = 2019
    series_id = 1
    race_id = 4809
    race_number = 35
    stage_length = 75
    col = 140
    hashtags = ['#Bluegreen500', '#NASCARPlayoffs']
    pause = 15
    
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
    fetch.all_drivers(series=series_id, year=year)
    fetch.ineligible_drivers(series=series_id, year=year)
    fetch.results_to_csv(race_id=race_id, stage_id=-1, col=csv_col)
    fetch.laps_to_csv(series=series_id, year=year)
    
    exl = excel.Excel(year=year, series=series_id)
    exl.pre_race()
    
    # Set up live race position tracking
    live = Database.LiveRace()
    live.drop_table()
    live.add_table(qry.qry.driver_list)
    
    # Set up social
    reddit = social.reddit()
    reddit_id = reddit.get_id(thread=1, series=series_id)
    track_id = fetch.track_id_from_race_id(race_id)
    track = fetch.twitter_from_track_id(track_id)
    
    
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
    
    exl.in_race()
    
    twitter = social.twitter(series=series_id, track=track, hashtags=hashtags)
    tweet_id = twitter.top_10_standings(name_list=qry.qry.name_list, stg=stage)
    reddit = social.reddit()
    comment = social.imgur_upload(stage=stage, name_list=qry.qry.name_list)
    reddit.comment(url_id=reddit_id, comment=comment)
    
    
    # Stage 2
    stage = 2
    stage_lap = stage_length*stage
    qry.live_race(stage_lap=stage_lap, refresh=3, results_pause=pause)
    db.web_query(web)
    db.update_results(stage=stage)
    db.update_laps()
    
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
    csv_col = str(col + stage)
    fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
    fetch.laps_to_csv(series=series_id, year=year)
    live.get_results()
    
    exl.in_race()
    
    twitter = social.twitter(series=series_id, track=track, hashtags=hashtags)
    tweet_id = twitter.top_10_standings(name_list=qry.qry.name_list, stg=stage)
    reddit = social.reddit()
    comment = social.imgur_upload(stage=stage, name_list=qry.qry.name_list)
    reddit.comment(url_id=reddit_id, comment=comment)
    
    
    # Finish
    stage = 0
    stage_lap = 0
    qry.live_race(stage_lap=stage_lap, refresh=3, results_pause=pause*4)
    db.web_query(web)
    db.update_results(stage=stage)
    db.update_laps()
    
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
    csv_col = str(col + 3)
    fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
    fetch.laps_to_csv(series=series_id, year=year)
    live.get_results()
    
    exl.in_race()
    
    twitter = social.twitter(series=series_id, track=track, hashtags=hashtags)
    tweet_id = twitter.top_10_standings(name_list=qry.qry.name_list, stg=stage)
    reddit = social.reddit()
    comment = social.imgur_upload(stage=stage, name_list=qry.qry.name_list)
    reddit.comment(url_id=reddit_id, comment=comment)
    
    
    # Post Race
    reddit_id = reddit.get_id(thread=2, series=series_id)
    reddit.comment(url_id=reddit_id, comment=comment)
    if series_id == 1:
        twitter.manufacturer(tweet_id)


def practice():
    year = 2019
    series = 1
    race_id = 4807
    practice_id = 3
    hashtags = ['#FirstData500', '#NASCARPlayoffs',]
    track = '@MartinsvilleSwy'
#    fetch = Database.Fetch()
#    track_id = fetch.track_id_from_race_id(race_id)
#    track = fetch.twitter_from_track_id(track_id)
    
    p = practice2.Practice(year, series, race_id, practice_id)
    p.query()
    p.comment(track, hashtags)
    p.excel()
    
    e = excel.v2(year, series)
    e.practice()
    
    t = social.twitter(series, track, hashtags)
    t.practice2(p.com)
    
    
if __name__ == '__main__':
    
    timer.run(timer.delay_start2(2019,11,10,14,30))
    
    race()
#    practice()