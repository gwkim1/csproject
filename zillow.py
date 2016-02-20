#import requests
import bs4
import urllib.parse
import urllib.request
import re


class House:
	# Need to work more on this
	def __init__(self, property_info):
		self.address = property_info.find("span", {'itemprop': 'streetAddress'}).text
		# add other information
	









URL = "http://www.zillow.com/homes/for_sale/Chicago-IL-60615/84617_rid/1-_beds/50000-60400_price/178-215_mp/any_days/built_sort/41.81521,-87.554469,41.794992,-87.63824_rect/13_zm/"


def create_url(zipcode, listing_type = [], price_range = (0, 0), min_bedroom = 0, min_bathroom = 0, house_type = [], size_range = (0, 0)):
	'''
	zipcode: zipcode
	For listing_type and house_type the following are the options(put in as string)
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
"address": ['span', {'itemprop': 'streetAddress'}],
"latlong": ['meta', {'itemprop': re.compile(r'^(latitude|longitude)$')}],
"house/listing": [],
"price": ['dt', {'class': 'price-large'}],
"bedroom": ['span', {'class': 'beds-baths-sqft'}],
"bathroom": ['span', {'class': 'beds-baths-sqft'}], # same thing
"size": ['span', {'class': 'beds-baths-sqft'}], # same thing
"built_year": ['span', {'class': 'built-year'}],
"days_on_zillow": ['dt', {'class': 'doz'}],
}

def get_house_info(soup, output_info = []):
	'''
	As output_info, put the key of the COMMAND_DICT above.
	'''
	houses = soup.find_all("div", {"class": "property-info"})
	# we may want address, latlong, house/listing, price, bedroom, bathroom, size, built_year, days on zillow
	# For each house
	final_result = []
	for house in houses:
		#print(house)
		result_list = [house.find("span", {'itemprop': 'streetAddress'}).text]
		# For each output information that the user wants
		for info in output_info:
			#print(info)
			#print(COMMAND_DICT[info])
			# Append the result into result_list
			#print(COMMAND_DICT[info][0])
			##########Why isn't this working?
			resultset = house.find_all(COMMAND_DICT[info][0], COMMAND_DICT[info][1])
			for result in resultset:
				if info == "latlong":
					result_list.append(result["content"])
				else:
					result_list.append(result.text)
			#print(type(COMMAND_DICT[info][0]))
			#print(COMMAND_DICT[info[0]])
			#print(resultset)
			final_result.append(result_list)
	return final_result
