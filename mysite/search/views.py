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


DATABASE_CATEGORIES=["Violent", "Property", "Other", "QoL"]#, "bike_racks", "fire", "police"]
HOUSE_PATH="search/templates/search/house_info"
PREF_OPTIONS_DICT = {"zillow": ["price", "house_type","bathroom","bedroom"],
    "yelp":["restaurants", "active life" , "arts and entertainment",  "schools/education",  "health establishments",  "nightlife",  "shopping outlets"],
     "crime":["violent crime",  "property crime", "other victimed non-violent crime",  "quality of life crime"]}
YELP_DICT = {"restaurants": 0, "active life":1 , "arts and entertainment":2,  "schools/education":3,  
"health establishments": 4,  "nightlife": 5,  "shopping outlets":6}
def about(request):
    c={'names': 'Pedro, Eric, Ryan,'}
    return render(request, 'search/about.html', c)

def homepage(request):
    c = {}
    c['current_distance'] = request.POST.get('distance', 1000)
    c['current_loc']= request.POST.get('location', 60637)
    c["current_price_upper_limit"] =request.POST.get("price_upper_limit", 650)
    c["current_price_lower_limit"] =request.POST.get("price_lower_limit", 0)
    c["current_min_bathroom"] =request.POST.get("min_bathroom", 0)
    c["current_min_bedroom"] =request.POST.get("min_bedroom", 0)
    c["current_max_bathroom"] =request.POST.get("max_bathroom", 8)
    c["current_max_bedroom"] =request.POST.get("max_bedroom", 8)
    # Takes the survey question from txt file and appends them to a list to pass in
    questions=[]
    count=1
    with open(current_path+"/search/templates/search/survey.txt") as f:
        for line in f:
            questions.append([line, count])
            count+=1
    c["survey"]=questions
    return render(request, 'search/home.html', c)


def error(request):
    c = {}
    return render(request, 'search/error.html', c)



def results(request):
    c={}

    # The first part of this function validates the data
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
        # Checks if the house types are valid and in the right order
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


    criteria_list =  [["price", current_price_lower_limit, current_price_upper_limit], ["bedroom", current_min_bedroom, current_max_bedroom],
                      ["bathroom", current_min_bathroom, current_max_bathroom], house_types]
    
    print("Querying zillow...")
    
    print("Here are the inputs:", loc, listing_type, criteria_list)
    house_list = ranking.get_house_list(loc, listing_type, criteria_list)
    print("Done. Found {} matching properties".format(len(house_list


        )))
    # Adds error message if the number of results is 0 or too large
    if len(house_list) > 100:
        errors.append("Too many results, please narrow down your search.")
        c["errors"]=errors
        return render(request, 'search/home.html', c)
    if len(house_list) ==0:
        errors.append("No results found.")
        c["errors"]=errors
        return render(request, 'search/home.html', c)



    zillow_pref, Yelp_pref, database_pref=weights[:4],weights[4:11], weights[11:]
    list_of_house_coords=[(j.lat,j.long) for j in house_list]
    scores=[]

    # Stores the scores gotten from yelp
    print("Requesting Yelp")
    Yelp_results=Yelp.get_yelp_scores(list_of_house_coords,distance,Yelp_pref)
    # Stores the results gotten from database
    database_results=sql_stuff.search(date, list_of_house_coords, distance, "search.db")
    # Extracts the scores from the results
    database_scores=[]
    for l in database_results:
        house_scores=[l[j][1] for j in DATABASE_CATEGORIES]
        database_scores.append(house_scores)
    


    #for when I test at csil
    #fake_yelp=[]
    #for k in range(len(house_list)):
    #   new_list=[]
    #   for j in range(7):
    #       new_list.append(0)
    #   fake_yelp.append(new_list)
    #for i in range(len(fake_yelp)):
    #   total_scores.append(fake_yelp[i]+database_scores[i])




    # Creates a list of lists with the yelp and city scores
    total_scores = []
    for i in range(len(Yelp_results)):
        total_scores.append(Yelp_results[i]+database_scores[i])
    # Passes the houses, user input, scores, and preferences into ranking to get the final scores 
    # Also sets the scores of each house object
    raw_scores_dict = ranking.get_final_scores(house_list, criteria_list, total_scores, zillow_pref, database_pref,Yelp_pref)
    scores_dict = {}
    top_ten_address = []
    for pref in raw_scores_dict:
        scores_list = []
        for tup in raw_scores_dict[pref]:
            if pref not in list(scores_dict.keys()):
                scores_dict[pref] = [tup[1]]
            else:
                scores_dict[pref].append(tup[1])
            if tup[2] not in top_ten_address:
                top_ten_address.append(tup[2])
    scores = {"zillow":{}, "yelp":{},"crime":{}}
    # Divides the scores in scores_dict into 3 categories: zillow, yelp, crime
    for key in scores_dict:
        for pref in PREF_OPTIONS_DICT:
            if key in PREF_OPTIONS_DICT[pref]:
                scores[pref][key] = (scores_dict[key])

    # If there are more than 10 results the graphs can get messy looking
    # We separate out the top 10 to use in graph generation
    if len(house_list) > 10:
        list_top_coords = []
        list_top_houses = []
        for address in top_ten_address:
            for house in house_list:
                if address == house.address:
                    list_top_coords.append((house.lat, house.long))
                    list_top_houses.append(house)
    
        top_Yelp_results=Yelp.get_yelp_scores(list_top_coords,distance,Yelp_pref)
    else:
        list_top_houses = house_list

    # Changes the data in scores into Address, value, value, value form to use in the bar chart
    # Also stores the variable names
    bar_data_dict = {"zillow":[[]], "yelp":[[]],"crime":[[]]}
    # For preference category
    for key in scores:
        variable_list = PREF_OPTIONS_DICT[key]
        # For each property in the top 10
        for i in range(len(top_ten_address)):
            value_list = []
            # Checks for the variables that the user cares about
            for variable in PREF_OPTIONS_DICT[key]:
                if variable in scores[key]:
                    # If the yelp scores were not generated before, generate them
                    if len(house_list) > 10 and key == "yelp":
                        value_list.append(math.ceil(top_Yelp_results[i][YELP_DICT[variable]]*100))
                    else:
                    # Add the score as 0 if the user does not care
                        value_list.append(scores[key][variable][i])
                else:
                    value_list.append(0)
            # Puts the data in desired form
            bar_data_dict[key][0].append([top_ten_address[i]] + value_list)
        # Adds the variable name
        bar_data_dict[key].append(variable_list)

    


    shutil.rmtree(HOUSE_PATH, ignore_errors=True)
    os.mkdir(HOUSE_PATH)
    index=0
    for i in house_list:
        os.mkdir(HOUSE_PATH+"/{}".format(i.house_id))
        for j in DATABASE_CATEGORIES:
            with open(HOUSE_PATH+"/{}/{}.csv".format(i.house_id, j), "w") as f:
                f.write("date,primary type,secondary type,latitude,longitude\n")
                for k in database_results[index][j][0]:
                    tuple_list=[str(l) for l in k]
                    row_string=",".join(tuple_list)
                    f.write(row_string+"\n")
        index+=1

    with open(HOUSE_PATH+"/attributes.csv", "w") as f:
        f.write("id,address,price,bedroom,bathroom,latitude,longitude,score\n")
        for j in house_list:
            address = j.address
            if "," in address:
                address = address.replace(',', '')

            row_string="{},{},{},{},{},{},{},{}".format(j.house_id, address, j.price, j.bedroom, j.bathroom, j.lat, j.long, j.score)
            f.write(row_string+"\n")



    # Gets the data from the csv files and puts it in the correct form
    bar_data = []
    all_crimes = {}
    for i in list_top_houses:
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
    for key in top_ten_address:
        bar_list.append([key]+ bar_dict[key])
    # Replaces the c dictionary with the house_list and fills it with the bar graph data
    c={'results': house_list}
    c['database_cat'] = DATABASE_CATEGORIES
    c['bar_data'] = bar_list
    c['zbar_data']=bar_data_dict["zillow"][0]
    c['ybar_data']=bar_data_dict["yelp"][0]
    c['cbar_data']=bar_data_dict["crime"][0]
    c['zbar_var']=bar_data_dict["zillow"][1]
    c['ybar_var']=bar_data_dict["yelp"][1]
    c['cbar_var']=bar_data_dict["crime"][1]
    c['current_distance'] = distance
    c["current_date"]=request.POST.get("date")
    
    return render(request, 'search/results.html', c)

def detailed_results(request):
    
    c = {}
    house_id=request.POST.get("house_id")
    if not house_id:
        return render(request, 'search/error.html', c)
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
    # The following code both saves a graph using matlibplot and stores chart data to use in charts
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
        # Stores the pie data for crime
        c['pie_data'].append((j, sum(s)))
        if len(t)>15:
            step=(len(t)//15)+1
            for k in range(len(t_labels)):
                if k%step!=0:
                    t_labels[k]=""
        # Stores the graph data for crime
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

    # Changes graph_data_raw into correct format
    crime_list = []
    for date in graph_data_raw[0][1]:
        crime_list.append([date])
    for i in range(len(graph_data_raw)):
        crime_data = graph_data_raw[i][2]
        for j in range(len(crime_data)):
            crime_list[j].append(crime_data[j])
    c['graph_data'] = crime_list
    c['database_cat'] = DATABASE_CATEGORIES

    current_cat = request.POST.get('cat')
    if not current_cat:
        current_cat = ""

    c['categories'] = ["restaurants", "active", "arts", "education", "health", "nightlife", "shopping"]
    distance = float(c["current_distance"])
    units = request.POST.get("distance_type")
    # Corrects distance for units and limit (Yelp limit is 40000)
    if units == "miles":
        distance *= 1609.34
    if distance > 40000:
        distance = 40000
    c["current_term"] =request.POST.get("term", "food")
    page = request.POST.get('page',1)
    c['results'], total = Yelp.yelp_search((c["current_lat"], c["current_long"]), distance, c['current_term'], category_filter = current_cat, offset = (int(page)-1)*20)
    c['pages'] = list(range(1,math.ceil(total/20)))
    
    c['current_page'] = page
    return render(request, 'search/detailed_results.html', c)