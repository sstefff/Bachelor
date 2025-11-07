import random
import csv
#https://github.com/JonathanDeLeon/connect-four-ai

infinity = float('inf')

class State:

    def __init__(self, ai_position, opponent_position, game_position, move=None):
        self.ai_position = ai_position
        self.opponent_position = opponent_position
        self.game_position = game_position
        self.move = move

    @staticmethod
    def is_winning_state(bitboard):
        # Horizontal
        for row in range(8):
            for col in range(5):
                mask = 0
                for i in range(4):
                    mask |= 1 << (row + 8 * (col + i))
                if bitboard & mask == mask:
                    return True
        # Vertikal
        for col in range(8):
            for row in range(5):
                mask = 0
                for i in range(4):
                    mask |= 1 << ((row + i) + 8 * col)
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
        for row in range(3, 8):
            for col in range(5):
                mask = 0
                for i in range(4):
                    mask |= 1 << ((row - i) + 8 * (col + i))
                if bitboard & mask == mask:
                    return True
        return False

    @staticmethod
    def is_draw(position):
        return position == (1 << 64) - 1

    def terminal_node_test(self):
        """ Test if current state is a terminal node """
        if self.is_winning_state(self.ai_position):
            # AI Wins
            self.status = -1
            return True
        elif self.is_winning_state(self.opponent_position):
            # Opponent Wins
            self.status = 1
            return True
        elif self.is_draw(self.game_position):
            # Draw
            self.status = 0
            return True
        else:
            return False
    
    def calculate_heuristic(self, turn):
        ai_board = self.ai_position
        opp_board = self.opponent_position
        game_pos = ai_board | opp_board
        if turn == -1 and self.is_winning_state(ai_board): return 100
        if turn == -1 and self.is_winning_state(opp_board): return -100
        if turn == 1 and self.is_winning_state(ai_board): return -100
        if turn == 1 and self.is_winning_state(opp_board): return 100

        if turn == -1 and four(ai_board, game_pos): return 50
        if turn == -1 and four(opp_board, game_pos): return -50
        if turn == 1 and four(ai_board, game_pos): return -50
        if turn == 1 and four(opp_board, game_pos): return 50
        return three(ai_board) if turn == -1 else three(opp_board)
    
    def generate_children(self, who_went_first):
        children = []
        pos = []
        winning = []
        center = 3.5  # For 8x8: (0...7)/2
        game_board = self.ai_position | self.opponent_position
        for col in range(8):
            for row in range(8):
                bit = 1 << (row + 8*col)
                if game_board & bit:
                    continue

                test_ai = self.ai_position | (1 << (8 * col + row))
                test_player = self.opponent_position | (1 << (8 * col + row))
                if self.is_winning_state(test_ai) or self.is_winning_state(test_player):
                    winning.append((col, row))
                else:
                    pos.append((col, row))
        pos.sort(key=lambda pos: abs(pos[0] - center) + abs(pos[1] - center))
        candidate_moves = winning + pos[:20]

        for col, row in candidate_moves:
            bit = 1 << (row + 8*col)
            if game_board & bit:
                continue
            if who_went_first:
                new_ai = self.ai_position | bit
                new_opp = self.opponent_position
            else:
                new_ai = self.ai_position
                new_opp = self.opponent_position | bit
                #yield State(new_ai, new_opp, new_ai | new_opp, move=(col, row))
            children.append(State(new_ai, new_opp, new_ai | new_opp, move=(col, row)))
        return children

'''def is_winning_state(bitboard):
    # Horizontal
    for row in range(8):
        for col in range(5):
            mask = 0
            for i in range(4):
                mask |= 1 << (row + 8 * (col + i))
            if bitboard & mask == mask:
                return True
    # Vertikal
    for col in range(8):
        for row in range(5):
            mask = 0
            for i in range(4):
                mask |= 1 << ((row + i) + 8 * col)
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
    for row in range(3, 8):
        for col in range(5):
            mask = 0
            for i in range(4):
                mask |= 1 << ((row - i) + 8 * (col + i))
            if bitboard & mask == mask:
                return True
    return False'''

def four(position, game_position):
    # Horizontal
    for row in range(8):
        for col in range(5):
            '''window = [row + 8 * (col + i) for i in range(4)]
            stones = [(position & (1 << idx)) != 0 for idx in window]
            free_places = [not (game_position & (1 << idx)) for idx in window]
            if stones.count(True) == 3 and free_places.count(True) == 1:
                free_index = free_places.index(True)
                free_row = row
                free_col = col + free_index
                # Check: alle Felder darunter sind belegt
                if all((game_position & (1 << (r + 8 * free_col))) for r in range(free_row)):
                    # print(f"THREAT DETECTED: {row} {col} {free_index} HORIZONTAL")
                    return True'''
            idxs = [row + 8 * (col + i) for i in range(4)]
            bits = [1 if position & (1 << idx) else 0 for idx in idxs]
            occs = [1 if game_position & (1 << idx) else 0 for idx in idxs]
            # Optional: Print-Overlay zum Debuggen
            # print(f"row={row} cols={col}-{col+3} bits={bits} occs={occs}")

            # Alle Varianten mit 3 eigenen und 1 leerem Feld, keine Fremdsteine erlaubt
            #for zero_pos in range(4):
                #if bits.count(1) == 3 and occs.count(1) == 3:
            if bits.count(1) == 3 and occs.count(1) == 3:
                for zero_pos in range(4):
                    if bits[zero_pos] == 0 and occs[zero_pos] == 0:
                        return True

    # Vertikal
    for col in range(8):
        for row in range(5):
            '''window = [(row + i) + 8 * col for i in range(4)]
            stones = [(position & (1 << idx)) != 0 for idx in window]
            free_places = [not (game_position & (1 << idx)) for idx in window]
            if stones.count(True) == 3 and free_places.count(True) == 1:
                free_index = free_places.index(True)
                free_row = row + free_index
                free_col = col
                # Check: alle Felder darunter sind belegt
                if all((game_position & (1 << (r + 8 * free_col))) for r in range(free_row)):
                    # print(f"THREAT DETECTED: {row} {col} {free_index} VERTIKAL")
                    return True'''
            idxs = [(row + i) + 8 * col for i in range(4)]
            bits = [1 if position & (1 << idx) else 0 for idx in idxs]
            occs = [1 if game_position & (1 << idx) else 0 for idx in idxs]
            #for zero_pos in range(4):
                #if bits.count(1) == 3 and occs.count(1) == 3:
            if bits.count(1) == 3 and occs.count(1) == 3:
                for zero_pos in range(4):
                    if bits[zero_pos] == 0 and occs[zero_pos] == 0:
                        return True
    # Diagonal ↘
    for row in range(5):
        for col in range(5):
            '''window = [(row + i) + 8 * (col + i) for i in range(4)]
            stones = [(position & (1 << idx)) != 0 for idx in window]
            free_places = [not (game_position & (1 << idx)) for idx in window]
            if stones.count(True) == 3 and free_places.count(True) == 1:
                free_index = free_places.index(True)
                free_row = row + free_index
                free_col = col + free_index
                if all((game_position & (1 << (r + 8 * free_col))) for r in range(free_row)):
                    # print(f"THREAT DETECTED: {row} {col} {free_index} DIAGONAL1")
                    return True'''
            idxs = [(row + i) + 8 * (col + i) for i in range(4)]
            bits = [1 if position & (1 << idx) else 0 for idx in idxs]
            occs = [1 if game_position & (1 << idx) else 0 for idx in idxs]
            #for zero_pos in range(4):
                #if bits.count(1) == 3 and occs.count(1) == 3:
            if bits.count(1) == 3 and occs.count(1) == 3:
                for zero_pos in range(4):
                    if bits[zero_pos] == 0 and occs[zero_pos] == 0:
                        return True
    # Diagonal ↗
    for row in range(3, 8):
        for col in range(5):
            '''window = [(row - i) + 8 * (col + i) for i in range(4)]
            stones = [(position & (1 << idx)) != 0 for idx in window]
            free_places = [not (game_position & (1 << idx)) for idx in window]
            if stones.count(True) == 3 and free_places.count(True) == 1:
                free_index = free_places.index(True)
                free_row = row - free_index
                free_col = col + free_index
                if all((game_position & (1 << (r + 8 * free_col))) for r in range(free_row)):
                    # print(f"THREAT DETECTED: {row} {col} {free_index} DIAGONAL2")
                    return True'''
            idxs = [(row - i) + 8 * (col + i) for i in range(4)]
            bits = [1 if position & (1 << idx) else 0 for idx in idxs]
            occs = [1 if game_position & (1 << idx) else 0 for idx in idxs]
            #for zero_pos in range(4):
                #if bits.count(1) == 3 and occs.count(1) == 3:
            if bits.count(1) == 3 and occs.count(1) == 3:
                for zero_pos in range(4):
                    if bits[zero_pos] == 0 and occs[zero_pos] == 0:
                        return True
    return False

def three(position):
    # zähl alle Dreierreihen
    count = 0
    # Horizontal --
    # wenn position belegt und links + rechts neben belegt   
    for row in range(8):
        for col in range(0, 6): 
            # Horizontal --
            # wenn position belegt und links + rechts neben belegt 
            if position & (1 << (8 * col + row)) and position & (1 << ((col + 1) * 8 + row)) and position & (1 << ((col + 2) * 8 + row)): #########
                count += 1
                #print('three: horizontal')
    #print('count horizontal:', count)
    # Diagonal \    richtig mit + ???!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #position + links oben und rechts unten belegt
    for col in range(0, 6):
        for row in range(2, 8):
            if position & (1 << (8 * col + row)) and position & (1 << ((col + 1) * 8 + (row + 1))) and position & (1 << ((col + 2) * 8 + (row + 2))): ################
                count += 1
                #print('three: diagonal \\')
    #print('count diagonal \\', count)
    # Diagonal /    richtig mit - ???!!!!!!!!!!!!!!!!!!!!!
    #position + links unten und rechts oben belegt
    for col in range(0, 6):
        for row in range(0, 6):
            if position & (1 << (8 * col + row)) and position & (1 << ((col + 1) * 8 + (row - 1))) and position & (1 << ((col + 2) * 8 + (row - 2))): ###############
                count += 1
                #print('three: diagonal /')
    #print('count diagonal /', count)
    # Vertical |
    #position + drüber und drunter belegt
    for col in range(8):
        for row in range(0, 6):
            if position & (1 << (8 * col + row)) and position & (1 << (col * 8 + (row + 1))) and position & (1 << (col * 8 + (row + 2))): ###############
                count += 1
                #print('three: vertical')
    #print('count vertical', count)
    #print(count)
    return count

def alphabeta_search(state, turn=-1,d=4):
    """Search game state to determine best action; use alpha-beta pruning. """

    # Functions used by alpha beta
    def max_value(state, alpha, beta, depth):
        if cutoff_search(state, depth):
            return state.calculate_heuristic(state)

        v = -infinity
        for child in state.generate_children(turn):
            if child in seen:
                continue
            v = max(v, min_value(child, alpha, beta, depth + 1))
            seen[child] = alpha
            if v >= beta:
                # Min is going to completely ignore this route
                # since v will not get any lower than beta
                return v
            alpha = max(alpha, v)
        if v == -infinity:
            # If win/loss/draw not found, don't return -infinity to MIN node
            return infinity
        return v

    def min_value(state, alpha, beta, depth):
        if cutoff_search(state, depth):
            return state.calculate_heuristic(state)

        v = infinity
        for child in state.generate_children(turn):
            if child in seen:
                continue
            v = min(v, max_value(child, alpha, beta, depth + 1))
            seen[child] = alpha
            if v <= alpha:
                # Max is going to completely ignore this route
                # since v will not get any higher than alpha
                return v
            beta = min(beta, v)
        if v == infinity:
            # If win/loss/draw not found, don't return infinity to MAX node
            return -infinity
        return v

    # Keep track of seen states using their hash
    seen = {}
    actions = []

    # Body of alpha beta_search:
    cutoff_search = (lambda state, depth: depth > d or state.terminal_node_test())
    best_score = -infinity
    beta = infinity
    best_action = None
    
    for child in state.generate_children(turn):
        v = min_value(child, best_score, beta, 1)
        actions.append((v, child))
        if v > best_score:
            best_score = v
            best_action = child
    #return best_action

    # Zufällig einen aus den 5 besten Zügen wählen
    actions = sorted(actions, key=lambda tupel: tupel[0], reverse=True)
    actions = actions[:5]
    chosen = random.choice(actions)
    # Wenn die AI oder der Gegner gewinnen kann (Gewinn bzw. Verlust) gib den besten Zug best_action zurück
    if state.is_winning_state(best_action.ai_position) or state.is_winning_state(best_action.opponent_position):
        return best_action
    elif four(best_action.ai_position, best_action.game_position) or four(best_action.opponent_position, best_action.game_position):
    #if danger(state.ai_position, state.game_position) or danger(state.opponent_position, state.game_position):
        return best_action
    # Sonst random Zug aus den 5 besten Zügen
    return chosen[1]   # gibt ein State-Objekt zurück!

def print_board(KI1_board, KI2_board):
    '''for row in range(8):
        line = []
        for col in range(8):
            idx = row + 8 * col
            if KI1_board & (1 << idx):
                line.append("1")
            elif KI2_board & (1 << idx):
                line.append("2")
            else:
                line.append("0")
        print(" ".join(line))
    print("")'''
    for row in range(0, 8):
        print("")
        for column in range(8):
            if KI1_board & (1 << (8 * column + row)):
                print("1", end='')
            elif KI2_board & (1 << (8 * column + row)):
                print("2", end='')
            else:
                print("0", end='')
    print("")

'''def query_AI(state, global_turn, search_depth=4):
    #best_state = alphabeta_search(state, global_turn, depth=search_depth)
    best_state = alphabeta_search(state, global_turn, d=search_depth)
    score = best_state.calculate_heuristic(global_turn)
    move = best_state.move
    return move, score'''

def board_to_fen(ai_position, game_position, next_player):
    # ai_position = schwarz (b), game_position = weiß (w)
    fen_rows = []
    for row in range(8):   # Von oben (0) nach unten (7)
        fen_row = ""
        empty = 0
        for col in range(8):
            idx = col * 8 + row
            if ai_position & (1 << idx):
                if empty > 0:
                    fen_row += str(empty)
                    empty = 0
                fen_row += "b"
            elif game_position & (1 << idx):
                if empty > 0:
                    fen_row += str(empty)
                    empty = 0
                fen_row += "w"
            else:
                empty += 1
        if empty > 0:
            fen_row += str(empty)
        fen_rows.append(fen_row)
    fen = '/'.join(fen_rows)
    fen += " " + ("b" if next_player == -1 else "w") # ("b" if next_player == -1 else "w")
    return fen

def game_board_random(n):
    max_tries = 100
    all_indices = list(range(64))
    print("N:", n)
    for _ in range(max_tries):
        ai_board, opponent_board = 0, 0
        '''for _ in range(16): ####################### n
            idx_ai = random.randint(0, 63)
            if not (ai_board | opponent_board) & (1 << idx_ai):
                ai_board |= (1 << idx_ai)
            idx_op = random.randint(0, 63)
            if not (ai_board | opponent_board) & (1 << idx_op):
                opponent_board |= (1 << idx_op)'''
        random.shuffle(all_indices)
        indices = all_indices[:n]
        for i, idx in enumerate(indices):
            if i % 2 == 0:
                ai_board |= (1 << idx)
            else:
                opponent_board |= (1 << idx)

        if valid_start_board(ai_board, opponent_board):
            return ai_board, opponent_board
        
    return ai_board, opponent_board

def valid_start_board(ai_pos, opponent_pos):
    # Prüfe auf Gewinnlinien im Startboard:
    if State.is_winning_state(ai_pos) or State.is_winning_state(opponent_pos):
        return False
    '''# Prüfe auf schwebende Steine: In jeder Spalte dürfen nur von unten nach oben belegt werden
    for col in range(8):
        col_bits = [(col*8)+row for row in range(8)]
        found_empty = False
        for idx in col_bits:
            if not ((ai_pos | opponent_pos) & (1 << idx)):
                found_empty = True
            elif found_empty:
                # Es gibt Stein über leerem Feld
                return False'''
    return True

class Game:

    def __init__(self):
        self.KI1_board = 0
        self.KI2_board = 0
        self.turn = -1  # KI1 fängt an
        self.round = 1

    def query_AI(self, state, global_turn, search_depth=4):
        #best_state = alphabeta_search(state, global_turn, depth=search_depth)
        best_state = alphabeta_search(state, global_turn, d=search_depth)
        score = best_state.calculate_heuristic(global_turn)
        move = best_state.move
        return move, score

    def play_selfplay_game(self, search_depth=4):
        states = []
        self.KI1_board, self.KI2_board = game_board_random(random.randint(0, 32)) #(2, 16)
        
        ai_pieces = bin(self.KI1_board).count("1")
        opp_pieces = bin(self.KI2_board).count("1")
        if ai_pieces <= opp_pieces:
            self.turn = -1
        else: 
            self.turn = 1

        print(ai_pieces)
        print(opp_pieces)
        print("Startzustand:")
        print_board(self.KI1_board, self.KI2_board)
        while True:
            if self.turn == -1:
                state = State(self.KI1_board, self.KI2_board, self.KI1_board | self.KI2_board)
            else:
                state = State(self.KI2_board, self.KI1_board, self.KI1_board | self.KI2_board)
            move, score = self.query_AI(state, self.turn, search_depth=search_depth)
            col, row = move
            game_pos = self.KI1_board | self.KI2_board
            if self.turn == -1:
                self.KI1_board |= (1 << (row + 8 * col))
                print(f"Runde {self.round}  KI1 Zug: Column={col+1}, Row={row+1}, Score={score}")
                #fen = board_to_fen(self.KI1_board, game_pos, -game.turn)
            else:
                self.KI2_board |= (1 << (row + 8 * col))
                print(f"Runde {self.round}  KI2 Zug: Column={col+1}, Row={row+1}, Score={score}")
                #fen = board_to_fen(self.KI2_board, game_pos, -game.turn)
            print_board(self.KI1_board, self.KI2_board)

            fen = board_to_fen(self.KI1_board, game_pos, -game.turn)

            states.append({
            'fen': fen,
            #'action': (col, row),
            'action': (col+1, row+1),
            'score': score
            })
            
            # Gewinnprüfung
            if state.is_winning_state(self.KI1_board):
                print("KI1 hat gewonnen!")
                break
            if state.is_winning_state(self.KI2_board):
                print("KI2 hat gewonnen!")
                break
            if (self.KI1_board | self.KI2_board) == (1 << 64) - 1:
                print("Unentschieden!")
                break

            self.turn *= -1
            self.round += 1

        result = None
        if state.is_winning_state(self.KI1_board):
            result = 1
        if state.is_winning_state(self.KI2_board):
            result = -1
        if (self.KI1_board | self.KI2_board) == (1 << 64) - 1:
            result = 0

        for i, s in enumerate(states):
            if i == len(states)-1:
                s['result'] = result
            else:
                s['result'] = None
        print(states)
        return states

if __name__ == "__main__":
    game = Game()
    #game.play_selfplay_game(search_depth=4)

    print("Welcome to Connect Four!")
    n_games = 1000
    data = []
    for i in range(n_games):
        print("GAME", i)
        data.extend(game.play_selfplay_game(search_depth=4))
    with open('training_neu.csv', 'w', newline='') as f:
    #with open('trainingsdaten.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['fen', 'action', 'score', 'result'])
        writer.writeheader()
        for row in data:
            writer.writerow(row)