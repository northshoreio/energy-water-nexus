from datetime import datetime
import requests
import pandas as pd
import numpy as np
import psychrolib
import streamlit as st
from meteostat import Point, Hourly
import plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import utils


def geocode(query: str) -> tuple:
    """
    API wrapper to geocode a given query via https://positionstack.com/
    :param query: location query to geocode
    :return: tuple of (json response, latitude, longitude)
    """

    base_url = "http://api.positionstack.com/v1/"
    response = requests.get(f"{base_url}forward?access_key={st.secrets['POSITIONSTACK_API_KEY']}&query={query}")

    if response.status_code == 200:

        resp = response.json()
        data = resp['data'][0]
        latitude, longitude = data['latitude'], data['longitude']

        return data, latitude, longitude

    else:
        raise ValueError(f"Could not geocode query '{query}'\nError: '{response.text}'")


def update_geo(query: str):
    st.session_state.location_query = query
    # utils.initialize_st_session_state(['geo', 'lat', 'lon'])

    geo, lat, lon = geocode(query=query)

    st.session_state.geo = geo
    st.session_state.lat = lat
    st.session_state.lon = lon

    st.session_state.weather_data = None


def calculate_psychrometrics(dry_bulb, dew_point, rh, pressure, unit_system: str = 'SI') -> pd.DataFrame:
    """
    Utility function on top of Psychrolib's "CalcPsychrometricsFrom__"
    functions used to handle data structure and errors.

    Args:
    dry_bulb: Series object containing Dry Bulb temperatures [F]
    dew_point: Series object containing Dew Point temperatures [F]
    rh: Series object containing Relative Humidity [%]
    pressure: Series object containing ambient air Pressure [psi]

    Returns:
    Humidity ratio in lb_H₂O lb_Air⁻¹ [IP] or kg_H₂O kg_Air⁻¹ [SI]
    Wet-bulb temperature in °F [IP] or °C [SI]
    Dew-point temperature in °F [IP] or °C [SI]
    Partial pressure of water vapor in moist air in Psi [IP] or Pa [SI]
    Moist air enthalpy in Btu lb⁻¹ [IP] or J kg⁻¹ [SI]
    Specific volume of moist air in ft³ lb⁻¹ [IP] or in m³ kg⁻¹ [SI]
    Degree of saturation [unitless]
    """

    if unit_system == 'SI':
        psychrolib.SetUnitSystem(psychrolib.SI)
        temp_units = 'C'
        pressure_units = 'Pa'
        hum_ratio_units = 'kgH2O/kgAir'
        enthalpy_units = 'J/kg'
        moist_air_volume_units = 'm^3/kg'
    elif unit_system == 'IP':
        psychrolib.SetUnitSystem(psychrolib.IP)
        temp_units = 'F'
        pressure_units = 'psi'
        hum_ratio_units = 'lbH2O/lbAir'
        enthalpy_units = 'Btu/lb'
        moist_air_volume_units = 'ft^3/lb'
    else:
        raise ValueError(f"`unit_system` parameter must be one of: `SI` or `IP`, not {unit_system}")

    df = pd.DataFrame()

    df[f'Psychrometrics (in): dry_bulb [{temp_units}]'] = dry_bulb
    if dew_point is not None:
        df[f'Psychrometrics (in): dew_point [{temp_units}]'] = dew_point
    if rh is not None:
        df[f'Psychrometrics (in): relative_humidity [%]'] = rh
    df[f'Psychrometrics (in): ambient_pressure [{pressure_units}]'] = pressure

    try:
        df[f'Psychrometrics (out): humidity_ratio [{hum_ratio_units}]'], \
            df[f'Psychrometrics (out): wet_bulb [{temp_units}]'], \
            df[f'Psychrometrics (out): dew_point [{temp_units}]'], \
            df[f'Psychrometrics (out): partial_pressure_water_vapor [{pressure_units}]'], \
            df[f'Psychrometrics (out): moist_air_enthalpy [{enthalpy_units}]'], \
            df[f'Psychrometrics (out): specific_volume_moist_air [{moist_air_volume_units}]'], \
            df[f'Psychrometrics (out): degree_of_saturation [-]'] = \
            np.vectorize(psychrolib.CalcPsychrometricsFromRelHum)(dry_bulb, rh, pressure)

    except Exception as e:
        try:
            df[f'Psychrometrics (out): humidity_ratio [{hum_ratio_units}]'], \
                df[f'Psychrometrics (out): wet_bulb [{temp_units}]'], \
                df[f'Psychrometrics (out): relative_humidity [%]'], \
                df[f'Psychrometrics (out): partial_pressure_water_vapor [{pressure_units}]'], \
                df[f'Psychrometrics (out): moist_air_enthalpy [{enthalpy_units}]'], \
                df[f'Psychrometrics (out): specific_volume_moist_air [{moist_air_volume_units}]'], \
                df[f'Psychrometrics (out): degree_of_saturation [-]'] = \
                np.vectorize(psychrolib.CalcPsychrometricsFromTDewPoint)(dry_bulb, dew_point, pressure)
        except Exception as e:
            print(f'Error: {e}', 'Did not calculate with rh or dew_point, calculating wet_bulb only..')
            df[f'Psychrometrics (out): wet_bulb [{temp_units}]'] = \
                np.vectorize(psychrolib.GetTWetBulbFromTDewPoint)(dry_bulb, dew_point, pressure)

    return df


@st.cache
def get_weather_data(unit_system: str = 'SI') -> pd.DataFrame:

    def convert_hpa_to_pa(hpa):
        return hpa * 100

    def convert_pa_to_psi(pa):
        return pa / 6_894.76

    def convert_degC_to_degF(degC):
        return (degC * 9/5) + 32

    def convert_kmh_to_mph(kmh):
        return kmh / 1.609

    # https://dev.meteostat.net/
    # TODO: dynamic datetime fetching

    weather = Hourly(
        loc=Point(lat=st.session_state.lat, lon=st.session_state.lon),
        start=datetime(2022, 1, 1),
        end=datetime(2022, 9, 27)
    ).fetch()

    if len(weather.index) < 1:
        raise ValueError(f"Weather data unavailable for {st.session_state.geo['label']}. Please try another location.")

    # https://dev.meteostat.net/formats.html#meteorological-data-units
    weather = weather[['temp', 'dwpt', 'rhum', 'pres', 'wdir', 'wspd']]
    weather.rename(columns={
        'temp': 'temperature [C]',
        'dwpt': 'dew_point [C]',
        'rhum': 'relative_humidity [%]',
        'pres': 'air_pressure [hPa]',
        'wdir': 'wind_direction [deg]',
        'wspd': 'wind_speed [km/h]'
    }, inplace=True)
    weather['air_pressure [Pa]'] = convert_hpa_to_pa(weather['air_pressure [hPa]'])

    if unit_system == 'SI':

        psychro = calculate_psychrometrics(
            dry_bulb=weather['temperature [C]'],
            dew_point=weather['dew_point [C]'],
            rh=weather['relative_humidity [%]'],
            pressure=weather['air_pressure [Pa]']
        )

    elif unit_system == 'IP':

        weather['temperature [F]'] = convert_degC_to_degF(weather['temperature [C]'])
        weather['dew_point [F]'] = convert_degC_to_degF(weather['dew_point [C]'])
        weather['air_pressure [psi]'] = convert_pa_to_psi(weather['air_pressure [Pa]'])
        weather['wind_speed [mph]'] = convert_kmh_to_mph(weather['wind_speed [km/h]'])

        psychro = calculate_psychrometrics(
            dry_bulb=weather['temperature [F]'],
            dew_point=weather['dew_point [F]'],
            rh=weather['relative_humidity [%]'],
            pressure=weather['air_pressure [psi]'],
            unit_system=unit_system
        )

    else:
        raise ValueError(f"`unit_system` parameter must be one of: `SI` or `IP`, not {unit_system}")

    weather = pd.concat([weather, psychro], axis=1)

    st.session_state.weather_data = weather
    return weather


def plot_weather_data():

    def plot_column_min_max_avg(df: pd.DataFrame, cols: list, resample_type: str = '1D'):

        for col in cols:

            dff = df[[col]].copy()
            dfr = dff.resample('1d').agg(['min', 'mean', 'max'])
            dfr.columns = dfr.columns.map(' - '.join).str.strip(' - ')

            col_min = [c for c in dfr.columns if 'min' in c][0]
            col_avg = [c for c in dfr.columns if 'mean' in c][0]
            col_max = [c for c in dfr.columns if 'max' in c][0]

            fig = go.Figure([
                go.Scatter(
                    name='Max',
                    x=dfr.index,
                    y=dfr[col_max],
                    mode='lines',
                    line=dict(color='#b76856'),
                ),
                go.Scatter(
                    name='Avg',
                    x=dfr.index,
                    y=dfr[col_avg],
                    mode='lines',
                    line=dict(color='black'),
                    fillcolor='#b76856',
                    fill='tonexty'
                ),
                go.Scatter(
                    name='Min',
                    x=dfr.index,
                    y=dfr[col_min],
                    line=dict(color='#001736'),
                    mode='lines',
                    fillcolor='#00224E',
                    fill='tonexty',
                )
            ])
            fig.update_layout(
                yaxis_title=col,
                hovermode='x',
                showlegend=False,
                title=col
            )
            st.plotly_chart(fig, use_container_width=True)

    df = st.session_state.weather_data.copy()
    col_dry_bulb = [c for c in df.columns if 'Psychrometrics (in): dry_bulb' in c][0]
    col_rh = [c for c in df.columns if 'Psychrometrics (in): relative_humidity' in c][0]
    col_wet_bulb = [c for c in df.columns if 'Psychrometrics (out): wet_bulb' in c][0]

    fig_db_wb_contour = px.density_contour(
        df,
        x=col_dry_bulb,
        y=col_wet_bulb,
        title=f"Heat Map of Dry Bulb vs Wet Bulb",
        height=600,
    )
    fig_db_wb_contour.update_traces(contours_coloring="fill", contours_showlabels=True, colorscale='Cividis')

    fig_db_rh_contour = px.density_contour(
        df,
        x=col_dry_bulb,
        y=col_rh,
        range_y=[0,100],
        title=f"Heat Map of Dry Bulb vs Relative Humidity",
        height=600,
    )
    fig_db_rh_contour.update_traces(contours_coloring="fill", contours_showlabels=True, colorscale='Cividis')

    col01, col02 = st.columns(2)

    col01.plotly_chart(fig_db_rh_contour, use_container_width=True)
    col02.plotly_chart(fig_db_wb_contour, use_container_width=True)

    plot_column_min_max_avg(df, [col_dry_bulb, col_wet_bulb])


def __app_set_location__():
    st.subheader('Search for any location')

    location_query_placeholder = st.session_state.location_query if st.session_state.location_query else 'Singapore'

    location_query = st.text_input(
        label='Location query',
        placeholder=location_query_placeholder,
        help='Search for any location as when using mapping applications.'
    )

    if location_query:

        if location_query != st.session_state.location_query:
            update_geo(location_query)

    if st.session_state.geo:
        geo = st.session_state.geo
        lat = st.session_state.lat
        lon = st.session_state.lon

        st.markdown(f"#### {geo['label']}")
        st.map(pd.DataFrame.from_dict({'lat': [lat], 'lon': [lon]}))


def __app_set_weather__():
    if st.session_state.geo:

        if not isinstance(st.session_state.weather_data, pd.DataFrame):

            if st.button(label="Get Weather Data"):
                df_weather = get_weather_data(
                    unit_system='SI' if st.session_state.geo['country_code'] != 'USA' else 'IP'
                )

        if isinstance(st.session_state.weather_data, pd.DataFrame):

            st.subheader("Weather Data")
            plot_weather_data()

            with st.expander('View Raw Weather Data'):
                st.dataframe(st.session_state.weather_data)
                st.download_button(
                    label='Download as CSV',
                    data=st.session_state.weather_data.to_csv().encode('utf-8'),
                    file_name=f"weather_data_{st.session_state.geo['label'].replace(', ', '_')}.csv"
                )


st.set_page_config(
    page_title="Weather",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "https://github.com/northshoreio",
        "Get help": "mailto:sam.zastrow@northshore.io"
    }
)
with st.sidebar:
    st.info('Geocoding provided by [positionstack](https://positionstack.com/)', icon='🗺️')
    st.info('Weather data provided by [Metostat](https://dev.meteostat.net/)', icon='🌤️')
    st.info('Psychrometrics calculated with [PsychroLib](https://github.com/psychrometrics/psychrolib)', icon='🌡️')

utils.initialize_st_session_state(['location_query', 'geo', 'lat', 'lon', 'weather_data'])

st.header('Weather Data Acquisition and Analysis')

__app_set_location__()
__app_set_weather__()
