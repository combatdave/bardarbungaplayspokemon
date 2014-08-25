import time
import requests
import json
import datetime
import math
import random

#Enter your twitch username and oauth-key below, and the app connects to twitch with the details.
#Your oauth-key can be generated at http://twitchapps.com/tmi/
# username = "bardarbungaplayspokemon";
# key = "oauth:hdgqzc56vmcu8nf7m59j7oclhxzgpbi";
# t.twitch_connect(username, key);

def UnixToDatetime(unixTime):
    return datetime.datetime.utcfromtimestamp(int(unixTime))


class Earthquake:
    def __init__(self, quakeData):
        self.date = UnixToDatetime(quakeData["date"])
        self.depth = quakeData["depth"]
        self.lat = quakeData["lat"]
        self.loc_dir = quakeData["loc_dir"]
        self.loc_dist = quakeData["loc_dist"]
        self.loc_name = quakeData["loc_name"]
        self.long = quakeData["long"]
        self.quality = quakeData["quality"]
        self.size = quakeData["size"]
        self.verified = quakeData["verified"]


    def __str__(self):
        return u"{time}: Magnitude {size}, {loc_dist} {loc_dir} of {loc_name}.".format(
                        time = self.date.strftime('%Y-%m-%d %H:%M:%S'),
                        size = self.size,
                        loc_dist = self.loc_dist,
                        loc_dir = self.loc_dir,
                        loc_name = self.loc_name,
                    ).encode("utf-8")


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


minLat = 63.8
maxLat = 65.5

minLong = -18.5
maxLong = -15



def IsRelevant(quakeData):
    lat = quakeData["lat"]
    long = quakeData["long"]

    if lat < minLat or lat > maxLat:
        return False

    if long < minLong or long > maxLong:
        return False

    return True


class EarthquakeStore:
    def __init__(self):
        self.lastUpdate = None
        self.earthquakes = None
        self.centerPoint = None
        self.randomList = None


    def CheckShouldUpdate(self):
        now = datetime.datetime.now()
        if self.lastUpdate is None or (now - self.lastUpdate).seconds / 60 > 5:
            self.LoadData()
            self.lastUpdate = now


    def LoadData(self):
        self.lastUpdate = datetime.datetime.now()

        print "Fetching data"

        url = "http://isapi.rasmuskr.dk/api/earthquakes/?date=5-hoursago"
        r = requests.get(url)
        earthquakes = r.json().get("items")

        for quakeData in earthquakes:
            date = quakeData["date"]
            if not date in earthquakesByDate:
                if IsRelevant(quakeData):
                    q = Earthquake(quakeData)
                    earthquakesByDate[date] = q
            else:
                quake = earthquakesByDate[date]
                if quakeData["verified"] and not quake.verified:
                    earthquakesByDate[date] = Earthquake(quakeData)

        times = earthquakesByDate.keys()
        times = sorted(times)

        self.centerPoint = None
        for quake in earthquakesByDate.itervalues():
            if self.centerPoint is None:
                self.centerPoint = (quake.lat, quake.long)
            else:
                self.centerPoint = (self.centerPoint[0] + quake.lat, self.centerPoint[1] + quake.long)

        self.centerPoint = (self.centerPoint[0] / len(earthquakesByDate), self.centerPoint[1] / len(earthquakesByDate))

        latest = UnixToDatetime(times[-1])

        keysToUse = []
        for i in xrange(len(times)-1, -1, -1):
            thisTime = UnixToDatetime(times[i])
            oldness = latest - thisTime
            oldnessInMinutes = oldness.seconds / 60.0
            if oldnessInMinutes <= 60:
                keysToUse.append(times[i])
            else:
                break

        self.randomList = []
        for timeKey in keysToUse:
            quake = earthquakesByDate[timeKey]
            self.randomList += [quake] * int(math.pow(quake.size, 2.0) * 10)


    def GetCenter(self):
        self.CheckShouldUpdate()
        if self.centerPoint is None:
            self.LoadData()
        return self.centerPoint


    def GetRandomQuake(self):
        return random.choice(self.GetRandomList())


    def GetRandomList(self):
        self.CheckShouldUpdate()
        if self.randomList is None or len(self.randomList) == 0:
            self.LoadData()
        return self.randomList


if __name__ == "__main__":
    #The main loop
    while True:
        #Check for new mesasages
        #new_messages = t.twitch_recieve_messages();


        # Do a move every x seconds for y minutes
        secondsBetweenMoves = 2
        minutesUntilUpdate = 3
        start = datetime.datetime.now()
        while True:
            quakeToUse = random.choice(randomList)

            time.sleep(secondsBetweenMoves)

            now = datetime.datetime.now()
            timePassed = (now - start).seconds
            if timePassed > minutesUntilUpdate * 60:
                break


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