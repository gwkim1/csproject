import numpy as np
import zillow

'''
PEDRO AND RYAN: use get_house_list to get a list of houses that meets the criteria in zillow
3/8 NOTE: the format of criteria_list has changed. nothing too different. I just deleted ideal_value and weight because we don't need this in my function

USE GET_HOUSE_LIST instead of GET_HOUSE_LIST_ALT

zipcode: zipcode
listing_type: either "rent" or "sale"

example of a criteria list that includes all possible criteria:
criteria_list =  [["price", 20000, 80000], ["bedroom", 1, 3], ["bathroom", 1, 3], ["size", 900, 1300], ["house_type", "houses", "apartments", "condos/co-ops"]]
first entry: name of criterion
second ~ last:
    for numerical variable: minimum, maximum value
    for categorical variable: values in the most preferred order. for example, "houses", "apartments", "condos/co-ops"
'''


def get_house_list(zipcode, listing_type, criteria_list):
    '''
    This combines all functions involved in getting a list of House objects
    based on user inputs from the website

    Inputs
    zipcode: zipcode within which the user wants the search
    listing_type: either "sale" or "rent"
    criteria_list: list of lists that sets each condition
    e.g. [["price", 1000, 2000], ["bedroom", 1, 3], ["size", 800, 1000], 
          ["house_type", "houses", "apartments", "condos/co-ops"]]
    for numerical variable, the two number represents lower/upper bound
    for categorical variable, possible values are listed in order of preference
    
    Returns
    The list of House objects
    '''
    # The first three functions are explained in zillow.py
    url = zillow.create_url(zipcode, listing_type, criteria_list)
    soup = zillow.get_soup(url)
    house_list = zillow.create_house_objects(soup, url)
    # Return a new house list after filtering houses for the last time
    # Using the same criteria_list
    # The reason for this last filtering will be explained later
    new_house_list = filter_house(house_list, criteria_list)
    return new_house_list

'''
FOR RYAN AND PEDRO: when your website gives the scores and weights back run get_final_scores to get
a list of tuples with each tuple being like (rank, house address, score, House object)

Need to change the same of the arguments so that they are intuitive
'''

CRITERION_DICT = {0: "price", 1: "house_type", 2: "bathroom", 3: "bedroom", 4: "restaurants", 5: "active life" , 6: "arts and entertainment", 7: "schools/education", 8: "health establishments", 9: "nightlife", 10: "shopping outlets", 11: "violent crime", 12: "property crime", 13: "other victimed non-violent crime", 14: "quality of life crime"}

def get_final_scores(house_list, criteria_list, ypchicago_scores, zillow_pref, chicago_pref, Yelp_pref):
    '''
    After the website takes in user preferences for conditions related to
    Zillow, City of Chicago Database, and Yelp,
    And after the scores for City of Chicago and Yelp data are created,
    Merge the preferences and scores with scores created with Zillow data
    This function will eventually store the final weighted score in each House
    Object and also return data that would be used in creating charts

    Inputs
    house_list: list of House objects that went through the final filtering
    criteria_list: list of conditions that the user specified.
    (specific format given elsewhere)
    ypchicago_scores: array(list of lists) of scores using Yelp and Chicago data
    zillow_pref: list of preferences(weights) about data from zillow
                 that is revealed by the user input in website  
    chicago_pref: list of preferences about the chicago data
    Yelp_pref: list of preferences about the Yelp data

    Returns
    1. Updates self.score in House object with the final weighted score
    2. Returns a dictionary of score lists for drawing charts per each condition
    example format with 2 conditions and 3 houses: 
    {"price": [29, 40, 70], "nightlife": [93, 20, 84]} 
    '''
    # First convert ypchicago_scores to a numpy array
    ypchicago_scores = np.array(ypchicago_scores)
    ypchicago_scores *= 100
    # Get a numpy score array for the criteria related to zillow data as well
    zillow_scores = get_zillow_scores(house_list, criteria_list)
    # Concatenate ypchicago_scores array with zillow_scores array
    array_list = [zillow_scores, ypchicago_scores]
    new_array = concatenate_arrays(array_list)
    # Combine the user preferences on the 3 datasets
    weight_list = zillow_pref + Yelp_pref + chicago_pref
    # Apply the weights in order to get a single weighted score for each house
    weighted_array = get_weighted_score(new_array, weight_list)

    print("weight_list:", weight_list)
    users_pref = [0] * len(weight_list)
    for i in range(len(weight_list)):
        if weight_list[i] == 0:
            users_pref[i] = 1

    # This dictionary has key: condition and value: list of scores for houses
    score_per_criterion = {}
    for i in range(len(users_pref)):
        # Only create a key-value for conditions which the user gave answers
        if users_pref[i] != 1:
            score_list = []
            for house_scores in new_array:
                score_list.append(house_scores[i])
            score_per_criterion[CRITERION_DICT[i]] = score_list
    
    # Save the final weighted score in each House object as self.score
    for i in range(len(house_list)):
        house_list[i].score = weighted_array[i][0]

    # Return the dictionary that would be used for charts
    return score_per_criterion


def get_zillow_scores(house_list, criteria_list):
    '''
    Get a numpy array that stores scores for each house and each criterion

    Inputs
    house_list, criteria_list explained elsewhere

    Returns
    a numpy array that represents each house in each row
    and each criterion in each column
    '''
    # Create a base array with appropriate size and all 0s
    array = np.array([[0 for i in range(len(criteria_list))] for i in range(len(house_list))])

    # For each criterion in criteria_list:
    for col in range(len(criteria_list)):
        # First we need to set the "indifference" and "preference" threshold
        # For example, if the user wants to buy a house in the price range (0, 70000)
        # His preference may not be linear across the entire range
        # If the price is close to 0, whether it is 100 or 200 would not matter
        # So this could be considered as having surpassed the "preference" threshold
        # And we assign a score of 1 equally
        # Same for the "indifference" threshold. If the price is close to 70000
        # We equally set the score to 0. Between the thresholds we assume linear preference 
        if type(criteria_list[col][1]) in [int, float]:
            range_len = criteria_list[col][2] - criteria_list[col][1]
            indifference = criteria_list[col][1] + range_len * 0.1
            preference = criteria_list[col][2] - range_len * 0.1
        else:
            indifference = 0
            preference = 1    

        for row in range(len(house_list)):

            if type(criteria_list[col][1]) in [int, float]:
                # pref_value is the score
                pref_value = house_list[row].info_dict[criteria_list[col][0]]
            else:
                # prbly consider case in which the value in a cell is 0, not a string.
                pref_value = (len(criteria_list[col][1:]) - (criteria_list[col][1:].index(house_list[row].info_dict[criteria_list[col][0]]))) / len(criteria_list[col][1:])
                #print(criteria_list[col])
                #print("house_list[row].info_dict[criteria_list[col][0]]", house_list[row].info_dict[criteria_list[col][0]])
                #print(criteria_list[col][1:-1].index("houses")) #- ####index of the value e.g. house_type  / (len(criteria_list[col]) - 1)


            #print("pref:", pref_value, "indif:", indifference, "pref:", preference)
            if pref_value < indifference:
                array[row][col] = 0
            elif pref_value > preference:
                array[row][col] = 100
            else:
                array[row][col] = (pref_value - indifference) * 100 / (preference - indifference)
    return array
    


def filter_house(house_list, criteria_list):
    '''
    Creates a numpy array to store the scores for every house and every criterion
    For blocks in which a house doesn't meet a criterion, set the initial value as None

    Output:
    returns a numpy array filled with either 0 or None

    I may have to delete the "deleting" part, but I need this just in case zillow returns
    So while the criteria_list is the same as what we put in in create_url, what pedro and ryan should use
    is the house_list that this function outputs.
    '''
    criteria_dict = {}
    for j in range(len(criteria_list)):
        criteria_dict[j] = criteria_list[j]

    for house in house_list:
        remove = False
        for j in range(len(criteria_list)):
            if type(criteria_dict[j][1]) == str:
                if not (house.info_dict[criteria_dict[j][0]] in criteria_dict[j]):
                    print("house does not meet criterion", j)
                    print(house.info_dict["address"])
                    print(house.info_dict[criteria_dict[j][0]])
                    remove = True
            else:                       
                if not (house.info_dict[criteria_dict[j][0]] >= criteria_dict[j][1] and house.info_dict[criteria_dict[j][0]] <= criteria_dict[j][2]): 
                    print("house does not meet criterion", j)
                    print(house.info_dict["address"])
                    print(house.info_dict[criteria_dict[j][0]], criteria_dict[j][1], criteria_dict[j][2])
                    remove = True  
        if remove:
            house_list.remove(house)

    return house_list
    




def concatenate_arrays(array_list):
    '''
    Concatenates all numpy arrays that store scores
    '''
    new_arr = array_list[0]
    # Append second to last arrays to the first one
    # axis=1 means we are extending the columns(criteria)
    for arr in array_list[1:]:
        new_arr = np.append(new_arr, arr, axis=1)
    return new_arr


def get_weighted_score(score_array, weight_list):
    '''
    Apply weights to the score_array to get a single final score for each house

    Inputs
    score_array: array of scores for each house and each criterion
    weight_list: list of weights for each criterion
    '''
    # Calculate total weight from the weight_list
    total_weight = 0
    for weight in weight_list:
        total_weight += weight
    # Store the weight relative to the total weight in a numpy array
    weight_array = np.array([[weight_list[i]/total_weight] for i in range(len(weight_list))])
    # Conduct matrix calculation to apply the weights to the scores
    return np.dot(score_array, weight_array)

    