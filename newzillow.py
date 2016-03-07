import bs4
import urllib.parse
import urllib.request
import re

'''

icon strings that I didn't deal with yet: Foreclosure, Auction, For Sale by Owner

the order of articles are not ordered as shown in the website

I currently set default value as -1
'''



class House:
    def __init__(self, house_article):
        '''
        We assign: address, price, doz, built_year, bedroom, bathroom, size, listing_type and lat/long
        Let's add house_type too
        '''

        # need to deal with cases in which the data are missing.
        # There doesn't seem to be built_year in the new html structure

        # may have to clean "Chicago, IL" part at the back
        self.address = house_article.find("a", {"class": "zsg-photo-card-address"}).text
        
        self.price = extract_numbers(house_article.find("span", {"class": "zsg-photo-card-price"}).text)

        self.doz = extract_numbers(house_article.find("span", {"class": "zsg-photo-card-notification"}).text)

        self.beds_baths_sqft = house_article.find('span', {'class': 'zsg-photo-card-info'}).text.split(" ")
        self.bedroom = eval(self.beds_baths_sqft[0])
        self.bathroom = eval(self.beds_baths_sqft[3])
        self.size = extract_numbers(self.beds_baths_sqft[6])

        # or for listing_type, we can use span call "zsg-icon-for-sale" instead!!!!
        self.house_type, self.listing_type = get_house_and_listing_type(house_article.find('span', {'class': 'zsg-photo-card-status'}).text)

        self.lat = float(house_article["data-latitude"])/1000000
        self.long = float(house_article["data-longitude"])/1000000
        self.info_dict = {"price" : self.price, "days_on_zillow" : self.doz, "house_type" : self.house_type, "bedroom": self.bedroom, "bathroom": self.bathroom, "size": self.size}


HOUSE_TYPE_DICT = {"houses": "house", "apartments": "apartment_duplex", "condos/co-ops": "condo", "townhomes": "townhouse", "manufactured": "mobile", "lots/land": "land"}

# Keep on adding values in this dictionary
HOUSE_SEARCH_DICT = {"Co-op": "condos/co-ops"}


def get_house_and_listing_type(type_str):
    house_type = ""
    listing_type = ""
    if "For Sale" in type_str:
        listing_type = "sale"
        type_str = type_str.replace("For Sale", "")
    elif "For Rent" in type_str:
        listing_type = "rent"
        type_str = type_str.replace("For Sale", "")
    for search_term in HOUSE_SEARCH_DICT:
        if search_term in type_str:
            house_type = HOUSE_SEARCH_DICT[search_term]        
            return house_type, listing_type 

        # This is wrong. don't know what to do with "For Sale by Owner". One of them was condos/co-ops
        house_type = "houses"

    return house_type, listing_type 


def extract_numbers(num_str):
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
        base_url += addition + "_type/"

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

    This does not include the original soup
    '''
    # Base case
    next_page = soup.find("li", {"class":"zsg-pagination-next"})
    if next_page == None:
        return soup_list

    next_link = "http://www.zillow.com" + next_page.find("a")['href']
    new_soup = get_soup(next_link)
    soup_list.append(new_soup)
    return find_additional_links(new_soup, soup_list)


def create_house_objects(soup):
    '''
    many codes repeated with get_house_info, but we'll deal with this later
    '''
    soup_list = [soup]
    if soup.find("li", {"class": "zsg-pagination-next"}) != None:
        soup_list += find_additional_links(soup)

    # How should we get rid of similar results? I did find instead of find_all to exclude similar results that come out second
    house_articles_list = []
    for eachsoup in soup_list:
        house_articles_ul = eachsoup.find("ul", {"class": "photo-cards"})
        print(type(house_articles_ul))
        house_articles = house_articles_ul.find_all("article")
        house_articles_list += house_articles   


    house_list = []
    #print(len(house_articles))
    for house_article in house_articles_list:
        house_list.append(House(house_article))
    #if this is a multiple listing, from article we need to approach unit-list instead of property-listting-data -> property-info
    '''
        if "grouped" in house_article["class"]:
            print("this is a grouped article")
            unit_list = house_article.find("div", {"class": "unit-list"})
        else:
            unit_list = None
        property_info = house_article.find("div", {'class': 'property-info'})
    '''        
        #print(property_info)
        #house = House(property_info)
        #print("House created")
        
    return house_list
