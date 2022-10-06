import pandas as pd
import numpy as np
import streamlit as st
import utils
from models import equipment as eq


def __build_cooling_tower__(
        name: str,
        count: int,
        design_wetbulb: float,
        design_approach: float,
        design_range: float,
        design_air_flowrate: float,
        design_water_flowrate: float,
        design_fan_power: float,
        operating_tower_water_supply: float,
        operating_cycles_of_concentration: float
):
    st.session_state[name] = eq.CoolingTower(
        count=count,
        design_wetbulb_c=design_wetbulb,
        design_approach_c=design_approach,
        design_range_c=design_range,
        operating_tower_water_supply_temperature_c=operating_tower_water_supply,
        design_air_flowrate_m3_hr=design_air_flowrate,
        design_water_flowrate_m3_hr=design_water_flowrate,
        design_fan_power_kw=design_fan_power,
        operating_cycles_of_concentration=operating_cycles_of_concentration
    )


def __build_chiller__(
        name: str,
        count: int,
        design_cooling_capacity: float,
        design_chw_supply_temp: float
):
    st.session_state[name] = eq.Chiller(
        count=count,
        design_cooling_capacity_kw=design_cooling_capacity,
        design_chw_supply_temperature_c=design_chw_supply_temp
    )


def cooling_tower_form(default: bool, ct: eq.CoolingTower, name: str):
    count = st.number_input(
        label='Count',
        min_value=1,
        step=1,
        value=1 if default else ct.count
    )
    design_wetbulb = st.number_input(
        label='Design Wetbulb [C]',
        min_value=10.0,
        step=0.5,
        value=20.0 if default else ct.design_wetbulb_c
    )
    design_approach = st.number_input(
        label='Design Approach [C]',
        min_value=2.0,
        step=0.25,
        value=4.5 if default else ct.design_approach_c
    )
    design_range = st.number_input(
        label='Design Range [C]',
        min_value=0.0,
        step=0.25,
        value=4.5 if default else ct.design_range_c
    )
    design_air_flowrate = st.number_input(
        label='Design Air Flowrate [m^3/hr]',
        step=1_000,
        value=100_000 if default else ct.design_air_flowrate_m3_hr
    )
    design_water_flowrate = st.number_input(
        label='Design Water Flowrate [m^3/hr]',
        step=100,
        value=250 if default else ct.design_water_flowrate_m3_hr
    )
    design_fan_power = st.number_input(
        label='Design Fan Power [kW]',
        value=10 if default else ct.design_fan_power_kw
    )
    operating_tower_water_supply = st.number_input(
        label='Operating Tower Water Supply Temperature [C]',
        min_value=24.0,
        max_value=35.0,
        step=0.5,
        value=28.0 if default else ct.operating_tower_water_supply_temperature_c
    )
    operating_cycles_of_concentration = st.number_input(
        label='Operating Cycles of Concentration [-]',
        min_value=2.5,
        max_value=8.0,
        step=0.25,
        value=3.5 if default else ct.operating_cycles_of_concentration,
    )
    submitted = st.form_submit_button(
        label='Submit' if default else 'Update',
        help='Use the inputs above as Baseline Cooling Tower specifications.'
    )
    if submitted:
        __build_cooling_tower__(
            name=name,
            count=count,
            design_wetbulb=design_wetbulb,
            design_approach=design_approach,
            design_range=design_range,
            design_air_flowrate=design_air_flowrate,
            design_water_flowrate=design_water_flowrate,
            design_fan_power=design_fan_power,
            operating_tower_water_supply=operating_tower_water_supply,
            operating_cycles_of_concentration=operating_cycles_of_concentration
        )


def chiller_form(default: bool, ch: eq.Chiller, name: str):
    count = st.number_input(
        label='Count',
        min_value=1,
        step=1,
        value=1 if default else ch.count
    )
    design_cooling_capacity = st.number_input(
        label='Design Cooling Capacity [kW]',
        min_value=10.0,  # TODO: heat load
        step=50.0,
        value=1_500.0 if default else ch.design_cooling_capacity_kw
    )
    design_chw_supply_temp = st.number_input(
        label='Design CHW Supply Temperature [C]',
        min_value=5.0,
        max_value=10.0,
        step=0.25,
        value=5.0 if default else ch.design_chw_supply_temperature_c
    )
    submitted = st.form_submit_button(
        label='Submit' if default else 'Update',
        help='Use the inputs above as Baseline Chiller specifications.'
    )
    if submitted:
        __build_chiller__(
            name=name,
            count=count,
            design_cooling_capacity=design_cooling_capacity,
            design_chw_supply_temp=design_chw_supply_temp
        )


st.set_page_config(
    page_title="Design",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "https://github.com/northshoreio",
        "Get help": "mailto:hello@northshore.io"
    }
)
utils.initialize_st_session_state([
    'baseline_ct',
    'proposed_ct',
    'baseline_chiller',
    'proposed_chiller',
    'load_it_kw',
    'mechanical_system',
    'baseline_add_power_kw',
    'baseline_add_heat_load_kw',
    'proposed_add_power_kw',
    'proposed_add_heat_load_kw',
])

st.header('Design')
st.markdown('Populate the inputs below to simulate our **Baseline** and **Proposed** models.')

with st.container():
    st.subheader('Common Inputs')
    col01, col02, = st.columns(2)

    load_it_kw = col01.number_input(
        label='IT Load [kW]',
        min_value=100,
        value=1_000 if not st.session_state.load_it_kw else st.session_state.load_it_kw,
        step=50,
    )
    st.session_state.load_it_kw = load_it_kw

    mechanical_system = col02.selectbox(
        label='Mechanical System',
        options=['Water-Cooled-Chiller'],
        index=0,
        help='Future selection from multiple mechanical system archetypes.',
        disabled=True
    )
    st.session_state.mechanical_system = mechanical_system

baseline, proposed = st.columns(2)
baseline.header('Baseline Inputs')
proposed.header('Proposed Inputs')

with baseline.container():
    st.subheader('Baseline Operational Efficiency')

    baseline_add_power_kw = st.number_input(
        label='Baseline Additional Power Consumption [kW]',
        value=load_it_kw * 0.3
        if not st.session_state.baseline_add_power_kw else st.session_state.baseline_add_power_kw,
        step=50.0,
    )
    st.session_state.baseline_add_power_kw = baseline_add_power_kw

    baseline_add_heat_load_kw = st.number_input(
        label='Baseline Additional Heat Load [kW]',
        value=baseline_add_power_kw * 0.9
        if not st.session_state.baseline_add_heat_load_kw else st.session_state.baseline_add_heat_load_kw,
        step=50.0,
    )
    st.session_state.baseline_add_heat_load_kw = baseline_add_heat_load_kw

    st.subheader('Baseline Cooling Towers')

    ct_default = False if isinstance(st.session_state.baseline_ct, eq.CoolingTower) else True
    ct = None if ct_default else st.session_state.baseline_ct

    with st.form(key='baseline_cooling_towers', clear_on_submit=False):
        cooling_tower_form(default=ct_default, ct=ct, name='baseline_ct')

    st.subheader('Baseline Chillers')

    ch_default = False if isinstance(st.session_state.baseline_chiller, eq.Chiller) else True
    ch = None if ch_default else st.session_state.baseline_chiller

    with st.form(key='baseline_chillers', clear_on_submit=False):
        chiller_form(default=ch_default, ch=ch, name='baseline_chiller')

with proposed.container():
    st.subheader('Proposed Operational Efficiency')

    proposed_add_power_kw = st.number_input(
        label='Proposed Additional Power Consumption [kW]',
        value=load_it_kw * 0.3
        if not st.session_state.proposed_add_power_kw else st.session_state.proposed_add_power_kw,
        step=50.0,
    )
    st.session_state.proposed_add_power_kw = proposed_add_power_kw

    proposed_add_heat_load_kw = st.number_input(
        label='Proposed Additional Heat Load [kW]',
        value=proposed_add_power_kw * 0.9
        if not st.session_state.proposed_add_heat_load_kw else st.session_state.proposed_add_heat_load_kw,
        step=50.0,
    )
    st.session_state.proposed_add_heat_load_kw = proposed_add_heat_load_kw

    st.subheader('Proposed Cooling Towers')

    if isinstance(st.session_state.proposed_ct, eq.CoolingTower):
        ct_default = False
        ct = st.session_state.proposed_ct
    elif isinstance(st.session_state.baseline_ct, eq.CoolingTower):
        ct_default = False
        ct = st.session_state.baseline_ct
    else:
        ct_default = True
        ct = None

    with st.form(key='proposed_cooling_towers', clear_on_submit=False):
        cooling_tower_form(default=ct_default, ct=ct, name='proposed_ct')

    st.subheader('Proposed Chillers')

    if isinstance(st.session_state.proposed_chiller, eq.Chiller):
        ch_default = False
        ch = st.session_state.proposed_chiller
    elif isinstance(st.session_state.baseline_chiller, eq.Chiller):
        ch_default = False
        ch = st.session_state.baseline_chiller
    else:
        ch_default = True
        ch = None

    with st.form(key='proposed_chillers', clear_on_submit=False):
        chiller_form(default=ch_default, ch=ch, name='proposed_chiller')
