#import requests
import bs4
import urllib.parse
import urllib.request
import re


class House:
	# Need to work more on this
	def __init__(self, property_info, unit_list):

		'''
		if there are multiple matching list, we need to approach 

		We assign: address, price, doz, built_year, bedroom, bathroom, size, listing_type and lat/long
		'''
		# There is a property info without an address!! what is this?
		if property_info.find("span", {'itemprop': 'streetAddress'}) == None:
			if property_info.find("dt", {'class': 'building-name-address'}) != None:
				self.address = property_info.find("dt", {'class': 'building-name-address'}).text
			else:
				self.address = None
			#print("this is what went wrong", property_info)
		else:
			self.address = property_info.find("span", {'itemprop': 'streetAddress'}).text



		if unit_list != None:
			self.bedroom = extract_numbers(unit_list.find('td', {'class': 'grouped-result-beds'}).text)
			self.price = extract_numbers(unit_list.find('td', {'class': 'grouped-result-price'}).text)
			self.size = extract_numbers(unit_list.find('td', {'class': 'zsg-table-col_num grouped-result-sqft'}).text)
			self.doz = None
			self.built_year = None
			self.bathroom = None
			latlong_str = property_info.find("a", {"class": "routable"})["href"][-27:-4]
			latindex = 0
			longindex = 0
			for letter in latlong_str:
				if letter == "/":
					latindex = latlong_str.find(letter)
				elif letter == ",":
					longindex = latlong_str.find(letter)
			self.lat = float(latlong_str[latindex+1:longindex])
			self.long = float(latlong_str[longindex+1:])
 
			# for lat and long, use something like this: prop[43].find("a", {"class": "routable"})["href"][-27:]
			# and extract numbers from that
			#self.lat = eval(property_info.find('meta', {'itemprop': 'latitude'})["content"])
			#self.long = eval(property_info.find('meta', {'itemprop': 'longitude'})["content"])	

		else:
			if property_info.find('dt', {'class': 'price-large'}) == None:
				# Need to check this once
				# I don't think zestimate equals price. They are totally different.
				self.price = extract_numbers(property_info.find('dt', {'class': 'zestimate'}).text) * 1000
			elif property_info.find('dt', {'class': 'price-large'}).text[0] == "$":
				#self.price = eval(property_info.find('dt', {'class': 'price-large'}).text.replace(",", "")[1:])
				self.price = extract_numbers(property_info.find('dt', {'class': 'price-large'}).text)
			else:
				self.price = extract_numbers(property_info.find('dt', {'class': 'price-large'}).text) * 1000

			beds_baths_sqft = property_info.find('span', {'class': 'beds-baths-sqft'}).text.split(" ")
			self.bedroom = eval(beds_baths_sqft[0])
			self.bathroom = eval(beds_baths_sqft[3])
			
			if len(beds_baths_sqft) >= 6:
				self.size = eval(beds_baths_sqft[6].replace(",", ""))
			else:
				# This is problematic. Same.
				self.size = 0
			if property_info.find('dt', {'class': 'doz'}) == None:
				self.doz = 0
			else:
				self.doz = extract_numbers(property_info.find('dt', {'class': 'doz'}).text)


			self.lat = eval(property_info.find('meta', {'itemprop': 'latitude'})["content"])
			self.long = eval(property_info.find('meta', {'itemprop': 'longitude'})["content"])				
			#elif re.search(property_info.find('dt', {'class': 'doz'}).text[0], "[0-9]") == None:
			#	self.doz = property_info.find('dt', {'class': 'doz'}).text[10]
			#else:
			#	self.doz = eval(property_info.find('dt', {'class': 'doz'}).text.split(" ")[0])
			
			if property_info.find('span', {'class': 'built-year'}) != None:
				self.built_year = eval(property_info.find('span', {'class': 'built-year'}).text[9:])
			else:
				# This is problematic. Need to change to None later
				self.built_year = 0

		# Not sure if this would work.
		if "For Rent" in property_info.find("dt", {"class": "listing-type"}).text:
			self.listing = "for rent"
		else:
			self.listing = "for sale"

		if property_info.find('meta', {'itemprop': 'latitude'}) == None:
			print("this went wrong", property_info)

		self.info_dict = {"price" : self.price, "days_on_zillow" : self.doz, "built_year" : self.built_year, "bedroom": self.bedroom, "bathroom": self.bathroom, "size": self.size}
		
		self.weighted_score = 0


# This is unnecessary. just for reference
URL = "http://www.zillow.com/homes/for_sale/Chicago-IL-60615/84617_rid/1-_beds/50000-60400_price/178-215_mp/any_days/built_sort/41.81521,-87.554469,41.794992,-87.63824_rect/13_zm/"


def extract_numbers(num_str):
	num = ""
	for letter in num_str:
		if re.search("[0-9]", letter) != None:
			num += letter
	if len(num) > 0:
		return eval(num)
	else:
		# Should I return None or 0?
		return None


HOUSE_TYPE_DICT = {"houses": "house", "apartments": "apartment_duplex", "condos/co-ops": "condo", "townhomes": "townhouse", "manufactured": "mobile", "lots/land": "land"}
	#"house,condo,mobile,land,townhouse, apartment_duplex    _type"

def create_url(zipcode, listing_types = [], price_range = (0, 0), min_bedroom = 0, min_bathroom = 0, house_types = [], size_range = (0, 0)):
	'''
	zipcode: zipcode
	For listing_type and house_type the following are the options(put in as string)
	listing_type: sale, rent, potential listings, recently sold
	house_type: houses, apartments, condos/co-ops, townhomes, manufactured, lots/land
	-> for the url: house,apartment_duplex,condo,townhouse,mobile,land + need to add "_type"
	'''
	base_url = "http://www.zillow.com/homes/"
	end_url = ""

	# only three cases. for sale, for rent, for both
	# Should add "rent", "sale"
	# The "both" case doesn't work
	if len(listing_types) in (0, 2):
		base_url += "for_sale/"
		end_url = "0_mmm/1_fr/"
	elif listing_types[0] == "sale":
		base_url += "for_sale/"
		end_url = "0_mmm/"
	else:
		base_url += "for_rent/"

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

	if len(house_types) > 0:
		addition_list = []
		for house_type in house_types:
			addition_list.append(HOUSE_TYPE_DICT[house_type])
		addition = ",".join(addition_list)
		base_url += addition + "_type"

	# need to work with listing_type
	base_url += end_url


	return base_url


def get_soup(url):
	response = urllib.request.urlopen(url)
	str_response = response.readall().decode('utf-8')
	return bs4.BeautifulSoup(str_response, "lxml")


def find_additional_links(soup, soup_list = []):
	'''
	*IMPORTANT: need to limit the search result to less than 1000. Zillow only supports 1000
	
	should always follow the "nextpage" link

	This function would return the soup for each page.
	'''
	# Base case
	if soup.find("li", {"class": "zsg-pagination-next"}) == None:
		#print("finally", type(soup_list))
		return soup_list

	# Recursive case
	next_link = "http://www.zillow.com" + soup.find("li", {"class": "zsg-pagination-next"}).find("a")['href']
	new_soup = get_soup(next_link)
	soup_list.append(new_soup)
	#print("will run the function again")
	#print("len(soup_list):", len(soup_list))
	return find_additional_links(new_soup, soup_list)
	#pages = page_tag.find_all("a", {"onclick": re.compile(r'SearchMain*')})


def create_house_objects(soup):
	'''
	many codes repeated with get_house_info, but we'll deal with this later
	'''
	soup_list = [soup]
	if soup.find("li", {"class": "zsg-pagination-next"}) != None:
		soup_list = find_additional_links(soup)

	house_articles_list = []
	for eachsoup in soup_list:
		house_articles = soup.find_all("article", {"class": "property-listing"})
		similar_house_articles = soup.find_all("article", {"class": "relaxed-result"})
		for similar_house in similar_house_articles:
			house_articles.remove(similar_house)	
		house_articles_list += house_articles	

	#print(len(house_articles))


	'''
	# change to if there is a nextpage link
	if len(house_articles) >= 50:
		#page_tag = soup.find("div", {"id": "search-pagination-wrapper"})
		#pages = page_tag.find_all("a", {"onclick": re.compile(r'SearchMain*')})
		print("too many search results: try to add conditions")
		return
	'''

	house_list = []
	#print(len(house_articles))
	for house_article in house_articles_list:
	
	#if this is a multiple listing, from article we need to approach unit-list instead of property-listting-data -> property-info
	
		if "grouped" in house_article["class"]:
			print("this is a grouped article")
			unit_list = house_article.find("div", {"class": "unit-list"})
		else:
			unit_list = None
		property_info = house_article.find("div", {'class': 'property-info'})
			
		#print(property_info)
		#house = House(property_info)
		#print("House created")
		house_list.append(House(property_info, unit_list))
	return house_list



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
	house_articles = soup.find_all("article", {"class": "property-listing"})
	similar_house_articles = soup.find_all("article", {"class": "relaxed-result"})
	
	for similar_house in similar_house_articles:
		house_articles.remove(similar_house)

	# Need to fix this too
	if len(house_articles) >= 50:
		print("too many search results: try to add conditions")
		return
		# And this should automatically lead back to create_url

	#house_articles.difference_update(similar_house_articles)
	# we may want address, latlong, house/listing, price, bedroom, bathroom, size, built_year, days on zillow
	# For each house
	
	
	final_result = []
	for house_article in house_articles:
		house = house_article.find("div", {'class': 'property-info'})
		#print(house)
		#print(house.find("span", {'itemprop': 'streetAddress'}).text)
		#print(house.find("span", {'itemprop': 'streetAddress'}).text)
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

