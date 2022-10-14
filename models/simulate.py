import pandas as pd
import numpy as np
import streamlit as st
from dataclasses import dataclass
import utils


def build_common_model():

    weather = st.session_state.weather_data
    model = weather.copy()

    drybulb_c = model['temperature [C]'].to_numpy()
    wetbulb_c = model['Psychrometrics (out): wet_bulb [C]'].to_numpy()
    humidity_ratio_kgh2o_kgair = model['Psychrometrics (out): humidity_ratio [kgH2O/kgAir]'].to_numpy()
    pressure_pa = model['air_pressure [Pa]'].to_numpy()
    specific_volume_moist_air = model['Psychrometrics (out): specific_volume_moist_air [m^3/kg]'].to_numpy()

    model['it_load_kw'] = st.session_state.load_it_kw

    return model, drybulb_c, wetbulb_c, humidity_ratio_kgh2o_kgair, pressure_pa, specific_volume_moist_air


def apply_operational_efficiencies(model, baseline: bool = True):

    if baseline:
        add_power_kw = st.session_state.baseline_add_power_kw
        add_heat_load_kw = st.session_state.baseline_add_heat_load_kw
    else:
        add_power_kw = st.session_state.proposed_add_power_kw
        add_heat_load_kw = st.session_state.proposed_add_heat_load_kw

    model['additional_power_kw'] = add_power_kw
    model['additional_heat_load_kw'] = add_heat_load_kw
    model['total_heat_load_kw'] = st.session_state.load_it_kw + add_heat_load_kw

    return model


@dataclass
class WaterCooledChiller:

    drybulb_c: np.ndarray = None
    wetbulb_c: np.ndarray = None
    humidity_ratio_kgh2o_kgair: np.ndarray = None
    pressure_pa: np.ndarray = None
    specific_volume_moist_air: np.ndarray = None

    baseline: pd.DataFrame = None
    proposed: pd.DataFrame = None

    def simulate(self, do_model: str = 'both'):

        def __set_cooling_tower_params__(model, ct):
            model['ct_range_c'] = ct.design_range_c
            model['ct_tws_temp_setpoint_c'] = ct.operating_tower_water_supply_temperature_c
            model['ct_design_air_flowrate_m3_hr'] = ct.design_air_flowrate_m3_hr
            model['ct_design_water_flowrate_m3_hr'] = ct.design_water_flowrate_m3_hr
            model['ct_reference_fr_water'] = ct.get_reference_water_volumetric_flowrate()
            return model

        def __simulate_cooling_tower__(model, ct, ch):

            range_c = model['ct_range_c'].to_numpy()
            tws_temp_setpoint_c = model['ct_tws_temp_setpoint_c'].to_numpy()
            design_air_flowrate_m3_hr = model['ct_design_air_flowrate_m3_hr'].to_numpy()
            design_water_flowrate_m3_hr = model['ct_design_water_flowrate_m3_hr'].to_numpy()

            total_heat_load_kw = model['total_heat_load_kw']
            # accounting for estimate of heat load from chiller compressor
            total_heat_load_kw = total_heat_load_kw + total_heat_load_kw / ch.design_cop

            design_water_mass_flowrate_kg_s = \
                (design_water_flowrate_m3_hr / 3600) * utils.STANDARD_DENSITY_OF_WATER_KG_M3

            # q = m * cp * dT
            required_water_flowrate_kg_s = total_heat_load_kw / (utils.SPECIFIC_HEAT_CAPACITY_OF_WATER_KJ_KGC * range_c)
            fr_water = np.minimum(
                required_water_flowrate_kg_s / design_water_mass_flowrate_kg_s * 1.1,
                np.full_like(design_water_mass_flowrate_kg_s, fill_value=1.0)
            )

            tws_temp_at_max_fan_c = np.vectorize(ct.get_tws_temp_at_max_fan)(
                fr_water=fr_water,
                wetbulb_c=self.wetbulb_c,
                range_c=range_c
            )

            tws_temp_free_convection_c = np.vectorize(ct.get_tws_temp_free_convection)(
                tws_temp_at_max_fan_c=tws_temp_at_max_fan_c,
                twr_temp_c=tws_temp_setpoint_c + range_c
            )

            tws_temp, fr_air = np.vectorize(ct.get_tws_temp_and_fr_air)(
                fr_water=fr_water,
                tws_temp_at_max_fan_c=tws_temp_at_max_fan_c,
                tws_temp_free_convection_c=tws_temp_free_convection_c,
                tws_temp_setpoint_c=tws_temp_setpoint_c,
                wetbulb_c=self.wetbulb_c
            )

            ct_fan_kw = np.vectorize(ct.get_fan_power)(fr_air=fr_air)

            makeup_flowrate_evaporation_m3_s, makeup_flowrate_drift_m3_s, \
                makeup_flowrate_blowdown_m3_s, makeup_flowrate_total_m3_s = np.vectorize(
                    ct.get_makeup_water_usage
                )(
                    drybulb_c=self.drybulb_c,
                    humidity_ratio_kgh2o_kgair=self.humidity_ratio_kgh2o_kgair,
                    pressure_pa=self.pressure_pa,
                    specific_volume_moist_air=self.specific_volume_moist_air,
                    air_flowrate_m3_hr=design_air_flowrate_m3_hr * fr_air,
                    water_flowrate_m3_s=required_water_flowrate_kg_s / utils.STANDARD_DENSITY_OF_WATER_KG_M3,
                    fr_air=fr_air
                )

            results = pd.DataFrame({
                'ct_tower_water_supply_temp_at_max_fan [C]': tws_temp_at_max_fan_c,
                'ct_tower_water_supply_temp_free_convection [C]': tws_temp_free_convection_c,
                'ct_tower_water_supply_temp [C]': tws_temp,
                'ct_operating_fr_water [-]': fr_water,
                'ct_air_flowrate_ratio [-]': fr_air,
                'ct_fan_power [kW]': ct_fan_kw,
                'ct_makeup_flowrate_evaporation [m^3]': makeup_flowrate_evaporation_m3_s * 3600,
                'ct_makeup_flowrate_drift [m^3]': makeup_flowrate_drift_m3_s * 3600,
                'ct_makeup_flowrate_blowdown [m^3]': makeup_flowrate_blowdown_m3_s * 3600,
                'ct_makeup_flowrate_total [m^3]': makeup_flowrate_total_m3_s * 3600
            })
            results.index = model.index

            return pd.concat([model, results], axis=1)

        def __set_chiller_params__(model, chiller):
            model['chiller_design_cooling_capacity_kw'] = chiller.design_cooling_capacity_kw
            model['chiller_design_chw_supply_temp_c'] = chiller.design_chw_supply_temperature_c
            return model

        def __simulate_chiller__(model, chiller):

            heat_load_kw = model['total_heat_load_kw'].to_numpy()

            chw_supply_temp = model['chiller_design_chw_supply_temp_c'].to_numpy()
            ct_tower_water_supply_temp = model['ct_tower_water_supply_temp [C]'].to_numpy()

            cooling_capacity_kw = np.vectorize(chiller.get_cooling_capacity)(
                chw_leaving_temp_c=chw_supply_temp,
                cw_entering_temp_c=ct_tower_water_supply_temp
            )

            power_kw, eir_plr, eir_temps = np.vectorize(chiller.get_power)(
                chw_leaving_temp_c=chw_supply_temp,
                cw_entering_temp_c=ct_tower_water_supply_temp,
                cooling_output_kw=heat_load_kw
            )

            cop = heat_load_kw / power_kw

            results = pd.DataFrame({
                'chiller_operating_cooling_capacity [kW]': cooling_capacity_kw,
                'chiller_electric_input_ratio_function_of_part_load_ratio [-]': eir_plr,
                'chiller_electric_input_ratio_function_of_temperatures [-]': eir_temps,
                'chiller_power [kW]': power_kw,
                'chiller_coefficient_of_performance [-]': cop
            })
            results.index = model.index

            return pd.concat([model, results], axis=1)

        def __set_performance_metrics__(model):
            def __calculate_cumsum_water__(df) -> pd.DataFrame:
                water_cumsum = df[[
                    'ct_makeup_flowrate_evaporation [m^3]',
                    'ct_makeup_flowrate_drift [m^3]',
                    'ct_makeup_flowrate_blowdown [m^3]',
                    'ct_makeup_flowrate_total [m^3]'
                ]].cumsum()
                water_cumsum.rename(
                    columns={col: f"{col.split(' ')[0]}_cumulative {col.split(' ')[1]}" for col in
                             water_cumsum.columns},
                    inplace=True
                )
                water_cumsum.index = df.index
                return pd.concat([df, water_cumsum], axis=1)

            model['total_power_consumption [kW]'] = model['it_load_kw'] + model['additional_power_kw'] + \
                model['ct_fan_power [kW]'] + model['chiller_power [kW]']

            model['PUE [-]'] = model['total_power_consumption [kW]'] / model['it_load_kw']

            #  hourly timestep, so 1 kW = 1 kWh
            model['WUE [L/kWh]'] = (model['ct_makeup_flowrate_total [m^3]'] * 1000) / (model['it_load_kw'] * 1)

            model = __calculate_cumsum_water__(df=model)

            model['Water Cost [$]'] = model['ct_makeup_flowrate_total [m^3]'] * \
                st.session_state.water_cost_dollar_per_m3

            #  hourly timestep, so 1 kW = 1 kWh
            model['Energy Cost [$]'] = model['total_power_consumption [kW]'] * 1 * \
                st.session_state.energy_cost_dollar_per_kwh

            return model

        common_model, self.drybulb_c, self.wetbulb_c, self.humidity_ratio_kgh2o_kgair, \
            self.pressure_pa, self.specific_volume_moist_air = build_common_model()

        if do_model == 'both' or do_model == 'baseline':

            with st.spinner('Simulating Baseline...'):

                self.baseline = apply_operational_efficiencies(common_model.copy(), baseline=True)
                ct_b = st.session_state.baseline_ct
                ch_b = st.session_state.baseline_chiller

                self.baseline = __set_cooling_tower_params__(self.baseline, ct_b)
                self.baseline = __simulate_cooling_tower__(self.baseline, ct=ct_b, ch=ch_b)
                self.baseline = __set_chiller_params__(self.baseline, ch_b)
                self.baseline = __simulate_chiller__(self.baseline, ch_b)

                self.baseline = __set_performance_metrics__(self.baseline)

        if do_model == 'both' or do_model == 'proposed':

            with st.spinner('Simulating Proposed...'):

                self.proposed = apply_operational_efficiencies(common_model.copy(), baseline=False)
                ct_p = st.session_state.proposed_ct
                ch_p = st.session_state.proposed_chiller

                self.proposed = __set_cooling_tower_params__(self.proposed, ct_p)
                self.proposed = __simulate_cooling_tower__(self.proposed, ct=ct_p, ch=ch_p)
                self.proposed = __set_chiller_params__(self.proposed, ch_p)
                self.proposed = __simulate_chiller__(self.proposed, ch_p)

                self.proposed = __set_performance_metrics__(self.proposed)

        return self.baseline, self.proposed
