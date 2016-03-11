from math import radians, cos, sin, asin, sqrt, pi, e
import csv
import sqlite3
import os
import numpy as np
import re
ordered_columns={"crimes":
                          ["date", "code", "latitude", "longitude"],
                 "IUCR_codes":
                          ["code", "primary_type", "secondary_type"],
                 "bike_racks":
                          ["number", "latitude", "longitude"],
                 "fire_police":
                          ["address", "latitude", "longitude", "type"]
                }

sql_datatypes={"crimes":
                        {"date":"text", "code": "varchar(4)", "latitude": "real", "longitude": "real"},
               "IUCR_codes":
                        {"code":"varchar(4)", "primary_type":"text", "secondary_type": "text"},
               "bike_racks":
                        {"number": "integer", "latitude":"real", "longitude":"real"},
               "fire_police":
                        {"address": "text", "latitude": "real", "longitude": "real", "type": "varchar(1)"}
               }

LABELED_FILENAMES={"crimes":
                            ["crimes_2013.csv","crimes_2014.csv","crimes_2015.csv","crimes_2016.csv"],
                   "IUCR_codes":
                            ["IUCR_codes.csv"],
                   "bike_racks":
                            ["bike_racks.csv", "divvy_stations.csv"],
                   "fire_police":
                            ["fire_stations.csv", "police_stations.csv"]
                }

test_coordinates={"me": (41.783213,-87.601375), "low crime": (41.973047, -87.777324),
                  "middle_of_nowhere": (41.767393, -87.751276), "high_crime": (41.877388, -87.730634)}

sql_strings={"crimes":
                      {1: '''SELECT date, primary_type, secondary_type, latitude, longitude FROM IUCR_codes JOIN crimes 
                             ON IUCR_codes.code=crimes.code WHERE strftime('%s', date)>=strftime('%s', {}) 
                             AND distance({},{}, latitude, longitude)<={} AND primary_type IN {};''',

                       2: '''SELECT count(*) FROM crimes JOIN IUCR_codes ON IUCR_codes.code=crimes.code WHERE strftime('%s',date)>=strftime('%s', {}) AND primary_type IN {};'''},
             "bike_racks":
                      {1: '''SELECT number, latitude, longitude FROM bike_racks WHERE distance({},{}, latitude, longitude)<={}''',

                       2: '''SELECT number FROM bike_racks'''},
             "fire_police":
                      {1: '''SELECT address, latitude, longitude FROM fire_police WHERE distance({},{}, latitude, longitude)<={} AND type={}''',

                       2: '''SELECT count(*) FROM fire_police WHERE type={}'''}
            }

CRIME_TYPES={"Violent":['"ASSAULT"', "'BATTERY'", "'CRIM SEXUAL ASSAULT'", "'HOMICIDE'", "'KIDNAPPING'", "'SEX OFFENSE'", "'INTIMIDATION'", "'WEAPONS VIOLATION'", '"OFFENSE INVOLVING CHILDREN"'],
            "Property":['"ARSON"', '"BURGLARY"', '"CRIMINAL DAMAGE"', '"MOTOR VEHICLE THEFT"', '"ROBBERY"'],
            "Other":['"CRIMINAL TRESSPASS"','"CRIMINAL ABORTION"', '"STALKING"',  '"OTHER OFFENSE"', '"RITUALISM"'],
            "QoL": ['"INTERFERENCE WITH PUBLIC OFFICER"','"DECEPTIVE PRACTIVE"', '"GAMBLING"', '"LIQUOR LAW VIOLATION"', '"OBSCENITY"' '"HUMAN TRAFFICKING"', '"PROSTITUTION"',
                                       '"PUBLIC INDECENCY"', '"PUBLIC PEACE VIOLATION"', '"NARCOTICS"', '"OTHER NARCOTIC VIOLATION"','"CONCEALED CARRY LICENSE VIOLATION"']
            }

CHICAGO_AREA=606100000
project_path=os.path.abspath(os.curdir)
csv_folder="/chicago_data/Clean/"
csv_path=project_path+csv_folder

def haversine(lat1, lon1, lat2, lon2):
    '''
    Calculate the circle distance between two points 
    on the earth (specified in decimal degrees)
    '''
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 

    # 6367 km is the radius of the Earth
    km = 6367 * c
    m = km * 1000
    return m

def score_normalizer(x, tolerance=1.5, base=1.5):
    '''
    Function used to turn scores from 0 to infinity into scores from 0 to 1, such that:
         f(0)=1
         lim_{x-->inf} f(x)=0
         f is decreasing, and f>=0
    Tolerance and base should be a floats bigger than 1.
    A high tolerance value corresponds to small deviation between scores close to 0, but also makes it harsher on scores larger than 1
    (e.g. score_normalizer(0.25, 2, 2)=0.95760, score_normalizer(2,2,2)=0.0625
          score_normalizer(0.25, 1, 2)=0.8409, score_normalizer(2,1,2)=0.25)
    Base is the reciprocal of what we want f(1) to be.
    (i.e. score_normalizer(y, base, 1)=1/base)

    The values 1.5 and 1.5 produced reasonable numbers (this is just f(x)=1.5^(-x^1.5))
    '''

    assert tolerance>=1, "please make tolerance greater than 1"
    assert base>=1, "please make base greater than 1"
    return base**(-x**tolerance)

def db_helper(list_of_filenames, table_name, path=csv_path):
    '''
    This is a function which takes in a list of filenames, a table_name for them. Returns the necessary
    data and insertion/creation strings to import this into a database usable by sqlite3. Assumes all the files
    under the same table_name are formatted similarly
    '''

    data=[]
    for filename in list_of_filenames:
        with open(path+filename) as f:
            header=f.readline()
            length=len(header.split(","))
            reader=csv.reader(f, delimiter=",")
            for row in reader:

                ##sometimes csv finds empty lines for some reason
                if row!=[]:
                    assert len(row)==length, "row {} in {} has {} columns, but should have {}".format(row, filename, len(row), length)
                    data.append(tuple(row))

    create_column_string=", ".join([i + " " + sql_datatypes[table_name][i] for i in ordered_columns[table_name]])
    creation_string="CREATE TABLE "+table_name+" ("+create_column_string+");"
    insert_column_string=", ".join([i for i in ordered_columns[table_name]])
    num_values=len(sql_datatypes[table_name])
    insertion_string="INSERT INTO "+table_name+" ("+insert_column_string+") VALUES (?" +", ?"*(num_values-1)+");"
    return (data, creation_string, insertion_string)


def create_db(labeled_filenames, database_name, path=csv_path): 
    '''labeled filenames is a dictionary, with key value pairs as table_name: list of filenames under that table'''

    con=sqlite3.connect(database_name)
    cur=con.cursor()
    for j in labeled_filenames:
        print ("Inputting {} data... ".format(j))
        (data, creation_string, insertion_string)=db_helper(labeled_filenames[j], j)
        cur.execute(creation_string)
        cur.executemany(insertion_string, data)
        print ("done")
    con.commit()

def merge_results(list_of_lists_of_dictionaries):
    '''
    For use by search()
    The items (lists) in the outer-most list represent information for a specific set of categories.
        Each list in this outer list has n dictionaries, where n is the number of houses
            Each dictionary has (key, value) pairs as (category, information) which are specific to that particular house,
            under the specific categories from the outer list

    Output: Merge all dictionaries relevant to the same house into one, and return a list of dictionaries in the same order they came in'''
    num_houses=len(list_of_lists_of_dictionaries[0])
    for j in list_of_lists_of_dictionaries:
        assert len(j)==num_houses
    current_house=0
    rv=[]
    while current_house<num_houses:
        house_dict={}
        current_house_dicts=[k[current_house] for k in list_of_lists_of_dictionaries]
        for j in current_house_dicts:
            house_dict=dict_merge(house_dict,j)
        rv.append(house_dict)
        current_house+=1
    return rv

def dict_merge(d1,d2):
    '''
    d1 and d2 are dictionary with strings as keys. This function takes all the key, value pairs from d2
    and adds them to d1. Returns a merged dictionary.
    '''
    for j in d2:
        if j in d1:
            d1[j].update(d2[j])
        else:
            d1[j]=d2[j]
    return d1


def search(time, list_of_houses, distance, database_name): 
    prop_area=pi*distance**2/CHICAGO_AREA
    con=sqlite3.connect(database_name)
    con.create_function("distance", 4, haversine)
    cur=con.cursor()
    rv=[]
    for j in range(len(list_of_houses)):
        #initialize an empty dictionary for each house
        rv.append({})
    #these are all lists of dictionaries, containing dictionaries as values
    crime_results=crime_search_efficient(time, list_of_houses, distance, prop_area, cur)
    bike_results=bike_search(list_of_houses, distance, prop_area, cur)
    fire_police_results=fire_police_search(list_of_houses, distance, prop_area, cur)
    return merge_results([crime_results, bike_results, fire_police_results])
    #returns a list of dictionaries, with each key as a category, and the value is (results, score)

    
def crime_search_efficient(time, list_of_houses, distance, prop_area, cursor):
    rv=[]
    for j in range(len(list_of_houses)):
        rv.append({})
    #never going to get empty lists
    average_lat=np.mean([j[0] for j in list_of_houses])
    average_long=np.mean([j[1] for j in list_of_houses])
    #we want to capture all relevant data with only as few sql searches as possible for efficiency, since the database is over a million data points long.
    #Instead of using the distance given to run a query for each house lat long pair, we calculate the maximum distance from all houses to the average lat, long pair
    #Then, by the triangle inequality (I think S2 is a metric space with haversine metric?), for all data points p and all houses x, we have:
    #if d(x,p)<=distance, we must have d(x_avg,p)<=d(x,x_avg)+d(x,p)<=max(d(x,x_avg)+distance
    #So we widen our search to distance+max(d(x,x_avg)) for the sql query, and we will capture all the data points we need for each house.
    for i in CRIME_TYPES:
        print("searching {}".format(i))
        possible_crimes=CRIME_TYPES[i]
        possible_crimes_string="("+",".join(possible_crimes)+")"
        cursor.execute(sql_strings["crimes"][2].format(time, possible_crimes_string))
        total_i_crimes=cursor.fetchall()[0][0]
        print("found {} total results in the entire city. Searching for local results...".format(total_i_crimes))
        distances=[haversine(average_lat, average_long, j[0], j[1]) for j in list_of_houses]
        d_max=max(distances)
        print("enlarging radius from {} to {}".format(distance, distance+d_max))
        cursor.execute(sql_strings["crimes"][1].format(time,average_lat, average_long, distance+d_max, possible_crimes_string))
        results=cursor.fetchall()
        print("found {} local results. Refining...".format(len(results)))
        for j in range(len(list_of_houses)):
            #each of these was originally a sql query, but now we are only searching for things inside the results list (smaller)
            local_results=[k for k in results if haversine(list_of_houses[j][0], list_of_houses[j][1], k[3], k[4])<=distance]
            num_local_crimes=len(local_results)
            prop_crimes=num_local_crimes/total_i_crimes
            score=score_normalizer(prop_crimes/prop_area)
            rv[j][i]=(local_results, score)
        print("done")
    return rv
            

    
''' No longer used 


def crime_search(time, list_of_houses, distance, prop_area, cursor):
    rv=[]
    for j in range(len(list_of_houses)):
        rv.append({})
    for i in CRIME_TYPES:
        print("searching {}".format(i))
        possible_crimes=CRIME_TYPES[i]
        possible_crimes_string="("+",".join(possible_crimes)+")"
        cursor.execute(sql_strings["crimes"][2].format(time, possible_crimes_string))
        total_i_crimes=cursor.fetchall()[0][0]
        print("found {} total results for category {} in the entire city. Searching for local results...".format(total_i_crimes, i))
        for j in range(len(list_of_houses)):
            cursor.execute(sql_strings["crimes"][1].format(time,list_of_houses[j][0], list_of_houses[j][1], distance, possible_crimes_string))
            local_results=cursor.fetchall()
            num_local_crimes=len(local_results)
            prop_crimes=num_local_crimes/total_i_crimes
            score=score_normalizer(prop_crimes/prop_area)
            rv[j][i]=(local_results, score)
        print("done")
    return rv

'''
def bike_search(list_of_houses, distance,prop_area, cursor):
    #divvy vs nondivvy
    rv=[]
    for j in range(len(list_of_houses)):
        rv.append({})
    print("searching bike racks")
    cursor.execute(sql_strings["bike_racks"][2])
    total_results=cursor.fetchall()
    total_count=0
    for j in total_results:
        total_count+=j[0]
    print("found {} total bike racks. Searching for local results...".format(total_count))
    for j in range(len(list_of_houses)):
        cursor.execute(sql_strings["bike_racks"][1].format(list_of_houses[j][0], list_of_houses[j][1], distance))
        local_results=cursor.fetchall()
        local_count=0
        for k in local_results:
            local_count+=k[0]
        #print("found {} local bike racks".format(local_count))
        prop_bike_racks=local_count/total_count
        #avoid division by 0
        if prop_bike_racks==0:
            rv[j]["bike_racks"]=(local_results,0)
        else:
            score=score_normalizer(prop_area/prop_bike_racks)
            rv[j]["bike_racks"]=(local_results, score)
    print("done")
    return rv

def fire_police_search(list_of_houses, distance, prop_area, cursor):
    #not enough data points to use this well? not for ranking
    rv=[]
    for j in range(len(list_of_houses)):
        rv.append({})
    print("searching fire police")
    cursor.execute(sql_strings["fire_police"][2].format('"F"'))
    fire_total_results=cursor.fetchall()[0][0]
    cursor.execute(sql_strings["fire_police"][2].format('"P"'))
    police_total_results=cursor.fetchall()[0][0]

    print("found {} total fire stations, {} total police stations. Searching for local results...".format(fire_total_results, police_total_results))
    for j in range(len(list_of_houses)):
        cursor.execute(sql_strings["fire_police"][1].format(list_of_houses[j][0],list_of_houses[j][1], distance, '"F"'))
        fire_results=cursor.fetchall()
        cursor.execute(sql_strings["fire_police"][1].format(list_of_houses[j][0],list_of_houses[j][1], distance, '"P"'))
        police_results=cursor.fetchall()
        #print("found {} local fire stations, {} local police stations".format(len(fire_results), len(police_results)))
        prop_fire, prop_police=len(fire_results)/fire_total_results, len(police_results)/police_total_results
        if prop_fire==0:
            fire_score=0
        else:
            fire_score=score_normalizer(prop_area/prop_fire)
        if prop_police==0:
            police_score=0
        else:
            police_score=score_normalizer(prop_area/prop_police)
        rv[j]["police"]=(police_results, police_score)
        rv[j]["fire"]=(fire_results, fire_score)
    print("done")
    return rv

