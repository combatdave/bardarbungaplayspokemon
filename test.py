import pygame
import sys
from quakes import EarthquakeStore, bearing
import quakes
import datetime
import random
import math
import win32api, win32con

import twitch
import keypresser
import keyholder

t = twitch.Twitch();
k = keypresser.Keypresser();


leftpx = 400
toppx = 0
rightpx = leftpx + 400
bottompx = toppx + 457

leftdeg = -18.5
rightdeg = -15
topdeg = 65.5
bottomdeg = 63.8

depthtop = 12
depthbot = 290

maxdepth = 15
mindepth = 0

quakeStore = EarthquakeStore()


def LatLongToPixels(lon, lat):
	midlat = lat - bottomdeg

	latscale = topdeg - bottomdeg
	lerplat = midlat / latscale

	y = bottompx + ((toppx - bottompx) * lerplat)

	midlon = lon - rightdeg

	lonscale = leftdeg - rightdeg
	lerplon = midlon / lonscale

	x = rightpx + ((leftpx - rightpx) * lerplon)

	return int(x), int(y)


def DepthToPixels(depth):
	if depth < mindepth:
		depth = mindepth
	if depth > maxdepth:
		depth = maxdepth
	depth = float(depth)

	middepth = depth - mindepth
	depthscale = maxdepth - mindepth

	y = depthtop + ((depthbot - depthtop) * (middepth / depthscale))

	return int(y)


pygame.init()

size = width, height = rightpx, bottompx
screen = pygame.display.set_mode(size)

mapimg = pygame.image.load("mapcropped.png")
depthbar = pygame.image.load("depth.png")
depthbar.convert_alpha()
flagimg = pygame.image.load("flag.png")
flagimg.convert_alpha()

aButtonDepthThreshold = 2
bButtonDepthThreshold = 12.5
controls = {"up":"w", "down":"s", "left":"a", "right":"d", "a":"z", "b":"x", "select":"c", "start":"v"}


def DrawQuake(surface, quake, color, size=None):
	if size is None:
		size = int(1 + (math.pow(quake.size, 1.3) * 2))
	pygame.draw.circle(surface, color, LatLongToPixels(quake.long, quake.lat), size)


def DoMove(now, quake, lastQuake):
	if quake.depth < aButtonDepthThreshold:
		moveDir = "a"
		print now.strftime('%H:%M:%S'), "Depth:", quake.depth, "km, button:", moveDir
	elif quake.depth > bButtonDepthThreshold:
		moveDir = "b"
		print now.strftime('%H:%M:%S'), "Depth:", quake.depth, "km, button:", moveDir
	else:
		angleFromCenter = bearing((lastQuake.lat, lastQuake.long), (quake.lat, quake.long))

		moveDir = None
		if angleFromCenter > 45 and angleFromCenter <= 135:
			moveDir = "right"
		elif angleFromCenter > 135 and angleFromCenter <= 225:
			moveDir = "down"
		elif angleFromCenter > 225 and angleFromCenter <= 315:
			moveDir = "left"
		else:
			moveDir = "up"
		print now.strftime('%H:%M:%S'), "Heading from last position:", int(angleFromCenter), "button:", moveDir

	
	keyToPress = controls[moveDir]
	keyholder.holdForSeconds(keyToPress, 0.2)


keysToRelease = []


def PressKey(key):
	win32api.keybd_event(keyholder.VK_CODE[key], 0, 0, 0)
	keysToRelease.append(HeldKey(key, datetime.datetime.now() + datetime.timedelta(seconds=0.2)))


def ProcessKeysToRelease():
	now = datetime.datetime.now()
	for i, heldKey in enumerate(keysToRelease):
		if now > heldKey.releaseTime:
			win32api.keybd_event(keyholder.VK_CODE[heldKey.key], 0, win32con.KEYEVENTF_KEYUP, 0)
		else:
			break
	keysToRelease = keysToRelease[i:]


class HeldKey:
	def __init__(self, key, releaseTime):
		self.key = key
		self.releaseTime = releaseTime


def DoNewMove():
	# timeSinceLastButtonPressInSeconds = 1000000
	# if lastButtonPressTime is not None:
	# 	timeSinceLastButtonPress = now - lastButtonPressTime
	# 	timeSinceLastButtonPressInSeconds = timeSinceLastButtonPress.seconds + (timeSinceLastButtonPress.microseconds / 1000000.0)

	# if currentQuake is not None and timeSinceLastButtonPressInSeconds > 2.0:
	if True:
		quakePixels = pygame.mouse.get_pos() #LatLongToPixels(currentQuake.long, currentQuake.lat)

		DrawArrowPixels(centerPixelPos, quakePixels, pygame.Color("black"), 2)

		quakeXDist = quakePixels[0] - centerPixelPos[0]
		quakeYDist = quakePixels[1] - centerPixelPos[1]
		distanceToQuakeInPixels = math.sqrt(quakeXDist ** 2 + quakeYDist ** 2)

		buttonToPress = None

		if distanceToQuakeInPixels > doDirectionRadiusInPixels:
			if quakeYDist < 0:
				buttonToPress = "a"
			else:
				buttonToPress = "b"
		else:
			angleToQuake = math.atan2(-quakeYDist, quakeXDist) % (2 * math.pi)
			angleToQuake = math.degrees(angleToQuake)

			roundedAngle = ((angleToQuake - 45) / 90) % 4
			angleID = math.floor(roundedAngle)
			angleID2 = angleID

			remainder = roundedAngle - angleID
			if remainder < 0.5:
				angleID2 = angleID - 1
			else:
				angleID2 = angleID + 1

			angleID = int(angleID) % 4
			angleID2 = int(angleID2) % 4

			directionsByAngleID = ["north", "west", "south", "east"]

			closenessToStraight = 1.0 - math.fabs((roundedAngle % 1) - 0.5)

			firstChoice = directionsByAngleID[angleID]
			secondChoice = directionsByAngleID[angleID2]
			choices = []
			choices += [firstChoice] * int(closenessToStraight * 10)
			choices += [secondChoice] * int((1 - closenessToStraight) * 10)

			directionToGo = random.choice(choices)

			directionsToButtonName = {"north":"up", "west":"left", "south":"down", "east":"right"}

			buttonToPress = directionsToButtonName[directionToGo]

		if buttonToPress is not None:
			keyToPress = controls[buttonToPress]
			PressKey(keyToPress)


def DrawArrow(fromQuake, toQuake, color):
	fromPixels = LatLongToPixels(fromQuake.long, fromQuake.lat)
	toPixels = LatLongToPixels(toQuake.long, toQuake.lat)

	DrawArrowPixels(fromPixels, toPixels, color)


def DrawArrowPixels(fromPixels, toPixels, color, width=1):
	dx = fromPixels[0] - toPixels[0]
	dy = fromPixels[1] - toPixels[1]

	rads = math.atan2(-dy, dx)
	degs = math.degrees(rads)

	arrowLength = 5

	pygame.draw.line(transparentSurface, color, fromPixels, toPixels, width)

	leftDegs = degs + 45
	leftX = toPixels[0] + (math.sin(math.radians(leftDegs)) * arrowLength)
	leftY = toPixels[1] + (math.cos(math.radians(leftDegs)) * arrowLength)
	pygame.draw.line(transparentSurface, color, toPixels, (leftX, leftY), width)

	rightDegs = degs + 135
	rightX = toPixels[0] + (math.sin(math.radians(rightDegs)) * arrowLength)
	rightY = toPixels[1] + (math.cos(math.radians(rightDegs)) * arrowLength)
	pygame.draw.line(transparentSurface, color, toPixels, (rightX, rightY), width)


def LerpColor(color1, color2, lerp):
	red1, green1, blue1 = color1
	red2, green2, blue2 = color2
	red = red1+(red2-red1) * lerp
	green = green1+(green2-green1) * lerp
	blue = blue1+(blue2-blue1) * lerp
	lerpedColor = pygame.Color(int(red), int(green), int(blue))
	return lerpedColor


def TimeAgoToColor(positionInPeriod):
	color1 = (0, 0, 255)
	color2 = (255, 0, 0)

	return LerpColor(color1, color2, positionInPeriod)


transparentSurface = pygame.Surface(size, pygame.SRCALPHA)
#transparentSurface = transparentSurface.convert()
transparentSurface2 = pygame.Surface(size, pygame.SRCALPHA)
#transparentSurface2 = transparentSurface2.convert()


def TimeInDurationToMapPos(timeInDuration):
	return quakeGraphLeft + ((quakeGraphRight - quakeGraphLeft) * timeInDuration)


def DrawQuakeOnMagnitudeGraph(quake, timeInDuration, active=False):
	alpha = 128 if not active else 255
	graphPos = TimeInDurationToMapPos(timeInDuration)

	lowMagnitudePos = height - 20
	highMagnitudePos = height - 200
	lowMagnitudeNum = 0
	highMagnitudeNum = 5

	magnitudeLerp = (quake.size - lowMagnitudeNum) / (highMagnitudeNum - lowMagnitudeNum)
	magnitudeLerp = max(min(magnitudeLerp, 1.0), 0.0)
	magnitudePos = lowMagnitudePos + (magnitudeLerp * (highMagnitudePos - lowMagnitudePos))

	pygame.draw.line(transparentSurface, (0, 0, 0, alpha), (int(graphPos), int(magnitudePos)), (int(graphPos), lowMagnitudePos), 3)
	pygame.draw.circle(transparentSurface, (0, 0, 0, alpha), (int(graphPos), int(magnitudePos)), 7)

	circleColor = TimeAgoToColor(timeInDuration)
	circleColor.a = alpha
	pygame.draw.circle(transparentSurface, circleColor, (int(graphPos), int(magnitudePos)), 5)


def DrawQuakeOnMap(quake, timeInDuration, active=False):
	alpha = 100 if not active else 255
	circleColor = TimeAgoToColor(timeInDuration)
	circleColor.a = alpha
	DrawQuake(transparentSurface, quake, (0, 0, 0, alpha), 7)
	DrawQuake(transparentSurface, quake, circleColor, 5)


clock = pygame.time.Clock()
FPS = 20

periodTimeInSeconds = 60 * 60 * quakes.hoursOfData
timeForFullPeriodInSeconds = 60 * 60

currentQuake = None
prevQuake = None
startEvalTime = datetime.datetime.now()

lastTimeIndex = None
leftTime = None
rightTime = None

quakeStore.LoadData()

doDirectionRadiusInPixels = 60
lastButtonPressTime = None

while 1:
	milliseconds = clock.tick(FPS)

	for event in pygame.event.get():
		if event.type == pygame.QUIT: sys.exit()

	screen.fill(pygame.Color("#A5D6FF"))
	transparentSurface.fill((0, 0, 0, 0))

	screen.blit(mapimg, (leftpx, toppx))

	centerLat = quakeStore.centerPoint[0]
	centerLong = quakeStore.centerPoint[1]
	centerPixelPos = LatLongToPixels(centerLong, centerLat)
	
	for quakeTime in quakeStore.sortedKeys:
		quake = quakeStore.earthquakesByDate[quakeTime]

		timeSinceQuake = quakeStore.latestQuakeTime - quake.date

		quakeGraphLeft = 50
		quakeGraphRight = width - 50
		
		timeInDuration = 1.0 - (timeSinceQuake.seconds / float(periodTimeInSeconds))

		if timeInDuration < 0:
			continue

		DrawQuakeOnMagnitudeGraph(quake, timeInDuration)
		DrawQuakeOnMap(quake, timeInDuration)


	if leftTime is not None:
		currentQuake = quakeStore.earthquakesByDate[leftTime]
	else:
		currentQuake = None

	if currentQuake is not None:
		timeSinceQuake = quakeStore.latestQuakeTime - currentQuake.date

		quakeGraphLeft = 50
		quakeGraphRight = width - 50
		
		timeInDuration = 1.0 - (timeSinceQuake.seconds / float(periodTimeInSeconds))

		if timeInDuration >= 0:
			DrawQuakeOnMagnitudeGraph(currentQuake, timeInDuration, True)
			DrawQuakeOnMap(currentQuake, timeInDuration, True)

			DrawArrowPixels(centerPixelPos, LatLongToPixels(currentQuake.long, currentQuake.lat), pygame.Color("#FF00DC"), 3)


	flagDrawPos = (centerPixelPos[0] - 1, centerPixelPos[1] - flagimg.get_height())
	transparentSurface.blit(flagimg, flagDrawPos)

	now = datetime.datetime.now()
	timePassed = now - startEvalTime
	timePassedInSeconds = timePassed.seconds + (timePassed.microseconds / 1000000.0)
	currentEvalPos = timePassedInSeconds / float(timeForFullPeriodInSeconds)
	oldestPossibleQuake = quakeStore.latestQuakeTime - datetime.timedelta(seconds=periodTimeInSeconds)
	currentEvalTime = oldestPossibleQuake + datetime.timedelta(seconds=currentEvalPos * periodTimeInSeconds)

	if lastTimeIndex is None:
		lastTimeIndex = 1
		rightTime = quakeStore.sortedKeys[lastTimeIndex]
		while quakes.UnixToDatetime(rightTime) < currentEvalTime:
			lastTimeIndex += 1
			if lastTimeIndex < len(quakeStore.sortedKeys):
				rightTime = quakeStore.sortedKeys[lastTimeIndex]
			else:
				break
	else:
		currentRightTime = quakeStore.sortedKeys[lastTimeIndex]
		if quakes.UnixToDatetime(currentRightTime) < currentEvalTime:
			lastTimeIndex += 1

	if lastTimeIndex < len(quakeStore.sortedKeys) and currentEvalPos <= 1:
		leftIndex = max(0, lastTimeIndex-1)
		leftTime = quakeStore.sortedKeys[leftIndex]
		rightTime = quakeStore.sortedKeys[lastTimeIndex ]
	else:
		leftTime = None
		rightTime = None
		lastTimeIndex = None
		startEvalTime = now
		quakeStore.LoadData()


	pygame.draw.circle(transparentSurface, pygame.Color(0, 0, 0, 128), centerPixelPos, doDirectionRadiusInPixels, 3)
	pygame.draw.line(transparentSurface, pygame.Color(0, 0, 0, 128), (centerPixelPos[0]+doDirectionRadiusInPixels, centerPixelPos[1]), (width, centerPixelPos[1]), 3)
	pygame.draw.line(transparentSurface, pygame.Color(0, 0, 0, 128), (centerPixelPos[0]-doDirectionRadiusInPixels, centerPixelPos[1]), (leftpx, centerPixelPos[1]), 3)


	DoNewMove()


	triTipX = TimeInDurationToMapPos(currentEvalPos)
	triTipY = height - 20
	pygame.draw.polygon(screen, pygame.Color("black"), [[triTipX-5, triTipY+10], [triTipX, triTipY], [triTipX+5, triTipY+10]])

	screen.blit(transparentSurface, (0, 0))

	text = "Bardarbunga Plays Pokemon - FPS: {0:.2f}".format(clock.get_fps())
	pygame.display.set_caption(text)

	pygame.display.flip()

	ProcessKeysToRelease
