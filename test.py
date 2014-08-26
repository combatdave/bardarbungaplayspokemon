import pygame
import sys
from quakes import EarthquakeStore, bearing
import quakes
import datetime
import random
import math


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


def DrawArrow(fromQuake, toQuake, color):
	fromPixels = LatLongToPixels(fromQuake.long, fromQuake.lat)
	toPixels = LatLongToPixels(toQuake.long, toQuake.lat)

	DrawArrowPixels(fromPixels, toPixels, color)


def DrawArrowPixels(fromPixels, toPixels, color):
	dx = fromPixels[0] - toPixels[0]
	dy = fromPixels[1] - toPixels[1]

	rads = math.atan2(-dy, dx)
	degs = math.degrees(rads)

	arrowLength = 5

	pygame.draw.line(screen, color, fromPixels, toPixels)

	leftDegs = degs + 45
	leftX = toPixels[0] + (math.sin(math.radians(leftDegs)) * arrowLength)
	leftY = toPixels[1] + (math.cos(math.radians(leftDegs)) * arrowLength)
	pygame.draw.line(screen, color, toPixels, (leftX, leftY))

	rightDegs = degs + 135
	rightX = toPixels[0] + (math.sin(math.radians(rightDegs)) * arrowLength)
	rightY = toPixels[1] + (math.cos(math.radians(rightDegs)) * arrowLength)
	pygame.draw.line(screen, color, toPixels, (rightX, rightY))


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
timeForFullPeriodInSeconds = 5 #60

currentQuake = None
prevQuake = None
startEvalTime = datetime.datetime.now()

lastTimeIndex = None
leftTime = None
rightTime = None

while 1:
	milliseconds = clock.tick(FPS)

	for event in pygame.event.get():
		if event.type == pygame.QUIT: sys.exit()

	screen.fill(pygame.Color("#A5D6FF"))
	transparentSurface.fill((0, 0, 0, 0))

	screen.blit(mapimg, (leftpx, toppx))

	quakeStore.CheckShouldUpdate()
	
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
		quake = quakeStore.earthquakesByDate[leftTime]

		timeSinceQuake = quakeStore.latestQuakeTime - quake.date

		quakeGraphLeft = 50
		quakeGraphRight = width - 50
		
		timeInDuration = 1.0 - (timeSinceQuake.seconds / float(periodTimeInSeconds))

		if timeInDuration >= 0:
			DrawQuakeOnMagnitudeGraph(quake, timeInDuration, True)
			DrawQuakeOnMap(quake, timeInDuration, True)


	if rightTime is not None:
		quake = quakeStore.earthquakesByDate[rightTime]

		timeSinceQuake = quakeStore.latestQuakeTime - quake.date

		quakeGraphLeft = 50
		quakeGraphRight = width - 50
		
		timeInDuration = 1.0 - (timeSinceQuake.seconds / float(periodTimeInSeconds))

		if timeInDuration >= 0:
			DrawQuakeOnMagnitudeGraph(quake, timeInDuration, True)
			DrawQuakeOnMap(quake, timeInDuration, True)



	screen.blit(transparentSurface, (0, 0))

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

	if lastTimeIndex < len(quakeStore.sortedKeys):
		leftTime = quakeStore.sortedKeys[lastTimeIndex - 1]
		rightTime = quakeStore.sortedKeys[lastTimeIndex ]
	else:
		leftTime = None
		rightTime = None
		lastTimeIndex = None
		quakeStore.LoadData()


	triTipX = TimeInDurationToMapPos(currentEvalPos)
	triTipY = height - 20
	pygame.draw.polygon(screen, pygame.Color("black"), [[triTipX-5, triTipY+10], [triTipX, triTipY], [triTipX+5, triTipY+10]])


	# timePassed = (now - lastMove).seconds
	# if timePassed > secondsBetweenMoves:
	# 	lastQuake = moveQuake
	# 	moveQuake = quakeStore.GetRandomQuake()

	# 	DoMove(now, moveQuake, lastQuake)

	# 	lastMove = now

	text = "Bardarbunga Plays Pokemon - FPS: {0:.2f}".format(clock.get_fps())
	pygame.display.set_caption(text)

	pygame.display.flip()