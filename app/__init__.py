from flask import Flask, render_template
from flask.ext.pymongo import PyMongo
import json, urllib2, requests, dateutil.parser
from datetime import datetime, timedelta

app = Flask(__name__)
app.config.from_object('settings')
mongo = PyMongo(app)

class fetchData:
	def __init__(self):
		self.url = "https://api.everyblock.com/content/philly/topnews"
		self.headers = {'Authorization':'token %s' % app.config['EVERYBLOCK_KEY']}
		self.params = {'schema':'news-articles'}

	def initDB(self):
		with app.app_context():
			r = requests.get(self.url, params=self.params, headers=self.headers).json()
			while True:
				for item in r['results']:
					mongo.db.articles.insert(item)
				if (r['next'] is None):
					break
				url = r['next']
				print url
				r = requests.get(url, headers=self.headers).json()

	def search(self):
		url = 'https://api.twitter.com/oauth2/token'
		headers = {
			"Authorization" : "Basic %s" % (TWITTER_KEY),
			"Content-Type" : "application/x-www-form-urlencoded;charset=UTF-8"
		}

		req = requests.post(url, data="grant_type=client_credentials" ,headers=headers)
		print req.json()['access_token']

	def raw(self, range):
		original = mongo.db.articles.find()
		data = []
		cap = (datetime.now() - timedelta(days = range)).strftime("%Y-%m-%d %X")
		print cap
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
	data = fetchData().raw(5)
	return render_template('index.html', data=data)
