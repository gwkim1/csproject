import csv
import os
import re

data_folder="chicago_data/Clean/"


def change_date_column(filename):
	'''Crimes csv files have date in MM/DD/YYYY HH:MM:SS PM/AM.
	This changes the format to one accepted by sql as datetime, as YYYY-MM-DD HH:MM:SS
	Assumes the first column is the Date column'''
	with open(data_folder+filename, "r") as f, open(data_folder+filename+"2", "w") as g:
		header=f.readline()
		g.write(header)
		readerf=csv.reader(f,delimiter=",")
		#if AM and Hour==12, Hour=00
		#If PM and Hour!=12, Hour+=12
		for row in readerf:
			date_search=re.search("([0-9]{2})/([0-9]{2})/([0-9]{4}) ([0-9]{2}):([0-9]{2}):([0-9]{2}) ([APM]{2})", row[0])
			MM,DD,YYYY,HH,mm,SS,meridiem=date_search.group(1),date_search.group(2),date_search.group(3),date_search.group(4),date_search.group(5),date_search.group(6),date_search.group(7)
			if meridiem=="PM" and HH!="12":
				int_hour=int(HH)
				HH=str(int_hour+12)
			if meridiem=="AM" and HH=="12":
				HH="00"
			fixed_date=YYYY+"-"+MM+"-"+DD+" "+HH+":"+mm+":"+SS
			new_row=[fixed_date]+[j for j in row if j!=row[0]]
			assert len(new_row)==len(row)
			row_string=",".join(new_row)
			g.write(row_string+"\n")	
	os.remove(data_folder+filename)
	os.rename(data_folder+filename+"2", data_folder+filename)

def remove_entries_with_empty_fields(filename):
	with open(data_folder+filename, "r") as f, open(data_folder+filename+"2", "w") as g:
		header=f.readline()
		g.write(header)
		readerf=csv.reader(f,delimiter=",")
		for row in readerf:
			valid=True
			for j in row:
				if j=="":
					valid=False
					break
			if valid:
				row_string=",".join(row)
				g.write(row_string+"\n")
	os.remove(data_folder+filename)
	os.rename(data_folder+filename+"2", data_folder+filename)

def add_crime_codes(filename):
	'''Add crime_codes seen in filename, which are not in IUCR_codes.csv'''
	d={}
	with open(data_folder+"IUCR_codes.csv") as f:
		header=f.readline()
		reader=csv.reader(f, delimiter=",")
		for row in reader:
			if len(row[0])<4:
				assert "0"+row[0] not in d
				d["0"+row[0]]=(row[1].strip(),row[2].strip())
			else:
				assert row[0] not in d
				d[row[0]]=(row[1].strip(),row[2].strip())

	codes_not_in_IUCR_list=set()
	with open(data_folder+filename) as f:
		header=f.readline()
		reader=csv.reader(f, delimiter=",")
		for row in reader:
			try:
			    assert row[4].strip() in d
			except AssertionError:
				codes_not_in_IUCR_list.add(", ".join([row[4].strip(),row[5].strip(),row[6].strip()]))
	with open(data_folder+"IUCR_codes.csv", "a") as f:
		changed=False
		for j in codes_not_in_IUCR_list:
			changed=True
			f.write(j+"\n")
	return changed


def check_columns(filename):
	'''checks a CSV file for the expected number of fields for each row based on the number of fields in the first row, assumed to be a header
	also checks whether there are any commas inside fields.'''
	with open(data_folder+filename) as f:
		header=f.readline()
		columns=len(header.split(","))
		reader=csv.reader(f, delimiter=",")
		count=0
		for row in reader:
			count+=1
			assert columns==len(row), "row {} had {} lines, expected {}".format(count, len(row, columns))
			for j in row:
				assert "," not in j, "row {} has a comma in field {}. Please run comma_parser and try again {}".format(row, j)

def fix_codes(n, filename):
	'''Appends 0 to the beginning of IUCR codes at the nth spot for each row, specified as an input
	Makes it so every IUCR code is exactly 4 characters long'''
	with open(data_folder+filename) as f, open(data_folder+filename+"2", "w") as g:
		header=f.readline()
		g.write(header)
		reader=csv.reader(f, delimiter=",")
		for row in reader:
			if len(row[n])<4:
				row[n]="0"+row[n]
				string=",".join(row)
				string+="\n"
				g.write(string)
			else:
				string=",".join(row)
				string+="\n"
				g.write(string)
	os.remove(data_folder+filename)
	os.rename(data_folder+filename+"2", data_folder+filename)

def check_codes(filename):
	'''Used with the crimes datasets to check for consistency between them and IUCR_codes.csv (before erasing the columns)'''
	d={}
	with open(data_folder+filename) as f, open(data_folder+"IUCR_codes.csv") as g:
		headerf, headerg=f.readline(), g.readline()
		readerg=csv.reader(g, delimiter=",")
		for row in readerg:
			assert row[0].strip() not in d, "found duplicate entry in IUCR codes {}".format(row[0])
			d[row[0].strip()]=(row[1].strip(),row[2].strip())

		readerf=csv.reader(f, delimiter=",")
		for row in readerf:
			assert d[row[4].strip()]==(row[5].strip(), row[6].strip()), "code {} is {},{} in crime file, but {},{} in IUCR codes".format( row[4].strip() , d[row[4].strip()][0] ,d[row[4].strip()][1] ,row[5].strip(),row[6].strip())

def remove_columns(filename, columns_to_erase):
	'''columns=list of column strings to remove. Checks header in filename given, assumed csv
	Also strips every field. So, if columns_to_erase is an empty list, it simply strips every field of blank spaces.'''
	with open(data_folder+filename, "r") as f, open(data_folder+filename+"2", "w") as g:
		header=f.readline()
		columns=header.split(",")
		for j in range(len(columns)):
			columns[j]=columns[j].strip()
		indices=[]
		for k in range(len(columns)):
			if columns[k] not in columns_to_erase:
				indices.append(k)
		new_header=[columns[k].strip() for k in indices]
		new_header_string=",".join(new_header)
		g.write(new_header_string+"\n")
		reader=csv.reader(f, delimiter=",")
		for row in reader:
			try:
			    new_row=[row[k].strip() for k in indices]
			    new_row_string=",".join(new_row)
			    g.write(new_row_string+"\n")
			except:
				assert row==[], "row with unexpected length found"

	os.remove(data_folder+filename)
	os.rename(data_folder+filename+"2", data_folder+filename)

def turn_loc_into_latlong(filename):
	'''Some csv files had a 'location' field with a latitude, longitude tuple inside, plus some extra information (address, city, state, zip)
	This extracts the lat/long tuple and adds it to the file as two extra columns for each row, when available'''
	with open(data_folder+filename, "r") as f, open(data_folder+filename+"2", "w") as g:
		reader=csv.reader(f, delimiter=",")
		header=next(reader)
		header_string=",".join(header)
		g.write(header_string+",LATITUDE,LONGITUDE\n")
		for row in reader:
			location_string=row.pop(-1)
			location=re.search("\(([0-9.-]+), ([0-9.-]+)\)", location_string)
			if location:
				latitude, longitude=location.group(1), location.group(2)
			else:
				latitude, longitude="",""
			row_string=",".join(row)+',"'+location_string+'",'+latitude+","+longitude+"\n"
			g.write(row_string)

	os.remove(data_folder+filename)
	os.rename(data_folder+filename+"2", data_folder+filename)

def get_header(filename):
	with open(data_folder+filename, "r") as f:
		reader=csv.reader(f, delimiter=",")
		return next(reader)


def clean_crime_csv(filename):
	'''Runs a sequence of functions above, which was originally run for all crime files
	Makes my job easier when I redownload an updated crimes_2016.csv.
	Please run ./comma_parser.sh crimes_2016.csv BEFORE running this'''
	keep_these_columns=["Date", "IUCR", "Location Description", "Latitude", "Longitude"]
	header=get_header(filename)
	n=header.index("IUCR")
	cols_to_remove=[j for j in header if j not in keep_these_columns]
	check_columns(filename)
	fix_codes(n, filename)
	check_codes(filename)
	add_crime_codes(filename)
	remove_columns(filename, cols_to_remove)
	remove_entries_with_empty_fields(filename)
	change_date_column(filename)
	

if __name__=="__main__":
	pass
