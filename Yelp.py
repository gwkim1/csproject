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
VARIABLE_LIST = ["name", "distance", "location","rating", "review_count", "phone", "categories"]
# Second Set of API keys just in case
#Consumer_Key2 =   "nPpvHrRlTBQGMWrb4eOeLQ"
#Consumer_Secret2 =  "ZzruromYSM0p0bFYfMk4vP2ddvY"
#Token2 =  "iplo0WJS4t-7RD32q5pnqmEKIYDq9Yfv"
#Token_Secret2 =   "BocWy4tiJkScUStUeNMY-QNBGe8"

# get_results and get_search_parameters are used to request data from the yelp api
# get_score and get_Yelp_scores are used to generate scores for our application
# search performed yelp requests and returns the 
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
  if term != '' and term != None:
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
  if len(locations) > 10:
    print(category_filter, "scores will take too long to generate with 10+ properties")
    return [0]*len(locations)
  for location in locations:
    '''
    This is the code we used initially to obtain all the Yelp results, but we found that it took too much time
    Instead we changed it so that it only returns the top 20 results with the best ratings
    Also we limited the properties to a max of 10, so the function would not timeout
    # Yelp only gives 20 results maximum per request, so it must be offset to get all of the results
    count, results = search(location, category_filter = category_filter, count = True, radius = radius)
    if count == 0:
      score = 0 
    else:
      if count > 20:
        # Makes additional requests to get 20 results at a time until all the results are appended
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
    '''
    print("Searching", location, "for", category_filter)
    count, results = search(location, category_filter = category_filter, radius = radius,count = True, sort=2)
    score = 0
    if count > 0:
      for result in results:
        score += result["rating"]
    location_raw_scores.append(score)
  # Reduces the max score down to 1, and calculates other score relative to the max
  print("Reducing scores")
  max_score = max(location_raw_scores)
  if max_score == 0:
    new_scores = [0]*len(location_raw_scores)
  else:
    new_scores = [x / max_score for x in location_raw_scores]
  return new_scores

def get_yelp_scores(locations, distance, preferences):
  # Calculates the score for each category, only if the user cares about the category
  # Iterates get_score depending on the preferences
  score_list_category = []
  for i in range(len(CATEGORIES)):
    if preferences[i] == 0:
      score_list_category.append([0]*len(locations))
    else:
      score_list_category.append(get_score(locations, CATEGORIES[i], distance))
  score_list_location = list(map(list, zip(*score_list_category)))
  return score_list_location



def yelp_search(location, distance, term, category_filter = "", sort = 0, offset = 0):
  # Returns list in order of name, distance, rating, # of reviews, location, letter
  results = search(location, term = term, radius = distance, category_filter = category_filter, sort = sort, offset=offset)
  result_list = []
  # If empty, return an empty list and count of 0
  if results == []:
    return [], 0
  count = 0
  # Some results that the Yelp api lie outside our specified range
  # We make a new list to hold the results we want
  for result in results:
    if result["distance"] < float(distance):
      result_list.append(dict_to_list(result, ALPHABET[count]))
      count+=1
  return result_list, count


def dict_to_list(dictionary, letter):
  # Converts dictionary to list in wanted format
  categories = ""
  for i in dictionary["categories"]:
    categories += i[0]+" "
  output = [dictionary["name"], dictionary["distance"], dictionary["rating"],
   dictionary["review_count"], dictionary["location"]["latitude"], dictionary["location"]["longitude"], letter.upper()]
  return output


def search(location, term = "", radius = WALKING_DISTANCE, limit = 20, category_filter = "", offset = 0, sort = 0, count = False):
  # Calls the yelp api to get all of the results and returns the results the variable we are interested in 
  lat = location[0]
  long = location[1]
  params = get_search_parameters(lat, long, term, radius, limit, category_filter, offset = offset, sort = sort)
  api_call = get_results(params)
  # If there are no businesses, or there is an error retrun an empty list
  if "businesses" not in api_call.keys():
    return []
  time.sleep(1.0)
  total = 0
  results = []
  for business in api_call["businesses"]:
    total+=1
    business_dict = {}
    for variable in VARIABLE_LIST:
      if variable in business.keys():
        if variable == "location":
          business_dict[variable] = business[variable]["coordinate"]
        else:
          business_dict[variable] = business[variable]
    results.append(business_dict)
  if count:
    return total, results
  else:
    return results
