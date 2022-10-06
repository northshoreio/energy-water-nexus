import pandas as pd
import numpy as np
import streamlit as st
import plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from models import simulate as sim
import utils


def simulate():

    mechanical_system = st.session_state.mechanical_system

    if mechanical_system == 'Water-Cooled-Chiller':
        system = sim.WaterCooledChiller()
        return system.simulate()

    else:
        print('Future support for additional mechanical system archetypes.')


def get_performance_metrics(baseline, proposed):

    b_energy_kwh = round(baseline['total_power_consumption [kW]'].sum(), 0)
    b_it_energy_kwh = baseline['it_load_kw'].sum()
    b_water_liters = round(baseline['ct_makeup_flowrate_total [m^3]'].sum() * 1000, 0)

    b_pue = round(b_energy_kwh / b_it_energy_kwh, 2)
    b_wue = round(b_water_liters / b_it_energy_kwh, 2)

    p_energy_kwh = round(proposed['total_power_consumption [kW]'].sum(), 0)
    p_it_energy_kwh = proposed['it_load_kw'].sum()
    p_water_liters = round(proposed['ct_makeup_flowrate_total [m^3]'].sum() * 1000, 0)

    p_pue = round(p_energy_kwh / p_it_energy_kwh, 2)
    p_wue = round(p_water_liters / p_it_energy_kwh, 2)

    p_energy_savings_kwh = round(b_energy_kwh - p_energy_kwh, 0)
    p_water_savings_liters = round(b_water_liters - p_water_liters, 0)

    return {
        'baseline_total_energy_consumption_kwh': b_energy_kwh,
        'baseline_total_water_consumption_liters': b_water_liters,
        'baseline_pue': b_pue,
        'baseline_wue': b_wue,
        'proposed_total_energy_consumption_kwh': p_energy_kwh,
        'proposed_total_water_consumption_liters': p_water_liters,
        'proposed_pue': p_pue,
        'proposed_wue': p_wue,
        'proposed_energy_savings_kwh': p_energy_savings_kwh,
        'proposed_water_savings_liters': p_water_savings_liters
    }


st.set_page_config(
    page_title="Performance",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "https://github.com/northshoreio",
        "Get help": "mailto:hello@northshore.io"
    }
)
st.sidebar.info(
    '(1) Olympic-Sized Swimming Pool is [approximately 2,500,000 Liters]'
    '(https://en.wikipedia.org/wiki/Olympic-size_swimming_pool)',
    icon='🏊‍♀️'
)

baseline, proposed = simulate()
metrics = get_performance_metrics(baseline, proposed)

st.header('Performance')

col01, col02, col03, col04 = st.columns(4)

col01.metric(
    label='🔌PUE ',
    value=metrics['proposed_pue'],
    delta=-round(metrics['baseline_pue'] - metrics['proposed_pue'], 2),
    delta_color='inverse',
    help='**Power Usage Effectiveness** [-] *relative to baseline design*'
)
col02.metric(
    label='Annual Energy Consumption 🔌',
    value=f"{metrics['proposed_total_energy_consumption_kwh']:,}",
    delta=f"{-metrics['proposed_energy_savings_kwh']:,}",
    delta_color='inverse',
    help='**Annualized Energy Consumption** [kWh] *relative to baseline design*'
)
col03.metric(
    label='💧WUE',
    value=metrics['proposed_wue'],
    delta=-round(metrics['baseline_wue'] - metrics['proposed_wue'], 2),
    delta_color='inverse',
    help='**Water Usage Effectiveness** [L/kWh] relative to baseline design'
)

col04.metric(
    label='Annual Water Consumption 💧',
    value=f"{metrics['proposed_total_water_consumption_liters']:,}",
    delta=f"{-metrics['proposed_water_savings_liters']:,}",
    delta_color='inverse',
    help='**Annualized Water Consumption** [L] *relative to baseline design*'
)

fig_pue_wue_time = make_subplots(specs=[[{'secondary_y': True}]])
fig_pue_wue_time.add_trace(
    go.Line(
        x=proposed.index,
        y=proposed['PUE [-]'],
        name='PUE [-]'
    ),
    secondary_y=False
)
fig_pue_wue_time.add_trace(
    go.Line(
        x=proposed.index,
        y=proposed['WUE [L/kWh'],
        name='WUE [L/kWh'
    ),
    secondary_y=True
)
fig_pue_wue_time.update_layout(title_text='Performance over Time')
st.plotly_chart(fig_pue_wue_time, use_container_width=True)

savings_water_consumption_liters = metrics['proposed_water_savings_liters']

if savings_water_consumption_liters > 0:

    savings_water_consumption_olympic_sized_swimming_pools = \
        int(np.floor(metrics['proposed_water_savings_liters'] / utils.VOLUME_OF_OLYMPIC_SIZED_SWIMMING_POOL_LITERS))

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

st.dataframe(baseline)
st.dataframe(proposed)
