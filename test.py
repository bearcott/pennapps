import requests

url = 'https://api.twitter.com/oauth2/token'
headers = {
	"Authorization" : "Basic RHJLMWtGaGE2SkNTVHVOTXhIM1IzaHg1cjpGSXdreFVZYUtINldWWUlaTHNlZDJBTk9lWnk0UVh1RTcyaW9rU2tmUThhSEJYZ1VnSg==",
	"Content-Type" : "application/x-www-form-urlencoded;charset=UTF-8"
}

req = requests.post(url, data="grant_type=client_credentials" ,headers=headers)
print req.json()['access_token']