import numpy as np
import zillow

'''
Ideas for improvement:
1. May change the way of calculating the preferences if the result is not satisfactory for the user
2. 


What hasn't been done yet:
1. tiebreaking?
2. get_house_list doesn't work(because of create_array) and is too slow
'''




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
    url = zillow.create_url(zipcode, listing_type, criteria_list)
    soup = zillow.get_soup(url)
    house_list = zillow.create_house_objects(soup, url)
    print("num of houses before running create_array:", len(house_list))
    new_house_list = create_array(house_list, criteria_list, return_list=True)
    return new_house_list

'''
def get_house_list_alt(zipcode, listing_type, criteria_list):
    url = zillow.create_url(zipcode, listing_type, criteria_list)
    soup = zillow.get_soup(url)
    house_list = zillow.create_house_objects(soup, url)
    #print(house_list)
    #new_house_list = create_array(house_list, criteria_list, return_list=True)
    return house_list
'''

'''
FOR RYAN AND PEDRO: when your website gives the scores and weights back run get_final_scores to get
a list of tuples with each tuple being like (rank, house address, score, House object)

Need to change the same of the arguments so that they are intuitive
'''

CRITERION_DICT = {0: "price", 1: "house_type", 2: "bathroom", 3: "bedroom", 4: "restaurants", 5: "active life" , 6: "arts and entertainment", 7: "schools/education", 8: "health establishments", 9: "nightlife", 10: "shopping outlets", 11: "violent crime", 12: "property crime", 13: "other victimed non-violent crime", 14: "quality of life crime"}

def get_final_scores(house_list, criteria_list, ypchicago_scores, zillow_pref, database_pref, Yelp_pref):
    ypchicago_scores = np.array(ypchicago_scores)
    zillow_scores = get_zillow_scores(house_list, criteria_list)
    array_list = [zillow_scores, ypchicago_scores]
    weight_list = zillow_pref + database_pref + Yelp_pref


    new_array = concatenate_arrays(array_list)
    weighted_array = get_weighted_score(new_array, weight_list)

    print("weight_list:", weight_list)
    users_pref = [0] * len(weight_list)
    for i in range(len(weight_list)):
        if weight_list[i] == 0:
            users_pref[i] = 1

    score_per_criterion = []
    for i in range(len(users_pref)):
        if users_pref[i] != 1:
            score_list = []
            for house_scores in new_array:
                score_list.append(house_scores[i])
            score_per_criterion.append({CRITERION_DICT[i]: score_list})
            
    show_ranking(weighted_array, house_list)

    return score_per_criterion





def get_zillow_scores(house_list, criteria_list):
    '''
    do I need to sort criteria_list? prbly not
    '''
    base_array = np.array([[0 for i in range(len(criteria_list))] for i in range(len(house_list))])
    #print(base_array)
    return calculate_preference(base_array, house_list, criteria_list)


def suggest_house(house_list, criteria_list, weight_list):
    '''
    This is a function that combines all functions under

    house_list: [House, House, House] House objects
    criteria_list: [["price", 1000, 2000], ["house_type", "houses", "apartments", "condos/co-ops"]]
    for numerical criterion: [criterion name, lower bound, upper bound]
    for categorical criterion: [criterion name, first choice, second choice .... nth choice]

    returns a list with each tuple being: (ranking, address, score, house object)
    '''
    arr = create_array(house_list, criteria_list)
    score_array = calculate_preference(arr, house_list, criteria_list)
    weighted_array = get_weighted_score(score_array, weight_list)
    return show_ranking(weighted_array, house_list)



###### Order of zillow_pref: price house_type bathrooms bedrooms
def sort_criteria_list(criteria_list):
    order = ["price", "house_type", "bathroom", "bedroom"]
    sorted_list = []
    for criterion in order:
        for block in criteria_list:
            if block[0] == criterion:
                sorted_list.append(block)
    return sorted_list


# This also deletes houses that does not meet criteria from the original house_list
def create_array(house_list, criteria_list, return_list=False):
    '''
    Creates a numpy array to store the scores for every house and every criterion
    For blocks in which a house doesn't meet a criterion, set the initial value as None

    Output:
    returns a numpy array filled with either 0 or None

    I may have to delete the "deleting" part, but I need this just in case zillow returns
    So while the criteria_list is the same as what we put in in create_url, what pedro and ryan should use
    is the house_list that this function outputs.
    '''
    house_dict = {}
    criteria_dict = {}

    # should prbly define len of house_list and criteria_list

    for i in range(len(house_list)):
        house_dict[i] = house_list[i]
    for j in range(len(criteria_list)):
        criteria_dict[j] = criteria_list[j]

    score_array = np.array([[0 for i in range(len(criteria_list))] for i in range(len(house_list))])

    need_to_delete = set()


    for i in range(len(house_list)):
        for j in range(len(criteria_list)):
            if type(criteria_dict[j][1]) == str:
                if not (house_dict[i].info_dict[criteria_dict[j][0]] in criteria_dict[j]):
                    need_to_delete.add(i)
                    print("house", i, "does not meet criterion", j)
                    print(house_dict[i].info_dict["address"])
                    print(house_dict[i].info_dict[criteria_dict[j][0]])
            else:                       
                if not (house_dict[i].info_dict[criteria_dict[j][0]] >= criteria_dict[j][1] and house_dict[i].info_dict[criteria_dict[j][0]] <= criteria_dict[j][2]):
                    need_to_delete.add(i)  
                    print("house", i, "does not meet criterion", j)
                    print(house_dict[i].info_dict["address"])
                    print(house_dict[i].info_dict[criteria_dict[j][0]], criteria_dict[j][1], criteria_dict[j][2])

    if len(need_to_delete) != 0:
        need_to_delete = list(need_to_delete)
        need_to_delete.sort()
        need_to_delete.reverse()

    for i in need_to_delete:
        score_array = np.delete(score_array, i, 0)
        del house_list[i]        

    if return_list == True:
        return house_list

    return score_array
    


def calculate_preference(array, house_list, criteria_list):
    '''
    NOTE
    numpy array does not accept floating values! that is why I multiplied by 100 for now.

    example of a tuple for categorical variable: ["house_type", "houses", "apartments", "condos/co-ops", 500]
    '''
    for col in range(len(criteria_list)):
        #print(criteria_list[col])
        if type(criteria_list[col][1]) in [int, float]:
            range_len = criteria_list[col][2] - criteria_list[col][1]
            indifference = criteria_list[col][1] + range_len * 0.1
            preference = criteria_list[col][2] - range_len * 0.1
        else:
            # Not sure about this
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
    

def concatenate_arrays(array_list):
    '''
    concatenates all numpy arrays
    '''
    new_arr = array_list[0]
    for arr in array_list[1:]:
        new_arr = np.append(new_arr, arr, axis=1)
    return new_arr


'''
weight_list has to be the addition of the three weight_lists:
zillow_pref + database_pref + Yelp_pref
'''
def get_weighted_score(score_array, weight_list):
    total_weight = 0
    for weight in weight_list:
        total_weight += weight
    weight_array = np.array([[weight_list[i]/total_weight] for i in range(len(weight_list))])
    #for ctuple in criteria_list:
    #    total_weight += ctuple[-1]
    #    print(ctuple[-1])
    #print(criteria_list[0][-1])
    #print(criteria_list[0])
    #weight_array = np.array([[criteria_list[i][-1]/total_weight] for i in range(len(criteria_list))])

    '''
    need to add list of weights that Pedro and Ryan would pass me back to weight_array
    '''
    return np.dot(score_array, weight_array)


# need tiebreaking + sorting along with house_list
def show_ranking(weighted_array, house_list):
    '''
    Taking the array of weighted score and list of houses(that meet the criteria) as arguments,
    returns a list of tuples sorted by score in descending order with
    each tuple: (rank, house object, score)
    '''
    for i in range(len(house_list)):
        house_list[i].score = weighted_array[i][0]

    #for house in house_list:
        #print(house.score, house.info_dict)

    score_list = []
    index = 0
    for score in weighted_array:
        score_list.append((score[0], index))
        index += 1
    score_list.sort()
    score_list.reverse()
    #print(score_list)

    rank_list = []
    for score_tuple in score_list:
        # This if statement can probably be reduced to something simpler
        rank_list.append(house_list[score_tuple[1]])        
    return 111
    print("rank_list:", rank_list)
    return rank_list

        #if len(rank_list) == 0:
        #    rank_list.append((len(rank_list) + 1, house_list[score_tuple[1]].address, score_tuple[0], house_list[score_tuple[1]]))
        #elif score_tuple[0] == rank_list[-1][2]:
        #    print(rank_list[-1][0])
        #    rank_list.append((rank_list[-1][0], house_list[score_tuple[1]].address, score_tuple[0], house_list[score_tuple[1]]))
        #else:
        #    rank_list.append((len(rank_list) + 1, house_list[score_tuple[1]].address, score_tuple[0], house_list[score_tuple[1]]))
    #for house in rank_list:
    #    print(house.score)

    