SRC_IMAGES = '/content/dataset/images'       # path to your images folder
SRC_LABELS = '/content/dataset/labels'       # path to your labels folder
DEST_DIR   = '/content/dataset_split'         # output will have train/val/test subfolders
TRAIN_RATIO = 0.8
VAL_RATIO   = 0.1
TEST_RATIO  = 0.1
RANDOM_SEED = 42
import os, shutil, random
from tqdm import tqdm

IMAGE_EXTS = {'.jpg', '.jpeg', '.png'}
files = [f for f in os.listdir(SRC_IMAGES) if os.path.splitext(f)[1].lower() in IMAGE_EXTS]

files.sort()
random.seed(RANDOM_SEED)
random.shuffle(files)

n = len(files)
n_train = int(n * TRAIN_RATIO)
n_val   = int(n * VAL_RATIO)
train_files = files[:n_train]
val_files   = files[n_train:n_train + n_val]
test_files  = files[n_train + n_val:]

splits = {
    "train": train_files,
    "val":   val_files,
    "test":  test_files
}

for split_name, split_list in splits.items():
    out_img_dir = os.path.join(DEST_DIR, split_name, "images")
    out_lbl_dir = os.path.join(DEST_DIR, split_name, "labels")
    os.makedirs(out_img_dir, exist_ok=True)
    os.makedirs(out_lbl_dir, exist_ok=True)

    for fn in tqdm(split_list, desc=split_name):
        base, ext = os.path.splitext(fn)
        shutil.copy2(os.path.join(SRC_IMAGES, fn), os.path.join(out_img_dir, fn))
        lbl_file = base + ".txt"
        lbl_src  = os.path.join(SRC_LABELS, lbl_file)
        if os.path.exists(lbl_src):
            shutil.copy2(lbl_src, os.path.join(out_lbl_dir, lbl_file))

print("✅ Done!")
print("Counts:", {k: len(v) for k,v in splits.items()})
