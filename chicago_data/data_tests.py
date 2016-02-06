import csv

data_folder="Clean/"
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
	Also checks if double quotes are in any fields, usually a sign of commas inside the fields, which needs fixing.'''
	with open(data_folder+filename) as f:
		header=f.readline()
		columns=len(header.split(","))
		reader=csv.reader(f, delimiter=",")
		count=0
		for row in reader:
			count+=1
			try:
				assert columns==len(row)
			except AssertionError:
				print ("row {} had {} lines, expected {}".format(count, len(row), columns))
			for j in range(len(row)):
				if '"' in row[j]:
					print("row {} has double quotes inside field {}: {}".format(count, j, row[j]))

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

def check_codes(filename):
	'''Used with the crimes datasets to check for consistency between them and IUCR_codes.csv'''
	d={}
	with open(data_folder+filename) as f, open(data_folder+"IUCR_codes.csv") as g:
		headerf, headerg=f.readline(), g.readline()
		readerg=csv.reader(g, delimiter=",")
		for row in readerg:
			assert row[0] not in d
			d[row[0].strip()]=(row[1].strip(),row[2].strip())

		readerf=csv.reader(f, delimiter=",")
		for row in readerf:
			assert d[row[4].strip()]==(row[5].strip(), row[6].strip())

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
				assert row==[]

if __name__=="__main__":
	pass
