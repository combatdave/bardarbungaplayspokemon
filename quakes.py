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

def DatetimeToUnix(date):
    return str(int((date - datetime.datetime(1970, 1, 1)).total_seconds()))


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
    size = quakeData["size"]

    if lat < minLat or lat > maxLat:
        return False

    if long < minLong or long > maxLong:
        return False

    if size < 0.1:
        return False

    return True


hoursOfData = 24


class EarthquakeStore:
    def __init__(self):
        self.lastUpdate = None
        self.earthquakesByDate = None
        self.randomList = None
        self.centerPoint = None
        self.latestQuakeTime = None
        self.sortedKeys = None


    def CheckShouldUpdate(self):
        now = datetime.datetime.now()
        if self.lastUpdate is None or (now - self.lastUpdate).seconds / 60 > 5:
            self.LoadData()
            self.lastUpdate = now


    def LoadData(self):
        self.lastUpdate = datetime.datetime.now()

        print "Fetching data"

        url = "http://isapi.rasmuskr.dk/api/earthquakes/?date=" + str(hoursOfData) + "-hoursago"
        r = requests.get(url)
        earthquakes = r.json().get("items")
        self.earthquakesByDate = {}

        for quakeData in earthquakes:
            date = quakeData["date"]
            if IsRelevant(quakeData):
                q = Earthquake(quakeData)
                self.earthquakesByDate[date] = q

        times = self.earthquakesByDate.keys()
        times = sorted(times)
        self.sortedKeys = times

        self.latestQuakeTime = UnixToDatetime(times[-1])

        keysToUse = []
        for i in xrange(len(times)-1, -1, -1):
            thisTime = UnixToDatetime(times[i])
            oldness = self.latestQuakeTime - thisTime
            oldnessInMinutes = oldness.seconds / 60.0
            if oldnessInMinutes <= 2 * 60:
                keysToUse.append(times[i])
            else:
                break

        self.centerPoint = self._GetCenter()


    def GetQuakesByDate(self):
        self.CheckShouldUpdate()
        return self.earthquakesByDate


    def _GetCenter(self):
        centerPoint = None
        for quake in self.earthquakesByDate.itervalues():
            if centerPoint is None:
                centerPoint = (quake.lat, quake.long)
            else:
                centerPoint = (centerPoint[0] + quake.lat, centerPoint[1] + quake.long)

        centerPoint = (centerPoint[0] / len(self.earthquakesByDate), centerPoint[1] / len(self.earthquakesByDate))

        return centerPoint