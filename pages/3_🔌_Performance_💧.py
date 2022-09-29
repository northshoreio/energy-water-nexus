import pandas as pd
import numpy as np
import streamlit as st
import plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


VOLUME_OF_OLYMPIC_SIZED_SWIMMING_POOL_LITERS = 2_500_000  # https://en.wikipedia.org/wiki/Olympic-size_swimming_pool

st.set_page_config(
    page_title="Performance",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "https://github.com/northshoreio",
        "Get help": "mailto:sam.zastrow@northshore.io"
    }
)
st.sidebar.info(
    '(1) Olympic-Sized Swimming Pool is [approximately 2,500,000 Liters]'
    '(https://en.wikipedia.org/wiki/Olympic-size_swimming_pool)',
    icon='🏊‍♀️'
)

st.header('Performance')

col01, col02, col03, col04 = st.columns(4)

col01.metric(
    label='🔌PUE ',
    value=1.45,
    delta=-0.05,
    delta_color='inverse',
    help='**Power Usage Effectiveness** [-] *relative to baseline design*'
)
col02.metric(
    label='Annual Energy Consumption 🔌',
    value=f'{1_234_567:,}',
    delta=f'{-456_789:,}',
    delta_color='inverse',
    help='**Annualized Energy Consumption** [kWh] *relative to baseline design*'
)
col03.metric(
    label='💧WUE',
    value=0.87,
    delta=-0.01,
    delta_color='inverse',
    help='**Water Usage Effectiveness** [L/kWh] relative to baseline design'
)

baseline_water_consumption_liters = 456_456_789
proposed_water_consumption_liters = 123_345_678
savings_water_consumption_liters = baseline_water_consumption_liters - proposed_water_consumption_liters
savings_water_consumption_olympic_sized_swimming_pools = \
    int(np.floor(savings_water_consumption_liters / VOLUME_OF_OLYMPIC_SIZED_SWIMMING_POOL_LITERS))

col04.metric(
    label='Annual Water Consumption 💧',
    value=f'{baseline_water_consumption_liters:,}',
    delta=f'{-savings_water_consumption_liters:,}',
    delta_color='inverse',
    help='**Annualized Water Consumption** [L] *relative to baseline design*'
)

if savings_water_consumption_liters > 0:

    st.subheader('Water Consumption Savings')
    st.markdown(
        f'The proposed design is estimated to save **{savings_water_consumption_liters:,}** '
        f'Liters annually, equivalent to over **{savings_water_consumption_olympic_sized_swimming_pools:,}** '
        f'Olympic-Sized Swimming Pools!'
    )
    st.write('🏊‍♀️' * savings_water_consumption_olympic_sized_swimming_pools)
    st.write('**todo** costs')

st.subheader('Water Consumption Insights')
st.write('**todo** consumption vs dry/wetbulb, season')

