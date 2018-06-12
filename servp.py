import datetime
import requests
import json
from pprint import pprint

import flowserve_data # this has the security stuff

API_BASE=flowserve_data.API_BASE
APP_KEY=flowserve_data.APP_KEY

def fmt_date_time(d):
    return d.strftime("%Y-%m-%d %H:%M:%S")

def getDateStringTuple():
    end = datetime.datetime.now() - datetime.timedelta(hours = 2) #west cost time so minus two hours
    start = end - datetime.timedelta(seconds = 10) # minus two minutes because we want to pull from current time to 
                                                  # current time minus
    return (fmt_date_time(start),fmt_date_time(end))


def get_attr_status(*attr_name):
    # The reason that we get all the attributes at the same time is to reduce time spent on the requests.
    # If we tried to do each request individually, it takes a lot longer. For example, 3 attributes takes
    # just around 1.1s. If we did them each seperate it can take up to 7 seconds, at which point AWS lambda
    # will time out


    name_list = ""
    # this bit joins together all the attributes requested
    for name in attr_name:
        if name not in ['Suction Pressure', 'Discharge Pressure', 'Suction Temperature', 'Bearing Velocity' ]:
            return False # if you try to get an attribute that is not in the db, just return early
        else: 
            name_list += name
            name_list += ", " # adds a comma and space after every attribute so that Thingworx likes it
    #print(name_list)
    name_list = name_list[0:-2] # this trims off the last comma and space off of the end 


    print(name_list)
    print(attr_name)
    
    base = API_BASE
    time = getDateStringTuple()
    #print(time)
    params = { 
         'appKey'        :  APP_KEY,
         'pumpId'        : 'FLS_GTTC_PC5',
         'attributeList' :  attr_name,
         'startDate'     :  time[0],
         'endDate'       :  time[1]}

    url = API_BASE

    headers = {
        'accept': "application/json",
        'content-type': "application/json",
        'cache-control': "no-cache"
        }


    response = requests.request("POST", url, headers=headers, params=params)

    f = json.loads(response.text) 
    #pprint(f)

    # this bit goes through all of the values from the request and puts them in an easier
    # to use dictionary
    return_dict = {}
    for name in attr_name:
        name_dict = next(item for item in f['Result'] if item['Name'] == name)
        name_dict = {
            'status' : name_dict['Status'],
            'value'  : name_dict['Value'],
            'unit'   : name_dict['Unit']
        }
        return_dict[name] = name_dict
    pprint(return_dict)
    return return_dict
    #print(f['Result'][-1]['Status'])
    #return f['Result'][-1]['Status']


def test_individual_status():
    session_attributes = {}
    card_title = "Pump Status"
    reprompt_text = ""
    should_end_session = False

    # this gets the status of all of the attributes supplied
    vals = get_attr_status('Suction Pressure', 'Discharge Pressure', 'Suction Temperature', 'Bearing Velocity')

    succ = vals['Suction Pressure'] # gets just the suction pressure
    temp = vals['Suction Temperature'] #just temp ...
    disc = vals['Discharge Pressure'] # just discharge

    speech_output = str("Suction pressure is " + succ['status'] + " at ")
    speech_output += str(round(succ['value'],2)) + " " + str(succ['unit'] + ". ") 

    speech_output += str("Suction Temperature is " + temp['status'] + " at ")
    speech_output += str(round(temp['value'],2)) + " " + str(temp['unit'] + ". ") 

    speech_output += str("Discharge pressure is " + disc['status'] + " at ")
    speech_output += str(round(disc['value'],2)) + " " + str(disc['unit'] + ". ") 
    return speech_output

test_individual_status()
#print(test_individual_status())