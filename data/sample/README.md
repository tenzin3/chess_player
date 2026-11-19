# Sample data

This folder shows what the data looks like at both stages of the pipeline,
using **the same game** in both files, so you can compare them side by side.

| File | Stage | What it is |
|---|---|---|
| `raw_sample.pgn` | Raw (before preparing) | One game exactly as it appears in the downloaded Lichess file |
| `sample.csv` | Prepared (after `prepare.py`) | The first 20 moves of that game, as training rows |

The full data is not in git because of its size:

| | Raw data | Prepared data |
|---|---|---|
| Location | `data/raw/` | `data/processed/` |
| File | `lichess_db_standard_rated_2016-05.pgn.zst` | `train_0000.npz` ... `train_0059.npz`, `val_0000.npz`, `val_0001.npz` |
| Size | 1.11 GB compressed (5.37 GB unzipped) | 2.0 GB |
| Contents | 6,225,957 games, all ratings and speeds | 30,292,884 rows (one per move) from 394,229 games |
| Format | PGN text, compressed with Zstandard | NumPy arrays (`.npz`) |
| Made by | Downloaded from https://database.lichess.org | `python prepare.py` |

The game in the sample is https://lichess.org/SamItqBO, a blitz game from
30 April 2016 between a 2015-rated White and a 2276-rated Black, which Black
won. It is the first game in the validation set.

## Stage 1: raw data (`raw_sample.pgn`)

Lichess publishes every rated game as PGN, the standard text format for chess
games. Each game is a block of header lines followed by the moves:

```
[Event "Rated Blitz game"]
[Site "https://lichess.org/SamItqBO"]
[White "mpai3player"]
[Black "bigwh"]
[Result "0-1"]
[WhiteElo "2015"]
[BlackElo "2276"]
[TimeControl "180+2"]
[Termination "Normal"]
...

1. e4 c5 2. Nc3 e6 3. d4 cxd4 4. Qxd4 Nc6 ... 36. Qg4 d1=Q 0-1
```

| Header | Meaning | Used by `prepare.py`? |
|---|---|---|
| `Event` | Kind of game (Bullet, Blitz, Classical ...) | No |
| `Site` | The game's web address | Yes, to decide train or validation |
| `White`, `Black` | Usernames | No (dropped) |
| `Result` | `1-0` White won, `0-1` Black won, `1/2-1/2` draw | Yes, filter and `result` column |
| `UTCDate`, `UTCTime` | When the game was played | No |
| `WhiteElo`, `BlackElo` | Ratings before the game | Yes, filter (both 2000+) |
| `WhiteRatingDiff`, `BlackRatingDiff` | Rating change after the game | No |
| `ECO`, `Opening` | Opening code and name | No |
| `TimeControl` | Seconds per player + seconds added per move | Yes, filter (no bullet) |
| `Termination` | How it ended (`Normal`, `Time forfeit`, `Abandoned`) | Yes, filter |

The moves are in standard algebraic notation: `e4` a pawn to e4, `Nf3` a
knight to f3 (N knight, B bishop, R rook, Q queen, K king), `x` a capture,
`O-O` castling, `+` check, `=Q` promotion to a queen.

## Stage 2: prepared data (`sample.csv`)

`prepare.py` keeps only games where both players are rated 2000+, the game is
blitz or slower, it ended normally, there is no bot, and it lasted at least 20
half-moves. It then replays each kept game and writes **one row per move**:
the position just before the move, and the move that was played. This is what
the model trains on: "in this position, a strong player chose this move".

The game above has 72 half-moves, so it becomes 72 rows. `sample.csv` shows
the first 20.

The real prepared files store every value as a number to save space. For
`sample.csv` those numbers have been converted to readable text, and three
helper columns have been added.

### Columns

| Column | Example | Meaning | Why it is there |
|---|---|---|---|
| `ply` | `2` | Move number, counting White's and Black's moves separately | Helper, to follow the game. Not in the training files |
| `side_to_move` | `black` | Who is about to move | Helper. Not in the training files |
| `real_move` | `c7c5` | The move as played on the real board, from-square then to-square | Helper, to compare with the PGN. Not in the training files |
| `board` | `rnbqkbnr/pppp.ppp/...` | The position before the move, from the side to move's view (see below) | **Model input.** The pieces |
| `castling` | `KQkq` | Which castling moves are still allowed: `K`/`Q` the side to move (kingside/queenside), `k`/`q` the opponent, `-` none | **Model input.** Castling rights depend on earlier moves and cannot be seen from the pieces alone |
| `en_passant` | `e6` | After a pawn moves two squares, the square it skipped over, else `-`. Filled in even if no enemy pawn can capture | **Model input.** Also depends on the previous move |
| `move` | `c2c4` | The move from the side to move's view | **Model target.** What the model learns to predict |
| `promotion` | `-` | Piece a pawn promotes to (`n`, `b`, `r`, `q`), or `-` | Kept because the `move` label cannot tell promotions apart |
| `move_label` | `666` | The `move` as a number: from-square x 64 + to-square, with a1 = 0, b1 = 1 ... h8 = 63 | **Model target.** The network outputs 4,096 scores, one per label |
| `result` | `1` | How the game ended for the side to move: `1` won, `0` draw, `-1` lost | Not used yet. For a future model that also judges positions |

### Reading the `board` column

The board is 64 characters, one per square, written **rank 8 first** and
**a to h** within each rank, with `/` between ranks:

| Character | Meaning |
|---|---|
| `.` | **Empty square** |
| `P N B R Q K` (UPPERCASE) | The side to move's pawn, knight, bishop, rook, queen, king |
| `p n b r q k` (lowercase) | The opponent's pieces |

Every rank always has exactly 8 characters, with a dot for each empty square,
so you can read any square by its position.

Row 1, White to move in the starting position:

```
rnbqkbnr/pppppppp/......../......../......../......../PPPPPPPP/RNBQKBNR

8  r n b q k b n r
7  p p p p p p p p
6  . . . . . . . .
5  . . . . . . . .
4  . . . . . . . .
3  . . . . . . . .
2  P P P P P P P P
1  R N B Q K B N R
   a b c d e f g h
```

### Why Black's rows look flipped

The board is always shown from the side to move, with that side in UPPERCASE
at the bottom. When Black is to move, the board is turned upside down, so the
model learns one set of patterns instead of separate ones for White and Black.

Row 2, after 1. e4, Black to move:

```
rnbqkbnr/pppp.ppp/......../....p.../......../......../PPPPPPPP/RNBQKBNR

8  r n b q k b n r      White's pieces, now at the top
7  p p p p . p p p
6  . . . . . . . .
5  . . . . p . . .      White's e4 pawn, seen from Black's side
4  . . . . . . . .
3  . . . . . . . .
2  P P P P P P P P      Black's pieces, now at the bottom
1  R N B Q K B N R
```

Black played `c7c5` on the real board. Flipped, that is `c2c4`, so `move`
is `c2c4` and `move_label` is 10 x 64 + 26 = 666. The `real_move` column
shows the original `c7c5` for comparison. The `en_passant` value `e6` is the
square White's pawn skipped over (e3), flipped.

### How the real training files store the same row

| `sample.csv` column | Stored in the `.npz` files as |
|---|---|
| `board` | 64 numbers: 0 empty, 1-6 the side to move's P N B R Q K, 7-12 the opponent's |
| `castling` | One number, 0-15, one bit per castling right |
| `en_passant` | Square number 0-63, or -1 |
| `move` / `move_label` | `move_label` only |
| `promotion` | 0, or 2-5 for N B R Q |
| `result` | 1, 0 or -1 |

During training these are expanded into the 17 grids of 8 x 8 that the
network reads.
