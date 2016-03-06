import rauth
import math
import time




CONSUMER_KEY = "_c-Jb5bdZr9eMlFpyrcx7g"
CONSUMER_SECRET = "6EPdVZpPAPREEcG-jpga1hPMhlk"
TOKEN = "1pRf9RrQKu7xdpkePMkAAbrCV9E-zr7W"
TOKEN_SECRET = "59dHWliuAzv5wyOMFDtW57u_GiM"
# In Meters
WALKING_DISTANCE = 1000
CATEGORIES = ["restaurants", "active", "arts", "education", "health", "nightlife", "shopping"]

# Second Set of API keys just in case
#Consumer_Key2 =   "nPpvHrRlTBQGMWrb4eOeLQ"
#Consumer_Secret2 =  "ZzruromYSM0p0bFYfMk4vP2ddvY"
#Token2 =  "iplo0WJS4t-7RD32q5pnqmEKIYDq9Yfv"
#Token_Secret2 =   "BocWy4tiJkScUStUeNMY-QNBGe8"


def get_results(params):
  session = rauth.OAuth1Session(
  consumer_key = CONSUMER_KEY
  ,consumer_secret = CONSUMER_SECRET
  ,access_token = TOKEN
  ,access_token_secret = TOKEN_SECRET)
  request = session.get("http://api.yelp.com/v2/search", params = params)
  #Transforms the JSON API response into a Python dictionary
  data = request.json()
  session.close()
  return data


def get_search_parameters(lat, long, term, radius, limit, category_filter, sort=0):
  #See the Yelp API for more details
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
        iterations = math.ceil(count/20)-1
        offset = 20
        for i in range(iterations):
          additional_result = search(location, category_filter = category_filter, offset = offset, radius = radius)
          offset+=20
          results+=additional_result
      score = 0

      for result in results:
        score += result["rating"]
    location_raw_scores.append(score)

  
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
  score_list_category = []
  for i in range(len(CATEGORIES)):
    if preferences[i] == 0:
      score_list_category.append([0]*len(locations))
    else:
      score_list_category.append(get_score(locations, CATEGORIES[i], distance))
  score_list_location = list(map(list, zip(*score_list_category)))
  return score_list_location

def yelp_search(location, distance, term, category_filter = "", sort = 0, offset = 0):
  # returns list in order of name, distance, rating, # of reviews, location
  results = search(location, term = term, radius = distance, category_filter = category_filter, sort = sort)
  result_list = []
  for result in results:
    result_list.append(dict_to_list(result))
  return result_list


def dict_to_list(dictionary):
  categories = ""
  for i in dictionary["categories"]:
    categories += i[0]+" "
  output = [dictionary["name"], dictionary["distance"], dictionary["rating"],
   dictionary["review_count"], (dictionary["location"]["latitude"], dictionary["location"]["longitude"])]
  return output

def search(location, term = "", radius = WALKING_DISTANCE, limit = 20, category_filter = "", offset = 0, count= False, sort = 0):
  '''
  locations: tuple representing longlat pairs
  '''
  lat = location[0]
  long = location[1]
  params = get_search_parameters(lat, long, term, radius, limit, category_filter)
  api_call = get_results(params)
  if "businesses" not in api_call.keys():
    return 0, []
  
  #Be a good internet citizen and rate-limit yourself
  time.sleep(1.0)
  #location.coordinate
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



  '''
def main():
  locations = [(41.783213,-87.601375)]
  api_calls = []
  for lat,long in locations:
    params = get_search_parameters(lat,long)
    api_calls.append(get_results(params))

    #Be a good internet citizen and rate-limit yourself
    time.sleep(1.0)
    #print(api_calls)
  print ([api_calls[0]["businesses"][i]["name"] for i in range(len(api_calls[0]["businesses"]))])
'''