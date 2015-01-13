#!/usr/bin/env python
import math
import json
import time
# https://docs.python.org/2/howto/webservers.html
# using v2.7.5

def calculate_bits(result, market, update):
    update = float(update)
    market = float(market)
    if result:
        bits = 100 * math.log(update/market,2) #will error if market is zero do not let it be assigned a literal zero.
    else:
        bits = 100 * math.log((100-update)/(100-market),2) #will error if market is 100 do not let it be that
    return bits

def get_prediction_info(jsonfile, prediction_id):
    with open(jsonfile, 'r+') as file:
        jsondata = json.loads(file.read())

        return jsondata[prediction_id]

#open the json file

def score(jsonfile, userfile="userscores.json"):
    now = time.time() # i think this is utc, it might break cross-time zone if not.
    try:
        file = open(jsonfile,'r')
    #    if prediction_file.read() == "":
     #       raise IOError("SHTOP IT")
    except IOError:
        file = open(jsonfile,'w')
        file.write(""" "example_prediction":{
            "statement": "Sample Prediction: This prediction is false.",
            "history":
                [{"timestamp":%d, "credence":50, "signature":"House"}],
            "settled":false,
            "result":null,
            "tags":[
                "paradox", "example"]
            }}""" % (now))
        file.close()
        file = open(jsonfile,'r')
    finally:
        jsondata = json.loads(file.read())
        file.close()
        
        #second verse, same as the first!
    with open(userfile,'r') as myfile:
        users = json.loads(myfile.read())

    for id, prediction in jsondata.items():
        if prediction["settled"] and isinstance(prediction["result"],bool):
            result = prediction["result"]
        else:
            continue
        prev_bet = None
        for bet in prediction['history']:
            if bet["signature"] == "House":
                prev_bet = bet["credence"]
                continue
            else:
                bet["bits"] = calculate_bits(result, prev_bet, bet["credence"])
                try:
                    if bet["timestamp"] > users[bet["signature"]]["last-update"]:
                        users[bet["signature"]]["bits"] += bet["bits"]
                        users[bet["signature"]]["last-update"] = time.time()
                except KeyError:
                    users[bet["signature"]] = {"bits":bet["bits"],
                                                "last-update":time.time()}
                prev_bet = bet["credence"]
#        scores = {}"""

    with open(jsonfile,'w') as writer:
        writer.write(json.dumps(users, sort_keys=True))

    with open(jsonfile,'w') as writer:
        writer.write(json.dumps(jsondata, sort_keys=True))
    return users


def add_prediction(jsonfile,id,statement,housebet=50,tags=""):
    try:
        with open(jsonfile,'r') as myfile:
            jsondata = json.loads(myfile.read()) 
    except (IOError,ValueError):
        jsondata = {}

    if housebet >= 100 or housebet <= 0:
        raise ValueError("All bets must be greater than 0 and less than 100.")

    if id in jsondata.keys():
        if statement:
            jsondata[id]["statement"] = statement
    else:
        now = time.time()
        jsondata[id] = {"statement":statement,
            "history":[{"timestamp":now,"credence":housebet,"signature":"House"}],
            "settled":False,"result":None}
        if tags:
            if "tags" in jsondata[id].keys():
                jsondata[id]["tags"].extend([tag.strip() for tag in tags.split(",")])
            else:
                jsondata[id]["tags"] = [tag.strip() for tag in tags.split(",")]
    with open(jsonfile,'w') as writer:
        writer.write(json.dumps(jsondata, sort_keys=True))


def add_bet(jsonfile,user,id,bet,tags=""):
    try:
        with open(jsonfile,'r+') as myfile:
            jsondata = json.loads(myfile.read())
    except IOError:
        jsondata = {}
        #then write a function to extract and write fromthe jsonfile.
    if bet >= 100 or bet <= 0:
        raise ValueError("All bets must be greater than 0 and less than 100.")
    now = time.time()
    if tags:
        jsondata[id]["tags"] = [tag.strip() for tag in tags.split(",")]

    jsondata[id]["history"].append({"timestamp":now,"credence":bet,"signature":user})

    with open(jsonfile,'w') as writer:
        writer.write(json.dumps(jsondata, sort_keys=True))
    return jsondata[id]
