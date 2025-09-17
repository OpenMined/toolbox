# %%

from pathlib import Path

import datasets

ds = datasets.load_dataset("permutans/fineweb-bbc-news", "sample-10BT", split="train")


data_dir = Path(".") / "fineweb-bbc-news"
data_dir.mkdir(exist_ok=True)
n = 5000
leading_zeros = len(str(n))

for i, item in enumerate(ds.select(range(n))):
    fp = data_dir / f"{i:0{leading_zeros}}.txt"
    fp.write_text(item["text"])

# %%
