from shiny import reactive
from shiny.express import input, render, ui
from shinywidgets import render_widget

from plots import graph_plot, sp_plot
from shared import gaso, elec

ui.page_opts(title="Estudio de los Puntos de Recarga en España")

ui.nav_spacer()  # Push the navbar items to the right


ccaa = {
    "Andalucía": [
        "huelva",
        "sevilla",
        "córdoba",
        "cádiz",
        "málaga",
        "jaén",
        "granada",
        "almería",
    ],
    "Aragón": ["zaragoza", "teruel", "huesca"],
    "Asturias, Principado de": ["asturias"],
    "Balears, Illes": ["balears (illes)"],
    "Canarias": ["santa cruz de tenerife", "palmas (las)"],
    "Cantabria": ["cantabria"],
    "Castilla y León": [
        "león",
        "palencia",
        "burgos",
        "soria",
        "zamora",
        "valladolid",
        "segovia",
        "salamanca",
        "ávila",
    ],
    "Castilla - La Mancha": [
        "guadalajara",
        "toledo",
        "cuenca",
        "ciudad real",
        "albacete",
    ],
    "Cataluña": ["lleida", "tarragona", "barcelona", "girona"],
    "Comunitat Valenciana": ["alicante", "valencia / valència", "castellón / castelló"],
    "Extremadura": ["badajoz", "cáceres"],
    "Galicia": ["coruña (a)", "lugo", "pontevedra", "ourense"],
    "Madrid, Comunidad de": ["madrid"],
    "Murcia, Región de": ["murcia"],
    "Navarra, Comunidad Foral de": ["navarra"],
    "País Vasco": ["araba/álava", "gipuzkoa", "bizkaia"],
    "Rioja, La": ["rioja (la)"],
    "ceuta": ["ceuta"],
    "melilla": ["melilla"],
}


with ui.sidebar():
    ui.input_select(
        "ccaa",
        "Selecciona una CCAA:",
        {
            "Andalucía": "Andalucía",
            "Aragón": "Aragón",
            "Asturias, Principado de": "Principado de Asturias",
            "Balears, Illes": "Islas Baleares",
            "Canarias": "Islas Canarias",
            "Cantabria": "Cantabria",
            "Castilla y León": "Castilla y León",
            "Castilla - La Mancha": "Castilla - La Mancha",
            "Cataluña": "Cataluña",
            "Comunitat Valenciana": "Comunidad Valenciana",
            "Extremadura": "Extremadura",
            "Galicia": "Galicia",
            "Madrid, Comunidad de": "Comunidad de Madrid",
            "Murcia, Región de": "Región de Murcia",
            "Navarra, Comunidad Foral de": "Comunidad Foral de Navarra",
            "País Vasco": "Pais Vasco",
            "Rioja, La": "La Rioja",
            "ceuta": "Ciudad Autónoma de Ceuta",
            "melilla": "Ciudad Autónoma de Melilla",
        },
        selected="Comunitat Valenciana",
    )

    ui.input_radio_buttons(
        "rbs",
        "Elige un tipo de surtidor:",
        {
            "Gasolineras": "Gasolineras",
            "Electrolineras": "Electrolineras",
        },
    )


with ui.nav_panel("Visualización"):  # pagina 1

    with ui.layout_columns(col_widths=[4, 4, 4, 6, 6]):

        with ui.card():

            with ui.value_box(
                showcase=ui.HTML(
                    '<img src="https://cdn-icons-png.flaticon.com/512/1946/1946245.png" width="60" height="60">'
                )
            ):
                "Número de Gasolineras"

                @render.ui
                def out1():
                    val = gaso[
                        gaso.provincia.apply(
                            lambda x: (True if x in ccaa[input.ccaa()] else False)
                        )
                    ].shape[0]

                    return val

        with ui.card():
            with ui.value_box(
                showcase=ui.HTML(
                    '<img src="https://riberamovisse.consorcioeder.es/wp-content/uploads/2022/10/wind2.png" width="75" height="75">'
                )
            ):
                "Número de Electrolineras"

                @render.ui
                def out2():
                    val = elec[elec.ccaa == input.ccaa()].shape[0]

                    return val

        with ui.card():
            with ui.value_box(
                showcase=ui.HTML(
                    '<img src="https://cdn-icons-png.flaticon.com/512/9588/9588758.png" width="60" height="60">'
                )
            ):
                "Ratio Gasolineras vs. Electrolineras"

                @render.ui
                def out3():
                    val1 = gaso[
                        gaso.provincia.apply(
                            lambda x: (True if x in ccaa[input.ccaa()] else False)
                        )
                    ].shape[0]

                    val2 = elec[elec.ccaa == input.ccaa()].shape[0]

                    try:
                        return round(val1 / val2, 2)
                    except ZeroDivisionError as e:
                        return val1

        with ui.card():

            @render.express
            def header():
                ui.card_header(f"Mapa Interactivo de España ({input.rbs()})")

            @render.ui
            def plot_folium():
                return sp_plot(gaso, elec, surtidor=input.rbs())

        with ui.card(full_screen=True):

            @render.express
            def header2():
                ui.card_header(f"Mapa de la Comunidad ({input.ccaa()})")

            @render.plot(width=800, height=800)
            def plot():
                return graph_plot(
                    gaso[
                        gaso.provincia.apply(
                            lambda x: True if x in ccaa[input.ccaa()] else False
                        )
                    ],
                    elec[elec.ccaa == input.ccaa()],
                    surtidor=input.rbs(),
                )


with ui.nav_panel("Análisis"):  # pagina 2
    "This is the second 'page'."

with ui.nav_panel("Datos"):  # pagina 3

    with ui.navset_card_underline(title="Tablas"):

        with ui.nav_panel("Gasolineras"):

            @render.data_frame
            def data_gaso():
                return gaso[
                    gaso.provincia.apply(
                        lambda x: True if x in ccaa[input.ccaa()] else False
                    )
                ]

        with ui.nav_panel("Electrolineras"):

            @render.data_frame
            def data_elec():
                return elec[elec.ccaa == input.ccaa()]
