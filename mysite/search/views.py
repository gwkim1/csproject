from django.shortcuts import render
import sys
import os
import re
project_path=os.path.abspath("..")+"/"
sys.path.insert(0, project_path)
import zillow
import sql_stuff
import Yelp

def about(request):
	c={'names': 'Pedro, Eric, Ryan,'}
	return render(request, 'search/about.html', c)

def homepage(request):
    c = {}
    c['names'] = 'Pedro, Eric, Ryan'
    c['current_distance'] = request.POST.get('distance', 200)
    c['current_loc']= request.POST.get('location', 60647)
    c["current_price_limit"] =request.POST.get("price_limit", 1500)
    attributes=["Restaurants nearby", "Active life nearby (parks, gyms, basketball courts)", "Arts and entertainment nearby","Schools/education nearby",
    "Health establishments nearby (dentists, pharmacies)", "Nightlife nearby", "Shopping outlets nearby","Violent crime nearby (homicide, assault, arson, etc)",
    "Property crime nearby (theft, burglarly, criminal damage, etc)", "Quality of life crime nearby (gambling, narcotics, public peace violations, etc)"]
    new_attributes=[]
    count=0
    for j in attributes:
        count+=1
        new_attributes.append([j,count])
    c["survey"]=new_attributes
    return render(request, 'search/home.html', c)


def results(request):
	distance = float(request.POST.get('distance', 200))
	loc=int(request.POST.get("location"))
	price_limit=round(float(request.POST.get("price_limit")))
	house_type=request.POST.get("house_type")
	listing_type=request.POST.get("listing_type")
	time=request.POST.get("time")
	preferences=[]
	for j in range(1,11):
		preferences.append(request.POST.get("pref_"+str(j)))
	print(distance, loc, price_limit, house_type, listing_type, time, preferences)
	url=zillow.create_url(loc, listing_types=[listing_type], price_range= (40000, price_limit), min_bedroom=0, min_bathroom=0, house_types= [house_type])
	soup=zillow.get_soup(url)
	result=zillow.get_house_info(soup, output_info=["latlong", "price", "address"])

	Yelp_pref=preferences[:7]
	database_pref=preferences[7:]
	list_of_house_coords=[(j[1],j[2]) for j in result]

	Yelp_results=Yelp.get_yelp_scores(list_of_house_coords,distance,Yelp_pref)
	database_results=sql_stuff.ranking(list_of_house_coords, "test.db",time,distance)
	for j in range(len(Yelp_results)):
		Yelp_results[j]+=database_results[j]

	print (Yelp_results)

	c={'results': result, "distance": distance}
	return render(request, 'search/results.html', c)

def detailed_results(request):

	lat=float(request.POST.get("lat"))
	lon=float(request.POST.get("long"))
	distance=float(request.POST.get("distance"))
	time=float(request.POST.get("time"))
	

	c={"results": crime_list[0], "score": crime_list[1]}
	return render(request, 'search/detailed_results.html', c)


# Create your views here.
