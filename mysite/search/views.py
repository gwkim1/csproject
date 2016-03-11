from django.shortcuts import render
import sys
import os
import re
import numpy as np
import math
current_path=os.path.abspath(os.curdir)
project_path=os.path.abspath("..")+"/"
sys.path.insert(0, project_path)
import zillow
import sql_stuff
import Yelp
import ranking

DATABASE_CATEGORIES=["Violent crimes", "Property crimes", "Other victimed non-violent crimes", "Quality of life crimes"]#, "bike_racks", "fire", "police"]
def about(request):
	c={'names': 'Pedro, Eric, Ryan,'}
	return render(request, 'search/about.html', c)

def homepage(request):
	c = {}
	c['names'] = 'Pedro, Eric, Ryan'
	c['current_distance'] = request.POST.get('distance', 1000)
	c['current_loc']= request.POST.get('location', 60637)
	c["current_price_upper_limit"] =request.POST.get("price_upper_limit", 650)
	c["current_price_lower_limit"] =request.POST.get("price_lower_limit", 0)
	c["current_min_bathroom"] =request.POST.get("min_bathroom", 0)
	c["current_min_bedroom"] =request.POST.get("min_bedroom", 0)
	c["current_max_bathroom"] =request.POST.get("max_bathroom", 8)
	c["current_max_bedroom"] =request.POST.get("max_bedroom", 8)
	questions=[]
	count=1
	with open(current_path+"/search/templates/search/survey.txt") as f:
		for line in f:
			questions.append([line, count])
			count+=1
	c["survey"]=questions
	return render(request, 'search/home.html', c)


def results(request):
	#validate the data
	c={}
	errors=[]
	try:
		c["current_distance"]=request.POST.get("distance")
		distance=float(c["current_distance"])
		units = request.POST.get("distance_type")
		if units == "miles":
			distance *= 1609.34
		assert distance>0

	except:
		errors.append("distance should be a numeric value greater than 0")
	try:
		c["current_loc"]=request.POST.get("location")
		loc=int(c["current_loc"])
		# Which are the chicago zip codes?
	except:
		errors.append("location should be a zip code in Chicago")
	try:
		c["current_price_upper_limit"]=request.POST.get("price_upper_limit")
		current_price_upper_limit=round(float(c["current_price_upper_limit"]))
		assert current_price_upper_limit>=0
		try:
			c["current_price_lower_limit"]=request.POST.get("price_lower_limit")
			current_price_lower_limit=round(float(c["current_price_lower_limit"]))
			assert current_price_lower_limit<=current_price_upper_limit and current_price_lower_limit>=0
		except:
			errors.append("min price should be a numeric value greater than or equal to 0, and less than or equal to max price")
	except:
		errors.append("max price should be a numeric value greater than 0")
	c["current_date"]=request.POST.get("date")
	date='"'+c["current_date"].strip()+'"'
	search_date=re.search('"([\d]{4})-([\d]{2})-([\d]{2})"', date)
	if bool(search_date)!=True:
		errors.append("Please enter the date in YYYY-MM-DD format")
	else:
		year=search_date.group(1)
		if year not in ["2013", "2014", "2015", "2016"]:
			errors.append("no data available for year {}".format(year))
		database_name=str(year.strip())+".db"
	weights=[]
	for j in range(1,16):
		try:
			weights.append(float(request.POST.get("pref_"+str(j))))
		except:
			errors.append("Survey question {} was not filled in".format(j))
	try:
		house_type1=request.POST.get("house_type1")
		house_type2=request.POST.get("house_type2")
		house_type3=request.POST.get("house_type3")
		assert house_type1 != None
		try:
			assert house_type1 != house_type2 and house_type1 != house_type3
		except:
			errors.append("House types repeat")
		if house_type2 == "" and house_type3 != "":
			errors.append("Invalid ordering")
		house_types = ["house_type"]
		house_types.append(house_type1)
		if house_type2 != "":
			house_types.append(house_type2)
			if house_type3 != "":
				house_types.append(house_type3)
		#house_types.append(500)
	except:
		errors.append("Need first field for house type preference")

	listing_type=request.POST.get("listing_type")

	try:
		c["current_max_bathroom"]=request.POST.get("max_bathroom")
		current_max_bathroom=int(c["current_max_bathroom"])
		assert current_max_bathroom>=0
		try:
		    c["current_min_bathroom"]=request.POST.get("min_bathroom")
		    current_min_bathroom=int(c["current_min_bathroom"])
		    assert current_min_bathroom>=0 and current_min_bathroom<=current_max_bathroom
		except: 
			errors.append("min bathroom should be an integer value greater than or equal to 0, and less than or equal to max bathroom")
	except:
		errors.append("max bathroom should be an integer value greater than or equal to 0")

	try:
		c["current_max_bedroom"]=request.POST.get("max_bedroom")
		current_max_bedroom=int(c["current_max_bedroom"])
		assert current_max_bedroom>=0
		try:
		    c["current_min_bedroom"]=request.POST.get("min_bedroom")
		    current_min_bedroom=int(c["current_min_bedroom"])
		    assert current_min_bedroom>=0 and current_min_bedroom<=current_max_bedroom
		except: 
			errors.append("min bedroom should be an integer value greater than or equal to 0, and less than or equal to max bedroom")
	except:
		errors.append("max bedroom should be an integer value greater than or equal to 0")
	questions=[]
	count=1
	with open(current_path+"/search/templates/search/survey.txt") as f:
		for line in f:
			questions.append([line, count])
			count+=1
	c["survey"]=questions
	if len(errors)>0:
		c["errors"]=errors
		return render(request, 'search/home.html', c)


	#run the data through
	criteria_list =  [["price", current_price_lower_limit, current_price_upper_limit], ["bedroom", current_min_bedroom, current_max_bedroom],
                      ["bathroom", current_min_bathroom, current_max_bathroom],["size", 0, 10000], house_types]
	# criteria_list =  [["price", 20000, 80000], ["bedroom", 1, 3], ["bathroom", 1, 3], ["size", 900, 1300],
	print("Querying zillow...")
	#url=zillow.create_url(loc, listing_type, criteria_list)
	#soup=zillow.get_soup(url)
	#result=zillow.create_house_objects(soup)
	print(loc, listing_type, criteria_list)
	result = ranking.get_house_list(loc, listing_type, criteria_list)
	print("Done. Found {} matching properties".format(len(result)))
	if len(result) > 100:
		errors.append("Too many results, please narrow down your search.")
		c["errors"]=errors
		return render(request, 'search/home.html', c)
	if len(result) ==0:
		errors.append("No results found.")
		c["errors"]=errors
		return render(request, 'search/home.html', c)
	zillow_pref, Yelp_pref, database_pref=weights[:4],weights[4:11], weights[11:]
	#print(zillow_prep, Yelp_pref, database_pref)
	#they have been ordered
	list_of_house_coords=[(j.lat,j.long) for j in result]
	scores=[]

	#for when I test at csil
	#fake_yelp=[]
	#for k in range(len(result)):
	#	new_list=[]
	#	for j in range(7):
	#		new_list.append(0)
	#	fake_yelp.append(new_list)

	Yelp_results=Yelp.get_yelp_scores(list_of_house_coords,distance,Yelp_pref)
	#print(len(Yelp_results[0]))
	database_results=sql_stuff.search(date, list_of_house_coords, distance, database_name)
	
	database_scores=[]
	for l in database_results:
		house_scores=[l[j][1] for j in DATABASE_CATEGORIES]
		database_scores.append(house_scores)
	total_scores = []
	for i in range(len(Yelp_results)):
		total_scores.append(Yelp_results[i]+database_scores[i])
	print(len(total_scores[0]))
	# FOR ERIC
	# WEIGHTS FOR ZILLOW IN ORDER OF PRICE, HOUSETYPE, BATHROOM, BEDROOM: zillow_pref
	# LIST OF HOUSE TYPES: house_types
	# PEDROS AND RYANS SCORES: total_scores
	# PEDROS AND RYANS WEIGHTS: database_pref, Yelp_pref

		
	# print(zillow_pref, database_pref, Yelp_pref, house_types, total_scores)
	house_list = result
	# get_final_scores(house_list, score_array, total_scores, zillow_pref, database_pref, Yelp_pref)
	score_array = ranking.create_array(house_list, criteria_list)
	#print(criteria_list)
	#if sum(weights) !=0:
		#print(house_list, score_array, total_scores, zillow_pref, database_pref, Yelp_pref)
		#print(ranking.get_final_scores(house_list, score_array, total_scores, zillow_pref, database_pref, Yelp_pref))
	'''
	for j in range(len(Yelp_results)):
	#for j in range(len(fake_yelp)):
		#fake_yelp[j]+=database_scores[j]
		Yelp_results[j]+=database_scores[j]
		dot_product=0
		for i in range(len(Yelp_results[j])):
		#for i in range(len(fake_yelp[j])):
			dot_product+=Yelp_results[j][i]*weights[i]
			#dot_product+=fake_yelp[j][i]*weights[i]
		result[j].score=dot_product
		print("property {} has score {}".format(result[j].address,result[j].score))
	result = sorted(result, key=lambda x: x.score)
	result.reverse()
	'''
	variable_list = []
	for house in result:
		variable_list.append([house.score, house.address, house.lat, house.long, house.price, house.bathroom, house.bedroom])
	c={'results': result}
	c['variable_list'] = variable_list
	return render(request, 'search/results.html', c)

def detailed_results(request):
	
	c = {}
	c["current_lat"] = request.POST.get("lat")
	c["current_long"] = request.POST.get("long")
	c['current_distance'] = request.POST.get('distance', 1200)
	c['current_term'] = request.POST.get('term', "food")
	c['current_cat'] = request.POST.get('cat')
	
	page = request.POST.get('page',1)
	print(page)
	#print(c['current_cat'])
	
	c['categories'] = ["all","restaurants", "active", "arts", "education", "health", "nightlife", "shopping"]
	distance = float(c["current_distance"])
	units = request.POST.get("distance_type")
	if units == "miles":
		distance *= 1609.34
	if distance > 40000:
		distance = 40000
	if c['current_term'] != "":
		if c['current_cat'] == "all":
			c['results'], total = Yelp.yelp_search((c["current_lat"], c["current_long"]), distance, c['current_term'], offset = int(page)*20)
		else:
			c['results'], total = Yelp.yelp_search((c["current_lat"], c["current_long"]), distance, c['current_term'], c['current_cat'], offset = int(page)*20)
	
	c['pages'] = list(range(1,math.ceil(total/20)+1))
	c['current_page'] = page
	print(c['results'])
	address = request.POST.get("address")
	
	c["address"] = address
	return render(request, 'search/detailed_results.html', c)


# Create your views here.
