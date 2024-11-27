# import seaborn as sns

from shiny.express import input, render, ui

from plots import graph_plot
from shared import gaso, elec

ui.page_opts(title="Shiny navigation components")

ui.nav_spacer()  # Push the navbar items to the right

# footer = ui.input_select(
#     "var", "Select variable", choices=["bill_length_mm", "body_mass_g"]
# )

# with ui.sidebar():
#     ui.input_slider("t", "Tamaño del plot", 1000, 2000, 1000)

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
    "Asturias": ["asturias"],
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

with ui.nav_panel("Visualización"):  # pagina 1

    # ventana de plot y tabla
    # with ui.navset_card_underline(id="contenido", title="Gasolineras y Electrolineras"):

    #     with ui.nav_panel("Plot"):
    # with ui.card():

    @render.plot  # (width=1000, height=1000)
    # def plot():
    #     return graph_plot(
    #         gaso[
    #             gaso.provincia.apply(
    #                 lambda x: True if x in ccaa[input.ccaa()] else False
    #             )
    #         ]
    #     )
    def plot():
        return graph_plot(elec[elec.ccaa == input.ccaa()])


with ui.nav_panel("Análisis"):  # pagina 2
    "This is the second 'page'."

with ui.nav_panel("Datos"):  # pagina 3

    with ui.navset_card_underline(title="Tablas"):

        with ui.nav_panel("Gasolineras"):

            @render.data_frame
            def data_gaso():
                return gaso

        with ui.nav_panel("Electrolineras"):

            @render.data_frame
            def data_elec():
                return elec[elec.ccaa == input.ccaa()]
