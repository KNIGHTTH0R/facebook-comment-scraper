import urllib2
import json
import mysql.connector
import datetime
import requests


def connect_db():
    # fill this out with your db connection info
    connection = mysql.connector.connect(user='', password='', # add own MySQl user & password
                                         host='127.0.0.1',
                                         database='disneylife')
    return connection


def create_post_url(graph_url, APP_ID, APP_SECRET):
    # create URL for authenticated request to gather FB posts
    post_args = "/posts?fields=id,message,created_time,shares,type,status_type,link,updated_time&key=value&access_token=" + APP_ID + "|" + APP_SECRET + "&date_format=U"
    post_url = graph_url + post_args

    return post_url


def create_page_url(graph_url, APP_ID, APP_SECRET):
    # create URL for authenticated request to gather page details
    page_args = "?fields=likes,talking_about_count,id,username&key=value&access_token=" + APP_ID + "|" + APP_SECRET
    page_url = graph_url + page_args

    return page_url


def create_comments_url(graph_url, post_id, APP_ID, APP_SECRET):
    # create URL for authenticated request to gather comments on FB posts
    comments_args = post_id + "/comments/?fields=created_time,from,message,id,like_count,comment_count,comments&key=value&access_token=" + APP_ID + "|" + APP_SECRET + "&date_format=U"
    comments_url = graph_url + comments_args

    return comments_url


def render_to_json(post_url):
    # render graph url call to JSON
    web_response = urllib2.urlopen(post_url)
    readable_page = web_response.read()
    json_data = json.loads(readable_page)

    return json_data


def fb_to_mysql_datetime(fb_timestamp):
    # convert datetime from FB to a datetime format to insert into mySQL
    fb_datetime = datetime.datetime.fromtimestamp(int(fb_timestamp))
    mysql_datetime = fb_datetime.strftime('%Y-%m-%d %H:%M:%S')

    return mysql_datetime


def if_exists(check_field):
    # takes a field to see if it exists
    if check_field:
        return_field = check_field
    else:
        return_field = 0

    return return_field


def get_likes_count(post_id, APP_ID, APP_SECRET):
    # create URL for authenticated request to get the number of likes on a FB post
    graph_url = "https://graph.facebook.com/"
    likes_args = post_id + "/likes?summary=true&key=value&access_token=" + APP_ID + "|" + APP_SECRET
    likes_url = graph_url + likes_args
    likes_json = render_to_json(likes_url)

    # pick out the likes count
    likes_count = if_exists(likes_json["summary"]["total_count"])

    return likes_count


def get_sentiment(message):
   
    # take a text comment and return its sentiment using the Brain enricher.
    api_url = "" # contact Black Swan for access to API
    body = '{"requests": [{"language": "en", "content": "' + message + '"}]}'
    r = requests.post(api_url, data=body)
    json_data = r.json()
    sentiment_response = json_data["responses"][0]["sentiment"]

    if sentiment_response == 1:
        sentiment = 'positive'
    elif sentiment_response == 0:
        sentiment = 'neutral'
    elif sentiment_response == -1:
        sentiment = 'negative'
    else:
        sentiment = 'error'

    return sentiment


def scrape_posts_by_date(graph_url, date, post_data, APP_ID, APP_SECRET):

    # render URL to JSON
    page_posts = render_to_json(graph_url)

    # check that data exists on current page
    if len(page_posts["data"]) < 1:
        collecting = False
    else:
        # extract next page
        next_page = page_posts["paging"]["next"]

        # grab all posts from current page
        page_posts = page_posts["data"]

        # boolean to tell us when to stop collecting
        collecting = True

        # for each post capture data
        for post in page_posts:
            try:
                likes_count = get_likes_count(post["id"], APP_ID, APP_SECRET)

                time_created = fb_to_mysql_datetime(post["created_time"])
                updated_time = fb_to_mysql_datetime(post["updated_time"])

                if 'shares.count' in post:
                    shares_count = post["shares"]["count"]
                else:
                    shares_count = 0

                current_post = [
                    post['id'],
                    str(post['message']),
                    likes_count,
                    time_created,
                    shares_count,
                    post['type'],
                    post['status_type'],
                    post['link'],
                    updated_time
                ]

            except Exception as e:
                current_post = ["error", "error", "error", "error", "error", "error", "error", "error", "error"]
                print "Post exception error: " + str(e) + ". Post: " + str(post)

            if current_post[2] != "error":
                print str(current_post[3])

                if date <= current_post[3]:
                    post_data.append(current_post)

                elif date > current_post[2]:
                    print "Done collecting"
                    collecting = False
                    break

    # If we still don't meet date requirements, run on next page
    if collecting == True:
        scrape_posts_by_date(next_page, date, post_data, APP_ID, APP_SECRET)

    return post_data


def get_comments_data(comments_url, comment_data, post_id):
    # render URL to JSON
    comments = render_to_json(comments_url)["data"]

    # for each comment capture data
    for comment in comments:
        try:
            time_created = fb_to_mysql_datetime(comment["created_time"])
            sentiment = get_sentiment(comment["message"])

            current_comment = [
                comment["id"],
                str(comment["message"]),
                comment["like_count"],
                time_created,
                post_id,
                comment["from"]["name"],
                comment["from"]["id"],
                comment["comment_count"],
                sentiment
            ]

            comment_data.append(current_comment)

        except Exception as e:
            current_comment = ["error", "error", "error", "error", "error"]
            print "Comment exception error: " + str(e) + ". Comment: " + str(comment)

    # check if there is another page
    try:
        # extract next page
        next_page = comments["paging"]["next"]
    except Exception as e:
        next_page = None

    # if we have another page, recurse
    if next_page is not None:
        get_comments_data(next_page, comment_data, post_id)
        print "Got next comment page"
    else:
        return comment_data


def get_econtext_data(message, comment_id):

    api_url = 'https://api.econtext.com/v2/classify/social'
    username = '' # add own eContext creds
    password = '' # add own eContext creds

    body = '{"social":[' + message + '], "async": false}'
    headers = '{"content-type": "application/json"}'
    r = requests.post(api_url, data=body, auth=(username, password), headers=headers)
    json_data = r.json()
    print json_data

    return json_data


def main():

    # Facebook App Secret and App ID
    APP_SECRET = "" # add own FB app creds
    APP_ID = "" # add own FB app creds

    # to find go to page's FB page, at the end of URL find username
    # e.g. http://facebook.com/walmart, walmart is the username
    list_companies = ["DisneyLifeUK"]
    graph_url = "https://graph.facebook.com/"

    # the time of last weeks crawl
    last_crawl = datetime.datetime.now() - datetime.timedelta(weeks=4)
    last_crawl = last_crawl.isoformat()

    # create db connection
    connection = connect_db()
    cursor = connection.cursor()

    cursor.callproc('refresh_db', args=())
    print "DB Restored"

    # SQL statement for adding Facebook page data to database
    insert_info = ("""INSERT INTO page_info
                   (datetime, fb_id, likes, talking_about, username)
                   VALUES (NOW(), %s, %s, %s, %s)""")

    # SQL statement for adding Facebook posts to database
    insert_posts = ("""INSERT INTO post_info
                    (fb_post_id, message, likes_count, time_created, shares, type, status_type, link, time_updated, page_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""")

    # SQL statement for adding Facebook comments to database
    # Must update to include all fields
    insert_comments = ("""INSERT INTO comment_info
                       (comment_id, message, likes_count, time_created, post_id, from_username, from_userid, replies_count, sentiment)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""")

    for company in list_companies:
        # make graph api url with company username
        current_page = graph_url + company

        page_url = create_page_url(current_page, APP_ID, APP_SECRET)

        # open public page in facebook graph api
        json_fbpage = render_to_json(page_url)

        #gather our page level JSON Data
        page_data = (json_fbpage["id"], json_fbpage["likes"],
                     json_fbpage["talking_about_count"],
                     json_fbpage["username"])

        # insert the data we pulled into db
        cursor.execute(insert_info, page_data)
        print page_data

        # grab primary key
        last_key = cursor.lastrowid

        # extract post data
        post_url = create_post_url(current_page, APP_ID, APP_SECRET)

        post_data = []
        post_data = scrape_posts_by_date(post_url, last_crawl, post_data, APP_ID, APP_SECRET)

        comment_data = []
        # loop through and insert data
        for post in post_data:
            post.append(last_key)
            post = tuple(post)
            cursor.execute(insert_posts, post)

            #capture post id of data just inserted
            post_key = cursor.lastrowid
            print post_key
            comment_url = create_comments_url(graph_url, post[0], APP_ID, APP_SECRET)
            print comment_url
            comments = get_comments_data(comment_url, comment_data, post_key)

            #insert comments
            for comment in comments:
                comment = tuple(comment)
                cursor.execute(insert_comments, comment)

                comment_key = cursor.lastrowid
                print comment_key
                econtext_topics = get_econtext_data(comment)
                for topic in econtext_topics:


            comment_data = []

        # commit the data to the db
        connection.commit()

    connection.close()


if __name__ == "__main__":
    main()
