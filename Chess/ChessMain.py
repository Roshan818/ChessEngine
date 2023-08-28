"""
This is the main driver file. Responsible for handling user input and displaying game state.
"""
from lib2to3 import pygram
import pygame
import ChessEngine
import ChessAI

WIDTH = HEIGHT = 512
DIMENSION = 8  # Dimension of chess board (8x8)
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15  # For Animation
IMAGES = {}


def load_images():
    """
    Initialize a global dictionary of images.
    Called exactly once in the main.
    """
    pieces = [
        "wp", "wR", "wN", "wB", "wQ", "wK",
        "bp", "bR", "bN", "bB", "bQ", "bK"
    ]

    for piece in pieces:
        IMAGES[piece] = pygame.transform.scale(
            pygame.image.load("images/" + piece + ".png"),
            (SQ_SIZE, SQ_SIZE)
        )
        # We can access image by saying IMAGES['wp']


def main():
    """
    main driver of code. 
    will handle input and update the graphics
    """
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    screen.fill(pygame.Color('white'))
    gs = ChessEngine.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False  # Flag variable when move is made

    animate = False  # Flag varible for animating the move

    # print(gs.board)
    load_images()
    running = True
    sq_selected = ()  # No Square is selected, keep track of last click
    player_clicks = []
    # Keep track of player clicks (two tuples: [(6, 4), (4, 4)])

    gameOver = False

    playerOne = False  # if Human is playing white then true
    playerTwo = True  # if Human is playing black then true

    while running:
        humanTurn = (gs.whiteToMove and playerOne) or\
            (not gs.whiteToMove and playerTwo)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if not gameOver and humanTurn:
                    location = pygame.mouse.get_pos()  # (x, y) location of mouse
                    col = location[0] // SQ_SIZE
                    row = location[1] // SQ_SIZE
                    # The user clicked the same square twice
                    if sq_selected == (row, col):
                        sq_selected = ()  # Deselect the square
                        player_clicks = []  # clear the player_clicks
                    else:
                        sq_selected = (row, col)
                        # Append for two clicks
                        player_clicks.append(sq_selected)
                    if len(player_clicks) == 2:  # After 2nd Click
                        move = ChessEngine.Move(
                            player_clicks[0],
                            player_clicks[1],
                            gs.board
                        )
                        for i in range(len(validMoves)):

                            if move == validMoves[i]:
                                # if not move.isEnpassantMove == validMoves[i].isEnpassantMove:
                                #     move.isEnpassantMove = validMoves[i].isEnpassantMove
                                # print(move.isEnpassantMove == validMoves[i].isEnpassantMove)
                                print(validMoves[i].getChessNotation())
                                gs.makeMove(validMoves[i])
                                moveMade = True
                                animate = True
                                # reset user clicks
                                sq_selected = ()
                                player_clicks = []
                        if not moveMade:
                            player_clicks = [sq_selected]

            elif e.type == pygame.KEYDOWN:  # Key Handler
                if e.key == pygame.K_z:
                    # undo move when 'z' is pressed
                    gs.undoMove()
                    moveMade = True
                    animate = False
                if e.key == pygame.K_r:
                    # Reset board when 'r' is pressed
                    gs = ChessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sq_selected = ()
                    player_clicks = []
                    moveMade = False
                    animate = False
                    gameOver = False

        # AI will find the move
        if not gameOver and not humanTurn:
            # AIMove = ChessAI.findRandomMove(validMoves)
            # AIMove = ChessAI.findBestMoveGreedy(gs, validMoves)
            # AIMove = ChessAI.findBestMoveMinMaxIter(gs, validMoves)
            # AIMove = ChessAI.findBestMoveMinMax(gs, validMoves)
            # AIMove = ChessAI.findBestMoveNegaMax(gs, validMoves)
            AIMove = ChessAI.findBestMoveNegaMaxAlphaBeta(gs, validMoves)
            if AIMove == None:
                AIMove = ChessAI.findRandomMove(validMoves)
            gs.makeMove(AIMove)
            moveMade = True
            animate = False

        if moveMade:
            if animate:
                animateMove(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False
        drawGameState(screen, gs, validMoves, sq_selected)

        if gs.checkmate:
            gameOver = True
            if gs.whiteToMove:
                drawText(screen, "Black wins by checkmate")
            else:
                drawText(screen, "WHite wins by checkmate")
        elif gs.stalemate:
            gameOver = True
            drawText(screen, "Stalemate")

        clock.tick(MAX_FPS)
        pygame.display.flip()


def highlightSquares(screen, gs, validMoves, sqSelected):
    """
    Highlights square selected and shows possible moves
    """
    if sqSelected != ():
        row, col = sqSelected
        if gs.board[row][col][0] == ('w' if gs.whiteToMove else 'b'):
            # Highlight Selected Square
            s = pygame.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)
            s.fill(pygame.Color('blue'))
            screen.blit(s, (col * SQ_SIZE, row * SQ_SIZE))

            # Highlight Moves from that square
            s.fill(pygame.Color('yellow'))
            for move in validMoves:
                if move.startRow == row and move.startCol == col:
                    screen.blit(
                        s,
                        (
                            move.endCol * SQ_SIZE,
                            move.endRow * SQ_SIZE
                        )
                    )


def drawGameState(screen, gs, validMoves, sqSelected):
    """
    Responsible for graphics within current game state
    """
    drawBoard(screen)  # Draw square on the board
    highlightSquares(screen, gs, validMoves, sqSelected)
    drawPieces(screen, gs.board)  # draw pieces on top of squares


def drawBoard(screen):
    """
    Draw the squares on the board.
    Top Left Square is always light.
    """
    global colors
    colors = [pygame.Color("white"), pygame.Color("gray")]

    for row in range(DIMENSION):
        for col in range(DIMENSION):
            color = colors[(row + col) % 2]
            pygame.draw.rect(
                screen,
                color,
                pygame.Rect(
                    col * SQ_SIZE,
                    row * SQ_SIZE,
                    SQ_SIZE,
                    SQ_SIZE
                )
            )


def drawPieces(screen, board):
    """
    Draw Pieces on board using current GameState.board
    """
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            piece = board[row][col]
            if piece != "--":
                # If not empty, draw the piece on board
                screen.blit(
                    IMAGES[piece],
                    pygame.Rect(
                        col * SQ_SIZE,
                        row * SQ_SIZE,
                        SQ_SIZE,
                        SQ_SIZE
                    )
                )


def animateMove(move, screen, board, clock):
    """
    Animate a move
    """
    global colors
    coords = []  # List of coordinates that the animation will move
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framesPerSquare = 10  # Frames to move one square
    frameCount = (abs(dR) + abs(dC)) * framesPerSquare
    for frame in range(frameCount + 1):

        row, col = (
            move.startRow + dR * frame / frameCount,
            move.startCol + dC * frame / frameCount
        )
        drawBoard(screen)
        drawPieces(screen, board)
        # erase piece moved from its ending square
        color = colors[(move.endRow + move.endCol) % 2]
        endSquare = pygame.Rect(
            move.endCol * SQ_SIZE,
            move.endRow * SQ_SIZE,
            SQ_SIZE, SQ_SIZE
        )
        pygame.draw.rect(screen, color, endSquare)
        # Draw Captured Piece on rectangle
        if move.pieceCaptured != "--":
            screen.blit(IMAGES[move.pieceCaptured], endSquare)
        # Draw moving piece
        screen.blit(
            IMAGES[move.pieceMoved],
            pygame.Rect(
                col * SQ_SIZE,
                row * SQ_SIZE,
                SQ_SIZE,
                SQ_SIZE
            )
        )
        pygame.display.flip()
        clock.tick(60)


def drawText(screen, text):
    font = pygame.font.SysFont("Helvetica", 32, True, False)
    text_object = font.render(text, 0, pygame.Color("gray"))
    text_location = pygame.Rect(0, 0, WIDTH, HEIGHT).move(
        WIDTH / 2 - text_object.get_width() // 2,
        HEIGHT / 2 - text_object.get_height() // 2
    )
    screen.blit(text_object, text_location)
    text_object = font.render(text, 0, pygame.Color("black"))
    screen.blit(text_object, text_location.move(2, 2))


if __name__ == "__main__":
    main()
