"""Step 3: train the chess model.

    python train.py 2      # quick test on 2 training files (1 million positions)
    python train.py        # full run on all training files

Saves the best model to models/policy.keras.
"""
import glob, os, sys

os.environ.setdefault("KERAS_BACKEND", "torch")    # Keras running on PyTorch (uses the Mac GPU)
import keras
import numpy as np
from keras import layers

BATCH, EPOCHS = 1024, 2
train_files = sorted(glob.glob("data/processed/train_*.npz"))
train_files = train_files[:int(sys.argv[1])] if len(sys.argv) > 1 else train_files
val_files = sorted(glob.glob("data/processed/val_*.npz"))


def planes(d, i):
    """Rows i of a shard -> network input (B, 8, 8, 17): 12 piece grids, 4 castling, 1 en passant."""
    pieces = np.eye(13, dtype="float32")[d["squares"][i]][..., 1:]
    castle = np.repeat(((d["castling"][i][:, None] >> np.arange(4)) & 1)[:, None, :], 64, axis=1)
    ep = np.eye(65, dtype="float32")[d["ep"][i] + 1][:, 1:, None]
    return np.concatenate([pieces, castle.astype("float32"), ep], axis=-1).reshape(-1, 8, 8, 17)


def stream(files, shuffle):
    """Endless batches of (positions, move labels), one file in memory at a time."""
    while True:
        for f in np.random.permutation(files) if shuffle else files:
            d = dict(np.load(f))
            order = np.random.permutation(len(d["move"])) if shuffle else np.arange(len(d["move"]))
            for s in range(0, len(order), BATCH):
                i = order[s:s + BATCH]
                yield planes(d, i), d["move"][i].astype("int64")


def steps(files):
    return sum(-(-len(np.load(f)["move"]) // BATCH) for f in files)


def conv(x, channels, size, relu=True):
    x = layers.BatchNormalization()(layers.Conv2D(channels, size, padding="same", use_bias=False)(x))
    return layers.ReLU()(x) if relu else x


inputs = keras.Input((8, 8, 17))
x = conv(inputs, 128, 3)
for _ in range(6):                                              # 6 residual blocks
    x = layers.ReLU()(layers.Add()([x, conv(conv(x, 128, 3), 128, 3, relu=False)]))
outputs = layers.Dense(4096)(layers.Flatten()(conv(x, 32, 1)))  # one score per move label
model = keras.Model(inputs, outputs)

model.compile(
    optimizer=keras.optimizers.AdamW(keras.optimizers.schedules.CosineDecay(1e-3, steps(train_files) * EPOCHS, alpha=0.05)),
    loss=keras.losses.SparseCategoricalCrossentropy(from_logits=True),
    metrics=["accuracy"],
)
os.makedirs("models", exist_ok=True)
model.fit(
    stream(train_files, True), steps_per_epoch=steps(train_files), epochs=EPOCHS,
    validation_data=stream(val_files, False), validation_steps=steps(val_files),
    callbacks=[keras.callbacks.ModelCheckpoint("models/policy.keras", monitor="val_accuracy", save_best_only=True)],
)
