import numpy as np


def create_array(house_list, criteria_list):
    '''
    Creates a numpy array to store the scores for every house and every criterion
    For blocks in which a house doesn't meet a criterion, set the initial value as None

    for now, the two arguments must look like:
    house_list: [House, House, House] House objects
    criteria_list: [("price", 1000, 2000, None), ("house_type", "houses", "apartments", "condos/co-ops")]
    for numerical criterion: (criterion name, lower bound, upper bound, ideal value)
    for categorical criterion: (criterion name, first choice, second choice .... nth choice)

    Output:
    returns a numpy array filled with either 0 or None
    '''
    house_dict = {}
    criteria_dict = {}

    # should prbly define len of house_list and criteria_list

    for i in range(len(house_list)):
        house_dict[i] = house_list[i]
    for j in range(len(criteria_list)):
        criteria_dict[j] = criteria_list[j]
    
    score_array = np.array([[0 for i in range(len(criteria_list))] for i in range(len(house_list))])
    
    for i in range(len(house_list)):
        for j in range(len(criteria_list)):
            if type(criteria_dict[j][1]) == str:
                # This obviously does not work. how to fix this problem?
                if not house_dict[i].info_dict[criteria_dict[j][0]] in criteria_dict[j]:
                    # array only accepts numbers!!! need to change this default value
                    score_array[i][j] = -1
            else:
                if not (house_dict[i].info_dict[criteria_dict[j][0]] >= criteria_dict[j][1] and house_dict[i].info_dict[criteria_dict[j][0]] <= criteria_dict[j][2]):
                    score_array[i][j] = -1   
    
    return score_array


IDEAL_VALUE = {}


def calculate_preference(array, house_list, criteria_list):
    '''
    NOTE
    numpy array does not accept floating values! that is why I multiplied by 100 for now.
    '''
    for col in range(len(criteria_list)):
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
                pref_value = house_list[row].info_dict[criteria_list[col][0]]
            else:
                pref_value =   len(criteria_list[col]) - ####index of the value e.g. house_type  / (len(criteria_list[col]) - 1)


            print("pref:", pref_value, "indif:", indifference, "pref:", preference)
            if pref_value < indifference:
                array[row][col] = 0
            elif pref_value > preference:
                array[row][col] = 100
            else:
                array[row][col] = (pref_value - indifference) * 100 / (preference - indifference)
    return array 


def get_weighted_score(array, weight_list, house_list):
    '''
    return a list of weighted scores for each house

    NOT SURE whether I should return a score_list or just store the score in House object.
    '''
    score_list = []
    for row in range(len(array)):
        score = 0
        for i in range(len(array[row])):
            score += array[row][i] * weight_list[i]
        score_list.append(score)
        house_list[row].weighted_score = score
    return score_list