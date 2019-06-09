import os
import praw
import tweepy
from imgurpython import ImgurClient
import json

imgur_client_id = 'd141e46a0cfdfd5'
imgur_client_secret = '66d56183964e5ecdfe907076e831f251cb1edf9f'
path = r'C:\Users\greg5\Documents\NASCAR\Pictures'

reddit_client_id = 'DBII9GIP1CI9mQ'
reddit_client_secret = '2FnjxPswZF5VexRlAQwwGPkR_1k'
reddit_username = 'AirplaneBottleOfBour'
reddit_password = 'banana123456'
reddit_user_agent = 'comment_bot'

twitter_consumer_key = 'nFfBiZf2rghcy0iVufpn6EIRW'
twitter_consumer_secret = 'noztJVJD5kx2nVxX6ApV0RSLZ8YHx0Sunm4pF0jkSNevDR7ZTI'
twitter_access_token = '893122594630758402-7HL2qTwK5RuONPAVmYWsAO94hrJqp50'
twitter_access_token_secret = '4NjTsbOZX6Qp4oRGB8gyZTXrsEUpR1MoXjrLa0gvcNH3M'
#owner_ID = '893122594630758402'
# @NASCAR_Score
# banana123456

header = {
         1: 'Stage 1 Top 10:  ',
         2: 'Stage 2 Top 10:  ',
         3: 'Stage 3 Top 10:  ',
         0: 'Top 10 Finishers:  ',
         }
srs = {
         1: '@NASCAR',
         2: '@NASCAR_XFINITY',
         3: '@NASCAR_Trucks',
         }
stage = {
        1: 'Stage 1',
        2: 'Stage 2',
        3: 'Stage 3',
        0: 'the race',
        }
top_10 = {
         1: 'Stage 1 Top 10:',
         2: 'Stage 2 Top 10:',
         3: 'Stage 3 Top 10:',
         0: 'Top 10 Finishers:',
         }

def imgur_upload(stage, name_list):
    client = ImgurClient(client_id=imgur_client_id, 
                         client_secret=imgur_client_secret)
    pics = os.listdir(path)
    print('Uploading images to imgur...\n')
    comment = f'{header[stage]}  \n\n'
    count = 0
    # Add top 10 to comment
    while count < 10:
        position = f'{count + 1})'
        comment = f'{comment}  {position:<5}{name_list[count]}  \n'
        count += 1
    comment = f'{comment}  \n'
    pic_list = [
                'Playoff Grid.png',
                'Points.png',
                'Playoff Points.png',
                'Stats.png',
                'Manufacturer.png',
                ]
    for pic in pic_list:
        if pic in pics:
            print('Uploading: ', pic)
            image = client.upload_from_path(f'{path}\{pic}')
            name = pic.replace('.png', '')
            link = image['link']
            comment = f'{comment}[{name}]({link})  \n'
    # Add twitter plug
    comment = comment + ('\n*^(These are also posted to)* [*^(Twitter)*]'
          '(https://twitter.com/NASCAR_Score) *^(for anyone interested.)*')
    print('\n' + comment)
    return(comment)


class reddit:
    
    def __init__(self):
        self.reddit = praw.Reddit(client_id = reddit_client_id,
                             client_secret = reddit_client_secret,
                             user_agent = reddit_user_agent,
                             username = reddit_username,
                             password = reddit_password)   
    
    def comment(self, url_id, comment):
        if url_id != 'error':
            r = self.reddit.submission(id=url_id)
            r.reply(comment)
            print(f'\nReddit comment posted to\n{r.title}')
        
    def get_id(self, thread, series):
        title = {1: 'Race Thread: ',
                 2: 'Post-Race Discussion Thread: ',}
        srs = {1: 'MENCS',
               2: 'NXS',
               3: 'NGOTS',}
        keyword = title[thread] + srs[series]
        subreddit = self.reddit.subreddit('NASCAR')
        new = subreddit.new(limit=60)
        for post in new:
            if keyword in post.title:
                print(f'\n{post.title} id was found!\n')
                return post.id
                break
        print('Reddit post not found')
        return 'error'

        
        
class twitter:
    
    def __init__(self, series, track, hashtags):
        auth = tweepy.OAuthHandler(twitter_consumer_key, twitter_consumer_secret)
        auth.set_access_token(twitter_access_token, twitter_access_token_secret)
        self.api = tweepy.API(auth)
        self.series = srs[series]
        self.track = track
        self.hashtags = ''
        for tag in hashtags:
            self.hashtags = f'{self.hashtags}{tag}\n'
            
    def practice(self, comment, reply_id=0):
        if not comment:
            print('No comment to tweet...')
            return
        comment = f'{comment}\n\n{self.track}\n{self.hashtags}'
        print(comment)
        if reply_id != 0:
            status = self.api.update_status(status=comment, 
                                            in_reply_to_status_id = reply_id)
        else:
            status = self.api.update_status(status=comment)
        tweet_id = json.dumps(status._json['id'])
        print(tweet_id)
        return tweet_id

    def standings(self, stg):
        status = (f'.{self.series} standings after {stage[stg]} at {self.track}\n\n{self.hashtags}')
        pictures = [r'{}\Playoff Grid.png'.format(path),
                    r'{}\Points.png'.format(path),
                    r'{}\Playoff Points.png'.format(path),
                    r'{}\Stats.png'.format(path),]
        print('Uploading pictures to twitter...')
        media_ids = []
        for pic in pictures:
            res = self.api.media_upload(pic)
            media_ids.append(res.media_id)
            print('Uploading: ', pic)
        print('Tweeting...')
        self.api.update_status(status=status, media_ids=media_ids)
        print('\n', status)
        print('Standings posted to Twitter\n')
        
    def manufacturer(self):
        status = (f'.{self.series} manufacturer standings after the race at {self.track}\n\n{self.hashtags}')
        picture = r'{}\Manufacturer.png'.format(path)
        media_ids = []
        res = self.api.media_upload(picture)
        media_ids.append(res.media_id)
        self.api.update_status(status=status, media_ids=media_ids)
        print(status)
        print('Manufacturer standings posted to twitter\n')
        
    def top_10(self, name_list, stg):
        '''This method had been deprecated.
           No longer in use'''
        pass
#        comment = f'{top_10[stg]}\n\n'
#        count = 0    
#        while count < 10:
#            position = f'{count + 1})'
#            comment = f'{comment}{position:<5}{name_list[count]}\n'
#            count += 1
#        comment = f'{comment}\n{self.series}\n{self.track}\n{self.hashtags}'
#        self.api.update_status(status=comment)
#        print(f'\n{comment}')
#        print('Top 10 posted to Twitter\n')
        
    def top_10_standings(self, name_list, stg):
        comment = f'{top_10[stg]}\n\n'
        count = 0    
        while count < 10:
            position = f'{count + 1})'
            comment = f'{comment}{position:<5}{name_list[count]}\n'
            count += 1
        comment = f'{comment}\n{self.series}\n{self.track}\n{self.hashtags}'
        
        print('Uploading pictures to twitter...')
        pics = os.listdir(path)
        pic_list = [
            'Playoff Grid.png',
            'Points.png',
            'Playoff Points.png',
            'Stats.png',
            ]
        media_ids = []
        for pic in pic_list:
            if pic in pics:
                res = self.api.media_upload(f'{path}\{pic}')
                media_ids.append(res.media_id)
                print('Uploading: ', pic)         
        self.api.update_status(status=comment, media_ids=media_ids)
        print(f'\n{comment}')
        print('Top 10 posted to Twitter\n')
        
        
