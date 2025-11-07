import numbfish as nb
import connect4_AlphaBeta as ab

AI_NNUE = nb.Searcher()
game = ab.Game()
AI_NNUE.use_classical = False

def padded_to_bitboards(padded):
    ai_board = 0
    opp_board = 0
    for col in range(8):
        for row in range(8):
            idx_padded = (row + 2) * 10 + (col + 1)
            val = padded[idx_padded]
            if val in ('w', '1'):
                ai_board |= (1 << (col * 8 + row))
            elif val in ('b', '2'):
                opp_board |= (1 << (col * 8 + row))
    return ai_board, opp_board

def bitboards_to_padded(ai_board, opp_board):
    rows = []
    for row in range(12):
        line = []
        for col in range(10):
            if 2 <= row <= 9 and 1 <= col <= 8:
                board_row = row - 2
                board_col = col - 1
                bit_idx = board_col * 8 + board_row
                if (ai_board >> bit_idx) & 1:
                    line.append('w')
                elif (opp_board >> bit_idx) & 1:
                    line.append('b')
                else:
                    line.append('.')  # Nur Punkt!!
            else:
                line.append(' ')
        rows.append(''.join(line))
    return '\n'.join(rows)

def print_padded_board(board):
    lines = board.split('\n')
    for r in range(2, 10):  # Zeile 2–9
        line = ''.join(lines[r][1:9])
        print(line)

def is_winning_state(bitboard):
    # Horizontal
    for row in range(8):
        for col in range(5):
            mask = 0
            for i in range(4):
                mask |= 1 << (row + 8*(col+i))
            if bitboard & mask == mask:
                return True
    # Vertikal
    for col in range(8):
        for row in range(5):
            mask = 0
            for i in range(4):
                mask |= 1 << ((row+i) + 8*col)
            if bitboard & mask == mask:
                return True
    # Diagonal /
    for row in range(5):
        for col in range(5):
            mask = 0
            for i in range(4):
                mask |= 1 << ((row + i) + 8 * (col + i))
            if bitboard & mask == mask:
                return True
    # Diagonal \
    for row in range(3,8):
        for col in range(5):
            mask = 0
            for i in range(4):
                mask |= 1 << ((row-i) + 8 * (col + i))
            if bitboard & mask == mask:
                return True
    return False


'''def get_nnue_best_move(pos, max_depth=3):
    move = None
    print(pos.board)
    for depth, m, score in AI_NNUE.search(pos, movetime=None):
        move = m
        if depth >= max_depth:
            break
    return move'''
def get_nnue_best_move(pos, ai_board, opp_board, max_depth=1):
    legal_moves = [m for m in pos.gen_moves() if not (ai_board | opp_board) & (1 << ((m // 8) * 8 + (m % 8)))]
    best_score = float('-inf')
    best_move = None
    for move in legal_moves:
        # Simuliere den Zug: neue Position erzeugen
        new_pos = pos.move(move)
        # Führe eine Mini-Suche/Bewertung auf new_pos aus
        # (hier z.B. Depth 1 reicht häufig um Unterschiede zu finden)
        move_score = None
        for depth, m, score in AI_NNUE.search(new_pos, movetime=None):
            move_score = score
            if depth >= max_depth:
                break
        if move_score is not None and move_score > best_score:
            best_score = move_score
            best_move = move
    if best_move is not None:
        return best_move
    elif legal_moves:
        # Fallback, falls Bewertung fehlschlägt
        return legal_moves[0]
    else:
        return None

##########################################################
# Initial: Leeres Feld nur mit Punkten!
padded_board = (
    '          \n'  # 0-9 (Padding)
    '          \n'  # 10-19
    ' ...ww..b\n'  # 20-29
    ' w......b\n'  # 30-39
    ' ........\n'  # 40-49
    ' ........\n'  # 50-59
    ' .b.b..w.\n'  # 60-69
    ' b.......\n'  # 70-79
    ' ...w..b.\n'  # 80-89
    ' ..w.....\n'  # 90-99
    '          \n'  # 100-109
    '          '    # 110-119
)

ai_board, opp_board = padded_to_bitboards(padded_board)
global_turn = -1

while True:
    if global_turn == 1:
        state = ab.State(ai_board, opp_board, ai_board | opp_board)
        move1, score = game.query_AI(state, global_turn, 4)
        col, row = move1
        bit_idx = col * 8 + row
        ai_board |= (1 << bit_idx)
        padded_board = bitboards_to_padded(ai_board, opp_board)
        if is_winning_state(ai_board):
            print("KI1 gewinnt")
            print("Spiel vorbei!")
            break
    else:
        nnue_pos = nb.Position(padded_board, 0, 0, 'b')
        #print("LEGAL MOVES:", list(nnue_pos.gen_moves()))
        move2 = get_nnue_best_move(nnue_pos, ai_board, opp_board)
        if move2 is None:
            print("Kein legaler Zug mehr möglich (Unentschieden oder Spielende!)")
            break
        col = move2 // 8
        row = move2 % 8
        bit_idx = col * 8 + row
        opp_board |= (1 << bit_idx)
        padded_board = bitboards_to_padded(ai_board, opp_board)
        if is_winning_state(opp_board):
            print("KI2 gewinnt")
            print("Spiel vorbei!")
            break
    global_turn *= -1

print("GAME FINISH")