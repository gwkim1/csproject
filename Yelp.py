import rauth
import math
import time

# Note if the Yelp search does not work it may be due to expired time stamp, reboot VM to solve this issue

# Keys for API
CONSUMER_KEY = "_c-Jb5bdZr9eMlFpyrcx7g"
CONSUMER_SECRET = "6EPdVZpPAPREEcG-jpga1hPMhlk"
TOKEN = "1pRf9RrQKu7xdpkePMkAAbrCV9E-zr7W"
TOKEN_SECRET = "59dHWliuAzv5wyOMFDtW57u_GiM"
# In Meters
WALKING_DISTANCE = 1000
CATEGORIES = ["restaurants", "active", "arts", "education", "health", "nightlife", "shopping"]
ALPHABET = "abcdefghijklmnopqrstuvwxyz"
# Second Set of API keys just in case
#Consumer_Key2 =   "nPpvHrRlTBQGMWrb4eOeLQ"
#Consumer_Secret2 =  "ZzruromYSM0p0bFYfMk4vP2ddvY"
#Token2 =  "iplo0WJS4t-7RD32q5pnqmEKIYDq9Yfv"
#Token_Secret2 =   "BocWy4tiJkScUStUeNMY-QNBGe8"


def get_results(params):
  # This function is from http://letstalkdata.com/2014/02/how-to-use-the-yelp-api-in-python/
  session = rauth.OAuth1Session(consumer_key = CONSUMER_KEY, consumer_secret = CONSUMER_SECRET
  ,access_token = TOKEN, access_token_secret = TOKEN_SECRET)
  request = session.get("http://api.yelp.com/v2/search", params = params)
  data = request.json()
  session.close()
  return data


def get_search_parameters(lat, long, term, radius, limit, category_filter, sort=0, offset = 0):
  # See the Yelp API for more details
  # This function is a modified from http://letstalkdata.com/2014/02/how-to-use-the-yelp-api-in-python/
  '''
  Possible Filters
  term
  limit
  offset
  sort(0=Best matched (default), 1=Distance, 2=Highest Rated)
  category_filter (https://www.yelp.com/developers/documentation/v2/all_category_list)
  radius_filter(in meters, mac value is 40000)
  deals_filter
  '''
  params = {}
  params["ll"] = "{},{}".format(str(lat),str(long))
  params["radius_filter"] = radius
  if term != "":
    params["term"] = term
  if limit != 0:
    params["limit"] = limit
  if category_filter != "":
    params["category_filter"] = category_filter
  if sort !=0:
    params["sort"] = sort
  if offset !=0:
    params["offset"] = offset
  return params


def get_score(locations, category_filter, radius):
  location_raw_scores = []
  for location in locations:
    # Yelp only gives 20 results maximum per request, so it must be offset to get all of the results
    count, results = search(location, category_filter = category_filter, count = True, radius = radius)
    if count == 0:
      score = 0 
    else:
      if count > 20:
        # Makes additional requests to get more than 20 results
        iterations = math.ceil(count/20)-1
        offset = 20
        for i in range(iterations):
          additional_result = search(location, category_filter = category_filter, offset = offset, radius = radius)
          offset+=20
          results+=additional_result
      score = 0
      # Our yelp score is based on the aggregate ratings
      for result in results:
        score += result["rating"]
    location_raw_scores.append(score)

  # Reduces the max score down to 1, and calculates other score relative to the max
  max_score = 0
  for score in location_raw_scores:
    if score > max_score:
      max_score = score
  if max_score == 0:
    new_scores = [0]*len(location_raw_scores)
  else:
    new_scores = [x / max_score for x in location_raw_scores]
  return new_scores




def get_yelp_scores(locations, distance, preferences):
  # Calculates the score for each category, only if the user cares about the category
  score_list_category = []
  for i in range(len(CATEGORIES)):
    if preferences[i] == 0:
      score_list_category.append([0]*len(locations))
    else:
      score_list_category.append(get_score(locations, CATEGORIES[i], distance))
  score_list_location = list(map(list, zip(*score_list_category)))
  return score_list_location



def yelp_search(location, distance, term, category_filter = "", sort = 0, offset = 0):
  # returns list in order of name, distance, rating, # of reviews, location, letter
  total, results = search(location, term = term, radius = distance, category_filter = category_filter, sort = sort, count = True, offset=offset)
  result_list = []
  if results == (0, []):
    return []
  count = 0

  for result in results:
    if result["distance"] < float(distance):
      result_list.append(dict_to_list(result, ALPHABET[count]))
      count+=1
  return result_list, total


def dict_to_list(dictionary, letter):
  # Converts dictionary to list in wanted format
  categories = ""
  for i in dictionary["categories"]:
    categories += i[0]+" "
  output = [dictionary["name"], dictionary["distance"], dictionary["rating"],
   dictionary["review_count"], dictionary["location"]["latitude"], dictionary["location"]["longitude"], letter.upper()]
  return output


def search(location, term = "", radius = WALKING_DISTANCE, limit = 20, category_filter = "", offset = 0, count= False, sort = 0):
  '''
  locations: tuple representing longlat pairs
  '''
  lat = location[0]
  long = location[1]
  #print(offset)
  params = get_search_parameters(lat, long, term, radius, limit, category_filter, offset = offset)
  api_call = get_results(params)
  #print(api_call)
  if "businesses" not in api_call.keys():
    return 0, []
  time.sleep(1.0)
  variable_list = ["name", "distance", "location","rating", "review_count", "phone", "categories"]
  results = []
  for business in api_call["businesses"]:
    business_dict = {}
    for variable in variable_list:
      if variable in business.keys():
        if variable == "location":
          business_dict[variable] = business[variable]["coordinate"]
        else:
          business_dict[variable] = business[variable]
    results.append(business_dict)
  if count:
    return api_call["total"], results
  return results
