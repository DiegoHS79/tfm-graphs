import contextily as cx
import folium as fl

import geopandas as gpd
import libpysal as psl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from folium.plugins import MarkerCluster
from matplotlib.patches import Ellipse, Patch
from mpl_toolkits.axes_grid1 import make_axes_locatable
from pointpats import (
    centrography,
    distance_statistics,
    QStatistic,
    random,
    PointPattern,
)


def graph_plot(
    df, df2, area1, area2, surtidor="Gasolineras", ccaa="Comunitat Valenciana"
):
    if surtidor == "Gasolineras":
        dfa = df
        dfb = df2
        a_color = "black"
        b_color = "green"
        legend = ["Gasolineras", "Electrolineras"]
    elif surtidor == "Electrolineras":
        dfa = df2
        dfb = df
        a_color = "green"
        b_color = "black"
        legend = ["Electrolineras", "Gasolineras"]

    if ccaa == "Canarias":
        area = area2
    else:
        area = area1

    ax = sns.scatterplot(
        data=dfa,
        x="longitude",
        y="latitude",
        c=a_color,
        marker="o",
        alpha=0.5,
        # linewidth=0,
    )
    ax = sns.scatterplot(
        data=dfb,
        x="longitude",
        y="latitude",
        c=b_color,
        ax=ax,
        marker=".",
        alpha=0.5,
        # linewidth=0,
    )
    x_lim = ax.get_xlim()
    y_lim = ax.get_ylim()

    ax_aer = area.plot(ax=ax, facecolor="none", edgecolor="grey", linewidth=1.0)
    ax_aer.set_xlim(x_lim)
    ax_aer.set_ylim(y_lim)

    plt.legend(title="Surtidor", loc="upper left", labels=legend)
    cx.add_basemap(
        ax,
        crs="EPSG:4326",
        source=cx.providers.CartoDB.PositronNoLabels,
    )

    return ax


def sp_plot(df, df2, surtidor="Gasolineras"):
    if surtidor == "Gasolineras":
        df_sp = df
    elif surtidor == "Electrolineras":
        df_sp = df2

    locations = list(zip(df_sp.latitude, df_sp.longitude))

    f = fl.Figure(width=800, height=800)
    m = fl.Map(
        location=[40.40536297347694, -3.687868897257778],
        zoom_start=7,
        control_scale=True,
    ).add_to(f)

    marker_cluster = MarkerCluster(locations)
    marker_cluster.add_to(m)

    return m


def dot_density_plot(
    df,
    df2,
    map_type,
    surtidor="Gasolineras",
    zone="peninsula",
    area=None,
    densidad="no",
):
    if surtidor == "Gasolineras":
        df_p = df
        c = "black"
    elif surtidor == "Electrolineras":
        df_p = df2
        c = "darkgreen"

    if map_type == "Distribución espacial":
        if zone in ["peninsula", "ccaa"]:
            ybin = 80
        elif zone == "islas":
            ybin = 30

        ver = 18
        hor = ver * 1.2
        fig, axs = plt.subplots(
            2,
            2,
            figsize=(hor, ver),
            gridspec_kw={
                "hspace": 0,
                "wspace": 0,
                "width_ratios": [5, 1],
                "height_ratios": [1, 5],
            },
        )

        axs[0, 0].axis("off")
        axs[0, 1].axis("off")
        axs[1, 1].axis("off")

        axs[1, 0].scatter(
            df_p.loc[:, "longitude"], df_p.loc[:, "latitude"], s=5, c=c, alpha=0.5
        )
        axs[1, 0].set_xlabel("Longitude")
        axs[1, 0].set_ylabel("Latitude")

        axv = sns.histplot(
            df_p.loc[:, "longitude"], bins=80, ax=axs[0, 0], color="LightBlue", kde=True
        )
        axh = sns.histplot(
            y=df_p.loc[:, "latitude"],
            bins=ybin,
            ax=axs[1, 1],
            color="LightBlue",
            kde=True,
        )

    elif map_type == "Mapa de calor":
        fig, ax = plt.subplots(1)
        hb = ax.hexbin(
            df_p.longitude,
            df_p.latitude,
            gridsize=100,
            linewidths=0,
            alpha=0.5,
            cmap="magma_r",
        )
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        cx.add_basemap(ax, crs="EPSG:4326", source=cx.providers.CartoDB.Voyager)
        # divider = make_axes_locatable(ax)
        # cax = divider.append_axes("right", size="5%", pad=0.05)
        # cbar = plt.colorbar(hb, cax=cax)
        # cbar.ax.set_ylabel("Gasolineras", rotation=-90, va="bottom")

    elif map_type == "Densidad 'kernel'":
        fig, ax = plt.subplots(1)
        sns.kdeplot(
            x="longitude",
            y="latitude",
            data=df_p,
            n_levels=50,
            fill=True,
            alpha=0.25,
            cmap="viridis",
        )
        cx.add_basemap(ax, crs="EPSG:4326", source=cx.providers.CartoDB.Voyager)

    if densidad == "si":
        if surtidor == "Electrolineras":
            indices = area[
                (area.NAMEUNIT == "ceuta") | (area.NAMEUNIT == "melilla")
            ].index
            area.loc[indices, "electrolineras"] = 0.0

        surtidores = df_p.groupby("province").size()
        area = area.join(pd.DataFrame({"surtidores": surtidores}), on="NAMEUNIT")

        fig, ax = plt.subplots(1)
        area.plot(
            column="surtidores",
            scheme="quantiles",
            ax=ax,
            legend=True,
            legend_kwds={"loc": 4},
        )
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        cx.add_basemap(ax, crs="EPSG:4326", source=cx.providers.CartoDB.DarkMatter)

    return fig


def centrality_plot(df, df2, area1, area2, surtidor="Gasolineras", province="alicante"):
    if surtidor == "Gasolineras":
        df_sp = df
    elif surtidor == "Electrolineras":
        df_sp = df2

    if province in ["santa cruz de tenerife", "palmas (las)"]:
        area = area2
    else:
        area = area1

    mean_center = centrography.mean_center(df_sp[["longitude", "latitude"]])
    med_center = centrography.euclidean_median(df_sp[["longitude", "latitude"]])
    major, minor, rotation = centrography.ellipse(df_sp[["longitude", "latitude"]])

    coordinates = df_sp[["longitude", "latitude"]].values
    convex_hull_vertices = centrography.hull(coordinates)
    alpha_shape, alpha, circs = psl.cg.alpha_shape_auto(
        coordinates, return_circles=True
    )

    fig, ax = plt.subplots(1)

    ax.scatter(df_sp.longitude, df_sp.latitude, s=2.0, c="black", alpha=0.5)

    ax.scatter(*med_center, color="limegreen", marker="o", s=50, label="Median Center")
    ax.scatter(*mean_center, color="red", marker="x", s=50.0, label="Mean Center")

    ellipse = Ellipse(
        xy=mean_center,
        width=major * 2,
        height=minor * 2,
        angle=np.rad2deg(rotation),
        facecolor="none",
        edgecolor="red",
        linestyle="--",
        label="Std. Ellipse",
    )
    ax.add_patch(ellipse)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    ax.add_patch(
        plt.Polygon(
            convex_hull_vertices,
            closed=True,
            edgecolor="blue",
            facecolor="none",
            linestyle=":",
            linewidth=2,
            label="Convex Hull",
        )
    )

    x_lim = ax.get_xlim()
    y_lim = ax.get_ylim()

    gpd.GeoSeries([alpha_shape]).plot(
        ax=ax,
        edgecolor="green",
        facecolor="green",
        alpha=0.2,
        label="Tightest single alpha shape",
    )

    ax_aer = area.plot(ax=ax, facecolor="none", edgecolor="grey", linewidth=1.0)
    ax_aer.set_xlim(x_lim)
    ax_aer.set_ylim(y_lim)

    handles, labels = plt.gca().get_legend_handles_labels()
    handles.extend(
        [Patch(facecolor="g", edgecolor="g", label="Alpha shape", alpha=0.2)]
    )
    ax.legend(handles=handles, loc="upper left")

    cx.add_basemap(ax, crs="EPSG:4326", source=cx.providers.CartoDB.Voyager)

    return fig


def random_plot(df, pattern=False, n=9):
    #! https://pysal.org/notebooks/explore/pointpats/Quadrat_statistics.html
    #! https://pysal.org/pointpats/_modules/pointpats/quadrat_statistics.html#QStatistic.plot

    coordinates = df[["longitude", "latitude"]].values
    random_pattern = random.poisson(coordinates, size=len(coordinates))

    if pattern:
        qstat = QStatistic(random_pattern, nx=n, ny=n)
    else:
        qstat = QStatistic(coordinates, nx=n, ny=n)

    return qstat
