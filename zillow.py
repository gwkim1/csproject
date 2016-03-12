#import requests
import bs4
import urllib.parse
import urllib.request
import re



# Dictionary used when extracting house type information from a detailed page about a house option
HOUSE_TYPE_DICT_DETAILED = {"Condo": "condos/co-ops", "Single Family": "houses", "Multi Family": "apartments", "Cooperative": "condos/co-ops"}

# Dictionary used to extract house type information from the initial search page
HOUSE_SEARCH_DICT = {"co-op": "condos/co-ops", "condo": "condos/co-ops", "condos": "condos/co-ops", "apartment": "apartments", "apartments": "apartments", "houses": "houses", "house": "houses"}

# Dictionary used to format preferred house types according to the url structure of zillow
HOUSE_TYPE_DICT = {"houses": "house", "apartments": "apartment_duplex", "condos/co-ops": "condo", "townhomes": "townhouse", "manufactured": "mobile", "lots/land": "land"}




# Each House objects stores information about a single resulting rent/buy option from Zillow
class House:
	# global variable 
	house_id = 0
	
	def __init__(self, house_article, unit_info = None):
		'''
		Defines a new House object

		Inputs
		house_article: "article" tag in Zillow's html document for a single house
		unit_info: if the search has several room options, 
		each unit_info tag stores information about each room option
		'''
		# The final score weighted with various criteria will be stored here later
		self.score = None
		
		# Assign unique ids to each House object
		self.house_id = House.house_id
		House.house_id += 1
		
		# If the tags are missing any necessary information, this will later be
		# Set to True and an additional function follow_link is run
		self.missing_value = False

		# Tag within "house_article" that stores most information
		property_info = house_article.find("div", {'class': 'property-info'})

		# Set the coordinates (originally stored w/o floating point). 
		# This information is crucial in calculating scores
		# Using the Yelp and City of Chicago data 
		self.lat = float(house_article["latitude"])/1000000
		self.long = float(house_article["longitude"])/1000000

		# Link for page for each house options.
		# This is used when there are missing values on the initial search page
		# Or when the user wants to visit the Zillow page after getting
		# The final result of our software.
		self.link = "http://www.zillow.com" + house_article.find_all("a", {"class": "routable"})[1]["href"]
		
		# Address of the house
		self.address = property_info.find("a")["title"]

		# If the function get_house_type fails to extract the house type,
		# Set missing_value to True (a more detailed page will be visited later)
		if get_house_type(property_info.find('dt', {'class': 'listing-type'}).text) == "":
			self.missing_value = True
		else:
			self.house_type = get_house_type(property_info.find('dt', {'class': 'listing-type'}).text)

		# For the price, number of bedrooms, number of bathrooms and size,
		# 2 approaches were needed, as some rent search results
		# Contained multiple options with different values
		# If the rent search result includes multiple options:
		if unit_info != None:
			# Use extract_numbers to extract numerical value from various different formats
			self.price = extract_numbers(unit_info.find("td", {"class":"grouped-result-price"}).text)
			self.bedroom = extract_numbers(unit_info.find("td", {"class":"grouped-result-beds"}).text)
			self.bathroom = extract_numbers(unit_info.find("td", {"class":"grouped-result-baths"}).text)
			self.size = extract_numbers(unit_info.find("td", {"class":"grouped-result-sqft"}).text)
		
		# If there is only a single option:
		else:
			# If the tag for price is not present, set missing_value to True
			if property_info.find('dt', {'class': 'price-large'}) == None:
				self.missing_value = True
			# Or the tag might be present without price information
			elif property_info.find('dt', {'class': 'price-large'}).text == "":
				self.missing_value = True
			else:
				self.price = extract_numbers(property_info.find('dt', {'class': 'price-large'}).text)

			# Run the function for setting number of bathroom, number of bedroom and size
			self.set_beds_baths_sqft(property_info)
			
		# If any missing values were detected during the above process,
		# We need to visit the page with details about a single house option
		if self.missing_value:
			self.follow_link(self.link)
			
		# Dictionary that stores above information as values
		self.info_dict = {"address": self.address, "price" : self.price, "house_type": self.house_type, "bedroom": self.bedroom, "bathroom": self.bathroom, "size": self.size, "link": self.link}


	def follow_link(self, link):
		'''
		If there were any missing values about a house in the initial search page,
		Follow link towards a more detailed page to extract information
		
		Input
		link: link to detailed page that can be acquired from each "article" tag
		'''
		# Get a new beautifulsoup object with the new link
		new_soup = get_soup(link)

		# Find the div tag that stores information about the house type
		top_facts = new_soup.find("div", {"class": "top-facts"}).find_all("li")

		# There are other information about the house as well, so these lines
		# Determine whether the information about the house type
		for fact in top_facts:
			if fact.text in HOUSE_TYPE_DICT_DETAILED:
				self.house_type = HOUSE_TYPE_DICT_DETAILED[fact.text]

		# Set house price by finding the appropriate tag
		self.price = extract_numbers(new_soup.find("div", {"class": "main-row"}).text)


	def set_beds_baths_sqft(self, property_info):
		'''
		Set the number of bedrooms, number of bathrooms, and size of a single house
		'''
		# First set default value in case the information is not available
		self.bedroom = 0
		self.bathroom = 0
		self.size = 0
	
		# If the tag for our target information is present (this is almost always True)
		if property_info.find('span', {'class': 'beds-baths-sqft'}) != None:
			
			# Split the text within the tag. The original text is 
			# In the following form: "1 bd • 1 ba • 1,000 sqft"
			beds_baths_sqft = property_info.find('span', {'class': 'beds-baths-sqft'}).text.split(" ")
			
			# Since sometimes a few of the three information are missing from the text,
			# Save information if the text includes "bds", "bd", "ba" or "sqft"
			for i in range(len(beds_baths_sqft)):
				if beds_baths_sqft[i] == "bds" or beds_baths_sqft[i] == "bd":
					# Since I splitted the text based on spaces,
					# The actual number is in the previous element of the list
					self.bedroom = extract_numbers(beds_baths_sqft[i-1])
				elif beds_baths_sqft[i] == "ba":
					self.bathroom = extract_numbers(beds_baths_sqft[i-1])
				elif beds_baths_sqft[i] == "sqft":
					self.size = extract_numbers(beds_baths_sqft[i-1])

			# 0 number of bedroom is sometimes shown as "Studio"
			if beds_baths_sqft[0] == "Studio":
				self.bedroom = 0


def get_house_type(type_str):
    '''
    Extracts house type from the text within the tag that includes relevant info
    
    Input
    type_str: text within the tag

    NOTE: usually type_str is in the form "Apartments for Sale"
    but there are many exceptions such as "Foreclosure" or "For Sale by Owner"
    '''
    # Convert to lowercase letters
    type_str = type_str.lower()
    # First set a default value in case house type is not identified
    house_type = ""
    # Trim the part that includes information about type of listing
    if "for sale" in type_str:
        type_str = type_str.replace("for sale", "").strip()
    elif "for rent" in type_str:
        type_str = type_str.replace("for rent", "").strip()
    
    # If the remaining string includes one of the house types, return the type
    for search_term in HOUSE_SEARCH_DICT:
        if search_term in type_str:
            house_type = HOUSE_SEARCH_DICT[search_term]        
            return house_type

    # If the house type is not identified, the default value "" will be returned
    return house_type


def create_house_objects(soup, url):
	'''
	With the given search url for Zillow, create a House object for each result
	and return the list of House objects

	Input
	url: zillow search url created with create_url function and user inputs
	soup: beautifulsoup object created by the url
	'''
	# When creating multiple soup objects for several pages, Zillow sometimes
	# Blocks excessive queries and sends the soup of a blank page instead.
	# These two lines constantly tries get_soup until the soup contains info
	while soup.find("article", {"class": "property-listing"}) == None:
		soup = get_soup(url)

	# soup_list is a list of soups to use. This is necessary because
	# Several initial search pages must be visited for results over 30
	soup_list = [soup]

	# If the bottom part of zillow's search results column has the "next" button,
	# Append additional soups from next pages to the soup_list
	if soup.find("li", {"class": "zsg-pagination-next"}) != None:
		soup_list += find_additional_links(soup, [])

	#print("soup_list length", len(soup_list))
	#print(len(soup_list))
	
	# Create a list to store the "article" tags for each house
	house_articles_list = []
	
	soup_count = 0

	# For each beautifulsoup object 
	for eachsoup in soup_list:

		soup_count += 1

		# Find all "article" tags, which each represent each house
		house_articles = eachsoup.find_all("article", {"class": "property-listing"})

		# If there are less than 4 results, Zillow also shows similar results 
		# Around the target zipcode, which I decided to exclude
		# They share the same type of "article" tag but with added class name
		similar_house_articles = eachsoup.find_all("article", {"class": "relaxed-result"})

		# After deleting similar results from the list of articles
		for similar_house in similar_house_articles:
			house_articles.remove(similar_house)
		print("soup_count:", soup_count, "num of articles:", len(house_articles))

		# Append this beautifulsoup's list of articles to the total list of articles
		house_articles_list += house_articles	
		print("soup_count:", soup_count, "after adding:", len(house_articles_list))

	# Create a list to store the list of actual house objects
	house_list = []

	article_count = 0
	# For each article in the total article list created:
	for house_article in house_articles_list:
		article_count += 1	

		# 
		if house_article.find("div", {'class': 'property-info'}).find("a") != None:
			temp_address = house_article.find("div", {'class': 'property-info'}).find("a")["title"]
		else:
			temp_address = "No"
		print("article_count:", article_count, temp_address)

		# If the article represents a rent option with multiple suboptions:
		if "grouped" in house_article["class"]:
			# Find the div that represent the subunits
			unit_list = house_article.find("div", {"class": "unit-list"}).find_all("tr")
			for unit_tr in unit_list:
				# Pass both the article and the "tr" tag to create a House object
				# And add it to the list of House objects
				house_list.append(House(house_article, unit_tr))
		else:
			# If the article represents a single option, create a House object
			# Immediately and add it to the list of House objects
			house_list.append(House(house_article))

	return house_list


def get_multiple_units(house_article):
	'''
	If the house_article contains multiple options for rent,
	follow the link, scrape information and return the list of House objects.
	'''
	# Assuming this
	#if "grouped" in house_article["class"]:
	link = "http://www.zillow.com" + house_article.find_all("a", {"class": "routable"})[1]["href"]
	link_soup = get_soup(link)
	#print(link_soup.find("body")["id"])
	#print(link_soup.find("table", {"id" : "units-list_available"}))
	print("This link is visited:", link)
	table_match_list = []
	if link_soup.find("table", {"id" : "units-list_available"}) != None:
		table_match_list = link_soup.find("table", {"id" : "units-list_available"}).find_all("tr", {"class": "matches-filters"})
	print("Number of matches-filters", len(table_match_list))
	house_list = []
	match_count = 0
	for match in table_match_list:
		match_count += 1
		print("match_count:", match_count)
		house_list.append(House(house_article, unit_info = match))

	return house_list

    
def extract_numbers(num_str):
    '''
    Extract only the numbers from a string containing numbers
    And adjust appropriately for non-numeric letters related
    To the value of the numbers

    Input:
    num_str: string containing numbers

    Output:
    int/float that num_str represents
    '''
    # Set a default value
    num = ""

    # Add each letter to "num" only if it is a number
    for letter in num_str:
        if re.search("[0-9]", letter) != None:
            num += letter
        # If we find a floating point, stop the process
        # This is possible because no numeric value I use
        # Has a meaningful floating value after "."
        elif letter == ".":
        	break
    
    # If the price is repesented with K, return the number * 1000
    if len(num) > 0 and re.search("[0-9][Kk]", num_str) != None:
        return eval(num) * 1000
    elif len(num) > 0:
        return eval(num)
    else:
    	# If no number is found where there should be a number,
    	# Returning -1 would allow later functions to exclude this
    	# House option from the list of House objects
        return -1


def create_url(zipcode, listing_type, criteria_list):
	'''
	Creates a working url based on user input

	Inputs:
	zipcode: zipcode within which the user wants the search
	listing_type: either "sale" or "rent"
	criteria_list: list of lists that sets each condition
	e.g. [["price", 1000, 2000], ["bedroom", 1, 3], ["size", 800, 1000], 
		  ["house_type", "houses", "apartments", "condos/co-ops"]]
	for numerical variable, the two number represents lower/upper bound
	for categorical variable, possible values are listed in order of preference

	Returns:
	a string representing a zillow url
	'''
	# Set default values
	price_range = (0, 0) 
	min_bedroom = 0
	min_bathroom = 0
	house_types = []
	size_range = (0, 0)

	# For each condition(list within list), change the default value
	# If there is a condition specified in criteria_list
	for condition in criteria_list:
		if condition[0] == "price":
			price_range = (condition[1], condition[2])
		elif condition[0] == "bedroom":
			min_bedroom = condition[1]
		elif condition[0] == "bathroom":
			min_bathroom = condition[1]
		elif condition[0] == "size":
			size_range = (condition[1], condition[2])
		elif condition[0] == "house_type":
			house_types = condition[1:]

	# Define base_url and end_url that would be added in front and back
	base_url = "http://www.zillow.com/homes/"
	end_url = ""

	# Change base and end_url based on whether the user wants 
	# rent or sale options
	if listing_type == "sale":
		base_url += "for_sale/"
		end_url = "/0_mmm/"
	else:
		base_url += "for_rent/"

	# For the scope of our project, we are only letting users
	# Search for houses within Chicago.
	base_url += "Chicago-IL-" + str(zipcode) + "/"

	# Include price condition in the url.
	if not (price_range[0] == 0 and price_range[1] == 0):
		if listing_type == "sale":
			base_url += str(price_range[0]) + "-" + str(price_range[1]) + "_price/"
		else:
			base_url += str(price_range[0]) + "-" + str(price_range[1]) + "_mp/"

	# Include the minimum bedroom/bathroom condition
	if min_bedroom > 0 and min_bedroom < 7:
		base_url += str(min_bedroom) + "-_beds/"
	if min_bathroom > 0 and min_bathroom < 7:
		base_url += str(min_bathroom) + "-_baths/" 

	# Include the size condition
	if not (size_range[0] == 0 and size_range[1] == 0):
		base_url += str(size_range[0]) + "-" + str(size_range[1]) + "_size/"		

	# Include the house_type condition by adding all preferred house types
	# In the url. HOUSE_TYPE_DICT is used to format according to the url format
	if len(house_types) > 0:
		addition_list = []
		for house_type in house_types:
			addition_list.append(HOUSE_TYPE_DICT[house_type])
		addition = ",".join(addition_list)
		base_url += addition + "_type"

	# Return the completed url after adding end_url
	base_url += end_url

	return base_url


def get_soup(url):
	'''
	Returns a beautifulsoup object of an html document associated with the url
	'''
	response = urllib.request.urlopen(url)
	# Decodes the response object to a string
	str_response = response.readall().decode('utf-8')
	# Use lxml parser for getting the beautifulsoup object
	return bs4.BeautifulSoup(str_response, "lxml")


def find_additional_links(soup, soup_list):
	'''
	Recursive function for getting beautifulsoup objects
	For each page that contains the results

	Inputs
	soup: beautifulsoup object of the current page
	soup_list: cumulative list of soup objects

	Returns
	a complete soup_list
	'''
	# Base case: If the "Next" button is no longer found in the list of
	# Pages in zillow, return the current soup_list
	if soup.find("li", {"class": "zsg-pagination-next"}) == None:
		return soup_list

	# Recursive case
	# Create the full link that would lead to the next result page
	next_link = "http://www.zillow.com" + soup.find("li", {"class": "zsg-pagination-next"}).find("a")['href']

	# Since zillow sometimes returns blank soup instead of the actual one,
	# Create a new shoup based on next_link and make sure the soup has info
	new_soup = get_soup(next_link)
	while new_soup.find("article", {"class": "property-listing"}) == None:
		new_soup = get_soup(next_link)
	soup_list.append(new_soup)

	# Continue the recursion with the new_soup and soup_list
	return find_additional_links(new_soup, soup_list)