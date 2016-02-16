from django.shortcuts import render
import sys
import os
import re
project_path=re.search('(/[A-Za-z]+){3}', os.path.abspath(os.curdir)).group()
sys.path.insert(0, project_path)
import chicago_data.sql_stuff


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

def results(request):
	distance = float(request.POST.get('distance', 200))
	lon = float(request.POST.get('longitude', -87.601375))
	lat = float(request.POST.get('latitude', -41.783213))
	print(distance, lon, lat)
	results=chicago_data.sql_stuff.test_crimes(lat, lon, distance, ["crimes_2013.csv", "crimes_2014.csv", "crimes_2015.csv"])
	c={'results': results}
	return render(request, 'search/results.html', c)



# Create your views here.
