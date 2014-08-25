import pygame
import sys
from quakes import EarthquakeStore, bearing
import datetime
import random
import math


import twitch
import keypresser

t = twitch.Twitch();
k = keypresser.Keypresser();



leftpx = 0
toppx = 0
rightpx = 400
bottompx = 457

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


secondsBetweenMoves = 2
minutesUntilUpdate = 3
lastMove = datetime.datetime.now()

moveQuake = None

aButtonDepthThreshold = 2
bButtonDepthThreshold = 12.5
controls = {"up":"w", "down":"w", "left":"a", "right":"d", "a":"z", "b":"x", "select":"c", "start":"v"}


def DrawQuake(quake, color):
	pygame.draw.circle(screen, color, LatLongToPixels(quake.long, quake.lat), int(1 + (math.pow(quake.size, 2.0) * 2)))


def DoMove(quake, center):
	if quake.depth < aButtonDepthThreshold:
		moveDir = "a"
	elif quake.depth > bButtonDepthThreshold:
		moveDir = "b"
	else:
		angleFromCenter = bearing(centerPoint, (quake.lat, quake.long))

		moveDir = None
		if angleFromCenter > 45 and angleFromCenter <= 135:
			moveDir = "right"
		elif angleFromCenter > 135 and angleFromCenter <= 225:
			moveDir = "down"
		elif angleFromCenter > 225 and angleFromCenter <= 315:
			moveDir = "left"
		else:
			moveDir = "up"

	print "Depth:", quake.depth, "km, button:" moveDir
	keyToPress = controls[moveDir]
	k.key_press(keyToPress)


while 1:
	for event in pygame.event.get():
		if event.type == pygame.QUIT: sys.exit()

	screen.blit(mapimg, (0, 0))

	recentQuakes = quakeStore.GetRandomList()
	for q in recentQuakes:
		DrawQuake(q, pygame.Color("orange"))

	if moveQuake is not None:
		DrawQuake(moveQuake, pygame.Color("red"))

	centerPoint = quakeStore.GetCenter()
	pygame.draw.circle(screen, pygame.Color("green"), LatLongToPixels(centerPoint[1], centerPoint[0]), 2)

	screen.blit(depthbar, (0, 0))

	if moveQuake is not None:
		y = DepthToPixels(moveQuake.depth)
		pygame.draw.rect(screen, pygame.Color("#75BEFF"), (18, y-3, 15, 6))


	now = datetime.datetime.now()
	timePassed = (now - lastMove).seconds
	if timePassed > secondsBetweenMoves:
		moveQuake = quakeStore.GetRandomQuake()

		DoMove(moveQuake, centerPoint)

		lastMove = now

	pygame.display.flip()