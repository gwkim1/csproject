import csv
import os
import re

data_folder="chicago_data/Clean/"
'''data cleaning functions'''

def change_date_column(n, filename):
	'''Crimes csv files have date in MM/DD/YYYY HH:MM:SS PM/AM.
	This changes the format to one accepted by sql as datetime, as YYYY-MM-DD HH:MM:SS
	assumes the nth row is the date column'''
	with open(data_folder+filename, "r") as f, open(data_folder+filename+"2", "w") as g:
		header=f.readline()
		g.write(header)
		readerf=csv.reader(f,delimiter=",")
		#if AM and Hour==12, Hour=00
		#If PM and Hour!=12, Hour+=12
		for row in readerf:
			date_search=re.search("([0-9]{2})/([0-9]{2})/([0-9]{4}) ([0-9]{2}):([0-9]{2}):([0-9]{2}) ([APM]{2})",row[n])
			MM,DD,YYYY,HH,mm,SS,meridiem=date_search.group(1),date_search.group(2),date_search.group(3),\
			date_search.group(4),date_search.group(5),date_search.group(6),date_search.group(7)
			if meridiem=="PM" and HH!="12":
				int_hour=int(HH)
				HH=str(int_hour+12)
			if meridiem=="AM" and HH=="12":
				HH="00"
			fixed_date=YYYY+"-"+MM+"-"+DD+" "+HH+":"+mm+":"+SS
			new_row=[j for j in row if j!=row[n]]
			new_row.insert(n,fixed_date)
			assert len(new_row)==len(row)
			row_string=",".join(new_row)
			g.write(row_string+"\n")	
	os.remove(data_folder+filename)
	os.rename(data_folder+filename+"2", data_folder+filename)

def remove_entries_with_empty_fields(filename):
	'''Basically self-explanatory'''
	with open(data_folder+filename, "r") as f, open(data_folder+filename+"2", "w") as g:
		header=f.readline()
		g.write(header)
		readerf=csv.reader(f,delimiter=",")
		for row in readerf:
			valid=True
			for j in row:
				if j.strip()=="":
					valid=False
					break
			if valid:
				row_string=",".join(row)
				g.write(row_string+"\n")
	os.remove(data_folder+filename)
	os.rename(data_folder+filename+"2", data_folder+filename)

def add_crime_codes(filename, code_col, prim_col, sec_col):
	'''Add crime_codes seen in filename, which are not in IUCR_codes.csv
	code_col: column index for the IUCR code 
	prim_col: column index for the primary description
	sec_col: column index for the secondary description

	IUCR_codes.csv is assumed to have these at locations 0,1,2 respectively'''
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
			    assert row[code_col].strip() in d
			except AssertionError:
				codes_not_in_IUCR_list.add(", ".join([row[code_col].strip(),
					row[prim_col].strip(),row[sec_col].strip()]))
	with open(data_folder+"IUCR_codes.csv", "a") as f:
		changed=False
		for j in codes_not_in_IUCR_list:
			changed=True
			f.write(j+"\n")
	return changed


def check_columns(filename):
	'''checks a CSV file for the expected number of fields for each row
	based on the number of fields in the first row, assumed to be a header
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
	'''Appends 0 to the beginning of IUCR codes at the nth spot for each row,
	 specified as an input. Makes it so every IUCR code is exactly 4
	 characters long (i.e. 13A-> 013A) for constistency'''
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

def check_codes(filename, code_col, prim_col, sec_col):
	'''Used with the crimes datasets to check for consistency between them
	 and IUCR_codes.csv (before erasing the columns)
	Inputs: code_col is the column index for the IUCR codes, 
	        prim_col is column index for the primary type description, 
	        sec_col is column index for secondary type description 
	        (all in the input filename)
	
	filename is a crime dataset with these three columns

	(IUCR_codes.csv has code_col, prim_col, and sec_col 0,1,2 respectively)

	Some annoyances: IUCR Code is 5114 is inconsistent across crime files: 
	It is either NON - CRIMINAL or NON-CRIMINAL in different crime files'''
	d={}
	with open(data_folder+filename) as f, open(data_folder+"IUCR_codes.csv") as g:
		headerf, headerg=f.readline(), g.readline()
		readerg=csv.reader(g, delimiter=",")
		for row in readerg:
			assert row[0].strip() not in d, "found duplicate entry in IUCR codes {}".format(row[0])
			d[row[0].strip()]=(row[1].strip(),row[2].strip())

		readerf=csv.reader(f, delimiter=",")
		count=1
		for row in readerf:
			if row[code_col].strip()!="5114":
			    assert d[row[code_col].strip()]==(row[prim_col].strip(), row[sec_col].strip()),\
			     "code {} in row {} is {},{} in crime file but {},{} in IUCR codes".\
			     format( row[code_col].strip() , count+1, row[prim_col].strip(), row[sec_col].strip(),\
			     d[row[code_col].strip()][0] ,d[row[code_col].strip()][1])
			else:
				primary_types=["NON-CRIMINAL", "NON - CRIMINAL"]
				sec_types="FOID - REVOCATION"
				assert row[prim_col].strip() in primary_types and row[sec_col].strip()==sec_types
			count+=1

def remove_columns(filename, columns_to_erase):
	'''columns=list of column strings to remove. 
	Checks header in filename given, assumed csv
	Also strips every field. So, if columns_to_erase 
	is an empty list, it simply strips every field of blank spaces.'''
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
	'''Some csv files had a 'location' field with a latitude, longitude tuple
	 inside, plus some extra information (address, city, state, zip)
	This extracts the lat/long tuple and adds it to the file as 
	two extra columns for each row, when available'''
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
	'''Runs a sequence of functions above, which was originally run 
	for all crime files. Makes my job easier when I redownload an 
	updated crimes_2016.csv. Please run 
	./comma_parser.sh Clean/crimes_2016.csv 
	BEFORE running this'''
	keep_these_columns=["Date", "IUCR", "Latitude", "Longitude"]
	header=get_header(filename)

	code_col=header.index("IUCR")
	prim_col=header.index("Primary Type")
	sec_col=header.index("Description")
	date_col=header.index("Date")
	print("Checking if valid csv file...")
	check_columns(filename)
	print("Making all IUCR codes 4 character strings...")
	fix_codes(code_col, filename)
	print("Adding missing codes to IUCR_codes.csv...")
	add_crime_codes(filename, code_col, prim_col, sec_col)
	print("Checking for inconsistencies between IUCR_codes.csv and crime file...")
	check_codes(filename, code_col, prim_col, sec_col)
	print("Changing the date column to YYYY-MM-DD...")
	change_date_column(date_col, filename)
	print("Removing rows with missing data...")
	remove_entries_with_empty_fields(filename)
	cols_to_remove=[j for j in header if j not in keep_these_columns]
	print("Removing unecessary columns...")
	remove_columns(filename, cols_to_remove)

if __name__=="__main__":
	pass
