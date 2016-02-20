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
                if not house_dict[i].criteria_dict[j][0] in criteria_dict[j]:
                    score_array[i][j] = None
            else:
                if not house_dict[i].criteria_dict[j][0] >= criteria_dict[j][1] and house_dict[i].criteria_dict[j][0] <= criteria_dict[j][2]:
                    score_array[i][j] = None   

    return score_array