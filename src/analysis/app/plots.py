import contextily as cx
import matplotlib.pyplot as plt
import seaborn as sns


def graph_plot(df):
    # p = sns.histplot(
    #     df, x=input.var(), facecolor="#007bc2", edgecolor="white"
    # )
    # return p.set(xlabel=None)

    # pruebas
    # g = sns.jointplot(x="longitude", y="latitude", data=tokyo, s=0.5)
    # cx.add_basemap(
    #     g.ax_joint,
    #     crs="EPSG:4326",
    #     source=cx.providers.CartoDB.PositronNoLabels,
    # )
    # return g

    # MATPLOTLIB
    # f, ax = plt.subplots(1, figsize=(heigh, width))
    # ax.scatter(df["x"], df["y"], s=0.75)
    # cx.add_basemap(ax, source=cx.providers.CartoDB.Positron)

    # SEABORN
    ax = sns.scatterplot(data=df, x="longitude", y="latitude")
    cx.add_basemap(
        ax,
        crs="EPSG:4326",
        source=cx.providers.CartoDB.PositronNoLabels,
    )

    return ax
