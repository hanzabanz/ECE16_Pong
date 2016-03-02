import pygame
import socket
import select

"""
Adapted from: http://trevorappleton.blogspot.com/2014/04/writing-pong-using-python-and-pygame.html

ECE16 Final Project Pong Game - Student Version
"""


# Team-Specific Variables
TEAM1_NAME = 'Team 1'
TEAM2_NAME = 'Team 2'

# Match-Specific Variables
SPEEDMULTIPLIER = 1
PADDLESPEEDMULTIPLIER = 2 # adds this value to the multiplier, i.e. if 1, then max speed would be 1+1=2
BALLTHICKNESS = 20
PADDLESIZE = 240
COMPUTERDIFFICULTY = 1 # correlated with how fast the computer paddle moves; higher the faster

# Game-Specific Variables
INPUTRANGE = 20
FPS = 100

# Game Display Variables
WINDOWWIDTH = 1400
WINDOWHEIGHT = 900
LINETHICKNESS = 10
PADDLEOFFSET = 20

POSBOUNDARY = LINETHICKNESS + (BALLTHICKNESS/2)
WINDOWTOP = POSBOUNDARY
WINDOWBOTTOM = WINDOWHEIGHT - POSBOUNDARY
WINDOWBOTTOM = WINDOWHEIGHT - POSBOUNDARY
WINDOWSCALEOFFSET = (WINDOWBOTTOM-WINDOWTOP)/2
SCALE = (WINDOWBOTTOM-WINDOWTOP)/((2*INPUTRANGE))

BASICFONTSIZE = 20

BLACK     = (0  ,0  ,0  )
WHITE     = (255,255,255)

# Game Hosting Variables
UDP_IP = "127.0.0.1"
UDP_PORT = 5005

# Draws the arena the game will be played in
def drawArena():
    DISPLAYSURF.fill((0,0,0))
    #Draw outline of arena
    pygame.draw.rect(DISPLAYSURF, WHITE, ((0,0),(WINDOWWIDTH,WINDOWHEIGHT)), LINETHICKNESS*2)
    #Draw centre line
    pygame.draw.line(DISPLAYSURF, WHITE, ((WINDOWWIDTH/2),0),((WINDOWWIDTH/2),WINDOWHEIGHT), (LINETHICKNESS/4))


# Draws the paddle
def drawPaddle(paddle):
    #Stops paddle moving too low
    if paddle.bottom > WINDOWHEIGHT - LINETHICKNESS:
        paddle.bottom = WINDOWHEIGHT - LINETHICKNESS
    #Stops paddle moving too high
    elif paddle.top < LINETHICKNESS:
        paddle.top = LINETHICKNESS
    #Draws paddle
    pygame.draw.rect(DISPLAYSURF, WHITE, paddle)


# Draws the ball
def drawBall(ball):
    pygame.draw.rect(DISPLAYSURF, WHITE, ball)


# Moves the ball
# Returns new position
def moveBall(ball, ballDirX, ballDirY, paddleLoc):
    # convert relative paddle location to speed multiplier
    locAddition = (1.0-abs(paddleLoc))*PADDLESPEEDMULTIPLIER
    # adjust the speed based on the last paddle location
    ball.x += (ballDirX)*(SPEEDMULTIPLIER + locAddition)
    ball.y += (ballDirY)*(SPEEDMULTIPLIER + locAddition)
    return ball


# Checks for a collision with a wall, and 'bounces' ball off it
# Returns new direction
def checkEdgeCollision(ball, ballDirX, ballDirY, paddleLoc):
    if ball.top <= (LINETHICKNESS) or ball.bottom >= (WINDOWHEIGHT - LINETHICKNESS):
        ballDirY = ballDirY * -1
        while ball.top < (LINETHICKNESS) or ball.bottom > (WINDOWHEIGHT - LINETHICKNESS):
            # move slowly until it is out of the boundary so it doesn't keep switching directions
            # moveBall(ball, ballDirX, ballDirY, 1.0)
            ball.y += ballDirY
    if ball.left <= (LINETHICKNESS) or ball.right >= (WINDOWWIDTH - LINETHICKNESS):
        ballDirX = ballDirX * -1
        while ball.left < (LINETHICKNESS) or ball.right > (WINDOWWIDTH - LINETHICKNESS):
            # move slowly until it is out of the boundary so it doesn't keep switching directions
            # moveBall(ball, ballDirX, ballDirY, 1.0)
            ball.x += ballDirX
        paddleLoc = 1.0 # if hitting off edge, then reset to default speed
    return ballDirX, ballDirY, paddleLoc


# Checks if the ball has hit a paddle, scores, and 'bounces' ball off paddle
# Returns new scores, direction of ball, and relative location of paddle hit
def checkHitBall(ball, paddle1, paddle2, ballDirX, scoreOne, scoreTwo, paddleLoc):
    newDirX = 1*ballDirX
    # if either of these two conditions, then paddle has hit the ball
    if ball.left <= LINETHICKNESS:
        scoreOne -= 1
        paddleLoc = 1.0
    elif ballDirX == -1 and paddle1.right >= ball.left and paddle1.top < (ball.top + (ball.height/2)) and paddle1.bottom > (ball.bottom - (ball.height/2)):
        scoreOne += 1
        newDirX =  -1*ballDirX
        paddleLoc = calculateRelativeBallPaddleLoc(ball.centery, paddle1.top, paddle1.bottom, paddle1.centery)
    elif ball.right >= WINDOWWIDTH - LINETHICKNESS:
        scoreTwo -= 1
        paddleLoc = 1.0
    elif ballDirX == 1 and paddle2.left <= ball.right and paddle2.top < (ball.top + (ball.height/2)) and paddle2.bottom > (ball.bottom - (ball.height/2)):
        scoreTwo += 1
        newDirX =  -1*ballDirX
        paddleLoc = calculateRelativeBallPaddleLoc(ball.centery, paddle2.top, paddle2.bottom, paddle2.centery)
    return (scoreOne, scoreTwo, newDirX, paddleLoc)


# Returns distance from paddle center that the ball hit; on a scale from 0 (right at center) to 1 (top or bottom)
def calculateRelativeBallPaddleLoc(ballCenter, paddleTop, paddleBottom, paddleCenter):
    scaleSize = float(PADDLESIZE)
    relativeBallPos = 0.0
    if ballCenter > paddleCenter: # ball in bottom half
        relativeBallPos = ballCenter - paddleTop
    elif ballCenter < paddleCenter: # ball in top half
        relativeBallPos = paddleBottom - ballCenter
    else:
        return 0.0
    location = relativeBallPos/scaleSize
    return location


# Artificial intelligence of computer player
def artificialIntelligence(ball, ballDirX, paddle2):
    # If ball is moving away from paddle, center bat.
    if ballDirX == -1:
        if paddle2.centery < (WINDOWHEIGHT/2):
            paddle2.y += COMPUTERDIFFICULTY
        elif paddle2.centery > (WINDOWHEIGHT/2):
            paddle2.y -= COMPUTERDIFFICULTY
    # If ball moving towards bat, track its movement.
    elif ballDirX == 1:
        if paddle2.centery < ball.centery:
            paddle2.y += COMPUTERDIFFICULTY
        else:
            paddle2.y -= COMPUTERDIFFICULTY
    return paddle2

# Update paddle locations according to the input, where input is the new y position of the paddle
def updatePaddle(paddle, input):
    if input > WINDOWBOTTOM:
        paddle.centery = WINDOWBOTTOM
        return
    elif input < WINDOWTOP:
        paddle.centery = WINDOWTOP
        return
    paddle.centery = input

# Displays the current score on the screen
def displayScore(score_left, score_right):
    resultSurf1 = BASICFONT.render('%s' %(score_left), True, WHITE)
    resultSurf2 = BASICFONT.render('%s' %(score_right), True, WHITE)
    resultRect1 = resultSurf1.get_rect()
    resultRect2 = resultSurf2.get_rect()
    resultRect1.centerx = WINDOWWIDTH/2 - WINDOWWIDTH/4
    resultRect1.centery = WINDOWHEIGHT/5
    resultRect2.centerx = WINDOWWIDTH/2 + WINDOWWIDTH/4
    resultRect2.centery = WINDOWHEIGHT/5
    DISPLAYSURF.blit(resultSurf1, resultRect1)
    DISPLAYSURF.blit(resultSurf2, resultRect2)


# Team names are input manually on the very top!
def displayTeamNames():
    resultSurf1 = BASICFONT.render('%s' %(TEAM1_NAME), True, WHITE)
    resultSurf2 = BASICFONT.render('%s' %(TEAM2_NAME), True, WHITE)
    resultRect1 = resultSurf1.get_rect()
    resultRect2 = resultSurf2.get_rect()
    resultRect1.centerx = WINDOWWIDTH/2 - WINDOWWIDTH/4
    resultRect1.centery = WINDOWHEIGHT/6
    resultRect2.centerx = WINDOWWIDTH/2 + WINDOWWIDTH/4
    resultRect2.centery = WINDOWHEIGHT/6
    DISPLAYSURF.blit(resultSurf1, resultRect1)
    DISPLAYSURF.blit(resultSurf2, resultRect2)

# Creates map of arbitrary y range to pygame axis values
def locationMap():
    halfRange = float(((WINDOWBOTTOM-WINDOWTOP)/2) + WINDOWTOP)
    scale = float((halfRange-WINDOWTOP-(PADDLESIZE/2))/(INPUTRANGE))
    y_map = []
    y_map.append(WINDOWTOP + (PADDLESIZE/2))
    for i in range(INPUTRANGE-1):
        y_map.append(y_map[i]+scale)
    y_map.append(halfRange)
    for i in range(INPUTRANGE-1):
        y_map.append(y_map[INPUTRANGE+i]+scale)
    y_map.append(WINDOWBOTTOM - (PADDLESIZE/2))

    y_map = list(reversed(y_map))

    return y_map


# Main game function
def main():
    # Initiate y axis map
    y_map = locationMap()

    # Initiate game display
    pygame.init()
    global DISPLAYSURF

    # Set up font
    global BASICFONT
    BASICFONT = pygame.font.Font('freesansbold.ttf', BASICFONTSIZE)

    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH,WINDOWHEIGHT))
    pygame.display.set_caption('Pong')

    # Initiate variables and set starting positions any future changes made within rectangles
    ballX = WINDOWWIDTH/2 - BALLTHICKNESS/2
    ballY = WINDOWHEIGHT/2 - BALLTHICKNESS/2
    playerOnePosition = (WINDOWHEIGHT - PADDLESIZE) /2
    playerTwoPosition = (WINDOWHEIGHT - PADDLESIZE) /2
    scoreOne = 0
    scoreTwo = 0

    # Keeps track of ball direction and speed
    ballDirX = -1  # -1 = left, 1 = right
    ballDirY = -1  # -1 = up, 1 = down
    paddleLoc = 1.0

    # Creates Rectangles for ball and paddles.
    paddle1 = pygame.Rect(PADDLEOFFSET,playerOnePosition, LINETHICKNESS,PADDLESIZE)
    paddle2 = pygame.Rect(WINDOWWIDTH - PADDLEOFFSET - LINETHICKNESS, playerTwoPosition, LINETHICKNESS,PADDLESIZE)
    ball = pygame.Rect(ballX, ballY, BALLTHICKNESS, BALLTHICKNESS)

    # Draws the starting position of the Arena
    drawArena()
    drawPaddle(paddle1)
    drawPaddle(paddle2)
    drawBall(ball)

    pygame.mouse.set_visible(0) # make cursor invisible

    # Create UDP sockets
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.settimeout(0.00001)
    sock.setblocking(False)

    # Default input values
    global inputOne
    inputOne = 0.0

    while True: # main game loop
        # Draw the game components
        drawArena()
        drawPaddle(paddle1)
        drawPaddle(paddle2)
        drawBall(ball)

        # Update ball movement
        ball = moveBall(ball, ballDirX, ballDirY, paddleLoc)
        ballDirX, ballDirY, paddleLoc = checkEdgeCollision(ball, ballDirX, ballDirY, paddleLoc)

        tempInputOne = inputOne
        try:
            while True: # read until no other values
                ready = select.select([sock], [], [], 0.0)
                if ready[0]:
                    data, addr = sock.recvfrom(1024)
                    inputOne = float(data)
                else:
                    break # stop trying to read and use last value read
            # Check validity of input and updates paddles
            if 0 <= inputOne <= 1:
                # Convert the input into y_mapping range
                scaledInputOne = round((inputOne*(2*INPUTRANGE))-INPUTRANGE,0)
                # Map input to pixel location
                realInputOne = y_map[int(scaledInputOne)+INPUTRANGE]
                updatePaddle(paddle1, realInputOne)
                # print "%s  %s  %s  %s" %(data, inputOne, scaledInputOne, realInputOne)
            else:
                pass
        except:
            # if exception, reset everything to previous sample
            inputOne = tempInputOne
            print "EXCEPTION, Input: %d" %inputOne
            updatePaddle(paddle1, inputOne)

        # Move paddle 2 automatically
        paddle2 = artificialIntelligence(ball, ballDirX, paddle2)

        # Check edge collisions, change direction of ball, and adjust points
        # scoreOne, scoreTwo = checkPointScored(paddle1, paddle2, ball, scoreOne, scoreTwo, ballDirX)
        scoreOne, scoreTwo, ballDirX, paddleLoc = checkHitBall(ball, paddle1, paddle2, ballDirX, scoreOne, scoreTwo, paddleLoc)

        # Display everything and update according to FPS
        displayScore(scoreOne, scoreTwo)
        displayTeamNames()
        pygame.display.update()
        FPSCLOCK.tick(FPS)

        for event in pygame.event.get(): # ignore any game events, such as mouse clicks, etc.
            None

if __name__=='__main__':
    main()