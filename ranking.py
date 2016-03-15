import numpy as np
import zillow

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

# This is a dictionary used in get_final_scores for pulling out 
# List of scores for each category. The user preference given from the website
# Follows this order.
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
    example format with 2 conditions and 2 houses: 
    {"price": [(total score, price score, address1), (total score, price score, address2)], 
     "nightlife": [(total score, nightlife score, address1), (total score, nightlife score, address2)]} 
    '''
    # First convert ypchicago_scores to a numpy array
    # Scale them to 0-100 scale to match the zillow scores
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

    # Save the final weighted score in each House object as self.score
    for i in range(len(house_list)):
        house_list[i].score = weighted_array[i][0]

    # Create a list indicating preferences that user selected as 0
    # And preferences not selected as 1
    users_pref = [0] * len(weight_list)
    for i in range(len(weight_list)):
        if weight_list[i] == 0:
            users_pref[i] = 1

    # In the aforementioned dictionary,
    score_per_criterion = {}
    # For each possible preference category,
    for i in range(len(users_pref)):
        # Only create a key-value pair for conditions which the user gave answers
        if users_pref[i] != 1:
            score_list = []
            # For each house result,
            for j in range(len(new_array)):
                # Add the total score, category-specific score and address
                score_list.append((house_list[j].score, new_array[j][i], house_list[j].address))
            # Use the total score entry to sort and only leave top 10 results
            # For the sake of effective graphical representation
            score_list.sort()
            score_list.reverse()
            if len(score_list) > 10:
                score_list = score_list[:10]
            # Add the resulting data for top 10 houses in score_per_criterion
            score_per_criterion[CRITERION_DICT[i]] = score_list

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
            # Price is the only numerical value with which the lower value is better
            if criteria_list[col][0] == "price":
                preference = criteria_list[col][1] + range_len * 0.1
                indifference = criteria_list[col][2] - range_len * 0.1
            else:    
                indifference = criteria_list[col][1] + range_len * 0.1
                preference = criteria_list[col][2] - range_len * 0.1
        else:
            # For categorial variables, setting the threshold is meaningless
            indifference = 0
            preference = 1    

        # For each house,
        for row in range(len(house_list)):
            if type(criteria_list[col][1]) in [int, float]:
                # Get the numerical value that would be used in creating scores
                pref_value = house_list[row].info_dict[criteria_list[col][0]]
            else:
                # For categorical variable, measure how up front the current value
                # Is in the order of preference given from criteria_list
                # For example, for ["house_type": "house", "condo/co-ops"]
                # the value for house would be (2-0)/2 = 1, for condo (2-1)/2 = 0.5
                pref_value = (len(criteria_list[col][1:]) - (criteria_list[col][1:].index(house_list[row].info_dict[criteria_list[col][0]]))) / len(criteria_list[col][1:])
            
            # Again, for prices the lower value is better, so adjust accordingly
            if criteria_list[col][0] == "price":
                if pref_value < preference:
                    array[row][col] = 100
                elif pref_value > indifference:
                    array[row][col] = 0
                else:
                    # This calculates the linear preference within the thresholds
                    array[row][col] = abs(pref_value - indifference) * 100 / abs(preference - indifference)
            else:
                if pref_value < indifference:
                    array[row][col] = 0
                elif pref_value > preference:
                    array[row][col] = 100
                else:
                    array[row][col] = abs(pref_value - indifference) * 100 / abs(preference - indifference)                
    return array
    

def filter_house(house_list, criteria_list):
    '''
    Filters houses in addition to zillow's query

    Inputs
    house_list: list of house objects from running a zillow query
    criteria_list: list of criteria used in running the query

    Returns
    a new house_list with houses that don't meet criteria filtered out

    This serves 2 purposes:
    1. Zillow's url structure can only set the lower bound for
    number of bathrooms and bedrooms. This function will filter out
    houses that have more bathromm/bedrooms than the upper bound
    2. A few results that zillow returns with input criteria
    May internally store information that fit the conditions,
    But we might not have found where they are.
    Ideally this should not be the case but I added this to prevent errors
    '''
    # First create a dictionary of criteria from criteria_list
    criteria_dict = {}
    for j in range(len(criteria_list)):
        criteria_dict[j] = criteria_list[j]

    # For each house result
    for house in house_list:
        remove = False
        # For each criterion
        for j in range(len(criteria_list)):
            # If the condition is not met, set remove to True
            # The house is not removed in this stage in case
            # The house may not meet multiple criteria
            if type(criteria_dict[j][1]) == str:
                if not (house.info_dict[criteria_dict[j][0]] in criteria_dict[j]):
                    remove = True
            else:                       
                if not (house.info_dict[criteria_dict[j][0]] >= criteria_dict[j][1] and house.info_dict[criteria_dict[j][0]] <= criteria_dict[j][2]): 
                    remove = True  
        # Remove houses that did not meet the conditions
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
    # If the user did not specify any preferences and the weight_list only has 0s,
    # Assume that the user treates each preference equally
    if total_weight == 0:
        weight_array = np.array([[1 / len(weight_list)] for i in range(len(weight_list))])
    else:
        weight_array = np.array([[weight_list[i] / total_weight] for i in range(len(weight_list))])
    # Conduct matrix calculation to apply the weights to the scores
    return np.dot(score_array, weight_array)