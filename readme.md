# Chess Player

A small project for exploring chess data and building insights from real games.

## Overview

This repository is centered around the Lichess open database, which is published monthly at [database.lichess.org](https://database.lichess.org/). Lichess makes every rated game from its platform available for free, making it an excellent source for chess analysis, experimentation, and learning.

The project currently focuses on a manageable sample of that dataset so it is easy to work with locally while still having enough games to explore meaningful patterns.

## Dataset

The initial dataset chosen is:

- Source: Lichess open database
- Month: May 2016
- Size: approximately 1.11 GB
- Games: around 6 million

### Why this dataset?

The May 2016 snapshot was selected for a few practical and personal reasons:

- 2016 was the year the Golden State Warriors won 73 games in a single NBA season, which made it a memorable year.
- May is the month of the author's birth.
- 1.11 GB is a reasonable starting point: large enough to be interesting, but still small enough for local experimentation.

## Data preparation

`prepare.py` turns the raw file into training data. It reads the compressed
file directly, keeps games between strong players, and writes one row per move:
the position before the move (from the side of the player to move) and the
move that was played.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python prepare.py
```

### Filters

A game is kept only if:

- both players are rated 2000 or higher
- it is blitz speed or slower (base time + 40 x increment is at least 180 seconds)
- it has a normal result, no bot player, and was not abandoned
- it lasted at least 20 half-moves

There is no cap on the number of positions: the whole month is used.

### Result

Run on 2026-11-11.

| | |
|---|---|
| Games scanned | 6,225,957 |
| Games kept | 394,229 (6.3%) |
| Training positions | 29,689,066 in 60 files (`train_0000.npz` to `train_0059.npz`) |
| Validation positions | 603,818 in 2 files (`val_0000.npz`, `val_0001.npz`) |
| Total positions | 30,292,884 (about 77 per game) |
| Size on disk | 2.0 GB in `data/processed` |

Whole games go to either training or validation (2% of games), never both.

The log shows 2,568 seconds, but the run stalled for about 23 minutes between
the 1.6M and 1.8M lines (most likely the laptop went to sleep). The actual
processing time was about 20 minutes.

### Output

<details>
<summary>Full output of <code>python prepare.py</code></summary>

```
200000 games scanned, 12550 kept, 967078 positions, 39s
400000 games scanned, 24587 kept, 1890971 positions, 75s
600000 games scanned, 36086 kept, 2768191 positions, 111s
800000 games scanned, 48389 kept, 3702472 positions, 148s
1000000 games scanned, 60936 kept, 4673043 positions, 187s
1200000 games scanned, 72528 kept, 5561029 positions, 223s
1400000 games scanned, 84397 kept, 6463989 positions, 259s
1600000 games scanned, 97424 kept, 7468575 positions, 300s
1800000 games scanned, 110466 kept, 8463291 positions, 1685s
2000000 games scanned, 122884 kept, 9407099 positions, 1721s
2200000 games scanned, 135806 kept, 10391840 positions, 1760s
2400000 games scanned, 148401 kept, 11361420 positions, 1799s
2600000 games scanned, 160907 kept, 12316883 positions, 1837s
2800000 games scanned, 173508 kept, 13273272 positions, 1876s
3000000 games scanned, 185948 kept, 14239049 positions, 1914s
3200000 games scanned, 199245 kept, 15267336 positions, 1956s
3400000 games scanned, 212512 kept, 16295498 positions, 1997s
3600000 games scanned, 226005 kept, 17332104 positions, 2039s
3800000 games scanned, 239047 kept, 18342239 positions, 2080s
4000000 games scanned, 251875 kept, 19321455 positions, 2120s
4200000 games scanned, 264687 kept, 20302739 positions, 2160s
4400000 games scanned, 277867 kept, 21319417 positions, 2201s
4600000 games scanned, 289811 kept, 22237294 positions, 2239s
4800000 games scanned, 302305 kept, 23202870 positions, 2278s
5000000 games scanned, 314829 kept, 24168990 positions, 2318s
5200000 games scanned, 327529 kept, 25151538 positions, 2359s
5400000 games scanned, 340673 kept, 26163102 positions, 2400s
5600000 games scanned, 353243 kept, 27130922 positions, 2439s
5800000 games scanned, 365732 kept, 28102184 positions, 2479s
6000000 games scanned, 378972 kept, 29120883 positions, 2520s
6200000 games scanned, 392519 kept, 30161940 positions, 2562s
{
  "files": [
    "lichess_db_standard_rated_2016-05.pgn.zst"
  ],
  "games_scanned": 6225957,
  "games_kept": 394229,
  "train_positions": 29689066,
  "val_positions": 603818,
  "min_elo": 2000,
  "min_seconds": 180,
  "min_plies": 20
}
Done in 2568s
```

</details>
