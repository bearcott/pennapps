from flask import Flask, render_template, request, make_response
from flask.ext.pymongo import PyMongo
import urllib2, requests, dateutil.parser, json
from datetime import datetime, timedelta

app = Flask(__name__)
app.config.from_object('settings')
mongo = PyMongo(app)

class twitter():
	def __init__(self):
		pass

	def getToken(self):
		url = 'https://api.twitter.com/oauth2/token'
		headers = {
			"Authorization" : "Basic %s" % (app.config['TWITTER_KEY']),
			"Content-Type" : "application/x-www-form-urlencoded;charset=UTF-8"
		}
		req = requests.post(url, data="grant_type=client_credentials" ,headers=headers)
		print "REFRESHED"
		return req.json()['access_token']

	def search(self, token, query):
		#makes sure that tweet links to something
		url = "https://api.twitter.com/1.1/search/tweets.json?q=%s filter:links" % (query)
		headers = {
			"Authorization" : "Bearer %s" % (token),
			"Content-Type" : "application/x-www-form-urlencoded;charset=UTF-8"
		}
		req = requests.get(url,headers=headers)
		
		try:
			req = req.json()
			if 'statuses' in req:
				return req['statuses']
			else:
				return []
		except ValueError, e:
			return []

class fetchData:

	def addTwitter(self, token, item):
		tweets = []
		#mentions goes up every favorite, retweet, tweet
		mentions = 0
		search = twitter().search(token, item['title'])
		for tweet in search:
			mentions += tweet['favorite_count']
			mentions += tweet['retweet_count']
			mentions += 1
			tweets.append({
				"id" : tweet['id_str'],
				"name" : tweet['user']['name'],
				"screen_name" : tweet['user']['screen_name'],
				"text" : tweet['text']
			})
			print tweet['id_str']

		item["twitter"] = {
				"mentions" : mentions,
				"tweets" : tweets
			}
		return

	def getGeo(self, item):
		url = "https://maps.googleapis.com/maps/api/geocode/json"
		params = {'key':app.config['GOOGLEMAPS_KEY'],'address':"%s Philadelphia, PA" % (item['location_name'])}
		coords = requests.get(url,params=params).json()
		item["coords"] = {
			"lat" : coords['results'][0]['geometry']['location']['lat'],
			"lng" : coords['results'][0]['geometry']['location']['lng']
		}
		return

	def createEntries(self):
		with app.app_context():
			url = "https://api.everyblock.com/content/philly/topnews"
			headers = {'Authorization':'token %s' % app.config['EVERYBLOCK_KEY']}
			params = {'schema':'news-articles','date':'descending'}
			r = requests.get(url, params=params, headers=headers).json()
			while True:
				#refresh the token
				token = twitter().getToken()
				for item in r['results']:
					self.addTwitter(token, item)
					self.getGeo(item)
					mongo.db.articles.insert(item)

				if (r['next'] is None):
					break
				url = r['next']
				print url
				r = requests.get(url, headers=headers).json()

	def raw(self, range):
		original = mongo.db.articles.find()
		data = []
		cap = (datetime.now() - timedelta(days = range)).strftime("%Y-%m-%d %X")
		#set a date cap
		for item in original:
			item['pub_date'] = str(dateutil.parser.parse(item['pub_date']).strftime("%Y-%m-%d %X"))
			item['real_date'] = str(dateutil.parser.parse(item['pub_date']).strftime("%B %d, %Y"))
			data.append(item)
			if (item['pub_date'] <= cap):
				break
		#interesting, mongodb.
		#data.rewind()
		return data


@app.route('/')
def hello():
	days = 1
	data = fetchData().raw(days)
	return render_template('index.html', data=data, days=days, safetitle="json.dumps(str(item['title']))")

@app.route('/georss/<days>')
def geo(days=1):
	days = int(days)
	data = fetchData().raw(days)
	xml = render_template('georss.xml', data=data)
	response = make_response(xml)
	response.headers["Content-Type"] = "application/kml"
	return response
