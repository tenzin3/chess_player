"""Step 2: turn the raw Lichess file into training data.

    python prepare.py

Reads every .pgn.zst file in data/raw, keeps games between strong players and
writes one row per move into data/processed/train_0000.npz, ..., val_0000.npz.
Each row is a position (from the side of the player to move) and the move played.
"""
import glob, io, json, os, re, time, zlib

import chess, chess.pgn
import numpy as np
import zstandard

RAW, OUT = "data/raw", "data/processed"
MIN_ELO = 2000             # both players at least this rating
MIN_SECONDS = 180          # base time + 40 x increment; 180 removes bullet games
MIN_PLIES = 20             # skip very short games
SHARD_SIZE = 500_000       # rows per output file
VAL_PERCENT = 2            # share of games held back for validation

HEADER = re.compile(r'^\[(\w+) "(.*)"\]$')
RESULT = {"1-0": 1, "0-1": -1, "1/2-1/2": 0}   # from White's side


def games(path):
    """Yield (headers, full text) for each game, without parsing the moves yet."""
    raw = zstandard.ZstdDecompressor(max_window_size=2**31).stream_reader(open(path, "rb"))
    headers, lines = {}, []
    for line in io.TextIOWrapper(raw, encoding="utf-8", errors="replace"):
        if line.startswith("[Event ") and lines:
            yield headers, "".join(lines)
            headers, lines = {}, []
        match = HEADER.match(line.rstrip())
        if match:
            headers[match.group(1)] = match.group(2)
        lines.append(line)
    if headers:
        yield headers, "".join(lines)


def keep(h):
    """The filter: strong players, not bullet, a normal finish, no bots."""
    elo = [int(h.get(k, "0")) if h.get(k, "").isdigit() else 0 for k in ("WhiteElo", "BlackElo")]
    try:
        base, inc = h.get("TimeControl", "").split("+")
        seconds = int(base) + 40 * int(inc)
    except ValueError:
        return False
    return (h.get("Result") in RESULT and min(elo) >= MIN_ELO and seconds >= MIN_SECONDS
            and "BOT" not in (h.get("WhiteTitle"), h.get("BlackTitle"))
            and h.get("Termination") not in ("Abandoned", "Rules infraction"))


def encode(board, move):
    """One training row. The board is flipped when Black is to move."""
    b = board if board.turn else board.mirror()
    squares = np.zeros(64, np.int8)      # 0 empty, 1-6 my P N B R Q K, 7-12 theirs
    for sq, piece in b.piece_map().items():
        squares[sq] = piece.piece_type + (0 if piece.color else 6)
    castling = (b.has_kingside_castling_rights(True) | b.has_queenside_castling_rights(True) << 1
                | b.has_kingside_castling_rights(False) << 2 | b.has_queenside_castling_rights(False) << 3)
    f, t = move.from_square, move.to_square
    if not board.turn:
        f, t = chess.square_mirror(f), chess.square_mirror(t)
    ep = -1 if b.ep_square is None else b.ep_square
    return squares, castling, ep, f * 64 + t, move.promotion or 0   # label = from * 64 + to


class Writer:
    """Collects rows and saves them in files (shards) of SHARD_SIZE rows."""
    types = {"squares": np.int8, "castling": np.uint8, "ep": np.int8,
             "move": np.int16, "promo": np.int8, "result": np.int8}

    def __init__(self, name):
        self.name, self.rows, self.files, self.total = name, [], 0, 0

    def add(self, row):
        self.rows.append(row)
        self.total += 1
        if len(self.rows) == SHARD_SIZE:
            self.save()

    def save(self):
        if self.rows:
            columns = {k: np.array(col, dtype=t) for (k, t), col in zip(self.types.items(), zip(*self.rows))}
            np.savez(os.path.join(OUT, "%s_%04d.npz" % (self.name, self.files)), **columns)
            self.rows, self.files = [], self.files + 1


def main():
    files = sorted(glob.glob(os.path.join(RAW, "*.pgn.zst")))
    assert files, "No .pgn.zst file in data/raw"
    assert not glob.glob(os.path.join(OUT, "*.npz")), "data/processed already has shards; move them first"
    os.makedirs(OUT, exist_ok=True)
    train, val = Writer("train"), Writer("val")
    scanned = kept = 0
    start = time.time()
    for path in files:
        for headers, text in games(path):
            scanned += 1
            if scanned % 200_000 == 0:
                print("%d games scanned, %d kept, %d positions, %.0fs" % (
                    scanned, kept, train.total + val.total, time.time() - start), flush=True)
            if not keep(headers):
                continue
            game = chess.pgn.read_game(io.StringIO(text))
            moves = list(game.mainline_moves()) if game and not game.errors else []
            if len(moves) < MIN_PLIES:
                continue
            # whole games go to train or validation, decided from the game's URL
            writer = val if zlib.crc32(headers.get("Site", "").encode()) % 100 < VAL_PERCENT else train
            board, white_result = game.board(), RESULT[headers["Result"]]
            for move in moves:
                writer.add(encode(board, move) + (white_result if board.turn else -white_result,))
                board.push(move)
            kept += 1
    train.save()
    val.save()
    summary = {"files": [os.path.basename(f) for f in files], "games_scanned": scanned, "games_kept": kept,
               "train_positions": train.total, "val_positions": val.total,
               "min_elo": MIN_ELO, "min_seconds": MIN_SECONDS, "min_plies": MIN_PLIES}
    json.dump(summary, open(os.path.join(OUT, "meta.json"), "w"), indent=2)
    print(json.dumps(summary, indent=2))
    print("Done in %.0fs" % (time.time() - start))


if __name__ == "__main__":
    main()
