import streamlit as st
import numpy as np
import utils
from models import equipment as eq


def __autosize_cooling_tower__(do_model: str):

    load_it_kw = st.session_state.load_it_kw
    mechanical_system = st.session_state.mechanical_system

    if do_model == 'baseline':
        add_heat_load_kw = st.session_state.baseline_add_heat_load_kw
    elif do_model == 'proposed':
        add_heat_load_kw = st.session_state.proposed_add_heat_load_kw
    else:
        raise ValueError(f"`do_model` must either be 'baseline' or 'proposed', not '{do_model}'.")

    total_heat_load_kw = load_it_kw + add_heat_load_kw
    # accounting for chiller compressor heat addition to condenser water stream
    total_heat_load_kw = total_heat_load_kw + total_heat_load_kw / eq.Chiller.__curve_reference_cop__

    range_c = utils.convert_deltaF_to_deltaC(deltaF=10)  # rule of thumb
    required_water_flowrate_kg_s = total_heat_load_kw / (utils.SPECIFIC_HEAT_CAPACITY_OF_WATER_KJ_KGC * range_c)
    required_water_flowrate_m3_hr = required_water_flowrate_kg_s / utils.STANDARD_DENSITY_OF_WATER_KG_M3 * 3_600

    air_flowrate_m3_hr = round(total_heat_load_kw * 130, ndigits=-2)  # rule of thumb

    max_wetbulb_c = np.ceil(
            st.session_state.weather_data['Psychrometrics (out): wet_bulb [C]'].max()
    )
    design_approach_c = 3.5  # rule of thumb

    return {
        'design_wetbulb': max_wetbulb_c + 4.0,
        'design_approach': design_approach_c,
        'design_range': range_c,
        'design_air_flowrate': air_flowrate_m3_hr,
        'design_water_flowrate': int(round(required_water_flowrate_m3_hr * 1.3, ndigits=-2)),
        'design_fan_power': np.ceil(air_flowrate_m3_hr * 0.06 / 1_000),  # rule of thumb
        'operating_tower_water_supply': max(max_wetbulb_c + design_approach_c - 5.0, 28.0),  # rule of thumb
        'operating_cycles_of_concentration': 3.5  # low-end rule of thumb
    }


def __build_cooling_tower__(
        name: str,
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
        design_wetbulb_c=design_wetbulb,
        design_approach_c=design_approach,
        design_range_c=design_range,
        operating_tower_water_supply_temperature_c=operating_tower_water_supply,
        design_air_flowrate_m3_hr=design_air_flowrate,
        design_water_flowrate_m3_hr=design_water_flowrate,
        design_fan_power_kw=design_fan_power,
        operating_cycles_of_concentration=operating_cycles_of_concentration
    )


def __autosize_chiller__(do_model: str):

    load_it_kw = st.session_state.load_it_kw
    mechanical_system = st.session_state.mechanical_system

    if do_model == 'baseline':
        add_heat_load_kw = st.session_state.baseline_add_heat_load_kw
    elif do_model == 'proposed':
        add_heat_load_kw = st.session_state.proposed_add_heat_load_kw
    else:
        raise ValueError(f"`do_model` must either be 'baseline' or 'proposed', not '{do_model}'.")

    total_heat_load_kw = load_it_kw + add_heat_load_kw

    return {
        'design_cop': eq.Chiller.__curve_reference_cop__,
        'design_chw_supply_temp_c': 7.22,  # rule of thumb
        'design_cooling_capacity_kw': int(round(total_heat_load_kw * 1.25, ndigits=-2))
    }


def __build_chiller__(
        name: str,
        design_cop: float,
        design_cooling_capacity: float,
        design_chw_supply_temp: float
):
    st.session_state[name] = eq.Chiller(
        design_cop=design_cop,
        design_cooling_capacity_kw=design_cooling_capacity,
        design_chw_supply_temperature_c=design_chw_supply_temp
    )


def cooling_tower_form(default: bool, ct: eq.CoolingTower, name: str, do_model: str):

    auto = __autosize_cooling_tower__(do_model=do_model) if default else {}

    design_wetbulb = st.number_input(
        label='Design Wetbulb [C]',
        min_value=10.0,
        step=0.5,
        value=auto['design_wetbulb'] if default else ct.design_wetbulb_c
    )
    design_approach = st.number_input(
        label='Design Approach [C]',
        min_value=2.0,
        step=0.25,
        value=auto['design_approach'] if default else ct.design_approach_c
    )
    design_range = st.number_input(
        label='Design Range [C]',
        min_value=0.0,
        step=0.25,
        value=auto['design_range'] if default else ct.design_range_c
    )
    design_air_flowrate = st.number_input(
        label='Design Air Flowrate [m^3/hr]',
        step=1_000,
        value=int(auto['design_air_flowrate']) if default else ct.design_air_flowrate_m3_hr
    )
    design_water_flowrate = st.number_input(
        label='Design Water Flowrate [m^3/hr]',
        step=100,
        value=auto['design_water_flowrate'] if default else ct.design_water_flowrate_m3_hr
    )
    design_fan_power = st.number_input(
        label='Design Fan Power [kW]',
        value=auto['design_fan_power'] if default else ct.design_fan_power_kw
    )
    operating_tower_water_supply = st.number_input(
        label='Operating Tower Water Supply Temperature [C]',
        min_value=24.0,
        max_value=35.0,
        step=0.5,
        value=auto['operating_tower_water_supply'] if default else ct.operating_tower_water_supply_temperature_c
    )
    operating_cycles_of_concentration = st.number_input(
        label='Operating Cycles of Concentration [-]',
        min_value=2.5,
        step=0.25,
        value=auto['operating_cycles_of_concentration'] if default else ct.operating_cycles_of_concentration,
    )
    submitted = st.form_submit_button(
        label='Submit' if default else 'Update',
        help='Use the inputs above as Baseline Cooling Tower specifications.'
    )
    if submitted:
        __build_cooling_tower__(
            name=name,
            design_wetbulb=design_wetbulb,
            design_approach=design_approach,
            design_range=design_range,
            design_air_flowrate=design_air_flowrate,
            design_water_flowrate=design_water_flowrate,
            design_fan_power=design_fan_power,
            operating_tower_water_supply=operating_tower_water_supply,
            operating_cycles_of_concentration=operating_cycles_of_concentration
        )


def chiller_form(default: bool, ch: eq.Chiller, name: str, do_model: str):

    auto = __autosize_chiller__(do_model=do_model) if default else {}

    design_cooling_capacity = st.number_input(
        label='Design Cooling Capacity [kW]',
        step=100,
        value=auto['design_cooling_capacity_kw'] if default else ch.design_cooling_capacity_kw
    )
    design_cop = st.number_input(
        label='Design Coefficient of Performance [-]',
        min_value=1.5,
        step=0.25,
        value=auto['design_cop'] if default else ch.design_cop
    )
    design_chw_supply_temp = st.number_input(
        label='Design CHW Supply Temperature [C]',
        min_value=5.0,
        max_value=10.0,
        step=0.25,
        value=auto['design_chw_supply_temp_c'] if default else ch.design_chw_supply_temperature_c
    )
    submitted = st.form_submit_button(
        label='Submit' if default else 'Update',
        help='Use the inputs above as Baseline Chiller specifications.'
    )
    if submitted:
        __build_chiller__(
            name=name,
            design_cop=design_cop,
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
    'energy_cost_dollar_per_kwh',
    'water_cost_dollar_per_m3'
])

st.header('Design')
st.markdown(
    'Populate the inputs below to simulate our **Baseline** and **Proposed** models. '
    'Be sure to hit the `Submit` and `Update` buttons after any changes to equipment inputs.'
)

with st.container():
    st.subheader('Common Inputs')
    col01, col02, = st.columns(2)

    load_it_kw = col01.number_input(
        label='IT Load [kW]',
        min_value=100,
        value=10_000 if not st.session_state.load_it_kw else st.session_state.load_it_kw,
        step=50,
        help='Server (IT) load used within the data center whitespace.'
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

    energy_cost_dollar_per_kwh = col01.number_input(
        label='Electricity Cost [$/kWh]',
        value=0.10 if not st.session_state.energy_cost_dollar_per_kwh
            else st.session_state.energy_cost_dollar_per_kwh,
        step=0.125,
        help='Electric utility rate in your local currency.'
    )
    st.session_state.energy_cost_dollar_per_kwh = energy_cost_dollar_per_kwh

    water_cost_dollar_per_m3 = col02.number_input(
        label='Water Cost [$/m^3]',
        value=3.0 if not st.session_state.water_cost_dollar_per_m3
            else st.session_state.water_cost_dollar_per_m3,
        step=0.125,
        help='Water consumption utility rate in your local currency.'
    )
    st.session_state.water_cost_dollar_per_m3 = water_cost_dollar_per_m3

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
        help="Additional power consumption you'd like to account for. This value *only impacts PUE*. "
             "Heat losses are accounted for below. *Default: 30% of IT Load.*"
    )
    st.session_state.baseline_add_power_kw = baseline_add_power_kw

    baseline_add_heat_load_kw = st.number_input(
        label='Baseline Additional Heat Load [kW]',
        value=baseline_add_power_kw * 0.9
        if not st.session_state.baseline_add_heat_load_kw else st.session_state.baseline_add_heat_load_kw,
        step=50.0,
        help="Additional heat load we will need to reject to the atmosphere. "
             "This value *does not directly impact PUE*, "
             "instead encapsulating additional thermal losses in the data center beyond IT Load. "
             "*Default: 90% of additional Power Consumption*"
    )
    st.session_state.baseline_add_heat_load_kw = baseline_add_heat_load_kw

    st.subheader('Baseline Cooling Towers')

    ct_default = False if isinstance(st.session_state.baseline_ct, eq.CoolingTower) else True
    ct = None if ct_default else st.session_state.baseline_ct

    with st.form(key='baseline_cooling_towers', clear_on_submit=False):
        cooling_tower_form(default=ct_default, ct=ct, name='baseline_ct', do_model='baseline')

    st.subheader('Baseline Chillers')

    ch_default = False if isinstance(st.session_state.baseline_chiller, eq.Chiller) else True
    ch = None if ch_default else st.session_state.baseline_chiller

    with st.form(key='baseline_chillers', clear_on_submit=False):
        chiller_form(default=ch_default, ch=ch, name='baseline_chiller', do_model='baseline')

with proposed.container():
    st.subheader('Proposed Operational Efficiency')

    proposed_add_power_kw = st.number_input(
        label='Proposed Additional Power Consumption [kW]',
        value=load_it_kw * 0.3
        if not st.session_state.proposed_add_power_kw else st.session_state.proposed_add_power_kw,
        step=50.0,
        help="Additional power consumption you'd like to account for. This value *only impacts PUE*. "
             "Heat losses are accounted for below. *Default: 30% of IT Load.*"
    )
    st.session_state.proposed_add_power_kw = proposed_add_power_kw

    proposed_add_heat_load_kw = st.number_input(
        label='Proposed Additional Heat Load [kW]',
        value=proposed_add_power_kw * 0.9
        if not st.session_state.proposed_add_heat_load_kw else st.session_state.proposed_add_heat_load_kw,
        step=50.0,
        help="Additional heat load we will need to reject to the atmosphere. "
             "This value *does not directly impact PUE*, "
             "instead encapsulating additional thermal losses in the data center beyond IT Load. "
             "*Default: 90% of additional Power Consumption*"
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
        cooling_tower_form(default=ct_default, ct=ct, name='proposed_ct', do_model='proposed')

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
        chiller_form(default=ch_default, ch=ch, name='proposed_chiller', do_model='proposed')
