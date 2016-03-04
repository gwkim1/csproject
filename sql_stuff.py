from math import radians, cos, sin, asin, sqrt, pi
import csv
import sqlite3
import os
import re
ordered_columns={"crimes":
                          ["date", "code", "location", "latitude", "longitude"],
                 "IUCR_codes":
                          ["code", "primary_type", "secondary_type"]
                }

sql_datatypes={"crimes":
                        {"date":"text", "code": "varchar(4)", "location": "varchar(50)", "latitude": "real", "longitude": "real"},
               "IUCR_codes":
                        {"code":"varchar(4)", "primary_type":"varchar(50)", "secondary_type": "varchar(50)"}
               }

LABELED_FILENAMES={"crimes":
                            ["crimes_2013.csv", "crimes_2014.csv", "crimes_2015.csv", "crimes_2016.csv"],
                   "IUCR_codes":
                            ["IUCR_codes.csv"]
                }


my_lat=41.783213
my_long=-87.601375

CHICAGO_AREA=606100000
project_path=os.path.abspath(os.curdir)
csv_folder="/chicago_data/Clean/"
csv_path=project_path+csv_folder

def haversine(lon1, lat1, lon2, lat2):
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
        (data, creation_string, insertion_string)=db_helper(labeled_filenames[j], j)
        cur.execute(creation_string)
        print(insertion_string, data[3])
        cur.executemany(insertion_string, data)
    con.commit()

def crime_search(lat, lon, distance, time, database_name):
    prop_area=pi*distance**2/CHICAGO_AREA
    con=sqlite3.connect(database_name)
    con.create_function("distance", 4, haversine)
    cur=con.cursor()
    sqlstring='''SELECT date, primary_type, secondary_type, crimes.longitude, crimes.latitude FROM IUCR_codes JOIN crimes 
    ON IUCR_codes.code=crimes.code WHERE (strftime('%s', 'now')-strftime('%s', date))<={} AND distance({},{}, crimes.longitude, crimes.latitude)<={};'''.format(time, lon, lat, distance)
    #sqlstring=''' SELECT date, code, location, latitude, longitude FROM crimes'''
    cur.execute(sqlstring)
    results=cur.fetchall()

    cur.execute('''SELECT count(*) FROM crimes WHERE (strftime('%s', 'now')-strftime('%s',date))<={};'''.format(time))
    total_crimes=cur.fetchall()[0][0]
    if total_crimes==0:
        return "Not enough results, please widen your time frame"
    num_crimes=len(results)
    if num_crimes==0:
        return ([], 10)
    prop_crimes=num_crimes/total_crimes
    crime_ratio=prop_crimes/prop_area
    return (results, crime_ratio)

def ranking(lat, lon, distance, time):
    pass





