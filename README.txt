To Run The Website:
    type “sudo pip3 install rauth” in terminal if not installed
    type “sudo pip3 install django” in terminal if not installed
    ^ Ignore these if using a copy of the VM
    go to the folder, csproject/mysite
    type “python3 manage.py runserver”
    go to http://127.0.0.1:8000/home/ in the web browser
    (website will not work until the chicago database steps are followed)


Zillow:
zillow.py is a python file that creates url according to the input from the website,
creates a beautifulsoup object of the html document of the pages,
and returns a list of "House" objects that contain all necessary information about each house result.

NOTE: As I told Prof. Wachs earlier, Zillow completely changed its html structure at around 8-9th week and
this change consumed quite a lot of time for me to change the way my code scrapes data from Zillow.

ranking.py incorporates the 3 sets of scores generated from Zillow, Chicago, and Yelp dataset,
and generates a final weighted score based on the preference given by the user.

packages used: bs4, urllib.parse, urllib.request, re, numpy as np


Yelp:
The Yelp functions achieve 2 main goals, to search Yelp for businesses and relevant information and to generate a score based on under inputs.
It uses the Yelp API and uses the rauth package to make requests to Yelp.  The search function is the main function in yelp which makes and collects the results from Yelp.  The scoring functions aggregate the ratings of the businesses and reduces them to the range 0 to 1.  The other yelp search functions puts the Yelp results into the desired form.


Our Website:
The website has 3 main pages:
home: the page where the user inputs filters and preferences
results: the page where the score distributions are displayed as well as interesting information about the houses that were found
detailed_results: the page where the user can search Yelp, see more detailed information about the crime data, as well as go to zillow entry of the property
There are also two auxiliary pages, error and about which are relatively self explanatory.


Chicago database:
Structure:
--csproject/chicago_data/Clean: directory where all the csv files from the city of chicago data were stored. (crime data, fire/police stations, divvy bikes, libraries, parks). Only the crime datasets ended up being used, but all of these were cleaned substantially at some point. The crime datasets were the most substantial out of them all

--csproject/chicago_data/comma_parser.sh: file which is meant to remove commas from fields in csv files, replaces them with ; (commas problematic when inputting data into sqlite)

--csproject/Data_tests.py contains lots of functions which were designed for working with the datasets from the city of chicago portal, mostly towards the crime datasets. Also contains a wrapper function which cleans a crime file entirely with one call. This was to keep the crimes_2016.csv file up to date, since it gets updated every weekend
        
--csproject/sql_stuff.py contains functions which handle creating databases from the cleaned datasets, most notably the crime datasets, but also fire stations, police stations, and bike racks (we didn't end up using these for ranking properties, though). Also handles the sql queries from the website input

sql_stuff.py is called whenever the website performs a search, but it is possible to test the main function (search()) with the example input shown in the docstring

To get the crime data and clean it, do the following:

0) Remove any crime files and IUCR_codes.csv from csproject/chicago_data/Clean
1) Download csv exports of the crime datasets from the city of chicago data portal for any number of years (as many as you want)
example dataset: https://data.cityofchicago.org/Public-Safety/Crimes-2015/vwwp-7yr9 (only 2015). Also download https://data.cityofchicago.org/Public-Safety/Chicago-Police-Department-Illinois-Uniform-Crime-R/c7ck-438e, and call it IUCR_codes.csv
2) Move the files to csproject/chicago_data/Clean
3) Navigate to csproject/chicago_data in the terminal, then run ./comma_parser.sh Clean/<filename> for each csv file
4) Run ipython3 in the terminal, and run data_tests.py. Run the command:
>remove_columns("IUCR_codes.csv", ["INDEX CODE"])
5) Run the following command. This makes it so IUCR_codes.csv column "IUCR" is always a string of length 4. 
>fix_codes(0, "IUCR_codes.csv")
6) For each crime dataset called, run the following command (filename replaced by string with the name of the file):
>clean_crime_csv(filename).
This does a combination of functions from inside data_tests.py that make them usable files, see the docstrings

To create a database out of these, do the following:

0) in sql_stuff.py, change the value LABELED_FILENAMES["crimes"] to a list of the filenames of crime data you wish to add to the database
1) run the following command:
>create_db(LABELED_FILENAMES, "search.db")

There's a list of test coordinates in sql_stuff.py for some testing, which can be passed to search() for testing (make sure the database is in csproject directory, if running this from the terminal)
###When this function is called from the website, I could never get it to work with the database in the csproject directory, it always looked for the database in csproject/mysite. So, I had to move it there for the purpose of the website functionality. Thus, for testing the website, please move search.db to csproject/mysite directory###
