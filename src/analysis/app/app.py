from decimal import Decimal

from shiny import reactive
from shiny.express import input, render, ui
from shinywidgets import render_widget
from plots import (
    graph_plot,
    sp_plot,
    dot_density_plot,
    centrality_plot,
    random_plot,
    ripley_plot,
    cluster_plot,
    elbow_plot,
    silueta_plot,
)
from shared import (
    gaso,
    gaso_penin,
    gaso_canar,
    elec,
    elec_penin,
    elec_canar,
    areas_espania,
    areas_canarias,
)

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
    ui.HTML(
        '<p style="font-size: 25px; font-weight: bold; text-decoration: underline;">Opciones</p>'
    )

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

    ui.HTML(
        '<p style="font-size: 25px; font-weight: bold; text-decoration: underline;">Análisis</p>'
    )

    ui.HTML(
        '<p style="font-size: 15px; font-weight: bold; text-decoration: underline;">Densidad de puntos</p>'
    )

    ui.input_select(
        "map_type",
        "Selecciona el tipo de mapa:",
        {
            "Distribución espacial": "Distribución espacial",
            "Mapa de calor": "Mapa de calor",
            "Densidad 'kernel'": "Densidad 'kernel'",
            # "Densidad por CCAA": "Densidad por CCAA",
        },
        selected="Distribución espacial",
    )

    ui.input_radio_buttons(
        "densidad",
        "Densidad por CCAA:",
        {
            "si": "Mostrar",
            "no": "Quitar",
        },
        selected="no",
    )

    ui.HTML(
        '<p style="font-size: 15px; font-weight: bold; text-decoration: underline;">Centralidad y Aleatoriedad</p>'
    )

    ui.input_select(
        "provs",
        "Selecciona una Provincia:",
        {
            "albacete": "Albacete",
            "alicante": "Alicante",
            "almería": "Almería",
            "araba/álava": "Álaba",
            "asturias": "Asturias",
            "ávila": "Ávila",
            "badajoz": "Badajoz",
            "balears (illes)": "Islas Baleares",
            "barcelona": "Barcelona",
            "bizkaia": "Vizcaya",
            "burgos": "Burgos",
            "cáceres": "Cáceres",
            "cádiz": "Cádiz",
            "cantabria": "Cantabria",
            "castellón / castelló": "Castellón",
            "ceuta": "Ceuta",
            "ciudad real": "Ciudad Real",
            "córdoba": "Córdoba",
            "coruña (a)": "La Coruña",
            "cuenca": "Cuenca",
            "gipuzkoa": "Guipúzcoa",
            "girona": "Gerona",
            "granada": "Granada",
            "guadalajara": "Guadalajara",
            "huelva": "Huelva",
            "huesca": "Huesca",
            "jaén": "Jaén",
            "león": "León",
            "lleida": "Lérida",
            "lugo": "Lugo",
            "madrid": "Madrid",
            "málaga": "Málaga",
            "melilla": "Melilla",
            "murcia": "Murcia",
            "navarra": "Navarra",
            "ourense": "Ourense",
            "palencia": "Palencia",
            "palmas (las)": "Las Palmas",
            "pontevedra": "Pontevedra",
            "rioja (la)": "La Rioja",
            "salamanca": "Salamanca",
            "santa cruz de tenerife": "Tenerife",
            "segovia": "Segovia",
            "sevilla": "Sevilla",
            "soria": "Soria",
            "tarragona": "Tarragona",
            "teruel": "Teruel",
            "toledo": "Toledo",
            "valencia / valència": "Valencia",
            "valladolid": "Valladolid",
            "zamora": "Zamora",
            "zaragoza": "Zaragoza",
        },
        selected="alicante",
    )

    ui.input_numeric("nx", "QStat Columnas:", 9, min=1, max=100)
    ui.input_numeric("ny", "QStat Filas:", 9, min=1, max=100)

    ui.HTML(
        '<p style="font-size: 15px; font-weight: bold; text-decoration: underline;">Agrupaciones</p>'
    )

    ui.input_numeric("nk", "Valor K:", 8, min=1, max=21)

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
                        gaso.province.apply(
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
                        gaso.province.apply(
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
                        gaso.province.apply(
                            lambda x: True if x in ccaa[input.ccaa()] else False
                        )
                    ],
                    elec[elec.ccaa == input.ccaa()],
                    areas_espania,
                    areas_canarias,
                    surtidor=input.rbs(),
                    ccaa=input.ccaa(),
                )


with ui.nav_panel("Análisis"):  # pagina 2

    with ui.navset_card_underline():

        with ui.nav_panel("Densidad de puntos"):
            # Espana y CCAA
            with ui.layout_columns(col_widths=[6, 6, 7, 5]):
                # Espana
                with ui.card(full_screen=True):

                    @render.express
                    def header_sp():
                        ui.card_header(f"Distribución de {input.rbs()} en la Península")

                    @render.plot(width=950, height=900)
                    def plot_sp_dist():
                        dot_density_plot(
                            gaso_penin,
                            elec_penin,
                            input.map_type(),
                            surtidor=input.rbs(),
                            zone="peninsula",
                            area=areas_espania,
                            densidad=input.densidad(),
                        )

                # CCAA
                with ui.card(full_screen=True):

                    @render.express
                    def header_ccaa():
                        ui.card_header(f"Distribución de la CCAA: {input.ccaa()}")

                    @render.plot(width=800, height=800)
                    def plot_ccaa_dist():
                        return dot_density_plot(
                            gaso[
                                gaso.province.apply(
                                    lambda x: True if x in ccaa[input.ccaa()] else False
                                )
                            ],
                            elec[elec.ccaa == input.ccaa()],
                            input.map_type(),
                            surtidor=input.rbs(),
                            zone="ccaa",
                        )

                # Canarias
                with ui.card(full_screen=True):

                    @render.express
                    def header_can():
                        ui.card_header(f"Distribución de {input.rbs()} en la Península")

                    @render.plot()
                    def plot_can_dist():
                        dot_density_plot(
                            gaso_canar,
                            elec_canar,
                            input.map_type(),
                            surtidor=input.rbs(),
                            zone="islas",
                            area=areas_canarias,
                            densidad=input.densidad(),
                        )

        with ui.nav_panel("Centralidad y Aleatoriedad"):
            with ui.layout_columns(col_widths=[6, 6, 12]):
                with ui.card(full_screen=True):

                    @render.express
                    def header_centro():
                        ui.card_header(
                            f"Centrografía por provincias: {input.provs().upper()}"
                        )

                    @render.plot(width=900, height=900)
                    def plot_ccaa_entrality():
                        return centrality_plot(
                            gaso[gaso.province == input.provs()],
                            elec[elec.province == input.provs()],
                            areas_espania,
                            areas_canarias,
                            surtidor=input.rbs(),
                            province=input.provs(),
                        )

                with ui.card(full_screen=True):

                    @render.express
                    def header_aleatorio():
                        ui.card_header(
                            f"Aleatoriedad por provincias: {input.provs().upper()}"
                        )

                    with ui.layout_columns(col_widths=[6, 6, 6, 6]):

                        with ui.card(full_screen=True):

                            @render.plot()
                            def plot_random_g():
                                qstat_g = random_plot(
                                    gaso[gaso.province == input.provs()],
                                    nx=input.nx(),
                                    ny=input.ny(),
                                )

                                return qstat_g.plot(title="QStatistic - Gasolineras")

                        with ui.card(full_screen=True):

                            @render.plot()
                            def plot_random_e():
                                qstat_e = random_plot(
                                    elec[elec.province == input.provs()],
                                    nx=input.nx(),
                                    ny=input.ny(),
                                )

                                return qstat_e.plot(title="QStatistic - Electrolineras")

                        with ui.card(full_screen=True):

                            @render.plot()
                            def plot_random_a():
                                qstat_r = random_plot(
                                    gaso[gaso.province == input.provs()],
                                    pattern=True,
                                    nx=input.nx(),
                                    ny=input.ny(),
                                )

                                return qstat_r.plot(
                                    title="QStatistic - Muestra Aleatoria"
                                )

                        # Chi-square P-Value
                        with ui.card(full_screen=True):
                            with ui.layout_columns(col_widths=[12, 12, 12]):
                                with ui.card():
                                    with ui.value_box(
                                        showcase=ui.HTML(
                                            '<img src="https://cdn-icons-png.flaticon.com/512/1946/1946245.png" width="50" height="50">'
                                        )
                                    ):
                                        "P-value basado en la chi-squared:"

                                        @render.ui
                                        def rand1():
                                            qstat_g = random_plot(
                                                gaso[gaso.province == input.provs()],
                                                nx=input.nx(),
                                                ny=input.ny(),
                                            )
                                            return f"{Decimal(qstat_g.chi2_pvalue):.2E}"

                                with ui.card():
                                    with ui.value_box(
                                        showcase=ui.HTML(
                                            '<img src="https://riberamovisse.consorcioeder.es/wp-content/uploads/2022/10/wind2.png" width="60" height="60">'
                                        )
                                    ):
                                        "P-value basado en la chi-squared:"

                                        @render.ui
                                        def rand2():
                                            qstat_e = random_plot(
                                                elec[elec.province == input.provs()],
                                                nx=input.nx(),
                                                ny=input.ny(),
                                            )
                                            return f"{Decimal(qstat_e.chi2_pvalue):.2E}"

                                with ui.card():
                                    with ui.value_box(
                                        showcase=ui.HTML(
                                            '<img src="https://cdn-icons-png.flaticon.com/512/7101/7101743.png" width="50" height="50">'
                                        )
                                    ):
                                        "P-value basado en la chi-squared:"

                                        @render.ui
                                        def rand3():
                                            qstat_r = random_plot(
                                                gaso[gaso.province == input.provs()],
                                                pattern=True,
                                                nx=input.nx(),
                                                ny=input.ny(),
                                            )
                                            return f"{Decimal(qstat_r.chi2_pvalue):.2E}"

                with ui.card(full_screen=True):

                    @render.express
                    def header_ripley():
                        ui.card_header("Funciones de Ripley")

                    @render.plot()
                    def plot_ripley():
                        return ripley_plot(
                            gaso[gaso.province == input.provs()],
                            elec[elec.province == input.provs()],
                            surtidor=input.rbs(),
                        )

        with ui.nav_panel("Agrupaciones"):
            with ui.layout_columns(col_widths=[7, 5]):
                with ui.card(full_screen=True):

                    @render.express
                    def header_cluster():
                        ui.card_header(f"Agrupaciones de {input.rbs()}")

                    @render.plot(width=1100, height=1100)
                    def plot_cluster():
                        return cluster_plot(
                            gaso[gaso.province == input.provs()],
                            elec[elec.province == input.provs()],
                            areas_espania,
                            areas_canarias,
                            surtidor=input.rbs(),
                            groups=input.nk(),
                        )

                with ui.card():
                    with ui.layout_columns(col_widths=[12, 12]):
                        with ui.card(full_screen=True):

                            @render.express
                            def header_elbow():
                                ui.card_header("Método Elbow")

                            @render.plot(width=700, height=600)
                            def plot_cluster_elbow():
                                return elbow_plot(
                                    gaso[gaso.province == input.provs()],
                                    elec[elec.province == input.provs()],
                                    surtidor=input.rbs(),
                                )

                        with ui.card(full_screen=True):

                            @render.express
                            def header_silueta():
                                ui.card_header("Análisis de la silueta")

                            @render.plot(width=700, height=600)
                            def plot_cluster_silueta():
                                return silueta_plot(
                                    gaso[gaso.province == input.provs()],
                                    elec[elec.province == input.provs()],
                                    surtidor=input.rbs(),
                                )


with ui.nav_panel("Datos"):  # pagina 3

    with ui.navset_card_underline(title="Tablas"):

        with ui.nav_panel("Gasolineras"):

            @render.data_frame
            def data_gaso():
                return gaso[
                    gaso.province.apply(
                        lambda x: True if x in ccaa[input.ccaa()] else False
                    )
                ]

        with ui.nav_panel("Electrolineras"):

            @render.data_frame
            def data_elec():
                return elec[elec.ccaa == input.ccaa()]
