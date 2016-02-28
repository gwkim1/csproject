import Yelp
import sql_stuff
def rankings(property_list, user_preferences):
	Yelp_scores=Yelp.score_function(property_list)
	[property 1[restaurant score, grocery_store score, ???],property 2[],property 3[],[],[],[],[]]
	other_scores=sql_stuff.score_function(property_list)
	[property 1[safety_score, library_score, bike_score, transportation_score]]
	
	for y in Yelp_scores:
		#add the two vectors
		user_preferences *dot product* final_vector


