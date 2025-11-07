#!/usr/bin/env python3 -u
# -*- coding: utf-8 -*-

from __future__ import print_function
import re, sys, time
from itertools import count
from collections import namedtuple

#import tools

from nnue_eval import *
#https://github.com/dimdano/numbfish

###############################################################################
# Piece-Square tables. Tune these to change numbfish's behaviour
###############################################################################
    
piece = { 'b': 100, 'w': 100 } #P = piece - uniform stone value

pst = {
    'b': (   0,   0,   0,   0,   0,   0,   0,   0,
             0,   0,   0,   0,   0,   0,   0,   0,
             0,   0,  10,  10,  10,  10,   0,   0,
             0,   0,  10,  20,  20,  10,   0,   0,
             0,   0,  10,  20,  20,  10,   0,   0,
             0,   0,  10,  10,  10,  10,   0,   0,
             0,   0,   0,   0,   0,   0,   0,   0,
             0,   0,   0,   0,   0,   0,   0,   0),
    'w': (   0,   0,   0,   0,   0,   0,   0,   0,
             0,   0,   0,   0,   0,   0,   0,   0,
             0,   0,  10,  10,  10,  10,   0,   0,
             0,   0,  10,  20,  20,  10,   0,   0,
             0,   0,  10,  20,  20,  10,   0,   0,
             0,   0,  10,  10,  10,  10,   0,   0,
             0,   0,   0,   0,   0,   0,   0,   0,
             0,   0,   0,   0,   0,   0,   0,   0)
} #center bonus
# Pad tables and join piece and pst dictionaries
'''k = 'p'
table = pst[k]
padrow = lambda row: (0,) + tuple(x+piece[k] for x in row) + (0,)
pst[k] = sum((padrow(table[i*8:i*8+8]) for i in range(8)), ())
pst[k] = (0,)*20 + pst[k] + (0,)*20'''
for k, table in pst.items():
    padrow = lambda row: (0,) + tuple(x+piece[k] for x in row) + (0,)
    pst[k] = sum((padrow(table[i*8:i*8+8]) for i in range(8)), ())
    pst[k] = (0,)*20 + pst[k] + (0,)*20

###############################################################################
# Global constants
###############################################################################

# Our board is represented as a 120 character string. The padding allows for
# fast detection of moves that don't stay within the board.
A1, H1, A8, H8 = 91, 98, 21, 28
initial = (
    '         \n'  #   0 -  9
    '         \n'  #  10 - 19
    ' ........\n'  #  20 - 29
    ' ........\n'  #  30 - 39
    ' ........\n'  #  40 - 49
    ' ........\n'  #  50 - 59
    ' ........\n'  #  60 - 69
    ' ........\n'  #  70 - 79
    ' ........\n'  #  80 - 89
    ' ........\n'  #  90 - 99
    '         \n'  # 100 -109
    '         \n'  # 110 -119
)

# Lists of possible moves for each piece type.
#N, E, S, W = -10, 1, 10, -1
#!!!!!!!!!!!!FUNKTION LÖSCHEN????!!!!!!!!!!!!!!
'''directions = {
    'P': () #the piece cannot move after it has been set
}'''

# Mate value must be greater than 8*queen + 2*(rook+knight+bishop)
# King value is set to twice this value such that if the opponent is
# 8 queens up, but we got the king, we still exceed MATE_VALUE.
# When a MATE is detected, we'll set the score to MATE_UPPER - plies to get there
# E.g. Mate in 3 will be MATE_UPPER - 6
#MATE_LOWER = piece['K'] - 10*piece['Q']
#MATE_UPPER = piece['K'] + 10*piece['Q']
LOWER = -1000000
UPPER = 1000000

# The table size is the maximum number of elements in the transposition table.
TABLE_SIZE = 1e7

# Constants for tuning search
QS_LIMIT = 219
EVAL_ROUGHNESS = 13
DRAW_TEST = True
OPENING_BOOK = False
###############################################################################
# Chess logic
###############################################################################

class Position(namedtuple('Position', 'board score num_pieces turn')):
    """ A state of a chess game
    board -- a 120 char representation of the board
    score -- the board evaluation
    num_pieces -- number of pieces on the board
    turn -- player's move
    """

    def gen_moves(self):
        #all empty fields are possible moves
        for i, p in enumerate(self.board):
            if p == '.' and A8 <= i <= H1:
                yield i

    '''def rotate(self):
        #Rotates the board
        return Position(
            self.board[::-1].swapcase(), -self.score, self.num_pieces)'''

    #!!!!!!!!!!!!!!FUNKTION LÖSCHEN!!!!!!!!!!!!!!!!
    '''def nullmove(self):
        #Like rotate, but clears ep and kp
        return Position(
            self.board[::-1].swapcase(), -self.score,
            self.bc, self.wc, 0, 0)'''

    def move(self, move):
        if move is None:
            raise ValueError("Ungültiger Zug")
        assert isinstance(move, int)
        assert self.board[move] == '.', "the field is occupied"
        player = self.turn
        new_board = self.board[:move] + player + self.board[move+1:]
        # Copy variables
        score = self.score + self.value(move)
        num_pieces = self.num_pieces + 1
        # We rotate the returned position, so it's ready for the next player
        #return Position(new_board, score, num_pieces).rotate()
        player = 'b' if self.turn == 'w' else 'w'
        return Position(new_board, score, num_pieces, player)

    def value(self, move):
        # Actual move
        #score = pst['p'][move]
        if self.turn == 'b':
            score = pst['b'][move]
        else:
            score = pst['w'][move]      
        return score

###############################################################################
# Search logic
###############################################################################

# lower <= s(pos) <= upper
Entry = namedtuple('Entry', 'lower upper')

class Searcher:
    def __init__(self):
        self.tp_score = {}
        self.tp_move = {}
        self.history = set()
        self.nodes = 0
        self.use_classical = False

        '''if finish(pos, 'b'): # Black
            #AI wins
            return 100
        if finish(pos, 'w'): # White
            #Player wins
            return -100
        #Board is full -> no more pieces can be placed (Draw)
        if pos.num_pieces >= 64: 
            return 0 '''

    #def bound(self, pos, gamma, depth, kings, accum_root, accum_up, pos_prev, move_prev, root=True):
    def bound(self, pos, gamma, depth, root=True):
        self.nodes += 1
        depth = max(depth, 0)

        # ABBRUCH: Tiefe 0 oder Spiel vorbei
        if depth == 0 or finish(pos, 'b') or finish(pos, 'w'):  # game_over prüft Sieg/Remis/Brett voll
            if not self.use_classical:
                board_ = parse_board(pos.board)
                features_ = features_full(board_, pos.turn)
                features_input = features_.reshape(input_details[0]['shape'])
                interpreter.set_tensor(input_details[0]["index"], features_input)
                interpreter.invoke()
                score_output = interpreter.get_tensor(output_details[0]["index"])
                score = float(score_output.flatten()[0])
            else:
                score = pos.score
            #print("NNUE-Score:", score, "| Stellung:", pos.board)
            return score  # <- KEIN generator, sondern Float!

        # Transposition Table Zugriff
        entry = self.tp_score.get((pos, depth, root), Entry(-UPPER, UPPER))
        if entry.lower >= gamma and (not root or self.tp_move.get(pos) is not None):
            return entry.lower
        if entry.upper < gamma:
            return entry.upper

        best = -UPPER
        best_move = None

        # Zug-Loop: Sortiere alle Züge, rekursiv bewerten
        for move in sorted(pos.gen_moves(), key=pos.value, reverse=True):
            if move is not None and not finish(pos, pos.turn):
                score = -self.bound(pos.move(move), 1 - gamma, depth - 1, root=False)
            else: 
                score = 0
            if score > best:
                best = score
                best_move = move
            if best >= gamma:
                if len(self.tp_move) > TABLE_SIZE:
                    self.tp_move.clear()
                self.tp_move[pos] = move
                break

        # Remis/Überlauf (optional, bei zu vielen Steinen/Ende)
        if best < gamma and best < 0 and depth > 0:
            if hasattr(pos, "num_pieces") and pos.num_pieces >= 64:
                best = -UPPER

        if len(self.tp_score) > TABLE_SIZE:
            self.tp_score.clear()
        if best >= gamma:
            self.tp_score[pos, depth, root] = Entry(best, entry.upper)
        elif best < gamma:
            self.tp_score[pos, depth, root] = Entry(entry.lower, best)

        return best  # <- KEIN Generator, sondern Float/Int!


    def search(self, pos, movetime, use_classical = False, history=()):
        """ Iterative deepening MTD-bi search """
        self.nodes = 0
        if DRAW_TEST:
            self.history = history
            self.tp_score.clear()
        
        self.use_classical = use_classical
        #global OPENING_BOOK
        
        '''if OPENING_BOOK:
            try:
                with chess.polyglot.open_reader("Perfect2021.bin") as opening_book:  
                    time.sleep(0.01)  #may need delay for some chess guis, i.e. cutechess              
                    opening = opening_book.choice(chess.Board(tools.renderFEN(pos)))
                    opening_book.close()
                    print('Found book move')
                    yield 1, opening.move, 0, True
                    return 
            except:
                OPENING_BOOK = False'''
                

        for depth in range (1,100):
            lower, upper = -UPPER, UPPER
            while lower < upper - EVAL_ROUGHNESS:
                gamma = (lower+upper+1)//2   
                #score = self.bound(pos, gamma, depth, None, np.empty([1, 512], dtype=np.float32) , True, pos, None)
                score = self.bound(pos, gamma, depth, None) #root=True
                if score >= gamma:
                    lower = score
                if score < gamma:
                    upper = score  
            #self.bound(pos, lower, depth, None, np.empty([1, 512], dtype=np.float32), True, pos, None)
            self.bound(pos, gamma, depth, None) #root=True

            #yield depth, self.tp_move.get(pos), self.tp_score.get((pos, depth, True)).lower, False
            entry = self.tp_score.get((pos, depth, True))
            if entry is not None:
                lower = entry.lower
            else:
                lower = 0
            yield depth, self.tp_move.get(pos), lower
            #yield depth, self.tp_move.get(pos), self.tp_score.get((pos, depth, True)).lower
            
#Check if there are 4 pieces in a row 
def finish(pos, player):
    board = pos.board
    directions = [1, 10, 11, 9] #horizontal, diagonal, vertical
    range_ = set(range(A8, H1+1))
    for field in range_:
        if board[field] != player:
            continue
        for dir_ in directions:
            index = [field + i * dir_ for i in range(4)]
            if all(j in range_ and board[j] == player for j in index):
                return True
    return False


###############################################################################
# User interface
###############################################################################       
    
# Python 2 compatability
if sys.version_info[0] == 2:
    input = raw_input


def parse(c):
    fil, rank = ord(c[0]) - ord('a'), int(c[1]) - 1
    return A1 + fil - 10*rank


def move_render(pos, m):
    # Numbfish always assumes promotion to queen
    '''p = 'q' if A8 <= m[1] <= H8 and pos.board[m[0]] == 'P' else ''
    m = m if tools.get_color(pos) == 0 else (119-m[0], 119-m[1])
    
    
    rank1, fil1 = divmod(m[0] - A1, 10)
    rank2, fil2 = divmod(m[1] - A1, 10)
    
    return chr(fil1 + ord('a')) + str(-rank1 + 1) + chr(fil2 + ord('a')) + str(-rank2 + 1) + p'''
    return render(m)

def render(i):
    if i == None:
        return '-'
    rank, fil = divmod(i - A1, 10)
    return chr(fil + ord('a')) + str(-rank + 1)


def print_pos(pos):
    print()
    uni_pieces = {'w':'●', 'b':'○' ,'.':'·'}
    for i, row in enumerate(pos.board.split()):
        print(' ', 8-i, ' '.join(uni_pieces.get(p, p) for p in row))
    print('    a b c d e f g h \n\n')

def parse_board(board_str):
    lines = board_str.split('\n')
    # Relevant sind nur die Zeilen 2 bis 9 (inklusive; 8 Zeilen ohne Padding oben/unten)
    game_lines = lines[2:10]
    # Jede Zeile hat links und rechts ein Padding, also nimm die Spalten 1 bis 8 (inklusive)
    parsed = [list(line[1:9]) for line in game_lines if len(line) >= 9 and all(c in ".bw" for c in line[1:9])]
    return parsed

def winner(pos):
    for player in ('b', 'w'):
        if finish(pos, player):
            return player
    # Remis (kein Spieler gewinnt)
    return None


def main():
    #hist = [Position(initial, 0, (True,True), (True,True), 0, 0)]
    hist = [Position(initial, 0, 0, 'b')]
    searcher = Searcher()
    #player = 'p'
    while True:
        print_pos(hist[-1])

        #if hist[-1].score <= -LOWER:
        if finish(hist[-1], 'w'):
            print("You lost")
            break
        if finish(hist[-1], 'b'):
            print("You won")
            break

        # We query the user until she enters a (pseudo) legal move.
        move = None
        while move not in hist[-1].gen_moves():
            input_ = input('Your move: ')
            match = re.match('^[a-h][1-8]$', input_.strip())
            #match = re.match('([a-h][1-8])'*2, input('Your move: '))
            if match:
                #move = parse(match.group(1)), parse(match.group(2))
                move = parse(match.group(0))
            else:
                # Inform the user when invalid input (e.g. "help") is entered
                print("Please enter a move like d5")
        if move is not None and not finish(hist[-1], hist[-1].turn):
            hist.append(hist[-1].move(move))
        else:
            sieger = winner(hist[-1])
            if sieger == 'b':
                print("Schwarz gewinnt!")
            elif sieger == 'w':
                print("Weiß gewinnt!")
            else:
                print("Unentschieden!")
            break

        #player = 'P' if player == 'p' else 'p'
        # After our move we rotate the board and print it again.
        # This allows us to see the effect of our move.
        #print_pos(hist[-1].rotate())
        print_pos(hist[-1])

        #if hist[-1].score <= -LOWER:
        if finish(hist[-1], 'b'):
            print("You won")
            break
        if finish(hist[-1], 'w'):
            print("You lost")
            break

        # Fire up the engine to look for a move.
        start = time.time()
        best = None
        for _depth, move, score in searcher.search(hist[-1], hist):
            best = move
            if time.time() - start > 1:
                break

        '''if score == UPPER:
            print("Checkmate!")'''
        '''if finish(hist[-1], 'w'):
            print("You lost")
            break
        if finish(hist[-1], 'b'):
            print("You won")
            break'''
        # The black player moves from a rotated position, so we have to
        # 'back rotate' the move before printing it.
        #print("My move:", render(119-move[0]) + render(119-move[1]))
        print("My move:", render(best))
        #print("My move:", render(best))
        #hist.append(hist[-1].move(move))

        if move is not None and not finish(hist[-1], 'w'):
            hist.append(hist[-1].move(best))
        else:
            sieger = winner(hist[-1])
            if sieger == 'b':
                print("Schwarz gewinnt!")
            elif sieger == 'w':
                print("Weiß gewinnt!")
            else:
                print("Unentschieden!")
            break



if __name__ == '__main__':
    main()

