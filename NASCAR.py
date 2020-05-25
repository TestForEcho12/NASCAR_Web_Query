import WebQuery4
import Database
import excel
import social
import timer
import practice2
import scoring2


def race():
    year = 2020
    series_id = 2
    race_id = 4970
    race_number = 5
    stage_length = 45
    hashtags = ['#Toyota200', '#NASCAR']
    pause = 15
    timer.run(timer.delay_start2(2020,5,21,16,30))
    
    # set up live feed web object
    web = WebQuery4.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=0)
    
    # query object and return inital results
    qry = WebQuery4.Query(web)
    qry.results()
    
    # Database object, load web object, add race and results to DB
    db = Database.Database()
    fetch = Database.Fetch()
    
    #**************Penalty*************
    # db.add_penalty('Ricky Stenhouse Jr.', race_id, 10)
    #**************Penalty*************
    
    # Update database
    db.web_query(web)
    db.update_drivers()
    db.update_tracks()
    db.add_race(year=year, race_number=race_number, stage_length=stage_length)
    db.add_results()
    
    # Initialize scoring
    v2 = scoring2.Score(series_id, year)
    
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
    stage_lap = qry.qry.race_status['stage_end']
    qry.live_race(stage_lap=stage_lap, refresh=3, results_pause=pause)
    db.web_query(web)
    db.update_results(stage=stage)
    db.update_laps()
    live.get_results()
    
    v2.calc()
    v2.export()
    
    twitter = social.twitter(series=series_id, track=track, hashtags=hashtags)
    tweet_id = twitter.top_10_standings(name_list=qry.qry.name_list, stg=stage)
    reddit = social.reddit()
    comment = social.imgur_upload(stage=stage, name_list=qry.qry.name_list)
    reddit.comment(url_id=reddit_id, comment=comment)

    
    # Stage 2
    stage = 2
    qry.check_for_next_stage(stage_lap)
    stage_lap = qry.qry.race_status['stage_end']
    qry.live_race(stage_lap=stage_lap, refresh=3, results_pause=pause)
    db.web_query(web)
    db.update_results(stage=stage)
    db.update_laps()
    live.get_results()
    
    print('Double checking Stage 1')
    web1 = WebQuery4.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=1)
    db.web_query(web1)
    db.update_results(stage=1)
    
    v2.calc()
    v2.export()
    
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
    live.get_results()
    
    print('Double checking Stage 2')
    web2 = WebQuery4.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=2)
    db.web_query(web2)
    db.update_results(stage=2)
    
    v2.calc()
    v2.export()
    
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
    year = 2020
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
    
    race()
#    practice()