import io
from datetime import timedelta, timezone

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.dates import DateFormatter
from PIL import Image

pd.plotting.register_matplotlib_converters()


def generate_graph(df):
    types = df["type"].unique()
    num_types = len(types)
    print("Total type count: %s" % num_types)
    print("Selected type is: %s" % types)

    fig = plt.figure(figsize=(8, 4 * num_types), dpi=192)
    sns.set()
    sns.set(rc={"lines.linewidth": 3, "grid.linestyle": "--"},)

    fig_count = 1
    ax = {}
    for type in types:
        print("Generate graph for: %s" % type)
        filtered_df = df[df["type"] == type]

        ax[type] = fig.add_subplot(num_types, 1, fig_count)
        ax[type].xaxis.set_major_formatter(
            DateFormatter("%H:%M", tz=timezone(timedelta(hours=+9), "JST"))
        )
        ax[type].plot(filtered_df.index, filtered_df["value"], label=type)
        ax[type].legend()
        ax[type].set_title(type)
        fig_count += 1

    print("Save as binary data")
    png = io.BytesIO()
    plt.savefig(png, format="png")
    plt.close("all")
    png.seek(0)

    return generate_thumb(png, 240)


def generate_thumb(img, max):
    print("Generate thumbnail of graph")

    pil = Image.open(img)
    pil = pil.convert("RGB")
    print("Original size: %s x %s" % (pil.size[0], pil.size[1]))

    fullsize = pil.copy()
    fulljpg = io.BytesIO()
    fullsize.save(fulljpg, "jpeg")
    fulljpg.seek(0)

    pil.thumbnail((max, max), Image.ANTIALIAS)
    thumbjpg = io.BytesIO()
    pil.save(thumbjpg, "jpeg")
    thumbjpg.seek(0)

    return {
        "full": fulljpg,
        "thumb": thumbjpg,
    }
