import WebQuery3
import Database
import excel


year = 2019
series_id = 1
race_id = 4799
race_number = 25
stage_length = 100
col = 100


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

print('Double checking Stage 1')
stage = 1
csv_col = str(col + stage)
web = WebQuery3.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=stage)
db.web_query(web)
db.update_results(stage=stage)
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
exl.results_from_csv()


print('Double checking Stage 2')
stage = 2
csv_col = str(col + stage)
web = WebQuery3.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=stage)
db.web_query(web)
db.update_results(stage=stage)
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
exl.results_from_csv()


# Finish
stage = 0
csv_col = str(col + 3)

web = WebQuery3.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=0)
db.web_query(web)
db.update_results(stage=stage)
db.update_laps()
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
fetch.laps_to_csv(series=series_id, year=year)

exl.in_race()

