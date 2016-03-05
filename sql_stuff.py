from math import radians, cos, sin, asin, sqrt, pi, e
import csv
import sqlite3
import os
import re
ordered_columns={"crimes":
                          ["date", "code", "location", "latitude", "longitude"],
                 "IUCR_codes":
                          ["code", "primary_type", "secondary_type"],
                 "bike_racks":
                          ["number", "latitude", "longitude"],
                 "fire_police":
                          ["address", "latitude", "longitude", "type"]
                }

sql_datatypes={"crimes":
                        {"date":"text", "code": "varchar(4)", "location": "varchar(50)", "latitude": "real", "longitude": "real"},
               "IUCR_codes":
                        {"code":"varchar(4)", "primary_type":"varchar(50)", "secondary_type": "varchar(50)"},
               "bike_racks":
                        {"number": "integer", "latitude":"real", "longitude":"real"},
               "fire_police":
                        {"address": "varchar(50)", "latitude": "real", "longitude": "real", "type": "varchar(1)"}
               }

LABELED_FILENAMES={"crimes":
                            ["crimes_2013.csv", "crimes_2014.csv", "crimes_2015.csv","crimes_2016.csv"],
                   "IUCR_codes":
                            ["IUCR_codes.csv"],
                   "bike_racks":
                            ["bike_racks.csv", "divvy_stations.csv"],
                   "fire_police":
                            ["fire_stations.csv", "police_stations.csv"]
                }

test_coordinates={"me": (41.783213,-87.601375), "low crime": (41.973047, -87.777324), "high_bike_ratio": (41.892385, -87.631885),
                  "middle_of_nowhere": (41.767393, -87.751276), "high_crime": (41.877388, -87.730634)}

sql_strings={"crimes":
                      {1: '''SELECT date, primary_type, secondary_type, longitude, latitude FROM IUCR_codes JOIN crimes 
                             ON IUCR_codes.code=crimes.code WHERE strftime('%s', date)>=strftime('%s', {}) 
                             AND distance({},{}, latitude, longitude)<={};''',

                       2: '''SELECT count(*) FROM crimes WHERE strftime('%s',date)>=strftime('%s', {});'''},
             "bike_racks":
                      {1: '''SELECT number, latitude, longitude FROM bike_racks WHERE distance({},{}, latitude, longitude)<={}''',

                       2: '''SELECT number FROM bike_racks'''},
             "fire_police":
                      {1: '''SELECT address, latitude, longitude FROM fire_police WHERE distance({},{}, latitude, longitude)<={} AND type={}''',

                       2: '''SELECT count(*) FROM fire_police WHERE type={}'''}}
CRIME_TYPES=['ARSON','ASSAULT','BATTERY','BURGLARY','CONCEALED CARRY LICENSE VIOLATION','CRIM SEXUAL ASSAULT','CRIMINAL ABORTION','CRIMINAL DAMAGE',
 'CRIMINAL TRESPASS','DECEPTIVE PRACTICE','GAMBLING','HOMICIDE','HUMAN TRAFFICKING','INTERFERENCE WITH PUBLIC OFFICER','INTIMIDATION','KIDNAPPING',
 'LIQUOR LAW VIOLATION','MOTOR VEHICLE THEFT','NARCOTICS','NON - CRIMINAL','NON-CRIMINAL','NON-CRIMINAL (SUBJECT SPECIFIED)','OBSCENITY',
 'OFFENSE INVOLVING CHILDREN','OTHER NARCOTIC VIOLATION','OTHER OFFENSE','PROSTITUTION','PUBLIC INDECENCY','PUBLIC PEACE VIOLATION','RITUALISM',
 'ROBBERY','SEX OFFENSE','STALKING','THEFT', 'WEAPONS VIOLATION'] #weighting

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
    '''Function used to turn scores from 0 to infinity into scores from 0 to 1, such that:
         f(0)=1
         lim_{x-->inf} f(x)=0
         f is decreasing, and f>=0
    Tolerance and base should be a floats bigger than 1. The values 1.5 and 1.5 produced reasonable numbers
    A high tolerance value corresponds to small deviation between scores close to 0, but also makes it harsher on scores larger than 1
    (e.g. score_normalizer(2, 2, 0.25)=0.95760, score_normalizer(2,2,2)=0.0625
          score_normalizer(1, 2, 0.25)=0.8409, score_normalizer(1,2,2)=0.25)
    Base is the reciprocal of what we want f(1) to be.
    (i.e. score_normalizer(y, base, 1)=1/base)'''
    assert tolerance>=1, "please make tolerance greater than 1"
    assert base>=1, "please make base greater than 1"
    return base**(-x**tolerance)

def db_helper(list_of_filenames, table_name, path=csv_path):
    '''This is a function which takes in a list of filenames, a table_name for them. Returns the necessary
    data and insertion/creation strings to import this into a database usable by sqlite3. Assumes all the files
    are formatted similarly.'''

    data=[]
    for filename in list_of_filenames:
        with open(path+filename) as f:
            header=f.readline()
            length=len(header.split(","))
            reader=csv.reader(f, delimiter=",")
            for row in reader:

                if row==[]:
                    break
                if len(row)!=length:
                    print("Warning: row {} has {} columns, but should have {}".format(row, len(row), length))
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

def search(time, lat, lon, distance, database_name): 
    prop_area=pi*distance**2/CHICAGO_AREA
    con=sqlite3.connect(database_name)
    con.create_function("distance", 4, haversine)
    cur=con.cursor()
    rv=[]
    crime_results=crime_search(time, lat, lon, distance, cur)
    rv.append({"results":crime_results[0], "score": score_normalizer(x=crime_results[1]/prop_area)})
    bike_results=bike_search(lat,lon,distance,cur)
    #rv.append({"results": bike_results[0], "score": score_normalizer(x=prop_area/bike_results[1])})
    fire_police_results=fire_police_search(lat,lon,distance,cur)
    if fire_police_results["fire"][1]==0:
        rv.append({"results":fire_police_results["fire"][0], "score": 0})
    else:
        rv.append({"results":fire_police_results["fire"][0], "score": score_normalizer(x=prop_area/fire_police_results["fire"][1])})
    if fire_police_results["police"][1]==0:
        rv.append({"results":fire_police_results["police"][0], "score": 0})
    else:
        rv.append({"results":fire_police_results["police"][0], "score": score_normalizer(x=prop_area/fire_police_results["police"][1])})

    #list of dictionaries, in order crimes, bike, fire, police
    return rv

def crime_search(time, lat, lon, distance, cursor):
    cursor.execute(sql_strings["crimes"][1].format(time, lat, lon, distance))
    results=cursor.fetchall()
    cursor.execute(sql_strings["crimes"][2].format(time))
    total_crimes=cursor.fetchall()[0][0]

    if total_crimes==0:
        print("Not enough results, please widen your time frame")
        return

    num_crimes=len(results)
    prop_crimes=num_crimes/total_crimes

    return (results, prop_crimes)

def bike_search(lat, lon, distance, cursor):
    cursor.execute(sql_strings["bike_racks"][1].format(lat, lon, distance))
    results=cursor.fetchall()
    cursor.execute(sql_strings["bike_racks"][2])
    total_results=cursor.fetchall()
    count, total_count=0,0
    for j in results:
        count+=j[0]
    for j in total_results:
        total_count+=j[0]
    prop_bike_racks=count/total_count
    return (results, prop_bike_racks)

def fire_police_search(lat, lon, distance, cursor):
    #not enough data points to use this well? not for ranking
    cursor.execute(sql_strings["fire_police"][1].format(lat, lon, distance, '"F"'))
    fire_results=cursor.fetchall()
    cursor.execute(sql_strings["fire_police"][2].format('"F"'))
    fire_total_results=cursor.fetchall()
    cursor.execute(sql_strings["fire_police"][1].format(lat, lon, distance, '"P"'))
    police_results=cursor.fetchall()
    cursor.execute(sql_strings["fire_police"][2].format('"P"'))
    police_total_results=cursor.fetchall()


    prop_fire,prop_police=len(fire_results)/fire_total_results[0][0],len(police_results)/police_total_results[0][0]
    
    return {"fire":(fire_results, prop_fire), "police":(police_results, prop_police)}

def ranking(houses, database_name, time, distance):
    '''Houses is a list of tuples with lat, long pairs'''
    rv=[]
    for j in houses:
        ###each item is a house, where each item inside the house is a ranking###
        scores=search(time, j[0], j[1], distance, database_name)
        rv.append([scores[0]["score"]])
    return rv




[""]




