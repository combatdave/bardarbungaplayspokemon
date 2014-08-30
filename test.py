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
dpadimg = pygame.image.load("dpad.png")
dpadimg.convert_alpha()
dpadupimg = pygame.image.load("dpadup.png")
dpadupimg.convert_alpha()
dpadrightimg = pygame.image.load("dpadright.png")
dpadrightimg.convert_alpha()
dpaddownimg = pygame.image.load("dpaddown.png")
dpaddownimg.convert_alpha()
dpadleftimg = pygame.image.load("dpadleft.png")
dpadleftimg.convert_alpha()
abuttonimg = pygame.image.load("abutton.png")
abuttonimg.convert_alpha()
bbuttonimg = pygame.image.load("bbutton.png")
bbuttonimg.convert_alpha()
abuttonselectedimg = pygame.image.load("abuttonselected.png")
abuttonselectedimg.convert_alpha()
bbuttonselectedimg = pygame.image.load("bbuttonselected.png")
bbuttonselectedimg.convert_alpha()


aButtonDepthThreshold = 2
bButtonDepthThreshold = 12.5
controls = {"up":"w", "down":"s", "left":"a", "right":"d", "a":"z", "b":"x", "select":"c", "start":"v"}

quakeGraphLeft = 50
quakeGraphRight = width - 50


def DrawQuake(surface, quake, color, size=None):
	if size is None:
		size = int(1 + (math.pow(quake.size, 1.3) * 2))
	pygame.draw.circle(surface, color, LatLongToPixels(quake.long, quake.lat), size)


heldKeys = []


def PressKey(key, holdTimeInSeconds=0.2):
	win32api.keybd_event(keyholder.VK_CODE[key], 0, 0, 0)
	heldKeys.append(HeldKey(key, datetime.datetime.now() + datetime.timedelta(seconds=holdTimeInSeconds)))


def ProcessKeysToRelease(keysToRelease):
	now = datetime.datetime.now()
	releasedIndex = 0
	for i, heldKey in enumerate(keysToRelease):
		if now > heldKey.releaseTime:
			releasedIndex = i+1
			win32api.keybd_event(keyholder.VK_CODE[heldKey.key], 0, win32con.KEYEVENTF_KEYUP, 0)
		else:
			break

	return keysToRelease[releasedIndex:]


class HeldKey:
	def __init__(self, key, releaseTime):
		self.key = key
		self.releaseTime = releaseTime

lastButtonPressed = None

def DoNewMove():
	now = datetime.datetime.now()
	timeSinceLastButtonPressInSeconds = 1000000
	global lastButtonPressTime
	global sendKeyPresses
	global lastButtonPressed

	if lastButtonPressTime is not None:
		timeSinceLastButtonPress = now - lastButtonPressTime
		timeSinceLastButtonPressInSeconds = timeSinceLastButtonPress.seconds + (timeSinceLastButtonPress.microseconds / 1000000.0)

	if currentQuake is not None and timeSinceLastButtonPressInSeconds > 2.0:
		quakePixels = LatLongToPixels(currentQuake.long, currentQuake.lat)

		quakeXDist = quakePixels[0] - centerPixelPos[0]
		quakeYDist = quakePixels[1] - centerPixelPos[1]
		distanceToQuakeInPixels = math.sqrt(quakeXDist ** 2 + quakeYDist ** 2)

		buttonToPress = None

		humanText = ""

		if distanceToQuakeInPixels > doDirectionRadiusInPixels:
			if quakeYDist < 0:
				humanText = "Too far away (North)"
				buttonToPress = "a"
			else:
				humanText = "Too far away (South)"
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

			directionsByAngleID = ["North", "West", "South", "East"]

			closenessToStraight = 1.0 - math.fabs((roundedAngle % 1) - 0.5)

			firstChoice = directionsByAngleID[angleID]
			secondChoice = directionsByAngleID[angleID2]
			choices = []
			choices += [firstChoice] * int(closenessToStraight * 10)
			choices += [secondChoice] * int((1 - closenessToStraight) * 10)

			directionToGo = random.choice(choices)

			directionsToButtonName = {"North":"up", "West":"left", "South":"down", "East":"right"}

			buttonToPress = directionsToButtonName[directionToGo]

			humanText = "Direction from last quake: "
			if angleID == angleID2:
				humanText += directionsByAngleID[angleID]
			elif angleID % 2 == 0:
				humanText += directionsByAngleID[angleID] + "-" + directionsByAngleID[angleID2]
			else:
				humanText += directionsByAngleID[angleID2] + "-" + directionsByAngleID[angleID]

		if buttonToPress is not None:
			lastButtonPressed = buttonToPress
			keyToPress = controls[buttonToPress]
			if sendKeyPresses:
				print now.strftime('%H:%M:%S'), humanText, "- Pressing", buttonToPress
				DrawArrowPixels(centerPixelPos, quakePixels, pygame.Color("black"), 3)
				PressKey(keyToPress)
			else:
				print now.strftime('%H:%M:%S'), humanText, "- Pressing", buttonToPress, "(sendKeyPresses = False)"
			lastButtonPressTime = now
			

def DrawArrow(fromQuake, toQuake, color):
	fromPixels = LatLongToPixels(fromQuake.long, fromQuake.lat)
	toPixels = LatLongToPixels(toQuake.long, toQuake.lat)

	DrawArrowPixels(fromPixels, toPixels, color)


def DrawArrowPixels(fromPixels, toPixels, color, width=1):
	dx = fromPixels[0] - toPixels[0]
	dy = fromPixels[1] - toPixels[1]

	rads = math.atan2(-dy, dx)
	degs = math.degrees(rads)

	arrowLength = 10

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

	positionInPeriod = min(max(positionInPeriod, 0.0), 1.0)

	return LerpColor(color1, color2, positionInPeriod)


transparentSurface = pygame.Surface(size, pygame.SRCALPHA)
#transparentSurface = transparentSurface.convert()
transparentSurface2 = pygame.Surface(size, pygame.SRCALPHA)
#transparentSurface2 = transparentSurface2.convert()

staticQuakeSurface = pygame.Surface(size, pygame.SRCALPHA)


def TimeInDurationToMapPos(timeInDuration):
	return quakeGraphLeft + ((quakeGraphRight - quakeGraphLeft) * timeInDuration)


def DrawQuakeOnMagnitudeGraph(surface, quake, timeInDuration, active=False):
	alpha = 128 if not active else 255
	graphPos = TimeInDurationToMapPos(timeInDuration)

	lowMagnitudePos = height - 20
	highMagnitudePos = height - 200
	lowMagnitudeNum = 0
	highMagnitudeNum = 5

	magnitudeLerp = (quake.size - lowMagnitudeNum) / (highMagnitudeNum - lowMagnitudeNum)
	magnitudeLerp = max(min(magnitudeLerp, 1.0), 0.0)
	magnitudePos = lowMagnitudePos + (magnitudeLerp * (highMagnitudePos - lowMagnitudePos))

	pygame.draw.line(surface, (0, 0, 0, alpha), (int(graphPos), int(magnitudePos)), (int(graphPos), lowMagnitudePos), 3)
	pygame.draw.circle(surface, (0, 0, 0, alpha), (int(graphPos), int(magnitudePos)), 7)

	circleColor = TimeAgoToColor(timeInDuration)
	circleColor.a = alpha
	pygame.draw.circle(surface, circleColor, (int(graphPos), int(magnitudePos)), 5)


def DrawQuakeOnMap(surface, quake, timeInDuration, active=False):
	alpha = 100 if not active else 255
	circleColor = TimeAgoToColor(timeInDuration)
	circleColor.a = alpha
	DrawQuake(surface, quake, (0, 0, 0, alpha), 7)
	DrawQuake(surface, quake, circleColor, 5)


def DrawButtons():
	global lastButtonPressed

	dpadImgToUse = dpadimg
	abuttonImgToUse = abuttonimg
	bbuttonImgToUse = bbuttonimg

	if lastButtonPressed == "up":
		dpadImgToUse = dpadupimg
	elif lastButtonPressed == "right":
		dpadImgToUse = dpadrightimg
	elif lastButtonPressed == "down":
		dpadImgToUse = dpaddownimg
	elif lastButtonPressed == "left":
		dpadImgToUse = dpadleftimg
	elif lastButtonPressed == "a":
		abuttonImgToUse = abuttonselectedimg
	elif lastButtonPressed == "b":
		bbuttonImgToUse = bbuttonselectedimg

	screen.blit(abuttonImgToUse, (centerPixelPos[0] - abuttonimg.get_width() / 2, centerPixelPos[1] - doDirectionRadiusInPixels - 40 - abuttonimg.get_height() / 2))
	screen.blit(bbuttonImgToUse, (centerPixelPos[0] - bbuttonimg.get_width() / 2, centerPixelPos[1] + doDirectionRadiusInPixels + 40 - bbuttonimg.get_height() / 2))
	screen.blit(dpadImgToUse, (centerPixelPos[0] - dpadimg.get_width() / 2, centerPixelPos[1] - dpadimg.get_height() / 2))


clock = pygame.time.Clock()
FPS = 10

periodTimeInSeconds = 60 * 60 * quakes.hoursOfData
timeForFullPeriodInSeconds = 60 * 5

currentQuake = None
prevQuake = None
startEvalTime = datetime.datetime.now()

lastTimeIndex = None

doDirectionRadiusInPixels = 60
lastButtonPressTime = None


def LoadFreshData():
	# Render all to staticQuakeSurface
	now = datetime.datetime.now()
	global startEvalTime
	global periodTimeInSeconds
	global lastTimeIndex
	global lastButtonPressed

	lastTimeIndex = None
	lastButtonPressed = None

	startEvalTime = now
	quakeStore.LoadData()
	staticQuakeSurface.fill((0,0,0,0))

	for quakeTime in quakeStore.sortedKeys:
		quake = quakeStore.earthquakesByDate[quakeTime]

		timeSinceQuake = quakeStore.latestQuakeTime - quake.date

		timeInDuration = 1.0 - (timeSinceQuake.seconds / float(periodTimeInSeconds))

		if timeInDuration < 0:
		 	continue

		DrawQuakeOnMagnitudeGraph(staticQuakeSurface, quake, timeInDuration)
		DrawQuakeOnMap(staticQuakeSurface, quake, timeInDuration)


LoadFreshData()


sendKeyPresses = False

font = pygame.font.Font(None, 20)


while 1:
	milliseconds = clock.tick(FPS)

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			sys.exit()
		elif event.type == pygame.MOUSEBUTTONDOWN:
			sendKeyPresses = not sendKeyPresses
			print "sendKeyPresses:", sendKeyPresses

	screen.fill(pygame.Color("#000000"))
	transparentSurface.fill((0, 0, 0, 0))

	pygame.draw.rect(screen, pygame.Color("#75C5FF"), (0, bottompx - 200, leftpx, 400))

	screen.blit(mapimg, (leftpx, toppx))
	screen.blit(staticQuakeSurface, (0, 0))

	if prevQuake is not None:
		centerPixelPos = LatLongToPixels(prevQuake.long, prevQuake.lat)
	else:
		centerLat = quakeStore.centerPoint[0]
		centerLong = quakeStore.centerPoint[1]
		centerPixelPos = LatLongToPixels(centerLong, centerLat)
	
	if currentQuake is not None:
		timeSinceQuake = quakeStore.latestQuakeTime - currentQuake.date

		quakeGraphLeft = 50
		quakeGraphRight = width - 50
		
		timeInDuration = 1.0 - (timeSinceQuake.seconds / float(periodTimeInSeconds))

		quakeSize = currentQuake.size
		quakeSize = min(max(quakeSize, 1.0), 6.0)
		sizeFraction = min(max(quakeSize / 6.0, 0.0), 1.0)
		minDirectionRadius = 30
		maxDirectionRadius = 70
		doDirectionRadiusInPixels = int(minDirectionRadius + ((maxDirectionRadius - minDirectionRadius) * sizeFraction))

		if timeInDuration >= 0:
			DrawQuakeOnMagnitudeGraph(transparentSurface, currentQuake, timeInDuration, True)
			DrawQuakeOnMap(transparentSurface, currentQuake, timeInDuration, True)
		else:
			currentQuake = None

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
		thisQuake = quakeStore.earthquakesByDate[leftTime]

		if thisQuake != currentQuake:
			prevQuake = currentQuake
			currentQuake = thisQuake
			lastButtonPressed = None
	else:
		LoadFreshData()


	pygame.draw.circle(transparentSurface, pygame.Color(0, 0, 0, 128), centerPixelPos, doDirectionRadiusInPixels, 3)
	pygame.draw.line(transparentSurface, pygame.Color(0, 0, 0, 128), (centerPixelPos[0]+doDirectionRadiusInPixels, centerPixelPos[1]), (width, centerPixelPos[1]), 3)
	pygame.draw.line(transparentSurface, pygame.Color(0, 0, 0, 128), (centerPixelPos[0]-doDirectionRadiusInPixels, centerPixelPos[1]), (leftpx, centerPixelPos[1]), 3)

	DoNewMove()

	triTipX = TimeInDurationToMapPos(currentEvalPos)
	triTipY = height - 20
	triColor = TimeAgoToColor(currentEvalPos)
	pygame.draw.polygon(screen, triColor, [[triTipX-5, triTipY+15], [triTipX, triTipY], [triTipX+5, triTipY+15]])

	DrawButtons()

	if currentQuake is not None:
		DrawArrowPixels(centerPixelPos, LatLongToPixels(currentQuake.long, currentQuake.lat), pygame.Color("#000000"), 3)

	screen.blit(transparentSurface, (0, 0))

	text = "Bardarbunga Plays Pokemon - FPS: {0:.2f}".format(clock.get_fps())
	pygame.display.set_caption(text)

	text = font.render("Data time: " + currentEvalTime.strftime("%Y-%m-%d %H:%M:%S"), 1, (255, 255, 255))
	screen.blit(text, (5, 280))
	if currentQuake is not None:
		text = font.render("Last quake: " + str(currentQuake), 1, (255, 255, 255))
		screen.blit(text, (5, 300))

	pygame.display.flip()

	heldKeys = ProcessKeysToRelease(heldKeys)