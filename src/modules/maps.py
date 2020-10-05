import json

import geopandas as gpd
import pandas as pd
from bokeh.models import (
    Circle,
    GeoJSONDataSource,
    HoverTool,
    Legend,
    Patches,
    WheelZoomTool,
)
from bokeh.plotting import figure
from bokeh.tile_providers import Vendors, get_provider
from pyproj import Proj, transform
from shapely import wkt


def update(PATH):
    try:
        # load metadata
        DF = pd.read_csv(PATH)
        DF = DF.dropna(subset=["geometry"])

        # create geodataframe for points with images
        geodf = to_geodf(DF)

        # transform map projection
        map_geodf = apply_transform(geodf)

        # update map
        export_map = update_map(map_geodf)

        return export_map

    except Exception as e:
        print(str(e))


def to_geodf(df):
    """
    Return geodf
    """

    df["geometry"] = df["geometry"].astype(str).apply(wkt.loads)

    geodf = gpd.GeoDataFrame(df, geometry="geometry", crs="epsg:4326")

    return geodf


def transform_proj(row):
    """
    Transforms WGS84(epsg:4326) to WEBMERCATOR(epsg:3857)
    """

    try:
        proj_in = Proj("epsg:4326")
        proj_out = Proj("epsg:3857")
        x1, y1 = row["lat"], row["lng"]
        x2, y2 = transform(proj_in, proj_out, x1, y1)
        # print(f"({x1}, {y1}) to ({x2}, {y2})")
        return pd.Series([x2, y2])

    except Exception as e:
        print(str(e))


def apply_transform(geodf):
    """
    Convert WGS84(epsg:4326) to WEBMERCATOR(epsg:3857) coordinates
    """

    # print("Transforming projections...")
    geodf[["lat2", "lng2"]] = geodf.apply(transform_proj, axis=1)
    # print("Done.")

    geodf["geometry"] = geodf["geometry"].to_crs("epsg:3857")

    # reduce columns and return final geodataframe

    map_geodf = geodf[
        ["id", "title", "creator", "img_sd", "geometry", "lat2", "lng2"]
    ]

    return map_geodf


def update_map(map_geodf):

    # create a geodatasource
    geosource = GeoJSONDataSource(geojson=map_geodf.to_json())

    # Description from points
    TOOLTIPS = """
        <div style="margin: 5px; width: 300px" >
        <img
            src="@img_sd" alt="@img_sd" height=200
            style="margin: 0px;"
            border="2"
            ></img>
            <h3 style='font-size: 10px; font-weight: bold;'>@id</h3>
            <p style='font-size: 10px; font-weight: light; font-style: italic;'>@creator</p>
        
        </div>
    """

    # Base map
    maps = figure(
        x_axis_type="mercator",
        y_axis_type="mercator",
        plot_width=1400,
        plot_height=900,
        toolbar_location=None,
    )

    tile_provider = get_provider(Vendors.CARTODBPOSITRON_RETINA)
    maps.add_tile(tile_provider)

    # construct points and wedges from hover
    viewcone = maps.patches(
        xs="xs",
        ys="ys",
        source=geosource,
        fill_color="white",
        fill_alpha=0,
        line_color=None,
        hover_alpha=0.7,
        hover_fill_color="grey",
        hover_line_color="grey",
    )

    point = maps.circle(
        x="lat2",
        y="lng2",
        source=geosource,
        size=7,
        fill_color="orange",
        fill_alpha=0.5,
        line_color="dimgray"
    )

    # create a hovertool
    h1 = HoverTool(renderers=[viewcone], tooltips=None, mode="mouse", show_arrow=False)
    h2 = HoverTool(renderers=[point], tooltips=TOOLTIPS, mode="mouse", show_arrow=False)

    maps.add_tools(h1, h2)
    maps.toolbar.active_scroll = maps.select_one(WheelZoomTool)
    maps.xaxis.major_tick_line_color = None
    maps.xaxis.minor_tick_line_color = None
    maps.yaxis.major_tick_line_color = None
    maps.yaxis.minor_tick_line_color = None
    maps.xaxis.major_label_text_font_size = "0pt"
    maps.yaxis.major_label_text_font_size = "0pt"

    return maps