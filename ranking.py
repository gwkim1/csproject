import numpy as np
import zillow

'''
Ideas for improvement:
1. May change the way of calculating the preferences if the result is not satisfactory for the user
2. 


What hasn't been done yet:
1. tiebreaking?
2. dealing with the "ideal value"
'''

def get_house_list(criteria_list, url):
    soup = zillow.get_soup(url)
    house_list = zillow.create_house_objects(soup)
    new_house_list = create_array(house_list, criteria_list, return_list=True)
    return new_house_list


def concatenate_arrays(array_list):
    '''
    concatenate all numpy arrays
    '''



def suggest_house(house_list, criteria_list):
    '''
    This is a function that combines all functions under

    house_list: [House, House, House] House objects
    criteria_list: [["price", 1000, 2000, None, 300], ["house_type", "houses", "apartments", "condos/co-ops", 500]]
    for numerical criterion: [criterion name, lower bound, upper bound, ideal value, weight]
    for categorical criterion: [criterion name, first choice, second choice .... nth choice, weight]

    returns a list with each tuple being: (ranking, address, score, house object)
    '''
    arr = create_array(house_list, criteria_list)
    score_array = calculate_preference(arr, house_list, criteria_list)
    weighted_array = get_weighted_score(score_array, criteria_list)
    return show_ranking(weighted_array, house_list)


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
    #print("score_array", score_array)
    #print(len(criteria_list))
    #print(len(house_list))
    need_to_delete = set()

    #score_array = np.delete(score_array, i, 0)
    #del house_list[i]
    
    
    for i in range(len(house_list)):
        for j in range(len(criteria_list)):
            if type(criteria_dict[j][1]) == str:
                if not house_dict[i].info_dict[criteria_dict[j][0]] in criteria_dict[j]:
                    # array only accepts numbers!!! need to change this default value
                    #score_array[i][j] = -1
                    need_to_delete.add(i)
                    print("house", i, "does not meet criterion", j)
            else:
                if not (house_dict[i].info_dict[criteria_dict[j][0]] >= criteria_dict[j][1] and house_dict[i].info_dict[criteria_dict[j][0]] <= criteria_dict[j][2]):
                    need_to_delete.add(i)  
                    print("house", i, "does not meet criterion", j)
                    print(house_dict[i].info_dict[criteria_dict[j][0]], criteria_dict[j][1], criteria_dict[j][2])
    
    #print("need_to_delete:", need_to_delete)

    if len(need_to_delete) != 0:
        need_to_delete = list(need_to_delete)
        need_to_delete.sort()
        need_to_delete.reverse()
    #print("need_to_delete:", need_to_delete)

    for i in need_to_delete:
        score_array = np.delete(score_array, i, 0)
        del house_list[i]        

    return score_array
    

IDEAL_VALUE = {}


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
                pref_value = (len(criteria_list[col][1:-1]) - (criteria_list[col][1:-1].index(house_list[row].info_dict[criteria_list[col][0]]))) / len(criteria_list[col][1:-1])
                #print(criteria_list[col])
                #print("house_list[row].info_dict[criteria_list[col][0]]", house_list[row].info_dict[criteria_list[col][0]])
                #print(criteria_list[col][1:-1].index("houses")) #- ####index of the value e.g. house_type  / (len(criteria_list[col]) - 1)


            print("pref:", pref_value, "indif:", indifference, "pref:", preference)
            if pref_value < indifference:
                array[row][col] = 0
            elif pref_value > preference:
                array[row][col] = 1
            else:
                array[row][col] = (pref_value - indifference) * 100 / (preference - indifference)
    return array


def get_weighted_score(score_array, criteria_list):
    total_weight = 0
    for ctuple in criteria_list:
        total_weight += ctuple[-1]
    weight_array = np.array([[criteria_list[i][-1]/total_weight] for i in range(len(criteria_list))])
    return np.dot(score_array, weight_array)


# need tiebreaking + sorting along with house_list
def show_ranking(weighted_array, house_list):
    '''
    Taking the array of weighted score and list of houses(that meet the criteria) as arguments,
    returns a list of tuples sorted by score in descending order with
    each tuple: (rank, house object, score)
    '''
    score_list = []
    index = 0
    for score in weighted_array:
        score_list.append((score[0], index))
        index += 1
    score_list.sort()
    score_list.reverse()

    rank_list = []
    for score_tuple in score_list:
        # This if statement can probably be reduced to something simpler
        if len(rank_list) == 0:
            rank_list.append((len(rank_list) + 1, house_list[score_tuple[1]].address, score_tuple[0], house_list[score_tuple[1]]))
        elif score_tuple[0] == rank_list[-1][2]:
            print(rank_list[-1][0])
            rank_list.append((rank_list[-1][0], house_list[score_tuple[1]].address, score_tuple[0], house_list[score_tuple[1]]))
        else:
            rank_list.append((len(rank_list) + 1, house_list[score_tuple[1]].address, score_tuple[0], house_list[score_tuple[1]]))

    return rank_list