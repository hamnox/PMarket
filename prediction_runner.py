#!/usr/bin/env python
import math
import json
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

#open the json file

def score(jsonfile, userfile=None):
    import time
    try:
        file = open(jsonfile,'r')
        predictions = json.load(file.read())
        file.close()
    #    if prediction_file.read() == "":
     #       raise IOError("SHTOP IT")
    except IOError:
        now = int(time.time())
        jsondata = json.loads(
        """[{"statement": "Sample Prediction: This prediction is false.",
                "history":
                    [{"timestamp":%d, "credence":50, "signature":"House"},
                    {"timestamp":1419028832, "credence":60, "signature":"Me"},
                    {"timestamp":1419028832, "credence":20, "signature":"You"},
                    {"timestamp":1419028832, "credence":50, "signature":"Me"}],
                "settled":true,
                "result":true,
                "tags":[
                    "paradoxes","initial sample"]
            }]""" % (now))
    try:
        file = open(userfile,'r')
        users = json.loads(file.read())
        file.close()
    except (IOError, TypeError):
        now = int(time.time())
        users = json.loads("""{"House":{"bits":0, "last-update":%d}, "Me":{"bits":0, "last-update":%d}}""" % (now, now))
    # print predictions,"\n\n", users, "\n\n"

    #load the subitems, woot
    # import pdb; pdb.set_trace()

    for prediction in jsondata:
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
                try:
                    users[bet["signature"]]["bits"] += calculate_bits(result, prev_bet, bet["credence"])
                    users[bet["signature"]]["last-update"] = int(time.time())
                except KeyError:
                    users[bet["signature"]] = {"bits":calculate_bits(result, prev_bet, bet["credence"]),
                                                "last-update":int(time.time())}
                #print bet["signature"], ":", str(bet["credence"]) + "%", "+" + str(calculate_bits(result, prev_bet, bet["credence"]))
                prev_bet = bet["credence"]
#        scores = {}"""

score("mispredictiones.txt")
"""
    for time, current_bet, user in Predictions:
        #can implement time cutoffs if needed
        if previous_bet == NaN:
            previous_bet = current_bet
            continue        #shall make it impossible to set a user as house, or repeat usernames.
        scores[user] = scores.get(user, 0) + calculate_bits(result,previous_bet,current_bet)"""

# json.dump(~~variable~~, prediction_file)