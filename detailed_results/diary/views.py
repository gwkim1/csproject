from django.shortcuts import render
import sys
import os
import re
from . import Property
import rauth
import time
project_path=os.path.abspath("..")+"/"
sys.path.insert(0, project_path)
import Yelp

# Create your views here.
def d_results(request):
    c = {}
    c['a'] = 'abc'
    c['current_distance'] = request.POST.get('distance', 500)
    c['current_long']= request.POST.get('longitude', -87.601375)
    c['current_lat']= request.POST.get('latitude', 41.783213)
    c['current_term'] = request.POST.get('term', "food")
    c['current_cat'] = request.POST.get('cat')
    print(c['current_cat'])
    c['categories'] = ["restaurants", "active", "arts", "education", "health", "nightlife", "shopping"]
    if c['current_term'] != "":
      if c['current_cat'] == "all":
        c['results'] = Yelp.yelp_search((c['current_lat'], c['current_long']), c['current_distance'], c['current_term'])
      else:
        c['results'] = Yelp.yelp_search((c['current_lat'], c['current_long']), c['current_distance'], c['current_term'], c['current_cat'])
    return render(request, 'diary/start.html', c)





