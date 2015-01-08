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

def score(jsonfile, userfile="userscores.json"):
    import time
    now = int(time.time()) # i think this is utc, it might break cross-time zone if not.
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
    try:
        file = open(userfile,'r')
        users = json.loads(file.read())
        file.close()
    except (IOError, TypeError):
        users = json.loads("""{"House":{}}""" % (now))
    # print predictions,"\n\n", users, "\n\n"

    #load the subitems, woot
    # import pdb; pdb.set_trace()

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
                try:
                    if bet["timestamp"] > bet["signature"]:
                        users[bet["signature"]]["bits"] += calculate_bits(result, prev_bet, bet["credence"])
                        users[bet["signature"]]["last-update"] = int(time.time())
                    else:
                        continue
                except KeyError:
                    users[bet["signature"]] = {"bits":calculate_bits(result, prev_bet, bet["credence"]),
                                                "last-update":int(time.time())}
                #print bet["signature"], ":", str(bet["credence"]) + "%", "+" + str(calculate_bits(result, prev_bet, bet["credence"]))
                prev_bet = bet["credence"]
#        scores = {}"""

    file = open(userfile,'w')
    try:
        json.dump(users,file, sort_keys=True,indent=4 * ' ')
    except TypeError:
        json.dump(users,file, sort_keys=True,indent=4)
    file.close

class DuplicationError(KeyError):
    pass

def add_prediction(jsonfile,id,statement,housebet=50,*args):
    try:
        myfile = open(jsonfile,'r')
        jsondata = json.loads(myfile.read()) #perhaps I can add an array of ID values to my json file to make parses like this faster.
    except (IOError,ValueError):
        myfile = open(jsonfile,'w')
        jsondata = {}
    if id in jsondata.keys():
        raise DuplicationError("A prediction already exists under this ID!")
    if housebet >= 100 or housebet <= 0:
        raise ValueError("All bets must be greater than 0 and less than 100.")
    import time
    now = int(time.time())
    jsondata[id] = {"statement":statement,
        "history":[{"timestamp":now,"credence":housebet,"signature":"House"}],
        "settled":False,"result":None}
    if args:
        jsondata[id]["tags"] = list(args)
    myfile.close()
    myfile = open(jsonfile,'w')
    myfile.write(json.dumps(jsondata))
    myfile.close()
    return


def add_bet(jsonfile,user,id,bet):
    try:
        file = open(jsonfile,'r+')
        jsondata = json.loads(file.read())
    except IOError:
        raise KeyError("Need to make a new file, this one ain't working.")
        jsondata = {}
        #then write a function to extract and write fromthe jsonfile.
    if id not in jsondata.keys():
        raise KeyError("Eeek! That prediction id does not appear to exist!")
    if bet >= 100 or bet <= 0:
        raise ValueError("All bets must be greater than 0 and less than 100.")
    import time
    now = int(time.time())
    jsondata[id]["history"].append({"timestamp":now,"credence":bet,"signature":user})
    #error may happen here.
    file.close()
    file = open(jsonfile,'w')
    json.dump(jsondata,file)
    file.close()
    return jsondata[id]
    
# add_prediction("testadd.json","Magic","will this work?",2,'example','test')
#score("mispredictiones.json")
