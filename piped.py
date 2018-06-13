import servp
import flowserve_data
import requests
from pprint import pprint

def post(attr_dict):
	url = flowserve_data.PUT_BASE
	key = flowserve_data.LOCAL_KEY

	payload = {
		"suc_p"    : attr_dict['Suction Pressure'],
		"dis_p"    : attr_dict['Discharge Pressure'],
		"suc_t"    : attr_dict['Suction Temperature'],
		"vel_horz" : attr_dict['Bearing Velocity'],
		"vel_vert" : attr_dict['Bearing Velocity Horizontal'],

	}

	headers = {
		"Content-Type" : "application/json",
		"appkey"       : key
	}


	response = requests.request("PUT", url, data=payload, headers=headers)

	return False

vals = servp.get_attr_status('Suction Pressure', 'Discharge Pressure', 'Suction Temperature', 'Bearing Velocity',
                           'Bearing Velocity Horizontal')

pprint(vals)