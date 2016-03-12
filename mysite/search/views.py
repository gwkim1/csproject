from django.shortcuts import render
import django.contrib.staticfiles
import sys
import os
import re
import numpy as np
import math
import csv
import matplotlib.pylab as plt
current_path=os.path.abspath(os.curdir)
project_path=os.path.abspath("..")+"/"
sys.path.insert(0, project_path)
import zillow
import sql_stuff
import Yelp
import ranking
import shutil

DATABASE_CATEGORIES=["Violent", "Property", "QoL", "Other"]#, "bike_racks", "fire", "police"]
HOUSE_PATH="search/templates/search/house_info"
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
                      ["bathroom", current_min_bathroom, current_max_bathroom], house_types]
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
	database_results=sql_stuff.search(date, list_of_house_coords, distance, "search.db")
	
	database_scores=[]
	for l in database_results:
		house_scores=[l[j][1] for j in DATABASE_CATEGORIES]
		database_scores.append(house_scores)
	total_scores = []
	#for i in range(len(fake_yelp)):
	#	total_scores.append(fake_yelp[i]+database_scores[i])
	for i in range(len(Yelp_results)):
		total_scores.append(Yelp_results[i]+database_scores[i])
	#print(len(total_scores[0]))
	# FOR ERIC
	# WEIGHTS FOR ZILLOW IN ORDER OF PRICE, HOUSETYPE, BATHROOM, BEDROOM: zillow_pref
	# LIST OF HOUSE TYPES: house_types
	# PEDROS AND RYANS SCORES: total_scores
	# PEDROS AND RYANS WEIGHTS: database_pref, Yelp_pref

		
	# print(zillow_pref, database_pref, Yelp_pref, house_types, total_scores)
	house_list = result
	# get_final_scores(house_list, score_array, total_scores, zillow_pref, database_pref, Yelp_pref)
	score_array = ranking.create_array(house_list, criteria_list)
	ranking.get_final_scores(house_list, criteria_list, total_scores, zillow_pref, database_pref, Yelp_pref)
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

	shutil.rmtree(HOUSE_PATH, ignore_errors=True)
	os.mkdir(HOUSE_PATH)
	index=0
	for i in result:
		os.mkdir(HOUSE_PATH+"/{}".format(i.house_id))
		for j in DATABASE_CATEGORIES:
		    with open(HOUSE_PATH+"/{}/{}.csv".format(i.house_id, j), "w") as f:
			    f.write("date,primary type,secondary type,latitude,longitude\n")
			    for k in database_results[index][j][0]:
			    	#need all of them to be strings for the join method
			    	tuple_list=[str(l) for l in k]
			    	#print(tuple_list)
			    	row_string=",".join(tuple_list)
			    	f.write(row_string+"\n")
		index+=1

	with open(HOUSE_PATH+"/attributes.csv", "w") as f:
		f.write("id,address,price,bedroom,bathroom,latitude,longitude,score\n")
		for j in result:
			address = j.address
			if "," in address:
				address = address.replace(',', '')

			row_string="{},{},{},{},{},{},{},{}".format(j.house_id, address, j.price, j.bedroom, j.bathroom, j.lat, j.long, j.score)
			f.write(row_string+"\n")
	bar_data = []
	all_crimes = {}
	for i in result:
		for j in DATABASE_CATEGORIES:
			all_crimes[j]={}
			with open(HOUSE_PATH+"/{}/{}.csv".format(i.house_id,j), "r") as f:
				header=f.readline()
				reader=csv.reader(f)
				for row in reader:
					date=row[0]
					month_year=date[:7]
					all_crimes[j][month_year]=all_crimes[j].get(month_year, 0)+1
			t_labels=list(all_crimes[j].keys())
			t_labels.sort()
			t=range(len(t_labels))
			s=[all_crimes[j][k] for k in t_labels]
			bar_data.append((i.address, j, sum(s)))
	bar_dict = {}
	for i in bar_data:
		if i[0] not in bar_dict:
			bar_dict[i[0]] = [i[2]]
		else:
			bar_dict[i[0]].append(i[2])
	bar_list = []
	for key, value in bar_dict.items():
		bar_list.append([key]+ value)
	#print(bar_list)
	c={'results': result}
	c['database_cat'] = DATABASE_CATEGORIES
	c['bar_data'] = bar_list
	
	return render(request, 'search/results.html', c)

def detailed_results(request):
	
	c = {}
	c["myHiddenField"] = request.POST.get("a")
	print("HERE", request.POST.get("a"))
	house_id=request.POST.get("house_id")
	print("adsf",house_id)
	with open(HOUSE_PATH+"/attributes.csv", "r") as f:
		header=f.readline()
		reader=csv.reader(f)
		for row in reader:
			if int(row[0])==int(house_id):
				c["current_lat"]=row[5]
				c["current_long"]=row[6]
				c["current_bedroom"]=row[3]
				c["current_bathroom"]=row[4]
				c["current_price"]=row[2]
				c["current_address"]=row[1]
				c["current_house_id"]=house_id
				break
	c['current_distance'] = request.POST.get('distance', 1200)
	data=[]
	all_crimes={}
	line_styles=[".r-", ".b-", ".g-", ".y-"]
	c['graph_data'] = []
	graph_data_raw = []
	c['pie_data']=[]
	for j in DATABASE_CATEGORIES:
		all_crimes[j]={}
		with open(HOUSE_PATH+"/{}/{}.csv".format(house_id.strip(),j), "r") as f:
			header=f.readline()
			reader=csv.reader(f)
			for row in reader:
				date=row[0]
				month_year=date[:7]
				all_crimes[j][month_year]=all_crimes[j].get(month_year, 0)+1
		t_labels=list(all_crimes[j].keys())
		t_labels.sort()
		t=range(len(t_labels))
		s=[all_crimes[j][k] for k in t_labels]
		c['pie_data'].append((j, sum(s)))
		
		if len(t)>15:
			step=(len(t)//15)+1
			for k in range(len(t_labels)):
				if k%step!=0:
					t_labels[k]=""
		graph_data_raw.append((j,t_labels,s))
		plt.xticks(t, t_labels, rotation=30)	
		plt.plot(t, s, line_styles.pop(), label =j)
	plt.xlabel("Date YYYY-MM")
	plt.ylabel("Number of crimes")
	plt.title("Crime within {}m of this property".format(c["current_distance"]))
	plt.legend()
	plt.grid(True)
	plt.savefig(HOUSE_PATH+"/{}/historical_crime.png".format(house_id.strip()))
	plt.clf()
	c["crime_graph"]=HOUSE_PATH+"/{}/historical_crime.png".format(house_id.strip())
	crime_list = []
	for date in graph_data_raw[0][1]:
		crime_list.append([date])
	
	for i in range(len(graph_data_raw)):

		crime_data = graph_data_raw[i][2]
		#print(crime_data)
		for j in range(len(crime_data)):
			crime_list[j].append(crime_data[j])
	c['graph_data'] = crime_list
	c['database_cat'] = DATABASE_CATEGORIES
	print(crime_list)


	page = request.POST.get('page',1)
	c['current_cat'] = request.POST.get('cat')
	
	c['categories'] = ["all","restaurants", "active", "arts", "education", "health", "nightlife", "shopping"]
	distance = float(c["current_distance"])
	units = request.POST.get("distance_type")
	if units == "miles":
		distance *= 1609.34
	if distance > 40000:
		distance = 40000
	#print(current_path, project_path, HOUSE_PATH)
	c["current_term"] =request.POST.get("term", "food")
	#if c['current_term'] != "":
	#print(c["current_term"])
	print((c["current_lat"], c["current_long"]), distance, c['current_term'], (int(page)-1)*20)
	if c['current_cat'] == "all" or c["current_cat"] == None:
		c['results'], total = Yelp.yelp_search((c["current_lat"], c["current_long"]), distance, c['current_term'], offset = (int(page)-1)*20)
	else:
		c['results'], total = Yelp.yelp_search((c["current_lat"], c["current_long"]), distance, c['current_term'], category_filter = c['current_cat'], offset = (int(page)-1)*20)

	c['pages'] = list(range(1,math.ceil(total/20)))
	c['current_page'] = page
	#print(c['results'])
	return render(request, 'search/detailed_results.html', c)