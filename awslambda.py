
import datetime
import requests
import json
from pprint import pprint

import flowserve_data # this has the security stuff

API_BASE=flowserve_data.API_BASE
APP_KEY=flowserve_data.APP_KEY

def lambda_handler(event, context):
    if event["session"]["new"]:
        on_session_started({"requestId": event["request"]["requestId"]}, event["session"])

    if event["request"]["type"] == "LaunchRequest":
        return on_launch(event["request"], event["session"])
    elif event["request"]["type"] == "IntentRequest":
        return on_intent(event["request"], event["session"])
    elif event["request"]["type"] == "SessionEndedRequest":
        return on_session_ended(event["request"], event["session"])

def on_session_started(session_started_request, session):
    return

def on_launch(launch_request, session):
    return get_welcome_response()

def on_intent(intent_request, session):
    intent = intent_request["intent"]
    intent_name = intent_request["intent"]["name"]

    if intent_name == "ManyPumpsIntent":
        return get_system_status()
    elif intent_name == "SinglePumpIntent":
        return get_individual_status()
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")

def on_session_ended(session_ended_request, session):
    # Cleanup goes here...
    return

def handle_session_end_request():
    card_title = "Flowserve - Thanks"
    speech_output = "Thank you for using the Flowserve skill.  See you next time!"
    should_end_session = True

    return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))

def get_welcome_response():
    session_attributes = {}
    card_title = "Flowserve"
    speech_output = "Welcome to the Alexa Flowserve Skill" \
                    "You can ask me for the status of all of your pumps" \
                    "or you can ask me about a specific pump by saying the tag"
    reprompt_text = "Please ask me for either the status of all your pumps, " \
                    "or a specific, for example, 'status of pump a. b. c. 4"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_system_status():
    session_attributes = {}
    card_title = "Flowserve pump status"
    reprompt_text = ""
    should_end_session = False

    speech_output = "All of the pumps are operating normally" # ... hopefuly

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_individual_status():
    session_attributes = {}
    card_title = "Pump Status"
    reprompt_text = ""
    should_end_session = False

    # this gets the status of all of the attributes supplied
    vals = get_attr_status('Suction Pressure', 'Discharge Pressure', 'Suction Temperature')

    succ = vals['Suction Pressure'] # gets just the suction pressure
    temp = vals['Suction Temperature'] #just temp ...
    disc = vals['Discharge Pressure'] # just discharge

    speech_output = str("Suction pressure is " + succ['status'] + " at ")
    speech_output += str(round(succ['value'],2)) + " " + str(succ['unit'] + ". ") 

    speech_output += str("Suction Temperature is " + temp['status'] + " at ")
    speech_output += str(round(temp['value'],2)) + " " + str(temp['unit'] + ". ") 

    speech_output += str("Discharge pressure is " + disc['status'] + " at ")
    speech_output += str(round(disc['value'],2)) + " " + str(disc['unit'] + ". ") 
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        "outputSpeech": {
            "type": "PlainText",
            "text": output
        },
        "card": {
            "type": "Simple",
            "title": title,
            "content": output
        },
        "reprompt": {
            "outputSpeech": {
                "type": "PlainText",
                "text": reprompt_text
            }
        },
        "shouldEndSession": should_end_session
    }

def build_response(session_attributes, speechlet_response):
    return {
        "version": "1.0",
        "sessionAttributes": session_attributes,
        "response": speechlet_response
    }

def fmt_date_time(d):
    return d.strftime("%Y-%m-%d %H:%M:%S")

def getDateStringTuple():
    end = datetime.datetime.now() - datetime.timedelta(hours = 2) #west cost time so minus two hours
    start = end - datetime.timedelta(seconds = 10) # minus two minutes because we want to pull from current time to 
                                                  # current time minus
    return (fmt_date_time(start),fmt_date_time(end)) 

def get_attr_values(*attr_name):
    """
    =======================
    DEEPLY BROKEN DON'T USE
    =======================
    """
    if attr_name not in ['Suction Pressure', 'Discharge Pressure', 'Suction Temperature']:
        return False
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

    #print(f['Result'][-1]['Status'])
    return str(round(f['Result'][-1]['Value'], 2)) + " " + str(f['Result'][-1]['Unit'])  


def get_attr_status(*attr_name):
    # The reason that we get all the attributes at the same time is to reduce time spent on the requests.
    # If we tried to do each request individually, it takes a lot longer. For example, 3 attributes takes
    # just around 1.1s. If we did them each seperate it can take up to 7 seconds, at which point AWS lambda
    # will time out


    name_list = ""
    # this bit joins together all the attributes requested
    for name in attr_name:
        if name not in ['Suction Pressure', 'Discharge Pressure', 'Suction Temperature']:
            return False # if you try to get an attribute that is not in the db, just return early
        else:
            name_list += name
            name_list += ", " # adds a comma and space after every attribute so that Thingworx likes it

    name_list = name_list[0:-2] # this trims off the last comma and space off of the end 


    #print(name_list)
    
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

    return return_dict
    #print(f['Result'][-1]['Status'])
    #return f['Result'][-1]['Status']
    



#test_get()
#print(getDateStringTuple())
#print(get_attr_status('Suction Pressure'))
#print(get_attr_status('Suction Temperature'))
#print(get_attr_status('Discharge Pressure'))
#print(get_individual_status())
#print(lambda_handler(test_case, []))

#vals = get_attr_status('Suction Pressure', 'Discharge Pressure')
#suc = vals["Suction Pressure"]
#pprint(suc)
print(get_individual_status())
