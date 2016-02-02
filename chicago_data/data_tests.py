import csv

data_folder="chicago_data/"
def add_codes(filename):
	d={}
	with open(data_folder+"IUCR_codes_new.csv") as f:
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
	with open(data_folder+"IUCR_codes_new.csv", "a") as f:
		changed=False
		for j in codes_not_in_IUCR_list:
			changed=True
			f.write(j+"\n")


	

if __name__=="__main__":
	pass
