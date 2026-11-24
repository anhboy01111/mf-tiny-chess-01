# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Makefun Hunter Engine
# Tiny Chess Alpha-Beta Engine with Piece-Square Tables (MIT License)

import os
import sys
import json
import urllib.request
import urllib.error

# 120-square board representation (10x12)
# Ranks 8 to 1 are at indices 20..90. Files a to h are offsets 1..8.
A1, H1, A8, H8 = 91, 98, 21, 28

PIECE_VALS = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

PST_P = [
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    0, 50, 50, 50, 50, 50, 50, 50, 50,  0,
    0, 10, 10, 20, 30, 30, 20, 10, 10,  0,
    0,  5,  5, 10, 25, 25, 10,  5,  5,  0,
    0,  0,  0,  0, 20, 20,  0,  0,  0,  0,
    0,  5, -5,-10,  0,  0,-10, -5,  5,  0,
    0,  5, 10, 10,-20,-20, 10, 10,  5,  0,
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0
]

PST_N = [
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    0,-50,-40,-30,-30,-30,-30,-40,-50,  0,
    0,-40,-20,  0,  0,  0,  0,-20,-40,  0,
    0,-30,  0, 10, 15, 15, 10,  0,-30,  0,
    0,-30,  5, 15, 20, 20, 15,  5,-30,  0,
    0,-30,  0, 15, 20, 20, 15,  0,-30,  0,
    0,-30,  5, 10, 15, 15, 10,  5,-30,  0,
    0,-40,-20,  0,  5,  5,  0,-20,-40,  0,
    0,-50,-40,-30,-30,-30,-30,-40,-50,  0,
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0
]

PST_B = [
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    0,-20,-10,-10,-10,-10,-10,-10,-20,  0,
    0,-10,  0,  0,  0,  0,  0,  0,-10,  0,
    0,-10,  0,  5, 10, 10,  5,  0,-10,  0,
    0,-10,  5,  5, 10, 10,  5,  5,-10,  0,
    0,-10,  0, 10, 10, 10, 10,  0,-10,  0,
    0,-10, 10, 10, 10, 10, 10, 10,-10,  0,
    0,-10,  5,  0,  0,  0,  0,  5,-10,  0,
    0,-20,-10,-10,-10,-10,-10,-10,-20,  0,
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0
]

PST_K = [
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    0,-30,-40,-40,-50,-50,-40,-40,-30,  0,
    0,-30,-40,-40,-50,-50,-40,-40,-30,  0,
    0,-30,-40,-40,-50,-50,-40,-40,-30,  0,
    0,-30,-40,-40,-50,-50,-40,-40,-30,  0,
    0,-20,-30,-30,-40,-40,-30,-30,-20,  0,
    0,-10,-20,-20,-20,-20,-20,-20,-10,  0,
    0, 20, 20,  0,  0,  0,  0, 20, 20,  0,
    0, 20, 30, 10,  0,  0, 10, 30, 20,  0,
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0
]

PST = {'P': PST_P, 'N': PST_N, 'B': PST_B, 'R': [0]*120, 'Q': [0]*120, 'K': PST_K}

DIRS = {
    'P': [-10], 'N': [-21, -19, -12, -8, 8, 12, 19, 21],
    'B': [-11, -9, 9, 11], 'R': [-10, -1, 1, 10],
    'Q': [-11, -10, -9, -1, 1, 9, 10, 11], 'K': [-11, -10, -9, -1, 1, 9, 10, 11]
}

def sq_to_uci(sq):
    return "abcdefgh"[sq % 10 - 1] + str(10 - sq // 10)

def uci_to_sq(u):
    return (10 - int(u[1])) * 10 + ("abcdefgh".index(u[0]) + 1)

def parse_fen(fen):
    b = [' '] * 120
    parts = fen.split()
    ranks = parts[0].split('/')
    for r, rank_str in enumerate(ranks):
        f = 1
        for ch in rank_str:
            if ch.isdigit():
                for _ in range(int(ch)):
                    b[(r + 2) * 10 + f] = '.'
                    f += 1
            else:
                b[(r + 2) * 10 + f] = ch
                f += 1
    turn = parts[1] if len(parts) > 1 else 'w'
    return b, turn

def eval_pos(b):
    score = 0
    for sq in range(21, 99):
        p = b[sq]
        if p in '. ':
            continue
        val = PIECE_VALS[p.upper()] + PST[p.upper()][sq if p.isupper() else (119 - sq)]
        score += val if p.isupper() else -val
    return score

def apply_move(b, move_uci):
    nb = list(b)
    s1 = uci_to_sq(move_uci[:2])
    s2 = uci_to_sq(move_uci[2:4])
    p = nb[s1]
    nb[s1] = '.'
    if len(move_uci) == 5:
        p = move_uci[4].upper() if p.isupper() else move_uci[4].lower()
    nb[s2] = p
    if p.upper() == 'P' and move_uci[0] != move_uci[2] and b[s2] == '.':
        nb[s1 // 10 * 10 + s2 % 10] = '.'
    return nb

def gen_simple_moves(b, white):
    moves = []
    for sq in range(21, 99):
        p = b[sq]
        if p in '. ' or (p.isupper() != white):
            continue
        u = p.upper()
        if u == 'P':
            step = -10 if white else 10
            if b[sq + step] == '.':
                moves.append((sq, sq + step, False))
                start_row = 8 if white else 3
                if sq // 10 == start_row and b[sq + 2 * step] == '.':
                    moves.append((sq, sq + 2 * step, False))
            for cap in (-11, -9) if white else (9, 11):
                target = b[sq + cap]
                if target not in '. ' and (target.isupper() != white):
                    moves.append((sq, sq + cap, True))
        elif u in 'NBRQK':
            rays = u in 'BRQ'
            for d in DIRS[u]:
                dest = sq + d
                while b[dest] != ' ':
                    target = b[dest]
                    if target == '.':
                        moves.append((sq, dest, False))
                    elif target.isupper() != white:
                        moves.append((sq, dest, True))
                        break
                    else:
                        break
                    if not rays:
                        break
                    dest += d
    return moves

def negamax(b, depth, alpha, beta, white):
    if depth == 0:
        val = eval_pos(b)
        return (val if white else -val), None

    moves = gen_simple_moves(b, white)
    if not moves:
        return (eval_pos(b) if white else -eval_pos(b)), None

    moves.sort(key=lambda m: (m[2], PIECE_VALS.get(b[m[1]].upper(), 0)), reverse=True)

    best_score = -999999
    best_move = None
    for s1, s2, is_cap in moves:
        m_uci = sq_to_uci(s1) + sq_to_uci(s2)
        nb = apply_move(b, m_uci)
        score, _ = negamax(nb, depth - 1, -beta, -alpha, not white)
        score = -score
        if score > best_score:
            best_score = score
            best_move = m_uci
        alpha = max(alpha, score)
        if alpha >= beta:
            break
    return best_score, best_move

def choose_move(fen, legal_moves):
    b, turn = parse_fen(fen)
    white = (turn == 'w')
    
    best_val = -999999
    best_uci = legal_moves[0] if legal_moves else ""
    
    def move_priority(m):
        s2 = uci_to_sq(m[2:4])
        victim = b[s2]
        return PIECE_VALS.get(victim.upper(), 0) if victim not in '. ' else 0

    sorted_legal = sorted(legal_moves, key=move_priority, reverse=True)

    for m in sorted_legal:
        nb = apply_move(b, m)
        score, _ = negamax(nb, 2, -999999, 999999, not white)
        score = -score
        if score > best_val:
            best_val = score
            best_uci = m

    return best_uci

def play_all(env_url=None):
    url = env_url or os.environ.get("MAKEFUN_ENV_URL")
    if not url:
        return
    
    def post(path, body):
        req = urllib.request.Request(
            url + path,
            data=json.dumps(body).encode(),
            headers={"content-type": "application/json"}
        )
        with urllib.request.urlopen(req) as res:
            return json.load(res)

    while True:
        g = post("/game", {})
        if g.get("status") == "done":
            break
        while g.get("status") == "your_move":
            mv = choose_move(g["fen"], g["legal_moves"])
            g = post("/move", {"game": g["game"], "move": mv})
        if g.get("status") == "over":
            continue
        break

if __name__ == "__main__":
    play_all()
