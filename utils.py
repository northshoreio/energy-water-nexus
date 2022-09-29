import streamlit as st


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
