import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from models import simulate as sim
import utils


def update_design_inputs(scope, name, value):
    if scope == 'ct':
        ct = st.session_state.proposed_ct
        setattr(ct, name, value)
        st.write(str(ct))
        st.session_state.proposed_ct = ct
    elif scope == 'chiller':
        setattr(st.session_state.proposed_chiller, name, value)
    else:
        st.session_state[f"proposed_{name}"] = value


def compare_design_inputs() -> dict:
    def __compare_dicts__(baseline, proposed):
        diff = {}
        for key, b, p in zip(baseline.keys(), baseline.values(), proposed.values()):
            if b != p:
                diff[key] = {
                    'baseline': b,
                    'proposed': p
                }
        return diff

    diff_common = __compare_dicts__(
        baseline={
            'add_power_kw': st.session_state.baseline_add_power_kw,
            'add_heat_load_kw': st.session_state.baseline_add_heat_load_kw
        },
        proposed={
            'add_power_kw': st.session_state.proposed_add_power_kw,
            'add_heat_load_kw': st.session_state.proposed_add_heat_load_kw
        }
    )

    diff_ct = __compare_dicts__(
        baseline=st.session_state.baseline_ct.__dict__,
        proposed=st.session_state.proposed_ct.__dict__
    )
    diff_ct = {f'ct_{k}': v for k, v in diff_ct.items()}

    diff_chiller = __compare_dicts__(
        baseline=st.session_state.baseline_chiller.__dict__,
        proposed=st.session_state.proposed_chiller.__dict__
    )
    diff_chiller = {f'chiller_{k}': v for k, v, in diff_chiller.items()}

    return {**diff_common, **diff_ct, **diff_chiller}


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
    b_energy_cost = round(baseline['Energy Cost [$]'].sum(), 0)
    b_water_cost = round(baseline['Water Cost [$]'].sum(), 0)

    b_pue = round(b_energy_kwh / b_it_energy_kwh, 2)
    b_wue = round(b_water_liters / b_it_energy_kwh, 2)

    p_energy_kwh = round(proposed['total_power_consumption [kW]'].sum(), 0)
    p_it_energy_kwh = proposed['it_load_kw'].sum()
    p_water_liters = round(proposed['ct_makeup_flowrate_total [m^3]'].sum() * 1000, 0)
    p_energy_cost = round(proposed['Energy Cost [$]'].sum(), 0)
    p_water_cost = round(proposed['Water Cost [$]'].sum(), 0)

    p_pue = round(p_energy_kwh / p_it_energy_kwh, 2)
    p_wue = round(p_water_liters / p_it_energy_kwh, 2)

    p_energy_savings_kwh = round(b_energy_kwh - p_energy_kwh, 0)
    p_energy_cost_savings = round(b_energy_cost - p_energy_cost, 0)
    p_water_savings_liters = round(b_water_liters - p_water_liters, 0)
    p_water_cost_savings = round(b_water_cost - p_water_cost, 0)
    p_total_cost_savings = p_energy_cost_savings + p_water_cost_savings

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
        'proposed_water_savings_liters': p_water_savings_liters,
        'baseline_total_energy_cost': b_energy_cost,
        'baseline_total_water_cost': b_water_cost,
        'baseline_total_cost': b_energy_cost + b_water_cost,
        'proposed_total_energy_cost': p_energy_cost,
        'proposed_total_water_cost': p_water_cost,
        'proposed_total_cost': p_energy_cost + p_water_cost,
        'proposed_energy_cost_savings': p_energy_cost_savings,
        'proposed_water_cost_savings': p_water_cost_savings,
        'proposed_total_cost_savings': p_total_cost_savings
    }


def plot_performance_metrics(metrics, baseline, proposed, energy_savings_kwh, water_savings_liters):
    col01, col02 = st.columns(2)

    delta_value = -round(metrics['baseline_pue'] - metrics['proposed_pue'], 2)
    col01.metric(
        label='🔌 PUE',
        value=metrics['proposed_pue'],
        delta=delta_value,
        delta_color='inverse' if delta_value != 0 else 'off',
        help='**Power Usage Effectiveness** [-] *relative to baseline design*'
    )
    delta_value = int(-metrics['proposed_energy_savings_kwh'])
    col01.metric(
        label='🔌 Annual Energy Consumption',
        value=f"{int(round(metrics['proposed_total_energy_consumption_kwh'], -2)):,}",
        delta=f"{delta_value:,}",
        delta_color='inverse' if delta_value != 0 else 'off',
        help='**Annualized Energy Consumption** [kWh] *relative to baseline design*'
    )
    delta_value = round(energy_savings_kwh / metrics['baseline_total_energy_consumption_kwh'], 3)
    col01.metric(
        label='🔌 Energy Savings',
        value=f"${int(metrics['proposed_energy_cost_savings']):,}",
        delta=f"{delta_value:.1%}",
        delta_color='normal' if delta_value != 0 else 'off',
        help='Percent improvement and cost savings *relative to baseline design*',
    )
    delta_value = -round(metrics['baseline_wue'] - metrics['proposed_wue'], 2)
    col02.metric(
        label='💧 WUE',
        value=metrics['proposed_wue'],
        delta=delta_value,
        delta_color='inverse' if delta_value != 0 else 'off',
        help='**Water Usage Effectiveness** [L/kWh] relative to baseline design'
    )
    delta_value = int(-metrics['proposed_water_savings_liters'])
    col02.metric(
        label='💧 Annual Water Consumption',
        value=f"{int(round(metrics['proposed_total_water_consumption_liters'], -2)):,}",
        delta=f"{delta_value:,}",
        delta_color='inverse' if delta_value != 0 else 'off',
        help='**Annualized Water Consumption** [L] *relative to baseline design*'
    )
    delta_value = round(water_savings_liters / metrics['baseline_total_water_consumption_liters'], 3)
    col02.metric(
        label='💧 Water Savings',
        value=f"${int(metrics['proposed_water_cost_savings']):,}",
        delta=f"{delta_value:.1%}",
        delta_color='normal' if delta_value != 0 else 'off',
        help='Percent improvement and cost savings *relative to baseline design*',
    )
    delta_value = round(metrics['proposed_total_cost_savings'] / metrics['baseline_total_cost'], 3)
    col01.metric(
        label='🔌 Total Savings 💧',
        value=f"${int(metrics['proposed_total_cost_savings']):,}",
        delta=f"{delta_value:.1%}",
        delta_color='normal' if delta_value != 0 else 'off',
        help='Percent improvement and cost savings *relative to baseline design*',
    )


def plot_results(baseline, proposed):
    def __update_legend_bottom_left__(fig):
        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4,
            xanchor="left",
            x=0
        ))

    st.subheader('Performance Insights')

    comparison = pd.DataFrame({
        'baseline_total_water_consumption [m^3]': baseline['ct_makeup_flowrate_total [m^3]'],
        'proposed_total_water_consumption [m^3]': proposed['ct_makeup_flowrate_total [m^3]']
    })
    comparison.index = baseline.index

    fig_pue_wue_time = make_subplots(specs=[[{'secondary_y': True}]])
    fig_pue_wue_time.add_trace(
        go.Line(
            x=proposed.index,
            y=proposed['PUE [-]'],
            name='PUE [-]',
            line=dict(color='#2f964a')
        ),
        secondary_y=False,
    )
    fig_pue_wue_time.add_trace(
        go.Line(
            x=proposed.index,
            y=proposed['WUE [L/kWh]'],
            name='WUE [L/kWh]',
            line=dict(color='#161870')
        ),
        secondary_y=True
    )
    fig_pue_wue_time.update_layout(title_text='Performance over Time')
    fig_pue_wue_time.update_yaxes(title_text="PUE [-]", secondary_y=False)
    fig_pue_wue_time.update_yaxes(title_text="WUE [L/kWh]", secondary_y=True)
    __update_legend_bottom_left__(fig_pue_wue_time)
    st.plotly_chart(fig_pue_wue_time, use_container_width=True)

    unit_system = 'SI' if st.session_state.geo['country_code'] != 'USA' else 'IP'
    temp_units = '[C]' if unit_system == 'SI' else '[F]'

    col_dry_bulb = f'Psychrometrics (in): dry_bulb {temp_units}'
    col_rh = f'Psychrometrics (in): relative_humidity [%]'
    col_wet_bulb = f'Psychrometrics (out): wet_bulb {temp_units}'

    col01, col02 = st.columns(2)

    fig_pue_wue_heatmap = px.density_contour(
        proposed,
        x='PUE [-]',
        range_x=[proposed['PUE [-]'].min(), proposed['PUE [-]'].max()],
        y='WUE [L/kWh]',
        range_y=[proposed['WUE [L/kWh]'].min(), proposed['WUE [L/kWh]'].max()],
        title=f"Heat Map of PUE vs WUE",
        height=600,
    )
    fig_pue_wue_heatmap.update_traces(contours_coloring="fill", contours_showlabels=True, colorscale='Cividis', showscale=False)
    col01.plotly_chart(fig_pue_wue_heatmap, use_container_width=True)

    fig_water_cumsum_heatmap = px.density_heatmap(
        proposed,
        x=proposed.index,
        y=col_wet_bulb,
        z='ct_makeup_flowrate_total [m^3]',
        nbinsx=365,
        histfunc='sum',
        height=600,
        color_continuous_scale='Cividis',
        title='Cumulative Water Consumption by Day and Wetbulb'
    )
    fig_water_cumsum_heatmap.update(layout_coloraxis_showscale=False)
    col02.plotly_chart(fig_water_cumsum_heatmap, use_container_width=True)

    wetbulb_bin_count = int(proposed[col_wet_bulb].max() - proposed[col_wet_bulb].min()) * 4
    fig_water_consumption_by_wetbulb = px.histogram(
        proposed,
        x=col_wet_bulb,
        y=[
            'ct_makeup_flowrate_evaporation [m^3]',
            'ct_makeup_flowrate_drift [m^3]',
            'ct_makeup_flowrate_blowdown [m^3]'
        ],
        histfunc='sum',
        height=600,
        nbins=wetbulb_bin_count,
        title='Water Consumption by Wetbulb and End-Use'
    )
    __update_legend_bottom_left__(fig_water_consumption_by_wetbulb)
    col01.plotly_chart(fig_water_consumption_by_wetbulb, use_container_width=True)

    fig_water_consumption_comparison = px.line(
        comparison,
        x=comparison.index,
        y=[
            'baseline_total_water_consumption [m^3]',
            'proposed_total_water_consumption [m^3]'
        ],
        height=600,
        title='Total Water Consumption | Baseline vs Proposed',
        color_discrete_map={
            'baseline_total_water_consumption [m^3]': '#161870',
            'proposed_total_water_consumption [m^3]': '#2f964a'
        }
    )
    __update_legend_bottom_left__(fig_water_consumption_comparison)
    col02.plotly_chart(fig_water_consumption_comparison, use_container_width=True)


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

# different_inputs = compare_design_inputs()
#
# if len(different_inputs.keys()) > 0:
#
#     with st.sidebar.form('proposed_updated_inputs'):
#
#         update_inputs_mapping = {}
#         for k, v in different_inputs.items():
#
#             if k.startswith('ct_'):
#                 scope = 'ct'
#             elif k.startswith('chiller_'):
#                 scope = 'chiller'
#             else:
#                 scope = 'common'
#
#             new_value = st.number_input(
#                 label=f"Proposed {k.replace('_', ' ').title()}",
#                 value=v['proposed'],
#             )
#             update_inputs_mapping[k] = {'scope': scope, 'value': new_value}
#
#         if st.form_submit_button('Resimulate'):
#
#             for k, v in update_inputs_mapping.items():
#
#                 scope = v['scope']
#                 new_value = v['value']
#                 update_design_inputs(scope, k, new_value)
#
#             st.experimental_rerun()

baseline, proposed = simulate()
metrics = get_performance_metrics(baseline, proposed)

energy_savings_kwh = metrics['proposed_energy_savings_kwh']
water_savings_liters = metrics['proposed_water_savings_liters']

st.header('Performance')
plot_performance_metrics(metrics, baseline, proposed, energy_savings_kwh, water_savings_liters)
plot_results(baseline, proposed)

savings_water_consumption_liters = metrics['proposed_water_savings_liters']

savings_water_consumption_annual_persons_drink_water = \
        int(np.floor(savings_water_consumption_liters / (utils.HUMAN_DAILY_DRINKING_WATER_REQUIREMENT_LITERS * 365)))

savings_water_consumption_olympic_sized_swimming_pools = \
    savings_water_consumption_liters / utils.VOLUME_OF_OLYMPIC_SIZED_SWIMMING_POOL_LITERS

if savings_water_consumption_liters > 0:

    st.subheader('Water Consumption Savings')

    st.markdown(
        f'The proposed design is estimated to save **{int(savings_water_consumption_liters):,}** '
        f'Liters annually, equivalent to the **annual drinking water** for over '
        f'**{savings_water_consumption_annual_persons_drink_water:,}** people!'
    )
    if savings_water_consumption_annual_persons_drink_water >= 1_000:
        persons = int(savings_water_consumption_annual_persons_drink_water / 1_000)
        persons_text = '(each 🤤️ represents 1,000 people)'
    elif savings_water_consumption_annual_persons_drink_water >= 100:
        persons = int(savings_water_consumption_annual_persons_drink_water / 100)
        persons_text = '(each 🤤️ represents 100 people)'
    else:
        persons = savings_water_consumption_annual_persons_drink_water
        persons_text = '(each 🤤️ represents 1 person)'

    st.write('🤤️' * persons + f' {persons_text}')

    if savings_water_consumption_olympic_sized_swimming_pools >= 1:

        st.sidebar.info(
            '(1) Olympic-Sized Swimming Pool is [approximately 2,500,000 Liters]'
            '(https://en.wikipedia.org/wiki/Olympic-size_swimming_pool)',
            icon='🏊‍♀️'
        )

        st.markdown(
            f'Which adds up to **{round(savings_water_consumption_olympic_sized_swimming_pools, 1):,}** '
            f'Olympic-Sized Swimming Pools!'
        )
        st.write('🏊‍♀️' * int(np.floor(savings_water_consumption_olympic_sized_swimming_pools)))

with st.expander('View Raw Results'):
    col01, col02 = st.columns(2)
    col01.text('Baseline Model')
    col01.dataframe(baseline)
    col01.download_button(
        label='Download as CSV',
        data=baseline.to_csv().encode('utf-8'),
        file_name=f"baseline.csv"
    )
    col02.text('Proposed Model')
    col02.dataframe(proposed)
    col02.download_button(
        label='Download as CSV',
        data=baseline.to_csv().encode('utf-8'),
        file_name=f"proposed.csv"
    )
