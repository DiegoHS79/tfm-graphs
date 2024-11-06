import sys
from math import floor, ceil

import geopy
from geopy.location import Location
from geopy.geocoders import Photon, Nominatim, ArcGIS

from utils.user_agents import get_user_agent

geopy.geocoders.options.default_user_agent = "Geoposicionador"


def get_coordinates(
    direction: str,
    lat_edges: tuple[float],
    long_edges: tuple[float],
) -> tuple[Location] | list[int]:
    run_arcgis = False
    geolocator = Photon(user_agent=get_user_agent(), timeout=60)
    location = geolocator.geocode(direction)

    if not location:
        run_arcgis = True
    elif (
        location.latitude > ceil(lat_edges[0])
        or location.latitude < floor(lat_edges[1])
        or location.longitude > ceil(long_edges[0])
        or location.longitude < floor(long_edges[1])
    ):
        run_arcgis = True

    if run_arcgis:
        print(f"ERROR - coordenadas geopy.")
        print(f"\tlimites provinciales (latitud): {lat_edges}")
        print(f"\tlimites provinciales (longitud): {long_edges}")
        print(f"\tlanzando ArcGIS.")
        nom = ArcGIS()
        locations = nom.geocode(direction, exactly_one=False)

        for location in locations:
            if (
                location.latitude < ceil(lat_edges[0])
                or location.latitude > floor(lat_edges[1])
                or location.longitude < ceil(long_edges[0])
                or location.longitude > floor(long_edges[1])
            ):
                print(f"\tdirection: {location.address}")
                break

    return location.latitude, location.longitude


# def get_coordinates_2(direction: str) -> list[int]:
#     try:
#         geolocator = Nominatim(user_agent="geoapiExercises")
#         location = geolocator.geocode(direction)

#         return location.latitude, location.longitude
#     except Exception as e:
#         print(e)
#         return get_coordinates_3(direction)


# def get_coordinates_3(direction: str) -> list[int]:
#     nom = ArcGIS()
#     location = nom.geocode(direction, exactly_one=False)[0]

#     return location.latitude, location.longitude
