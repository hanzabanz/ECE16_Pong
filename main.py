__author__ = ''
"""
Adapted from: http://trevorappleton.blogspot.com/2014/04/writing-pong-using-python-and-pygame.html

For added difficulty: Change the SPEEDMULTIPLIER to have faster effects (affects ball speed, not frame rate or otherwise)
- Tests latency of project
For accuracy of control: Change INPUTRANGE ranges from -value to +value. Uses these values to map the position of a paddle.


** Input by position, not velocity

Y position:
15 = LINETHICKNESS + (BALLTHICKNESS/2)
16
...
585
"""

import sys
import pygame
from random import randint
from pygame.locals import *
import pika
import time

# Number of frames per second
# Change this value to speed up or slow down your game
FPS = 200

#Global Variables to be used through our program

TEAM1_NAME = 'Team 1'
TEAM2_NAME = 'Team 2'

WINDOWWIDTH = 800
WINDOWHEIGHT = 600
LINETHICKNESS = 10
BALLTHICKNESS = 10
PADDLESIZE = 120
PADDLEOFFSET = 20
SPEEDMULTIPLIER = 2

INPUTRANGE = 5

POSBOUNDARY = LINETHICKNESS + (BALLTHICKNESS/2)
WINDOWTOP = POSBOUNDARY
WINDOWBOTTOM = WINDOWHEIGHT - POSBOUNDARY
WINDOWBOTTOM = WINDOWHEIGHT - POSBOUNDARY
WINDOWSCALEOFFSET = (WINDOWBOTTOM-WINDOWTOP)/2
SCALE = (WINDOWBOTTOM-WINDOWTOP)/((2*INPUTRANGE))


# Set up the colours
BLACK     = (0  ,0  ,0  )
WHITE     = (255,255,255)

#Draws the arena the game will be played in.
def drawArena():
    DISPLAYSURF.fill((0,0,0))
    #Draw outline of arena
    pygame.draw.rect(DISPLAYSURF, WHITE, ((0,0),(WINDOWWIDTH,WINDOWHEIGHT)), LINETHICKNESS*2)
    #Draw centre line
    pygame.draw.line(DISPLAYSURF, WHITE, ((WINDOWWIDTH/2),0),((WINDOWWIDTH/2),WINDOWHEIGHT), (LINETHICKNESS/4))


#Draws the paddle
def drawPaddle(paddle):
    #Stops paddle moving too low
    if paddle.bottom > WINDOWHEIGHT - LINETHICKNESS:
        paddle.bottom = WINDOWHEIGHT - LINETHICKNESS
    #Stops paddle moving too high
    elif paddle.top < LINETHICKNESS:
        paddle.top = LINETHICKNESS
    #Draws paddle
    pygame.draw.rect(DISPLAYSURF, WHITE, paddle)


#draws the ball
def drawBall(ball):
    pygame.draw.rect(DISPLAYSURF, WHITE, ball)

#moves the ball returns new position
def moveBall(ball, ballDirX, ballDirY):
    ball.x += (ballDirX)*SPEEDMULTIPLIER
    ball.y += (ballDirY)*SPEEDMULTIPLIER
    return ball

#Checks for a collision with a wall, and 'bounces' ball off it.
#Returns new direction
def checkEdgeCollision(ball, ballDirX, ballDirY):
    if ball.top <= (LINETHICKNESS) or ball.bottom >= (WINDOWHEIGHT - LINETHICKNESS):
        ballDirY = ballDirY * -1
    if ball.left <= (LINETHICKNESS) or ball.right >= (WINDOWWIDTH - LINETHICKNESS):
        ballDirX = ballDirX * -1
    return ballDirX, ballDirY

#Checks is the ball has hit a paddle, and 'bounces' ball off it.
def checkHitBall(ball, paddle1, paddle2, ballDirX):
    if ballDirX == -1 and paddle1.right >= ball.left and paddle1.top < (ball.top + (ball.height/2)) and paddle1.bottom > (ball.bottom - (ball.height/2)):
        return -1
    elif ballDirX == 1 and paddle2.left <= ball.right and paddle2.top < (ball.top + (ball.height/2)) and paddle2.bottom > (ball.bottom - (ball.height/2)):
        return -1
    else: return 1


#Checks to see if a point has been scored returns new score
def checkPointScored(paddle1, paddle2, ball, scoreOne, scoreTwo, ballDirX):
    #reset points if left wall is hit
    if ball.left <= LINETHICKNESS:
        scoreOne = 0
    #1 point for hitting the ball
    elif ballDirX == -1 and paddle1.right >= ball.left and paddle1.top < (ball.top + (ball.height/2)) and paddle1.bottom > (ball.bottom - (ball.height/2)):
        scoreOne += 1
    #5 points for beating the other paddle
    elif ball.right >= WINDOWWIDTH - LINETHICKNESS:
        scoreOne += 5

    if ball.right >= WINDOWWIDTH - LINETHICKNESS:
        scoreTwo = 0
    #1 point for hitting the ball
    elif ballDirX == 1 and paddle2.left <= ball.right and paddle2.top < (ball.top + (ball.height/2)) and paddle2.bottom > (ball.bottom - (ball.height/2)):
        scoreTwo += 1
    #5 points for beating the other paddle
    elif ball.left <= LINETHICKNESS:
        scoreTwo += 5

    return (scoreOne, scoreTwo)


#Artificial Intelligence of computer player
def artificialIntelligence(ball, ballDirX, paddle2):
    #If ball is moving away from paddle, center bat
    if ballDirX == -1:
        if paddle2.centery < (WINDOWHEIGHT/2):
            paddle2.y += 1
        elif paddle2.centery > (WINDOWHEIGHT/2):
            paddle2.y -= 1
    #if ball moving towards bat, track its movement.
    elif ballDirX == 1:
        if paddle2.centery < ball.centery:
            paddle2.y += 1
        else:
            paddle2.y -=1
    return paddle2


def updatePaddle(paddle, input):
    if input > WINDOWBOTTOM:
        paddle.centery = WINDOWBOTTOM
        return
    elif input < WINDOWTOP:
        paddle.centery = WINDOWTOP
        return
    # scaledInput = float((input*SCALE) + WINDOWSCALEOFFSET)
    # print "%f\t%f\t%f" %(input, input*SCALE, scaledInput)

    # if paddle.centery < input-1: # paddle higher than desired position
    #     paddle.y += SPEEDMULTIPLIER # move paddle down
    # elif input+1 < paddle.centery:
    #     paddle.y -= SPEEDMULTIPLIER # move paddle up
    paddle.centery = input

#Displays the current score on the screen
def displayScore(score_left, score_right):
    resultSurf = BASICFONT.render('%s                                %s' %(score_left, score_right), True, WHITE)
    resultRect = resultSurf.get_rect()
    resultRect.centerx = WINDOWWIDTH/2
    resultRect.centery = WINDOWHEIGHT/5
    DISPLAYSURF.blit(resultSurf, resultRect)


#Team names are input manually on the very top!
def displayTeamNames():
    resultSurf = BASICFONT.render('%s                   %s' %(TEAM1_NAME, TEAM2_NAME), True, WHITE)
    resultRect = resultSurf.get_rect()
    resultRect.centerx = WINDOWWIDTH/2
    resultRect.centery = WINDOWHEIGHT/6
    DISPLAYSURF.blit(resultSurf, resultRect)

def locationMap():
    halfRange = float(((WINDOWBOTTOM-WINDOWTOP)/2) + WINDOWTOP)
    scale = float((halfRange-WINDOWTOP-(PADDLESIZE/2))/(INPUTRANGE))
    adjustedBottom = WINDOWBOTTOM+(PADDLESIZE/2)
    map = []
    map.append(WINDOWTOP + (PADDLESIZE/2))
    for i in range(INPUTRANGE-1):
        # map.append(scale + WINDOWTOP + i*scale - (PADDLESIZE/2))
        map.append(map[i]+scale)
    map.append(halfRange)
    for i in range(INPUTRANGE-1):
        # map.append((PADDLESIZE/2) + scale + WINDOWTOP + (i+INPUTRANGE)*scale)
        map.append(map[INPUTRANGE+i]+scale)
    map.append(WINDOWBOTTOM - (PADDLESIZE/2))

    map = list(reversed(map))

    # print map
    return map


#Main function
def main():
    map = locationMap()

    pygame.init()
    global DISPLAYSURF
    ##Font information
    global BASICFONT, BASICFONTSIZE
    BASICFONTSIZE = 20
    BASICFONT = pygame.font.Font('freesansbold.ttf', BASICFONTSIZE)

    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH,WINDOWHEIGHT))
    pygame.display.set_caption('Pong')

    #Initiate variable and set starting positions
    #any future changes made within rectangles
    ballX = WINDOWWIDTH/2 - BALLTHICKNESS/2
    ballY = WINDOWHEIGHT/2 - BALLTHICKNESS/2
    playerOnePosition = (WINDOWHEIGHT - PADDLESIZE) /2
    playerTwoPosition = (WINDOWHEIGHT - PADDLESIZE) /2
    scoreOne = 0
    scoreTwo = 0

    newPosOne = True
    newPosTwo = True

    #Keeps track of ball direction
    ballDirX = -1 ## -1 = left 1 = right
    ballDirY = -1 ## -1 = up 1 = down

    #Creates Rectangles for ball and paddles.
    paddle1 = pygame.Rect(PADDLEOFFSET,playerOnePosition, LINETHICKNESS,PADDLESIZE)
    paddle2 = pygame.Rect(WINDOWWIDTH - PADDLEOFFSET - LINETHICKNESS, playerTwoPosition, LINETHICKNESS,PADDLESIZE)
    ball = pygame.Rect(ballX, ballY, BALLTHICKNESS, BALLTHICKNESS)

    #Draws the starting position of the Arena
    drawArena()
    drawPaddle(paddle1)
    drawPaddle(paddle2)
    drawBall(ball)

    pygame.mouse.set_visible(0) # make cursor invisible

    # create message queue connection
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    global channel
    channel = connection.channel()

    # create player input queues
    channel.queue_declare(queue='player1')
    channel.queue_declare(queue='player2')

    rand_counter = 0

    # RANDOM INPUTS
    global inputOne
    inputOne = 0.0
    global inputTwo
    inputTwo = 0.0

    prev_time = time.time()

    while True: #main game loop
        # Following code used to get the timing of the loop:
        # print time.time() - prev_time
        # prev_time = time.time()

        for event in pygame.event.get():
            if event.type == pygame.locals.QUIT:
                pygame.quit()
                sys.exit()

        drawArena()
        drawPaddle(paddle1)
        drawPaddle(paddle2)
        drawBall(ball)

        ball = moveBall(ball, ballDirX, ballDirY)
        print ball
        ballDirX, ballDirY = checkEdgeCollision(ball, ballDirX, ballDirY)

        # RANDOM INPUTS, used for randomizing input, when there is no scripts feeding inputs
        # if rand_counter == 100:
        #     inputOne = float(randint(-10, 10))/10
        #     inputTwo = float(randint(-10, 10))/10
        #     rand_counter = 0
        # rand_counter += 1

        channel.start_consuming()
        method_frame, header_frame, body = channel.basic_get(queue = 'player1')
        if method_frame == None or method_frame.NAME == 'Basic.GetEmpty':
            channel.stop_consuming()
        else:
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            channel.stop_consuming()
            inputOne = float(body)
            print "%s\t%s" %(inputOne, str(time.time()))
            # print inputOne

        method_frame, header_frame, body = channel.basic_get(queue = 'player2')
        if method_frame == None or method_frame.NAME == 'Basic.GetEmpty':
            channel.stop_consuming()
        else:
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            channel.stop_consuming()
            inputTwo = float(body)


        realInputOne = map[int(inputOne)+INPUTRANGE]
        updatePaddle(paddle1, realInputOne)
        realInputTwo = map[int(inputTwo)+INPUTRANGE]
        updatePaddle(paddle2, realInputTwo)

        scoreOne, scoreTwo = checkPointScored(paddle1, paddle2, ball, scoreOne, scoreTwo, ballDirX)
        ballDirX = ballDirX * checkHitBall(ball, paddle1, paddle2, ballDirX)
        # paddle2 = artificialIntelligence(ball, ballDirX, paddle2)

        displayScore(scoreOne, scoreTwo)
        displayTeamNames()

        pygame.display.update()
        FPSCLOCK.tick(FPS)

if __name__=='__main__':
    main()