# Sample data

`sample.csv` shows what the training data looks like: the first 20 moves of
one game from the validation set, one row per move. The real data is in
`data/processed` (30 million rows, `.npz` files, not in git).

## Columns

| Column | Meaning |
|---|---|
| `ply` | Move number counting each side separately (1 = White's first move) |
| `side_to_move` | Who is about to move |
| `real_move` | The move as it was played on the real board, e.g. `e7e5` |
| `board` | The position before the move, **seen from the side to move** (see below) |
| `castling` | Castling still allowed: `K`/`Q` = the side to move (kingside/queenside), `k`/`q` = the opponent, `-` = none |
| `en_passant` | If the previous move was a pawn moving two squares, the square it skipped over (where an en passant capture would land), else `-`. It is filled in even when no pawn is in place to make the capture. |
| `move` | The move from the side to move's point of view (what the model learns) |
| `promotion` | Piece a pawn promotes to (`n`, `b`, `r`, `q`), or `-` |
| `move_label` | The number the model predicts: from-square x 64 + to-square (0-4095), with a1 = 0 and h8 = 63 |
| `result` | How the game ended for the side to move: `1` won, `0` draw, `-1` lost |

`ply`, `side_to_move` and `real_move` are added here only to make the sample
readable; the training files do not store them.

## Reading the board

The board is written rank 8 first, ranks separated by `/`, one character per
square: UPPERCASE = the side to move, lowercase = the opponent, `.` = empty.
Letters: P pawn, N knight, B bishop, R rook, Q queen, K king.

When Black is to move, the board is flipped so Black is at the bottom in
UPPERCASE. That is why Black's first move `e7e5` appears in the `move`
column as `e2e4`: the model always sees the game from the mover's side.

Example, row 1 (White to move, the starting position):

```
r n b q k b n r     rank 8
p p p p p p p p
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
P P P P P P P P
R N B Q K B N R     rank 1
```

White played `e2e4`, label 12 x 64 + 28 = 796. White went on to lose, so
`result` is -1.
