#import requests
import bs4
import urllib.parse
import urllib.request

'''
def get_soup():
	# This is the ZWSID I got for my account. 1000 daily max query
	ZWSID = "X1-ZWz1f5eb856eq3_23up5"
	
	Below is an example of calling the API for the address for the exact address match "2114 Bigelow Ave", "Seattle, WA": 
	http://www.zillow.com/webservice/GetSearchResults.htm?zws-id=<ZWSID>&address=2114+Bigelow+Ave&citystatezip=Seattle%2C+WA
	



	url = "http://www.zillow.com/webservice/GetSearchResults.htm?zws-id=X1-ZWz1f5eb856eq3_23up5&address=2114+Bigelow+Ave&citystatezip=Seattle%2C+WA"
	r = requests.get(url)
	txt = r.text
	soup = bs4.BeautifulSoup(txt, "lxml")

	return soup
'''

URL = "http://www.zillow.com/homes/for_sale/Chicago-IL-60615/84617_rid/1-_beds/50000-60400_price/178-215_mp/any_days/built_sort/41.81521,-87.554469,41.794992,-87.63824_rect/13_zm/"


def create_url(search_terms):
	return


def get_soup(url):
	response = urllib.request.urlopen(url)
	str_response = response.readall().decode('utf-8')
	return bs4.BeautifulSoup(str_response, "lxml")