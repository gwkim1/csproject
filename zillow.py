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


def create_url(zipcode, listing_type = [], price_range = (0, 0), min_bedroom = 0, min_bathroom = 0, house_type = [], size_range = (0, 0)):
	'''
	zipcode: zipcode
	listing_type: sale, rent, potential listings, recently sold
	house_type: houses, apartments, condos/co-ops, townhomes, manufactured, lots/land
	'''
	base_url = "http://www.zillow.com/homes/"
	# Would hardcoding in Chicago and IL be okay?
	base_url += "Chicago-IL-" + str(zipcode) + "/"

	# Do we need to check if min_price is smaller?
	if not (price_range[0] == 0 and price_range[1] == 0):
		base_url += str(price_range[0]) + "-" + str(price_range[1]) + "_price/"

	if min_bedroom > 0 and min_bedroom < 7:
		base_url += str(min_bedroom) + "-_beds/"
	if min_bathroom > 0 and min_bathroom < 7:
		base_url += str(min_bathroom) + "-_baths/"

	if not (size_range[0] == 0 and size_range[1] == 0):
		base_url += str(size_range[0]) + "-" + str(size_range[1]) + "_size/"		

	return base_url


def get_soup(url):
	response = urllib.request.urlopen(url)
	str_response = response.readall().decode('utf-8')
	return bs4.BeautifulSoup(str_response, "lxml")



# parts of the find_all and print command according to each output that we want to get
COMMAND_DICT = {
"address": ["'span', {'itemprop': 'streetAddress'}", "result.text"],
"latlong": ["'meta', {'itemprop': re.compile(r'^(latitude|longitude)$)}", "result['content']"],
"house/listing": [],
"price": ["'dt', {'class': 'price-large'}", "result.text"],
"bedroom": ["'span', {'class': 'beds-baths-sqft'}", "result.text"],
"bathroom": ["", ""], # same thing
"size": ["", ""], # same thing
"built_year": ["'span', {'class': 'built-year'}", "result.text"],
"days_on_zillow": ["'dt', {'class': 'doz'}", "result.text"],
}

def get_house_info(soup, output_info = []):
	houses = soup.find_all("div", {"class": "property-info"})
	# we may want address, latlong, house/listing, price, bedroom, bathroom, size, built_year, days on zillow
	# For each house
	for house in houses:
		#print(house)
		result_list = []
		# For each output information that the user wants
		for info in output_info:
			#print(info)
			#print(COMMAND_DICT[info])
			# Append the result into result_list
			#print(COMMAND_DICT[info][0])
			##########Why isn't this working?
			resultset = soup.find_all(COMMAND_DICT[info][0])
			print(resultset)
			result_list.append(resultset)
	return result_list
'''
for prop in prop_info:
    results = prop.find_all("span", {"itemprop": re.compile(r"^(streetAddress|addressRegion)$")})
    for result in results:
        print(result.text)
'''






