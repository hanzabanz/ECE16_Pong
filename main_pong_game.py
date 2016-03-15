import pygame
import pygame.mixer as mx
import socket
import select
import time
import random
import sys

"""
Adapted from: http://trevorappleton.blogspot.com/2014/04/writing-pong-using-python-and-pygame.html

ECE16 Final Project Pong Game - Class Version
"""

# Team-Specific Variables
TEAM1_NAME = 'Team 1'
TEAM2_NAME = 'Team 2'

# Match-Specific Variables
SPEED_MULTIPLIER = 1  # default speed; how many pixels the ball is incremented; must be >= 1
PADDLE_SPEED_MULTIPLIER = 3  # adds speed, i.e. if 1, then max return speed would be 1+1=2 if hit in center of paddle
BALL_THICKNESS = 30  # size of one side of the rectangular ball in pixels
PADDLE_SIZE = 200  # size of paddle in pixels
COMPUTER_DIFFICULTY = 1  # correlated with how fast the computer paddle moves; higher the faster
MATCH_LENGTH = 5*60  # length of match in seconds
CALIBRATION_LENGTH = 5*60 # length of calibration in seconds

# Game-Hosting Variables
UDP_IP = "127.0.0.1"
UDP_PORT1 = 5005
UDP_PORT2 = 5006

# Game-Specific Variables
INPUT_RANGE = 100  # higher the value, the high specificity with y position
FPS = 200  # frames per second; can be changed to make the game refresh faster

# Game-Display Variables
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 900
LINE_THICKNESS = 10
PADDLE_OFFSET = 20

WINDOW_TOP = LINE_THICKNESS + (BALL_THICKNESS/2)
WINDOW_BOTTOM = WINDOW_HEIGHT - WINDOW_TOP
WINDOW_SCALE_OFFSET = (WINDOW_BOTTOM-WINDOW_TOP)/2
SCALE = (WINDOW_BOTTOM-WINDOW_TOP)/((2*INPUT_RANGE))

BASIC_FONT_SIZE = 30

BLACK     = (0  ,0  ,0  )
WHITE     = (255,255,255)
RED       = (255,0  ,0  )

# Sound Effect Variables
# BALL_BOUNCE_FILE = '/sounds/Ball_Bounce.wav'
BALL_BOUNCE_FILE = 'sounds/BallBounce2.wav'
BALL_THUD_FILE = 'sounds/BallThud.wav'
WINNER_FILE = 'sounds/Winner.wav'
READY_SET_GO_FILE = 'sounds/Countdown.wav'
GO_FILE = 'sounds/Go.wav'

# ------------------------------------- #
#             BALL METHODS              #
# ------------------------------------- #

# Moves the ball
# Returns new position
def moveBall(ball, ballDirX, ballDirY, paddleLoc):
    # convert relative paddle location to speed multiplier
    locAddition = (1.0-abs(paddleLoc))*PADDLE_SPEED_MULTIPLIER
    distToTravel = SPEED_MULTIPLIER + locAddition
    oneSideToTravel = pow((pow(distToTravel,2)/2),0.5)
    if oneSideToTravel < 1:  # cannot increment pixels by < 1
        oneSideToTravel = 1
    # adjust the speed based on the last paddle location
    ball.x += (ballDirX)*(oneSideToTravel)
    ball.y += (ballDirY)*(oneSideToTravel)
    return ball


# Checks for a collision with a wall, and 'bounces' ball off it
# Returns new direction
def checkEdgeCollision(ball, ballDirX, ballDirY, paddleLoc):
    if ball.top <= (LINE_THICKNESS) or ball.bottom >= (WINDOW_HEIGHT - LINE_THICKNESS):
        ballDirY = ballDirY * -1
        while ball.top <= (LINE_THICKNESS) or ball.bottom >= (WINDOW_HEIGHT - LINE_THICKNESS):
            # move slowly until it is out of the boundary so it doesn't keep switching directions
            ball.y += ballDirY
    if ball.left <= (LINE_THICKNESS) or ball.right >= (WINDOW_WIDTH - LINE_THICKNESS):
        ballDirX = ballDirX * -1
        while ball.left < (LINE_THICKNESS) or ball.right > (WINDOW_WIDTH - LINE_THICKNESS):
            # move slowly until it is out of the boundary so it doesn't keep switching directions
            ball.x += ballDirX
        paddleLoc = 1.0 # if hitting off left or right edge, then reset to default speed
    return ballDirX, ballDirY, paddleLoc


# Checks if the ball has hit a paddle, scores, and 'bounces' ball off paddle
# Returns new scores, direction of ball, and relative location of paddle hit
def checkHitBall(ball, paddle1, paddle2, ballDirX, scoreOne, scoreTwo, paddleLoc, ballBounceSound, ballThudSound):
    newDirX = 1*ballDirX
    # if either of these two conditions, then paddle has hit the ball
    if ball.left <= LINE_THICKNESS:
        ballThudSound.play()
        pygame.time.delay(35)
        scoreOne -= 1
        paddleLoc = 1.0
    elif ballDirX == -1 and paddle1.right >= ball.left and paddle1.top < (ball.top + (ball.height/2)) and paddle1.bottom > (ball.bottom - (ball.height/2)):
        ballBounceSound.play()
        pygame.time.delay(35)
        scoreOne += 1
        newDirX =  -1*ballDirX
        paddleLoc = calculateRelativeBallPaddleLoc(ball.centery, paddle1.top, paddle1.bottom, paddle1.centery)
    elif ball.right >= WINDOW_WIDTH - LINE_THICKNESS:
        ballThudSound.play()
        pygame.time.delay(35)
        scoreTwo -= 1
        paddleLoc = 1.0
    elif ballDirX == 1 and paddle2.left <= ball.right and paddle2.top < (ball.top + (ball.height/2)) and paddle2.bottom > (ball.bottom - (ball.height/2)):
        ballBounceSound.play()
        pygame.time.delay(35)
        scoreTwo += 1
        newDirX =  -1*ballDirX
        paddleLoc = calculateRelativeBallPaddleLoc(ball.centery, paddle2.top, paddle2.bottom, paddle2.centery)
    return (scoreOne, scoreTwo, newDirX, paddleLoc)


# Returns distance from paddle center that the ball hit; on a scale from 0 (right at center) to 1 (top or bottom)
def calculateRelativeBallPaddleLoc(ballCenter, paddleTop, paddleBottom, paddleCenter):
    scaleSize = float(PADDLE_SIZE)
    relativeBallPos = 0.0
    if ballCenter > paddleCenter: # ball in bottom half
        relativeBallPos = ballCenter - paddleTop
    elif ballCenter < paddleCenter: # ball in top half
        relativeBallPos = paddleBottom - ballCenter
    else:
        return 0.0
    location = relativeBallPos/scaleSize
    return location


# ------------------------------------- #
#            PADDLE METHODS             #
# ------------------------------------- #

def readSocket(sock, y_map, tempInput):
    input = 0.5
    try:
        while True: # read until no other values
            ready = select.select([sock], [], [], 0.0)
            if ready[0]:
                data, addr = sock.recvfrom(1024)
                input = float(data)
            else:
                break # stop trying to read and use last value read
    except:
        # if exception, reset everything to previous sample
        input = tempInput
    # Check validity of input and updates paddles
    if 0 <= input <= 1:
        # Convert the input into y_mapping range
        scaledInput = round((input*(2*INPUT_RANGE))-INPUT_RANGE,0)
        # Map input to pixel location
        realInput = y_map[int(scaledInput)+INPUT_RANGE]
        return realInput
    else:
        pass


# Update paddle locations according to the input, where input is the new y position of the paddle
def updatePaddle(paddle, input):
    if input > WINDOW_BOTTOM:
        paddle.centery = WINDOW_BOTTOM
        return
    elif input < WINDOW_TOP:
        paddle.centery = WINDOW_TOP
        return
    paddle.centery = input


# ------------------------------------- #
#        BASIC DISPLAY METHODS          #
# ------------------------------------- #

# Draws the arena the game will be played in
def drawArena():
    DISPLAY_SURF.fill((0,0,0))
    #Draw outline of arena
    pygame.draw.rect(DISPLAY_SURF, WHITE, ((0,0),(WINDOW_WIDTH,WINDOW_HEIGHT)), LINE_THICKNESS*2)
    #Draw centre line
    pygame.draw.line(DISPLAY_SURF, WHITE, ((WINDOW_WIDTH/2),0),((WINDOW_WIDTH/2),WINDOW_HEIGHT), (LINE_THICKNESS/4))


# Draws the paddle
def drawPaddle(paddle):
    #Stops paddle from moving too low
    if paddle.bottom > WINDOW_HEIGHT - LINE_THICKNESS:
        paddle.bottom = WINDOW_HEIGHT - LINE_THICKNESS
    #Stops paddle from moving too high
    elif paddle.top < LINE_THICKNESS:
        paddle.top = LINE_THICKNESS
    #Draws paddle
    pygame.draw.rect(DISPLAY_SURF, WHITE, paddle)


# Draws the ball
def drawBall(ball):
    pygame.draw.rect(DISPLAY_SURF, WHITE, ball)


# ------------------------------------- #
#         MATCH DISPLAY METHODS         #
# ------------------------------------- #

# Displays the current score on the screen
def displayScore(score_left, score_right):
    resultSurf1 = BASIC_FONT.render('%s' %(score_left), True, WHITE)
    resultSurf2 = BASIC_FONT.render('%s' %(score_right), True, WHITE)
    resultRect1 = resultSurf1.get_rect()
    resultRect2 = resultSurf2.get_rect()
    resultRect1.centerx = WINDOW_WIDTH/2 - WINDOW_WIDTH/4
    resultRect1.centery = WINDOW_HEIGHT/5
    resultRect2.centerx = WINDOW_WIDTH/2 + WINDOW_WIDTH/4
    resultRect2.centery = WINDOW_HEIGHT/5
    DISPLAY_SURF.blit(resultSurf1, resultRect1)
    DISPLAY_SURF.blit(resultSurf2, resultRect2)


# Team names are input manually on the very top!
def displayTeamNames():
    resultSurf1 = BASIC_FONT.render('%s' %(TEAM1_NAME), True, WHITE)
    resultSurf2 = BASIC_FONT.render('%s' %(TEAM2_NAME), True, WHITE)
    resultRect1 = resultSurf1.get_rect()
    resultRect2 = resultSurf2.get_rect()
    resultRect1.centerx = WINDOW_WIDTH/2 - WINDOW_WIDTH/4
    resultRect1.centery = WINDOW_HEIGHT/6
    resultRect2.centerx = WINDOW_WIDTH/2 + WINDOW_WIDTH/4
    resultRect2.centery = WINDOW_HEIGHT/6
    DISPLAY_SURF.blit(resultSurf1, resultRect1)
    DISPLAY_SURF.blit(resultSurf2, resultRect2)


def displayWinner(scoreOne, scoreTwo, FPS_CLOCK, winnerSound):
    displayLength = 10
    winningMsg = ''
    if scoreOne > scoreTwo:
        winningMsg = 'Winner: %s' %(TEAM1_NAME)
    elif scoreOne < scoreTwo:
        winningMsg = 'Winner: %s' %(TEAM2_NAME)
    else:
        winningMsg = 'Tie!'

    print "%s\nTeam 1: %d    Team 2: %d    Difference: %d" %(winningMsg, scoreOne, scoreTwo, abs(scoreOne-scoreTwo))

    winnerSound.play()
    begTime = time.time()
    while time.time() < begTime + displayLength:
        wordSurf = ANNOUNCE_FONT.render(winningMsg, True, WHITE)
        wordRect = wordSurf.get_rect()
        wordRect.centerx = WINDOW_WIDTH/2
        wordRect.centery = WINDOW_HEIGHT/2
        DISPLAY_SURF.blit(wordSurf, wordRect)
        pygame.display.update()
        FPS_CLOCK.tick(FPS)
        for event in pygame.event.get(): # ignore any game events, such as mouse clicks, etc.
            None


# Creates map of arbitrary y range to pygame axis values
def locationMap():
    halfRange = float(((WINDOW_BOTTOM-WINDOW_TOP)/2) + WINDOW_TOP)
    scale = float((halfRange-WINDOW_TOP-(PADDLE_SIZE/2))/(INPUT_RANGE))
    global y_map
    y_map = []
    y_map.append(WINDOW_TOP + (PADDLE_SIZE/2))
    for i in range(INPUT_RANGE-1):
        y_map.append(y_map[i]+scale)
    y_map.append(halfRange)
    for i in range(INPUT_RANGE-1):
        y_map.append(y_map[INPUT_RANGE+i]+scale)
    y_map.append(WINDOW_BOTTOM - (PADDLE_SIZE/2))

    y_map = list(reversed(y_map))

    return y_map

# ------------------------------------- #
#      TRANSITION DISPLAY METHODS       #
# ------------------------------------- #

def displayBeginRound(FPS_CLOCK, readySetGoSound):
    displayLength = 2  # number of seconds for each screen to display
    soundPlay = True
    begTime = time.time()
    words = ['READY', 'SET', 'GO!']
    DISPLAY_SURF.fill((0,0,0))
    while time.time() < begTime+(displayLength*3):
        DISPLAY_SURF.fill((0,0,0))
        if time.time() < begTime+displayLength:
            i = 0
            if soundPlay == True:
                readySetGoSound.play()
                pygame.time.delay(100)
                soundPlay = False
        elif time.time() < begTime+(displayLength*2):
            i = 1
            if soundPlay == False:
                readySetGoSound.play()
                pygame.time.delay(100)
                soundPlay = True
        else:
            i = 2
            if soundPlay == True:
                readySetGoSound.play()
                pygame.time.delay(100)
                soundPlay = False
        wordSurf = ANNOUNCE_FONT.render(words[i], True, WHITE)
        wordRect = wordSurf.get_rect()
        wordRect.centerx = WINDOW_WIDTH/2
        wordRect.centery = WINDOW_HEIGHT/2
        DISPLAY_SURF.blit(wordSurf, wordRect)

        pygame.display.update()
        FPS_CLOCK.tick(FPS)
        for event in pygame.event.get(): # ignore any game events, such as mouse clicks, etc.
                None


def displayCalibrationRound():
    word = "CALIBRATION"
    wordSurf = BASIC_FONT.render(word, True, WHITE)
    wordRect = wordSurf.get_rect()
    wordRect.centerx = WINDOW_WIDTH/2
    wordRect.centery = WINDOW_HEIGHT/2
    DISPLAY_SURF.blit(wordSurf, wordRect)


def displayCountDown(endTime):
    color = WHITE

    currTime = time.time()
    timeLeft = endTime - currTime
    if timeLeft < 0:
        return
    min = int(timeLeft/60)
    if min < 10:
        minStr = "0%d" %min
    elif min < 1:
        minStr = "00"
    else:
        minStr = str(min)
    sec = int(timeLeft%60)
    if sec < 10:
        secStr = "0%d" %sec
    else:
        secStr = str(sec)

    if min < 1 and sec < 30:
        color = RED
    word = "%s:%s" %(str(minStr), str(secStr))
    wordSurf = BASIC_FONT.render(word, True, color)
    wordRect = wordSurf.get_rect()
    wordRect.centerx = WINDOW_WIDTH/2
    wordRect.centery = WINDOW_HEIGHT/2+WINDOW_HEIGHT/3
    DISPLAY_SURF.blit(wordSurf, wordRect)


# ------------------------------------- #
#           MAIN GAME FUNCTION          #
# ------------------------------------- #
def main():
    # Initiate y axis map
    y_map = locationMap()

    # Initiate game display
    pygame.init()
    global DISPLAY_SURF

    # Set up font
    global BASIC_FONT
    BASIC_FONT = pygame.font.Font('freesansbold.ttf', BASIC_FONT_SIZE)
    global ANNOUNCE_FONT
    ANNOUNCE_FONT = pygame.font.Font('freesansbold.ttf', 4*BASIC_FONT_SIZE)

    FPS_CLOCK = pygame.time.Clock()
    DISPLAY_SURF = pygame.display.set_mode((WINDOW_WIDTH,WINDOW_HEIGHT))
    pygame.display.set_caption('ECE 16 Pong')

    # Initiate variables and set starting positions any future changes made within rectangles
    ballX = WINDOW_WIDTH/2 - BALL_THICKNESS/2
    ballY = WINDOW_HEIGHT/2 - BALL_THICKNESS/2
    playerOnePosition = (WINDOW_HEIGHT - PADDLE_SIZE) /2
    playerTwoPosition = (WINDOW_HEIGHT - PADDLE_SIZE) /2
    scoreOne = 0
    scoreTwo = 0

    # Keeps track of ball direction and speed
    ballDirX = random.choice([-1, 1])  # -1 = left, 1 = right
    ballDirY = random.choice([-1, 1])  # -1 = up, 1 = down
    paddleLoc = 1.0

    # Creates Rectangles for ball and paddles.
    paddle1 = pygame.Rect(PADDLE_OFFSET,playerOnePosition, LINE_THICKNESS,PADDLE_SIZE)
    paddle2 = pygame.Rect(WINDOW_WIDTH - PADDLE_OFFSET - LINE_THICKNESS, playerTwoPosition, LINE_THICKNESS,PADDLE_SIZE)
    ball = pygame.Rect(ballX, ballY, BALL_THICKNESS, BALL_THICKNESS)

    pygame.mouse.set_visible(0) # make cursor invisible

    # Create UDP sockets
    sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock1.bind((UDP_IP, UDP_PORT1))
    sock1.settimeout(0.00001)
    sock1.setblocking(False)
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock2.bind((UDP_IP, UDP_PORT2))
    sock2.settimeout(0.00001)
    sock2.setblocking(False)

    # Set up sound effects
    mx.pre_init(frequency=22050, size = -16, channels=4, buffer=4096)
    mx.init()
    ballBounceSound = mx.Sound(BALL_BOUNCE_FILE)
    ballThudSound = mx.Sound(BALL_THUD_FILE)
    ballThudSound.set_volume(0.3)
    readySetGoSound = mx.Sound(READY_SET_GO_FILE)
    goSound = mx.Sound(GO_FILE)
    winnerSound = mx.Sound(WINNER_FILE)

    # Default input values
    global inputOne
    inputOne = 0.5
    global inputTwo
    inputTwo = 0.5

    # ------------------------------------- #
    #           CALIBRATION LOOP            #
    # ------------------------------------- #

    finishCalibration = False
    begTime = time.time()
    endTime = begTime+CALIBRATION_LENGTH

    while time.time() < endTime:  # main game loop
        # Draw the game components
        drawArena()
        drawPaddle(paddle1)
        drawPaddle(paddle2)
        drawBall(ball)

        # Update ball movement
        ball = moveBall(ball, ballDirX, ballDirY, paddleLoc)
        ballDirX, ballDirY, paddleLoc = checkEdgeCollision(ball, ballDirX, ballDirY, paddleLoc)

        tempInputOne = inputOne
        tempInputTwo = inputTwo

        # read from socket 1
        newInputOne = readSocket(sock1, y_map, tempInputOne)
        inputOne = newInputOne
        updatePaddle(paddle1, inputOne)

        # read from socket 2
        newInputTwo = readSocket(sock2, y_map, tempInputTwo)
        inputTwo = newInputTwo
        updatePaddle(paddle2, inputTwo)

        # Check edge collisions, change direction of ball, and adjust scores
        scoreOne, scoreTwo, ballDirX, paddleLoc = checkHitBall(ball, paddle1, paddle2, ballDirX, scoreOne, scoreTwo, paddleLoc, ballBounceSound, ballThudSound)

        # Display everything and update according to FPS
        displayTeamNames()
        displayCalibrationRound()
        displayCountDown(endTime)
        pygame.display.update()
        FPS_CLOCK.tick(FPS)

        for event in pygame.event.get(): # ignore any game events, such as mouse clicks, etc.
            if event.type == pygame.K_ESCAPE:
                pygame.quit()
                sys.quit()
            if event.type == pygame.KEYDOWN:
                if event.key==pygame.K_SPACE:
                    finishCalibration = True
                    break
        if finishCalibration == True:
            break

    # pygame.time.delay(1000)
    currTime = time.time()
    while time.time() < currTime+1:
        drawArena()
        pygame.display.update()
        FPS_CLOCK.tick(FPS)

    # ------------------------------------- #
    #               GAME LOOP               #
    # ------------------------------------- #
    # Resets all variables
    ballX = WINDOW_WIDTH/2 - BALL_THICKNESS/2
    ballY = WINDOW_HEIGHT/2 - BALL_THICKNESS/2
    playerOnePosition = (WINDOW_HEIGHT - PADDLE_SIZE) /2
    playerTwoPosition = (WINDOW_HEIGHT - PADDLE_SIZE) /2
    scoreOne = 0
    scoreTwo = 0
    paddle1 = pygame.Rect(PADDLE_OFFSET,playerOnePosition, LINE_THICKNESS,PADDLE_SIZE)
    paddle2 = pygame.Rect(WINDOW_WIDTH - PADDLE_OFFSET - LINE_THICKNESS, playerTwoPosition, LINE_THICKNESS,PADDLE_SIZE)
    ball = pygame.Rect(ballX, ballY, BALL_THICKNESS, BALL_THICKNESS)
    inputOne = 0.5
    inputTwo = 0.5

    # Keeps track of ball direction and speed
    ballDirX = random.choice([-1, 1])  # -1 = left, 1 = right
    ballDirY = random.choice([-1, 1])  # -1 = up, 1 = down
    paddleLoc = 1.0

    begTime = time.time()
    endTime = begTime + MATCH_LENGTH

    # Draws the beginning ready, set, go sequence
    displayBeginRound(FPS_CLOCK, readySetGoSound)
    goSound.play()
    pygame.time.delay(1000)

    while time.time() < begTime+MATCH_LENGTH:  # main game loop
        # Draw the game components
        drawArena()
        drawPaddle(paddle1)
        drawPaddle(paddle2)
        drawBall(ball)

        # Update ball movement
        ball = moveBall(ball, ballDirX, ballDirY, paddleLoc)
        ballDirX, ballDirY, paddleLoc = checkEdgeCollision(ball, ballDirX, ballDirY, paddleLoc)

        tempInputOne = inputOne
        tempInputTwo = inputTwo

        # read from socket 1
        newInputOne = readSocket(sock1, y_map, tempInputOne)
        inputOne = newInputOne
        updatePaddle(paddle1, inputOne)

        # read from socket 2
        newInputTwo = readSocket(sock2, y_map, tempInputTwo)
        inputTwo = newInputTwo
        updatePaddle(paddle2, inputTwo)

        # Check edge collisions, change direction of ball, and adjust scores
        scoreOne, scoreTwo, ballDirX, paddleLoc = checkHitBall(ball, paddle1, paddle2, ballDirX, scoreOne, scoreTwo, paddleLoc, ballBounceSound, ballThudSound)

        # Display everything and update according to FPS
        displayScore(scoreOne, scoreTwo)
        displayTeamNames()
        if endTime > time.time() > endTime-30:
            displayCountDown(endTime)
        pygame.display.update()
        FPS_CLOCK.tick(FPS)

        for event in pygame.event.get(): # ignore any game events, such as mouse clicks, etc.
            if event.type == pygame.K_ESCAPE:
                pygame.quit()
                sys.quit()

    displayWinner(scoreOne, scoreTwo, FPS_CLOCK, winnerSound)
    pygame.quit()

if __name__=='__main__':
    main()