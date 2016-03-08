#import requests
import bs4
import urllib.parse
import urllib.request
import re


class House:
	# Need to work more on this
	def __init__(self, house_article, unit_info = None, missing_value=False):

		'''
		if there are multiple matching list, we need to approach 

		We assign: address, price, doz, built_year, bedroom, bathroom, size, and lat/long
		'''
		# Just for debugging purpose. will delete later
		self.article = house_article

		property_info = house_article.find("div", {'class': 'property-info'})

		self.lat = float(house_article["latitude"])/1000000
		self.long = float(house_article["longitude"])/1000000
		self.score = None

		# There is a property info without an address!! what is this?
		if property_info.find("span", {'itemprop': 'streetAddress'}) == None:
			if property_info.find("dt", {'class': 'building-name-address'}) != None:
				self.address = property_info.find("dt", {'class': 'building-name-address'}).text
			else:
				self.address = None
			#print("this is what went wrong", property_info)
		else:
			self.address = property_info.find("span", {'itemprop': 'streetAddress'}).text

		if unit_info != None:
			self.price = extract_numbers(unit_info.find("td", {"class": "building-units-price"}).text)
			self.bedroom = eval(unit_info["data-bedroom"])
			self.bathroom = extract_numbers(unit_info.find("td", {"class": "building-units-baths"}).text)
			self.size = extract_numbers(unit_info.find("td", {"class": "building-units-sqft"}).text)
			# what about self.doz?
			self.doz = -1
			# house_type is also not done
	
			if get_house_type(property_info.find('dt', {'class': 'listing-type'}).text) == "":
				missing_value = True
			else:
				self.house_type = get_house_type(property_info.find('dt', {'class': 'listing-type'}).text)

		
		else:
			if get_house_type(property_info.find('dt', {'class': 'listing-type'}).text) == "":
				missing_value = True
			else:
				self.house_type = get_house_type(property_info.find('dt', {'class': 'listing-type'}).text)
			#self.house_type = get_house_type(property_info.find('dt', {'class': 'listing-type'}).text)

			# This is wrong. zestimate shouldn't be used. should follow link instead.
			if property_info.find('dt', {'class': 'price-large'}) == None:
				missing_value = True
				# Need to check this once
				# I don't think zestimate equals price. They are totally different.
				#if property_info.find('dt', {'class': 'zestimate'}) == None:
					#print(property_info.find('dt', {'class': 'zestimate'}))
				#self.price = extract_numbers(property_info.find('dt', {'class': 'zestimate'}).text) * 1000
			#elif property_info.find('dt', {'class': 'price-large'}).text[0] == "$":
				#self.price = eval(property_info.find('dt', {'class': 'price-large'}).text.replace(",", "")[1:])
				#self.price = extract_numbers(property_info.find('dt', {'class': 'price-large'}).text)
			else:
				self.price = extract_numbers(property_info.find('dt', {'class': 'price-large'}).text)

			if property_info.find('span', {'class': 'beds-baths-sqft'}) != None:
				beds_baths_sqft = property_info.find('span', {'class': 'beds-baths-sqft'}).text.split(" ")

				if beds_baths_sqft[0] == "Studio":
					self.bedroom = 0
					if len(beds_baths_sqft) >= 3:
						self.bathroom = eval(beds_baths_sqft[2])
					else:
						self.bathroom = 0
					if len(beds_baths_sqft) >= 6:
						self.size = eval(beds_baths_sqft[5].replace(",", ""))
					else:
						# This is problematic. Same.
						self.size = 0				
				else:
					self.bedroom = eval(beds_baths_sqft[0])
					self.bathroom = eval(beds_baths_sqft[3])
					if len(beds_baths_sqft) >= 6:
						self.size = eval(beds_baths_sqft[6].replace(",", ""))
					else:
						# This is problematic. Same.
						self.size = 0
			
			else:
				self.bedroom = 0
				self.bathroom = 0
				self.size = 0
			
			if property_info.find('dt', {'class': 'doz'}) == None:
				self.doz = 0
			else:
				self.doz = extract_numbers(property_info.find('dt', {'class': 'doz'}).text)


			#self.lat = eval(property_info.find('meta', {'itemprop': 'latitude'})["content"])
			#self.long = eval(property_info.find('meta', {'itemprop': 'longitude'})["content"])				
			#elif re.search(property_info.find('dt', {'class': 'doz'}).text[0], "[0-9]") == None:
			#	self.doz = property_info.find('dt', {'class': 'doz'}).text[10]
			#else:
			#	self.doz = eval(property_info.find('dt', {'class': 'doz'}).text.split(" ")[0])
			
			if property_info.find('span', {'class': 'built-year'}) != None:
				self.built_year = eval(property_info.find('span', {'class': 'built-year'}).text[9:])
			else:
				# This is problematic. Need to change to None later
				self.built_year = 0



		if missing_value:
			print("we will run follow_link")
			self.follow_link(house_article)

		# Need to check back on this
		self.info_dict = {"price" : self.price, "house_type": self.house_type, "bedroom": self.bedroom, "bathroom": self.bathroom, "size": self.size}
		
		self.weighted_score = 0

# This has to be a part of House object
	def follow_link(self, house_article):
		link = "http://www.zillow.com" + house_article.find_all("a", {"class": "routable"})[1]["href"]
		new_soup = get_soup(link)

		top_facts = new_soup.find("div", {"class": "top-facts"}).find_all("li")
		for fact in top_facts:
			if fact.text in HOUSE_TYPE_DICT_2:
				self.house_type = HOUSE_TYPE_DICT_2[fact.text]
				#print(house_type)
			#return

		self.price = extract_numbers(new_soup.find("div", {"class": "main-row"}).text)


NEW_LINK_DICT = {
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

#self.price = extract_numbers(link_soup.find("div", {"class": "main-row"}).text)
# house_type isn't working.

#self.house_type = link_soup.find("div", {"class": "top-facts"}).find_all("li")

# Is there a way to use regular expression here for s's?

HOUSE_TYPE_DICT_2 = {"Condo": "condos/co-ops", "Single Family": "houses", "Multi Family": "apartments", "Cooperative": "condos/co-ops"}

HOUSE_SEARCH_DICT = {"Co-op": "condos/co-ops", "Condo": "condos/co-ops", "Condos": "condos/co-ops", "Apartment": "apartments", "Apartments": "apartments"}

HOUSE_TYPE_DICT = {"houses": "house", "apartments": "apartment_duplex", "condos/co-ops": "condo", "townhomes": "townhouse", "manufactured": "mobile", "lots/land": "land"}

'''
def get_house_list(zipcode, listing_type, criteria_list):
    url = create_url(zipcode, listing_type, criteria_list)
    soup = get_soup(url)
    house_list = create_house_objects(soup)
    new_house_list = create_array(house_list, criteria_list, return_list=True)
    return new_house_list
'''


def get_house_type(type_str):
    house_type = ""
    if "For Sale" in type_str:
        type_str = type_str.replace("For Sale", "").strip()
    elif "For Rent" in type_str:
        type_str = type_str.replace("For Rent", "").strip()
    #print(type_str)
    #print(len(type_str))
    for search_term in HOUSE_SEARCH_DICT:
        if search_term in type_str:
            house_type = HOUSE_SEARCH_DICT[search_term]        
            return house_type

    return house_type 
		

def create_house_objects(soup):
	'''
	many codes repeated with get_house_info, but we'll deal with this later
	'''
	soup_list = [soup]
	if soup.find("li", {"class": "zsg-pagination-next"}) != None:
		soup_list += find_additional_links(soup)
	#print("soup_list length", len(soup_list))
	#print(len(soup_list))
	house_articles_list = []
	for eachsoup in soup_list:
		#print(type(eachsoup))
		house_articles = eachsoup.find_all("article", {"class": "property-listing"})
		#print(type(house_articles)()
		similar_house_articles = eachsoup.find_all("article", {"class": "relaxed-result"})
		#print(len(similar_house_articles))
		for similar_house in similar_house_articles:
			house_articles.remove(similar_house)	
		#print("after subtracting", len(house_articles))
		house_articles_list += house_articles	
		#print(len(house_articles_list))
	#print(len(house_articles_list))

	house_list = []
	#print(len(house_articles))
	for house_article in house_articles_list:
		if "grouped" in house_article["class"]:
			house_list += get_multiple_units(house_article)
		else:
			house_list.append(House(house_article))
	return house_list



def get_multiple_units(house_article):
	'''
	if the house_article contains multiple options for rent,
	follow the link, scrape all data and return the list of House objects.
	'''
	# Assuming this
	#if "grouped" in house_article["class"]:
	link = "http://www.zillow.com" + house_article.find_all("a", {"class": "routable"})[1]["href"]
	link_soup = get_soup(link)
	#print(link_soup.find("body")["id"])
	#print(link_soup.find("table", {"id" : "units-list_available"}))
	table_match_list = link_soup.find("table", {"id" : "units-list_available"}).find_all("tr", {"class": "matches-filters"})
	#print(len(table_match_list))
	house_list = []
	for match in table_match_list:
		house_list.append(House(house_article, unit_info = match))

	return house_list


def extract_numbers(num_str):
	# Also need to account for "M" as million
    num = ""
    for letter in num_str:
        if re.search("[0-9]", letter) != None:
            num += letter
    if len(num) > 0 and re.search("[0-9][Kk]", num_str) != None:
        return eval(num) * 1000
    elif len(num) > 0:
        return eval(num)
    else:
        # Should I return None or 0 or -1?
        return -1

def create_url(zipcode, listing_type, criteria_list):
	'''
	zipcode, listing_type = "", price_range = (0, 0), min_bedroom = 0, min_bathroom = 0, house_types = [], size_range = (0, 0)
	zipcode: zipcode
	For listing_type and house_type the following are the options(put in as string)
	listing_type: sale, rent, potential listings, recently sold
	house_type: houses, apartments, condos/co-ops, townhomes, manufactured, lots/land
	-> for the url: house,apartment_duplex,condo,townhouse,mobile,land + need to add "_type"

	criteria_list =  [["price", 1000, 2000, None, 300], ["bedroom", 1, 3, None, 400], ["size", 800, 1000, None, 100], ["house_type", "houses", "apartments", "condos/co-ops", 500]]
	'''
	price_range = (0, 0) 
	min_bedroom = 0
	min_bathroom = 0
	house_types = []
	size_range = (0, 0)

	for condition in criteria_list:
		#print(condition)
		if condition[0] == "price":
			price_range = (condition[1], condition[2])
		elif condition[0] == "bedroom":
			min_bedroom = condition[1]
		elif condition[0] == "bathroom":
			min_bathroom = condition[1]
		elif condition[0] == "size":
			size_range = (condition[1], condition[2])
		elif condition[0] == "house_type":
			house_types = condition[1:-1]
	#print(price_range)

	base_url = "http://www.zillow.com/homes/"
	end_url = ""

	if listing_type == "sale":
		base_url += "for_sale/"
		end_url = "0_mmm/"
	else:
		base_url += "for_rent/"

	# Would hardcoding in Chicago and IL be okay?
	base_url += "Chicago-IL-" + str(zipcode) + "/"

	# Do we need to check if min_price is smaller?
	if not (price_range[0] == 0 and price_range[1] == 0):
		if listing_type in ["", "sale"]:
			base_url += str(price_range[0]) + "-" + str(price_range[1]) + "_price/"
		else:
			base_url += str(price_range[0]) + "-" + str(price_range[1]) + "_mp/"

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

'''
def create_url_alt(zipcode, listing_type = "", price_range = (0, 0), min_bedroom = 0, min_bathroom = 0, house_types = [], size_range = (0, 0)):
	
	zipcode: zipcode
	For listing_type and house_type the following are the options(put in as string)
	listing_type: sale, rent, potential listings, recently sold
	house_type: houses, apartments, condos/co-ops, townhomes, manufactured, lots/land
	-> for the url: house,apartment_duplex,condo,townhouse,mobile,land + need to add "_type"
	
	base_url = "http://www.zillow.com/homes/"
	end_url = ""

	if listing_type in ["", "sale"]:
		base_url += "for_sale/"
		end_url = "0_mmm/"
	else:
		base_url += "for_rent/"

	# Would hardcoding in Chicago and IL be okay?
	base_url += "Chicago-IL-" + str(zipcode) + "/"

	# Do we need to check if min_price is smaller?
	if not (price_range[0] == 0 and price_range[1] == 0):
		if listing_type in ["", "sale"]:
			base_url += str(price_range[0]) + "-" + str(price_range[1]) + "_price/"
		else:
			base_url += str(price_range[0]) + "-" + str(price_range[1]) + "_mp/"

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
'''

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

# .find(COMMAND_DICT[key]) works.

#def get_house_info(soup, output_info = []):
'''
	As output_info, put the key of the COMMAND_DICT above.
	
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
'''


'''
	ONE APPROACH I TRIED WHICH IS MORE ACCRUATE BUT TAKES TOO MUCH TIME


	still missing house_type, doz, built_year
	
	link = "http://www.zillow.com" + house_article.find_all("a", {"class": "routable"})[1]["href"]
	link_soup = get_soup(link)
	if link_soup.find("body")["id"] == "hdp":
		print("this is hdp")
		self.address = link_soup.find("header", {"class": "addr"}).find("h1").find("span").text
		#print(self.address)
		beds_baths_sqft = link_soup.find("header", {"class": "addr"}).find("h3").find_all("span", {"class" : "addr_bbs"})
		#print(beds_baths_sqft)
		if beds_baths_sqft[0].text == "Studio":
			self.bedroom = 0
		else:
			self.bedroom = extract_numbers(beds_baths_sqft[0].text)
		self.bathroom = extract_numbers(beds_baths_sqft[1].text)
		self.size = extract_numbers(beds_baths_sqft[2].text)

		if "for-rent" in link_soup.find("span", {"id": "listing-icon"})["class"]:
			self.listing_type = "rent"
		else:
			self.listing_type = "sale"

		self.price = extract_numbers(link_soup.find("div", {"class": "main-row"}).text)

		self.lat = float(link_soup.find("span", {"id": "hdp-map-coordinates"})["data-latitude"])
		self.long = float(link_soup.find("span", {"id": "hdp-map-coordinates"})["data-longitude"])
		# div class "hdp-facts" can be useful
		# section id "hdp-neighborhood" contains walk and transit scores
		
		# house_type isn't working.
		#self.house_type = link_soup.find("div", {"class": "top-facts"}).find_all("li", {"id": re.compile('*')})


		# This is not completed either.
		self.info_dict = {"address": self.address, "price" : self.price, "bedroom": self.bedroom, "bathroom": self.bathroom, "size": self.size}

	else:
		print("this is bdp")
		table_tag_list = link_soup.find("table", {"id" : "units-list_available"}).find_all("a", {"class": "routable"})
		link_list = []
		for tag in table_tag_list:
			link_list.append(tag["href"])
		
		for link in link_list:
			new_link_soup = get_soup(link)
			#### Start getting the info here.
			#### How do we initialize mutliple houses in here?
'''




'''
	This was in the House object __init__
	extracting info from multiple units right from the original link. prbly not going to use this



			if "grouped" in house_article["class"]:
			# Should we set studios as having no bedroom?
			unit_list = house_article.find("div", {"class": "unit-list"})
			if unit_list.find('td', {'class': 'grouped-result-beds'}).text in ["Studios", "Studio"]:
				self.bedroom = 0				
			else:
				self.bedroom = extract_numbers(unit_list.find('td', {'class': 'grouped-result-beds'}).text)

			self.price = extract_numbers(unit_list.find('td', {'class': 'grouped-result-price'}).text)
			self.size = extract_numbers(unit_list.find('td', {'class': 'zsg-table-col_num grouped-result-sqft'}).text)
			self.doz = None
			self.built_year = None
			self.bathroom = None
'''