import shutil
from bokeh.plotting import output_file, show
from bokeh.layouts import column
import pandas as pd
from tqdm import tqdm

from modules import report, maps


def dashboard(METADATA_PATH, PBAR):
    """
    Generates an HTML file with dashboard and map using bokeh
    """

    try:

        PBAR.set_description("Updating Report")
        hbar = report.update_hbar(METADATA_PATH)
        # pie = report.update_pie(METADATA_PATH)
        PBAR.update(5)

        PBAR.set_description("Updating Map")
        map_plot = maps.update(METADATA_PATH)
        PBAR.update(25)

        # export
        output_file("./index.html", title="Situated Views")
        show(column(hbar, map_plot), sizing_mode="stretch_both")

    except Exception as e:
        print(str(e))


def omeka_csv():
    pass


def commons_csv(METADATA_PATH, copy_to):
    final_df = pd.read_csv(METADATA_PATH)
    commons_df = pd.DataFrame(
        final_df[
            final_df["geometry"].notna()
            & final_df["img_hd"].notna()
            & final_df["wikidata_image"].isna()
        ]
    )

    for id in commons_df["id"]:
        shutil.copy2(f"./images/jpeg-hd/{id}.jpg", copy_to)


# commons_csv("./metadata/metadata.csv", "/Users/martimpassos/Pictures/Commons")
