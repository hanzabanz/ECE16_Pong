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
BALLTHICKNESS = 10
PADDLESIZE = 120

# Game-Specific Variables
INPUTRANGE = 20
FPS = 200

# Game Display Variables
WINDOWWIDTH = 800
WINDOWHEIGHT = 600
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
def moveBall(ball, ballDirX, ballDirY):
    ball.x += (ballDirX)*SPEEDMULTIPLIER
    ball.y += (ballDirY)*SPEEDMULTIPLIER
    return ball

# Checks for a collision with a wall, and 'bounces' ball off it
# Returns new direction
def checkEdgeCollision(ball, ballDirX, ballDirY):
    if ball.top <= (LINETHICKNESS) or ball.bottom >= (WINDOWHEIGHT - LINETHICKNESS):
        ballDirY = ballDirY * -1
    if ball.left <= (LINETHICKNESS) or ball.right >= (WINDOWWIDTH - LINETHICKNESS):
        ballDirX = ballDirX * -1
    return ballDirX, ballDirY

# Checks is the ball has hit a paddle, and 'bounces' ball off it
def checkHitBall(ball, paddle1, paddle2, ballDirX):
    if ballDirX == -1 and paddle1.right >= ball.left and paddle1.top < (ball.top + (ball.height/2)) and paddle1.bottom > (ball.bottom - (ball.height/2)):
        return -1
    elif ballDirX == 1 and paddle2.left <= ball.right and paddle2.top < (ball.top + (ball.height/2)) and paddle2.bottom > (ball.bottom - (ball.height/2)):
        return -1
    else: return 1


# Checks to see if a point has been scored returns new score
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


# Artificial intelligence of computer player
def artificialIntelligence(ball, ballDirX, paddle2):
    # If ball is moving away from paddle, center bat.
    if ballDirX == -1:
        if paddle2.centery < (WINDOWHEIGHT/2):
            paddle2.y += 1
        elif paddle2.centery > (WINDOWHEIGHT/2):
            paddle2.y -= 1
    # If ball moving towards bat, track its movement.
    elif ballDirX == 1:
        if paddle2.centery < ball.centery:
            paddle2.y += 1
        else:
            paddle2.y -=1
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
    resultSurf = BASICFONT.render('%s                                %s' %(score_left, score_right), True, WHITE)
    resultRect = resultSurf.get_rect()
    resultRect.centerx = WINDOWWIDTH/2
    resultRect.centery = WINDOWHEIGHT/5
    DISPLAYSURF.blit(resultSurf, resultRect)


# Team names are input manually on the very top!
def displayTeamNames():
    resultSurf = BASICFONT.render('%s                   %s' %(TEAM1_NAME, TEAM2_NAME), True, WHITE)
    resultRect = resultSurf.get_rect()
    resultRect.centerx = WINDOWWIDTH/2
    resultRect.centery = WINDOWHEIGHT/6
    DISPLAYSURF.blit(resultSurf, resultRect)

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

    # Keeps track of ball direction
    ballDirX = -1  # -1 = left, 1 = right
    ballDirY = -1  # -1 = up, 1 = down

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

    # Create UDP socket
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
        ball = moveBall(ball, ballDirX, ballDirY)
        ballDirX, ballDirY = checkEdgeCollision(ball, ballDirX, ballDirY)

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
            if -INPUTRANGE <= inputOne <= INPUTRANGE:
                # Convert the input into y_mapping range
                # inputOne = round(inputOne, 2)
                inputOne = (inputOne*(2*INPUTRANGE))-INPUTRANGE
                inputOne = round(inputOne, 0)
                # Map input to pixel location
                realInputOne = y_map[int(inputOne)+INPUTRANGE]
                updatePaddle(paddle1, realInputOne)
        except:
            # if exception, reset everything to previous sample
            inputOne = tempInputOne
            updatePaddle(paddle1, inputOne)

        # Move paddle 2 automatically
        paddle2 = artificialIntelligence(ball, ballDirX, paddle2)

        # Check edge collisions, change direction of ball, and adjust points
        scoreOne, scoreTwo = checkPointScored(paddle1, paddle2, ball, scoreOne, scoreTwo, ballDirX)
        ballDirX = ballDirX * checkHitBall(ball, paddle1, paddle2, ballDirX)

        # Display everything and update according to FPS
        displayScore(scoreOne, scoreTwo)
        displayTeamNames()
        pygame.display.update()
        FPSCLOCK.tick(FPS)

if __name__=='__main__':
    main()