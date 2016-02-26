from django.shortcuts import render
import sys
import os
import re
from . import Property
import rauth
import time

# Create your views here.
def d_results(request):
    c = {}
    c['a'] = 'abc'
    c['current_distance'] = request.POST.get('distance', 200)
    c['current_long']= request.POST.get('longitude', -87.601375)
    c['current_lat']= request.POST.get('latitude', 41.783213)
    c['current_term'] = request.POST.get('term', "food")
    if c['current_term'] != "":

        c['results'] = get_yelp(c['current_lat'], c['current_long'], c['current_distance'], c['current_term'])
    return render(request, 'diary/start.html', c)
def get_results(params):
    #Obtain these from Yelp's manage access page
    #Consumer Key  _c-Jb5bdZr9eMlFpyrcx7g
    #Consumer Secret 6EPdVZpPAPREEcG-jpga1hPMhlk
    #Token 1pRf9RrQKu7xdpkePMkAAbrCV9E-zr7W
    #Token Secret  59dHWliuAzv5wyOMFDtW57u_GiM
    consumer_key = "_c-Jb5bdZr9eMlFpyrcx7g"
    consumer_secret = "6EPdVZpPAPREEcG-jpga1hPMhlk"
    token = "1pRf9RrQKu7xdpkePMkAAbrCV9E-zr7W"
    token_secret = "59dHWliuAzv5wyOMFDtW57u_GiM"

    session = rauth.OAuth1Session(
    consumer_key = consumer_key
    ,consumer_secret = consumer_secret
    ,access_token = token
    ,access_token_secret = token_secret)
     
    request = session.get("http://api.yelp.com/v2/search",params=params)

    #Transforms the JSON API response into a Python dictionary
    data = request.json()
    session.close()

    return data

def get_search_parameters(lat,long,distance,term):
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
  params["term"] = term
  params["ll"] = "{},{}".format(str(lat),str(long))
  params["radius_filter"] = str(distance)
  params["limit"] = "20"
  #params["category_filter"] = "education"
 
  return params


def get_yelp(lat, long,distance, term):
  locations = [(41.783213,-87.601375, 2000)]
  api_calls = []
  for lat,long,distance in locations:
    params = get_search_parameters(lat,long, distance, term)
    api_calls.append(get_results(params))

    #Be a good internet citizen and rate-limit yourself
    time.sleep(1.0)
    #print(api_calls)
  return ([api_calls[0]["businesses"][i]["name"] for i in range(len(api_calls[0]["businesses"]))])

def clean_yelp(yelp,list):
    pass



'''
class AddMealForm(forms.ModelForm):
    class Meta:
        model = models.Meal
        fields = ['food', 'units']



def start(request):
    if request.method == 'POST':
        form = AddMealForm(request.POST)
        if form.is_valid():
            form.save()
            form = AddMealForm()

        print('Sent POST!!!!!!!!!')
    else:
        form = AddMealForm()

    #return HttpResponse('Test')
    now = datetime.now()
    start = now - timedelta(weeks=1)


    meals = models.Meal.objects.order_by(
        '-timestamp'
    ).filter(
        timestamp__gt=start
    )

    c = {
        'name': 'Gustav',
        'foods': models.Food.objects.all(),
        'meals': meals,
        'form': form,
    }

    return render(request, 'diary/start.html', c)


def about(request):
    now = datetime.now()
    c = {'title': 'about', 'now': now}

    return render(request, 'diary/about.html', c)


def pie(request):
    response = HttpResponse(content_type='image/png')
    plt.figure(figsize=(4, 4))

    meals = models.Meal.objects.all()

    totals = {}
    for meal in meals:
        name = meal.food.name
        if name in totals:
            totals[name] += meal.calories()
        else:
            totals[name] = meal.calories()

    names, tots = zip(*totals.items())


    plt.pie(tots, labels=names)
    plt.savefig(response, transparent=True)
    plt.close()

    return response
'''