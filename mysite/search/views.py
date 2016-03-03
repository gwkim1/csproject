from django.shortcuts import render
import sys
import os
import re
project_path=os.path.abspath("..")+"/"
sys.path.insert(0, project_path)
import zillow
import sql_stuff

def about(request):
	c={'names': 'Pedro, Eric, Ryan,'}
	return render(request, 'search/about.html', c)

def homepage(request):
	c = {}
	c['names'] = 'Pedro, Eric, Ryan'
	c['current_distance'] = request.POST.get('distance', 200)
	c['current_long']= request.POST.get('longitude', -87.601375)
	c['current_lat']= request.POST.get('latitude', 41.783213)

	#validate the data

	return render(request, 'search/home.html', c)

def homepage2(request):
	c = {}

	c["current_distance"] = request.POST.get('distance', 200)
	c["current_loc"] =request.POST.get('location',60637)
	c["current_price_limit"] =request.POST.get("price_limit", 1500)

	return render(request, 'search/home2.html', c)

def results(request):
	distance = float(request.POST.get('distance', 200))
	lon = float(request.POST.get('longitude', -87.601375))
	lat = float(request.POST.get('latitude', -41.783213))
	print(distance, lon, lat)
	results=chicago_data.sql_stuff.test_crimes(lat, lon, distance, ["crimes_2013.csv", "crimes_2014.csv", "crimes_2015.csv"])
	c={'results': results}
	return render(request, 'search/results.html', c)

def results_ph(request):

	distance = float(request.POST.get('distance'))
	loc = float(request.POST.get('location'))
	price_limit= float(request.POST.get('price_limit'))
	house_type=request.POST.get('house_type')
	listing_type=request.POST.get('listing_type')

	url=zillow.create_url(loc, listing_type = [listing_type], price_range = (0, price_limit), min_bedroom = 0, min_bathroom = 0, house_type = [house_type], size_range = (0, 100000000))
	print(url)
	soup=zillow.get_soup(url)
	result=zillow.get_house_info(soup, output_info=["latlong", "price", "address"])

	c={"results": result, "distance": distance}
	return render(request, 'search/results_ph.html', c)

def detailed_results(request):

	lat=float(request.POST.get("lat"))
	lon=float(request.POST.get("long"))
	distance=float(request.POST.get("distance"))
	crime_list=sql_stuff.crime_search(lat, lon, distance)

	c={"results": crime_list[0], "score": crime_list[1]}
	return render(request, 'search/detailed_results.html', c)


# Create your views here.
