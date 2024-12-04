import contextily as cx
import folium as fl

# import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
from folium.plugins import MarkerCluster, HeatMap


def graph_plot(df, df2, surtidor="Gasolineras"):
    if surtidor == "Gasolineras":
        dfa = df
        dfb = df2
        a_color = "black"
        a_coords = ("longitud", "latitud")
        b_color = "green"
        b_coords = ("longitude", "latitude")
        legend = ["Gasolineras", "Electrolineras"]
    elif surtidor == "Electrolineras":
        dfa = df2
        dfb = df
        a_color = "green"
        a_coords = ("longitude", "latitude")
        b_color = "black"
        b_coords = ("longitud", "latitud")
        legend = ["Electrolineras", "Gasolineras"]

    ax = sns.scatterplot(
        data=dfa,
        x=a_coords[0],
        y=a_coords[1],
        c=a_color,
        marker="o",
        alpha=0.5,
        # linewidth=0,
    )
    ax = sns.scatterplot(
        data=dfb,
        x=b_coords[0],
        y=b_coords[1],
        c=b_color,
        ax=ax,
        marker=".",
        alpha=0.5,
        # linewidth=0,
    )
    plt.legend(title="Surtidor", loc="upper left", labels=legend)
    cx.add_basemap(
        ax,
        crs="EPSG:4326",
        source=cx.providers.CartoDB.PositronNoLabels,
    )

    return ax


def sp_plot(df, df2, surtidor="Gasolineras"):
    if surtidor == "Gasolineras":
        locations = list(zip(df.latitud, df.longitud))
    elif surtidor == "Electrolineras":
        locations = list(zip(df2.latitude, df2.longitude))

    f = fl.Figure(width=800, height=800)
    m = fl.Map(
        location=[40.40536297347694, -3.687868897257778],
        zoom_start=7,
        control_scale=True,
    ).add_to(f)

    marker_cluster = MarkerCluster(locations)
    marker_cluster.add_to(m)
    # HeatMap(locations).add_to(m)

    return m
