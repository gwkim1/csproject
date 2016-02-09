import requests
import bs4



def get_soup():
	# This is the ZWSID I got for my account. 1000 daily max query
	ZWSID = "X1-ZWz1f5eb856eq3_23up5"
	'''
	Below is an example of calling the API for the address for the exact address match "2114 Bigelow Ave", "Seattle, WA": 
	http://www.zillow.com/webservice/GetSearchResults.htm?zws-id=<ZWSID>&address=2114+Bigelow+Ave&citystatezip=Seattle%2C+WA
	'''



	url = "http://www.zillow.com/webservice/GetSearchResults.htm?zws-id=X1-ZWz1f5eb856eq3_23up5&address=2114+Bigelow+Ave&citystatezip=Seattle%2C+WA"
	r = requests.get(url)
	txt = r.text
	soup = bs4.BeautifulSoup(txt, "lxml")

	return soup