from django.shortcuts import render
import sys
import os
import re
current_path=os.path.abspath(os.curdir)
project_path=os.path.abspath("..")+"/"
sys.path.insert(0, project_path)
import zillow
import sql_stuff
import Yelp

DATABASE_CATEGORIES=["Violent crimes", "Property crimes", "Other victimed non-violent crimes", "Quality of life crimes"]#, "bike_racks", "fire", "police"]
def about(request):
	c={'names': 'Pedro, Eric, Ryan,'}
	return render(request, 'search/about.html', c)

def homepage(request):
	c = {}
	c['names'] = 'Pedro, Eric, Ryan'
	c['current_distance'] = request.POST.get('distance', 1000)
	c['current_loc']= request.POST.get('location', 60637)
	c["current_price_upper_limit"] =request.POST.get("price_upper_limit", 2000)
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
	for j in range(1,12):
		try:
			weights.append(float(request.POST.get("pref_"+str(j))))
		except:
			errors.append("Survey question {} was not filled in".format(j))

	house_type=request.POST.get("house_type")
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

	if len(errors)>0:
		questions=[]
		count=1
		with open(current_path+"/search/templates/search/survey.txt") as f:
			for line in f:
				questions.append([line, count])
				count+=1
		c["survey"]=questions
		c["errors"]=errors
		return render(request, 'search/home.html', c)


	#run the data through
	criteria_list =  [["price", current_price_lower_limit, current_price_upper_limit, None, 300], ["bedroom", current_min_bedroom, current_max_bedroom, None, 400],
                      ["bathroom", current_min_bathroom, current_max_bathroom, None, 100],["size", 0, 10000, None, 100], ["house_type", "houses", "apartments", "condos/co-ops", 500]]
	
	print("Querying zillow...")
	url=zillow.create_url(loc, listing_type, criteria_list)
	soup=zillow.get_soup(url)
	result=zillow.create_house_objects(soup)
	print("Done. Found {} matching properties".format(len(result)))
	Yelp_pref,database_pref=weights[:7],weights[7:]
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
	database_results=sql_stuff.search(date, list_of_house_coords, distance, database_name)
	database_scores=[]
	for l in database_results:
		house_scores=[l[j][1] for j in DATABASE_CATEGORIES]
		database_scores.append(house_scores)
	print(database_scores)
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

	c={'results': result}
	return render(request, 'search/results.html', c)

def detailed_results(request):

	lat=float(request.POST.get("lat"))
	lon=float(request.POST.get("long"))
	distance=float(request.POST.get("distance"))
	time=float(request.POST.get("time"))
	

	c={"results": crime_list[0], "score": crime_list[1]}
	return render(request, 'search/detailed_results.html', c)


# Create your views here.
