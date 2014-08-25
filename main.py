import time
import requests
import json
import datetime
import math

import twitch
import keypresser

t = twitch.Twitch();
k = keypresser.Keypresser();

#Enter your twitch username and oauth-key below, and the app connects to twitch with the details.
#Your oauth-key can be generated at http://twitchapps.com/tmi/
# username = "bardarbungaplayspokemon";
# key = "oauth:hdgqzc56vmcu8nf7m59j7oclhxzgpbi";
# t.twitch_connect(username, key);

class Earthquake:
    def __init__(self, quakeData):
        self.date = quakeData["date"]
        self.depth = quakeData["depth"]
        self.lat = quakeData["lat"]
        self.loc_dir = quakeData["loc_dir"]
        self.loc_dist = quakeData["loc_dist"]
        self.loc_name = quakeData["loc_name"]
        self.long = quakeData["long"]
        self.quality = quakeData["quality"]
        self.size = quakeData["size"]
        self.verified = quakeData["verified"]


    def __repr__(self):
        pass

earthquakesByDate = {}


def bearing(origin, destination):
    lat1, lon1 = origin
    lat2, lon2 = destination
 
    rlat1 = math.radians(lat1)
    rlat2 = math.radians(lat2)
    rlon1 = math.radians(lon1)
    rlon2 = math.radians(lon2)
    dlon = math.radians(lon2-lon1)
 
    b = math.atan2(math.sin(dlon)*math.cos(rlat2),math.cos(rlat1)*math.sin(rlat2)-math.sin(rlat1)*math.cos(rlat2)*math.cos(dlon)) # bearing calc
    bd = math.degrees(b)
    br,bn = divmod(bd+360,360) # the bearing remainder and final bearing
    
    return bn


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    km = 6367 * c
    return km


minLat = 64.4
maxLat = 65.3

minLong = -18.1
maxLong = -15


keys = {"up":"w", "down":"w", "left":"a", "right":"d", "a":"z", "b":"x", "select":"c", "start":"v"}


def IsRelevant(quakeData):
    lat = quakeData["lat"]
    long = quakeData["long"]

    if lat < minLat or lat > maxLat:
        return False

    if long < minLong or long > maxLong:
        return False

    return True


#The main loop
while True:
    #Check for new mesasages
    #new_messages = t.twitch_recieve_messages();

    url = "http://isapi.rasmuskr.dk/api/earthquakes/?date=1-hoursago"
    r = requests.get(url)
    earthquakes = r.json().get("items")

    for quakeData in earthquakes:
        date = quakeData["date"]
        if not date in earthquakesByDate:
            if IsRelevant(quakeData):
                q = Earthquake(quakeData)

                print u"{time}: Magnitude {size}, {loc_dist} {loc_dir} of {loc_name}.".format(
                        time = datetime.datetime.utcfromtimestamp(int(q.date)).strftime('%Y-%m-%d %H:%M:%S'),
                        size = q.size,
                        loc_dist = q.loc_dist,
                        loc_dir = q.loc_dir,
                        loc_name = q.loc_name,
                    ).encode("utf-8")

                earthquakesByDate[date] = q
        else:
            quake = earthquakesByDate[date]
            if quakeData["verified"] and not quake.verified:
                earthquakesByDate[date] = Earthquake(quakeData)

    # if not new_messages:
    #     #No new messages...
    #     continue
    # else:
    #     for message in new_messages:
    #         #Wuhu we got a message. Let's extract some details from it
    #         msg = message['message'].lower()
    #         username = message['username'].lower()
    #         print(username + ": " + msg);

    #         #This is where you change the keys that shall be pressed and listened to.
    #         #The code below will simulate the key q if "q" is typed into twitch by someone
    #         #.. the same thing with "w"
    #         #Change this to make Twitch fit to your game!
    #         if msg == "q": k.key_press("q");
    #         if msg == "w": k.key_press("w");

    time.sleep(10)