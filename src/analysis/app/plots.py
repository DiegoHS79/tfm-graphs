import random as rd

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
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import silhouette_score


colors = [
    "black",
    "grey",
    "lightcoral",
    "red",
    "sienna",
    "peru",
    "orange",
    "green",
    "lime",
    "springgreen",
    "lightseagreen",
    "gold",
    "darkkhaki",
    "aqua",
    "teal",
    "deepskyblue",
    "royalblue",
    "slateblue",
    "darkviolet",
    "magenta",
    "deeppink",
    "crimson",
]

rd.shuffle(colors)


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


def random_plot(df, pattern=False, nx=9, ny=9):
    #! https://pysal.org/notebooks/explore/pointpats/Quadrat_statistics.html
    #! https://pysal.org/pointpats/_modules/pointpats/quadrat_statistics.html#QStatistic.plot

    coordinates = df[["longitude", "latitude"]].values
    random_pattern = random.poisson(coordinates, size=len(coordinates))

    if pattern:
        qstat = QStatistic(random_pattern, nx=nx, ny=ny)
    else:
        qstat = QStatistic(coordinates, nx=nx, ny=ny)

    return qstat


def ripley_plot(df, df2, surtidor="Gasolineras"):
    if surtidor == "Gasolineras":
        df_sp = df
    elif surtidor == "Electrolineras":
        df_sp = df2

    coordinates = df_sp[["longitude", "latitude"]].values
    g_test = distance_statistics.g_test(coordinates, support=40, keep_simulations=True)

    fig, ax = plt.subplots(1, 2, gridspec_kw=dict(width_ratios=(5, 5)))

    # G function ------------------------------------------------------------------------
    ax[0].plot(g_test.support, g_test.simulations.T, color="k", alpha=0.01)
    # and show the average of simulations
    ax[0].plot(
        g_test.support,
        np.median(g_test.simulations, axis=0),
        color="cyan",
        label="median simulation",
    )

    # and the observed pattern's G function
    ax[0].plot(g_test.support, g_test.statistic, label="observed", color="red")

    ax[0].set_xlabel("distance")
    ax[0].set_ylabel("% of nearest neighbor\ndistances shorter")
    ax[0].legend()
    ax[0].set_xlim(0, 0.095)
    ax[0].set_ylim(0, 1.01)
    ax[0].set_title(r"Ripley's $G(d)$ function")

    # F function ------------------------------------------------------------------------
    f_test = distance_statistics.f_test(coordinates, support=40, keep_simulations=True)
    ax[1].plot(f_test.support, f_test.simulations.T, color="k", alpha=0.01)
    # and show the average of simulations
    ax[1].plot(
        f_test.support,
        np.median(f_test.simulations, axis=0),
        color="cyan",
        label="median simulation",
    )

    # and the observed pattern's F function
    ax[1].plot(f_test.support, f_test.statistic, label="observed", color="red")

    ax[1].set_xlabel("distance")
    ax[1].set_ylabel("% of nearest point in pattern\ndistances shorter")
    ax[1].legend()
    ax[1].set_xlim(0, 0.095)
    ax[1].set_ylim(0, 1.01)
    ax[1].set_title(r"Ripley's $F(d)$ function")

    fig.tight_layout()

    return fig


def cluster_plot(
    df,
    df2,
    area1,
    area2,
    groups=8,
    surtidor="Gasolineras",
    state_r=0,
    province="alicante",
):
    if surtidor == "Gasolineras":
        df_sp = df
    elif surtidor == "Electrolineras":
        df_sp = df2

    if province in ["santa cruz de tenerife", "palmas (las)"]:
        area = area2
    else:
        area = area1

    clusterer = KMeans(
        n_clusters=groups,
        random_state=state_r,
        n_init="auto",
    )
    clusterer.fit(df_sp[["latitude", "longitude"]])

    df_prov = df_sp[["latitude", "longitude"]]
    df_prov.loc[:, ["lavels"]] = clusterer.labels_

    fig, ax = plt.subplots(1)

    for k in df_prov.lavels.unique():
        ax.scatter(
            df_prov[df_prov["lavels"] == k].longitude,
            df_prov[df_prov["lavels"] == k].latitude,
            c=colors[k],
            s=15,
            linewidth=0,
        )

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    x_lim = ax.get_xlim()
    y_lim = ax.get_ylim()

    ax_aer = area.plot(ax=ax, facecolor="none", edgecolor="grey", linewidth=1.0)
    ax_aer.set_xlim(x_lim)
    ax_aer.set_ylim(y_lim)

    cx.add_basemap(ax, crs="EPSG:4326", source=cx.providers.CartoDB.Voyager)

    fig.tight_layout()

    return fig


def elbow_plot(df, df2, surtidor="Gasolineras"):
    if surtidor == "Gasolineras":
        df_sp = df
    elif surtidor == "Electrolineras":
        df_sp = df2

    Sum_of_squared_distances = []
    k_index = range(1, 22)
    for num_clusters in k_index:
        kmeans = KMeans(n_clusters=num_clusters)
        kmeans.fit(df_sp[["latitude", "longitude"]])
        Sum_of_squared_distances.append(kmeans.inertia_)

    fig, ax = plt.subplots(1)

    ax.plot(k_index, Sum_of_squared_distances, "bx-")
    ax.grid(visible=True)
    ax.set_xlabel("Valor de K")
    ax.set_ylabel("Suma del cuadrado de las Distancias/Inercia")

    return fig


def silueta_plot(df, df2, surtidor="Gasolineras"):
    if surtidor == "Gasolineras":
        df_sp = df
    elif surtidor == "Electrolineras":
        df_sp = df2

    silhouette_avg = []
    s_range = range(2, 22)
    for num_clusters in s_range:
        kmeans = KMeans(n_clusters=num_clusters)
        kmeans.fit(df_sp[["latitude", "longitude"]])
        cluster_labels = kmeans.labels_
        silhouette_avg.append(
            silhouette_score(df_sp[["latitude", "longitude"]], cluster_labels)
        )

    fig, ax = plt.subplots(1)

    ax.plot(s_range, silhouette_avg, "bx-")
    ax.grid(visible=True)
    ax.set_xlabel("Valor de K")
    ax.set_ylabel("Puntuación de Silueta")

    return fig
