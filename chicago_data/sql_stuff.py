from math import radians, cos, sin, asin, sqrt
import csv
import sqlite3

#dictionary with {filename: (tuple containing [list containing tuples of the form (name of column imported, data type)], name of table }

crime_list=[("date","text"),("block","text"),("code", "varchar(4)"),("location_description","text"),("arrest","integer"),("domestic","integer"),("beat","text"),("district","text"),("ward","text"),("community_area","text"),("fbi_code","text"),("x_coord", "integer"),("y_coord", "integer"), ("lat", "real"), ("long", "real")]

d={
"IUCR_codes.csv":([("code", "varchar(4)"), ("primary_type", "text"), ("secondary_type", "text")],"IUCR_codes"),
"crimes":(crime_list,"crimes")
}

BOOLEANS={"false": 0, "true": 1}


#my apartment lat/long
my_lat=41.783213
my_long=-87.601375

def_path="/home/pdrjuarez/csproject/chicago_data/Clean/"

def haversine(lon1, lat1, lon2, lat2):
    '''
    Calculate the circle distance between two points 
    on the earth (specified in decimal degrees)
    '''
    if lon1=="" or lat1=="" or lon2=="" or lat2=="":
        return -1
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



###This is messy

def crimes(list_of_filenames, path=def_path):
    data=[]
    for filename in list_of_filenames:
        with open(path+filename) as f:
            header=f.readline()
            reader=csv.reader(f, delimiter=",")
            for row in reader:
                if row==[]:
                    break
                arrest,domestic=BOOLEANS[row[4]], BOOLEANS[row[5]]
                data.append((row[0],row[1],row[2],row[3],arrest,domestic,row[6],row[7],row[8],row[9],row[10], row[11], row[12], row[13], row[14]))

    create_column_string=", ".join([i[0] + " " + i[1] for i in d["crimes"][0]])
    creation_string="CREATE TABLE crimes ("+create_column_string+");"
    insert_column_string=", ".join([i[0] for i in d["crimes"][0]])
    values=len(d["crimes"][0])
    insertion_string="INSERT INTO "+ d["crimes"][1]+" ("+insert_column_string+") VALUES (?" +(", ?"*(values-1))+");"
    return (data, creation_string, insertion_string)

###test

def test_crimes(lat,lon, distance, filename_list, path=def_path):
    con=sqlite3.connect(":memory:")
    con.create_function("distance", 4, haversine)
    cur=con.cursor()

    cur.execute("CREATE TABLE IUCR_codes (code varchar(4), primary_type varchar(50), secondary_type varchar(50));")
    with open(path+"IUCR_codes.csv") as f:
        header=f.readline()
        reader=csv.reader(f, delimiter=",")
        codes_data=[(row[0], row[1], row[2]) for row in reader if row!=[]]
    cur.executemany("INSERT INTO IUCR_codes (code, primary_type, secondary_type) VALUES (?, ?, ?);", codes_data)
    con.commit()

    (data,creation_string, insertion_string)=crimes(filename_list)
    cur.execute(creation_string)
    cur.executemany(insertion_string, data)
    con.commit()

    sqlstring='''SELECT COUNT(*) as cnt, primary_type, secondary_type FROM IUCR_codes JOIN crimes ON IUCR_codes.code=crimes.code WHERE distance({},{}, crimes.long, crimes.lat)<={}
     AND distance({},{}, crimes.long, crimes.lat)>=0 GROUP BY secondary_type ORDER BY cnt;'''.format(lon, lat, distance, lon, lat)
    cur.execute(sqlstring)
    results=cur.fetchall()
    return results




