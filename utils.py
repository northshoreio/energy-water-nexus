import streamlit as st

STANDARD_DENSITY_OF_WATER_KG_M3 = 1_000  # [kg/m^3]
SPECIFIC_HEAT_CAPACITY_OF_WATER_KJ_KGC = 0.4184  # [kJ/kg-C]
VOLUME_OF_OLYMPIC_SIZED_SWIMMING_POOL_LITERS = 2_500_000  # https://en.wikipedia.org/wiki/Olympic-size_swimming_pool


def convert_degC_to_degF(degC):
    return (degC * 9 / 5) + 32


def convert_deltaC_to_deltaF(deltaC):
    return deltaC * 9 / 5

def convert_deltaF_to_deltaC(deltaF):
    return deltaF * 5 / 9


def initialize_st_session_state(variables):

    if isinstance(variables, list):
        for v in variables:
            if v not in st.session_state:
                st.session_state[v] = None
    elif isinstance(variables, dict):
        for v, initial_value in variables.items():
            if v not in st.session_state:
                st.session_state[v] = initial_value
    else:
        raise ValueError(f"The `variables` parameter must be of type List or Dict. Received {type(variables)}")
