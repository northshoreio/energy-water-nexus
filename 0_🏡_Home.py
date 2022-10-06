import streamlit as st
import pandas as pd
import psychrolib

st.set_page_config(
    page_title="Home",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "https://github.com/northshoreio",
        "Get help": "mailto:hello@northshore.io"
    }
)

st.header("Energy Water Nexus")
st.markdown("> *Exploring interactions between energy- and water-consumption in data centers.*")

