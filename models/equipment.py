import streamlit
from scipy import optimize
import psychrolib
from dataclasses import dataclass, fields
import utils


@dataclass
class CurveBiquadratic:
    constant: float
    x: float
    x2: float
    y: float
    y2: float
    xy: float
    x_min: float
    x_max: float
    y_min: float
    y_max: float


@dataclass
class CurveQuadratic:
    constant: float
    x: float
    x2: float
    x_min: float
    x_max: float


@dataclass
class CoolingTower:
    """
    Equipment class to define and simulate Cooling Towers.
    All calculations implemented from EnergyPlus's reference documentation:
    https://bigladdersoftware.com/epx/docs/8-3/engineering-reference/cooling-towers-and-evaporative-fluid.html#variable-speed-cooling-towers-empirical-models
    """
    design_wetbulb_c: float
    design_approach_c: float
    design_range_c: float
    design_water_flowrate_m3_hr: float
    design_air_flowrate_m3_hr: float
    design_fan_power_kw: float
    operating_tower_water_supply_temperature_c: float
    count: int = 1
    operating_cycles_of_concentration: float = 3.5
    operating_percent_of_water_loss_to_drift: float = 0.02
    __minimum_range_c__: float = 2.7777777
    __maximum_water_flowrate_ratio__: float = 1.0
    __minimum_air_flowrate_ratio__: float = 0.2
    __maximum_air_flowrate_ratio__: float = 1.0
    __tower_capacity_fraction_free_convection_regime__: float = 0.125
    """
    CoolTools model correlation coefficients
     (https://bigladdersoftware.com/epx/docs/8-3/engineering-reference/cooling-towers-and-evaporative-fluid.html#tower-heat-rejection)
    """
    __cool_tools_coefficients__: tuple = (
        None,  # blank 0th element for alignment with CoolTools definition
        0.52049709836241,  # c[1]
        -10.617046395344,  # c[2]
        10.7292974722538,  # c[3]
        -2.74988377158227,  # c[4]
        4.73629943913743,  # c[5]
        -8.25759700874711,  # c[6]
        1.57640938114136,  # c[7]
        6.51119643791324,  # c[8]
        1.50433525206692,  # c[9]
        -3.2888529287801,  # c[10]
        0.0257786145353773,  # c[11]
        0.182464289315254,  # c[12]
        -0.0818947291400898,  # c[13]
        -0.215010003996285,  # c[14]
        0.0186741309635284,  # c[15]
        0.0536824177590012,  # c[16]
        -0.00270968955115031,  # c[17]
        0.00112277498589279,  # c[18]
        -0.00127758497497718,  # c[19]
        0.0000760420796601607,  # c[20]
        1.43600088336017,  # c[21]
        -0.5198695909109,  # c[22]
        0.117339576910507,  # c[23]
        1.50492810819924,  # c[24]
        -0.135898905926974,  # c[25]
        -0.152577581866506,  # c[26]
        -0.0533843828114562,  # c[27]
        0.00493294869565511,  # c[28]
        -0.00796260394174197,  # c[29]
        0.000222619828621544,  # c[30]
        -0.0543952001568055,  # c[31]
        0.00474266879161693,  # c[32]
        -0.0185854671815598,  # c[33]
        0.00115667701293848,  # c[34]
        0.000807370664460284  # c[35]
    )

    def __get_approach_temp__(self, fr_water, fr_air, wetbulb_c, range_c):
        return (
                + self.__cool_tools_coefficients__[1]
                + self.__cool_tools_coefficients__[2] * fr_air
                + self.__cool_tools_coefficients__[3] * fr_air ** 2
                + self.__cool_tools_coefficients__[4] * fr_air ** 3
                + self.__cool_tools_coefficients__[5] * fr_water
                + self.__cool_tools_coefficients__[6] * fr_air * fr_water
                + self.__cool_tools_coefficients__[7] * fr_air ** 2 * fr_water
                + self.__cool_tools_coefficients__[8] * fr_water ** 2
                + self.__cool_tools_coefficients__[9] * fr_air * fr_water ** 2
                + self.__cool_tools_coefficients__[10] * fr_water ** 3
                + self.__cool_tools_coefficients__[11] * wetbulb_c
                + self.__cool_tools_coefficients__[12] * fr_air * wetbulb_c
                + self.__cool_tools_coefficients__[13] * fr_air ** 2 * wetbulb_c
                + self.__cool_tools_coefficients__[14] * fr_water * wetbulb_c
                + self.__cool_tools_coefficients__[15] * fr_air * fr_water * wetbulb_c
                + self.__cool_tools_coefficients__[16] * fr_water ** 2 * wetbulb_c
                + self.__cool_tools_coefficients__[17] * wetbulb_c ** 2
                + self.__cool_tools_coefficients__[18] * fr_air * wetbulb_c ** 2
                + self.__cool_tools_coefficients__[19] * fr_water * wetbulb_c ** 2
                + self.__cool_tools_coefficients__[20] * wetbulb_c ** 3
                + self.__cool_tools_coefficients__[21] * range_c
                + self.__cool_tools_coefficients__[22] * fr_air * range_c
                + self.__cool_tools_coefficients__[23] * fr_air ** 2 * range_c
                + self.__cool_tools_coefficients__[24] * fr_water * range_c
                + self.__cool_tools_coefficients__[25] * fr_air * fr_water * range_c
                + self.__cool_tools_coefficients__[26] * fr_water ** 2 * range_c
                + self.__cool_tools_coefficients__[27] * wetbulb_c * range_c
                + self.__cool_tools_coefficients__[28] * fr_air * wetbulb_c * range_c
                + self.__cool_tools_coefficients__[29] * fr_water * wetbulb_c * range_c
                + self.__cool_tools_coefficients__[30] * wetbulb_c ** 2 * range_c
                + self.__cool_tools_coefficients__[31] * range_c ** 2
                + self.__cool_tools_coefficients__[32] * fr_air * range_c ** 2
                + self.__cool_tools_coefficients__[33] * fr_water * range_c ** 2
                + self.__cool_tools_coefficients__[34] * wetbulb_c * range_c ** 2
                + self.__cool_tools_coefficients__[35] * range_c ** 3
        )

    def get_reference_water_volumetric_flowrate(self):
        def __solve_approach_temp__(fr_water):
            calc_approach_c = self.__get_approach_temp__(
                fr_water=fr_water,
                fr_air=1.0,
                wetbulb_c=self.design_wetbulb_c,
                range_c=self.design_range_c
            )
            return abs(self.design_approach_c - calc_approach_c)

        return min(optimize.newton(__solve_approach_temp__, 0.5), self.__maximum_water_flowrate_ratio__)

    def get_tws_temp_at_max_fan(self, fr_water, wetbulb_c, range_c=None):

        fr_air = 1.0
        range_c = range_c if range_c else self.design_range_c

        approach_temp_design_range = self.__get_approach_temp__(
            fr_water=fr_water,
            fr_air=fr_air,
            wetbulb_c=wetbulb_c,
            range_c=range_c
        )

        return wetbulb_c + approach_temp_design_range

    def get_tws_temp_free_convection(self, tws_temp_at_max_fan_c, twr_temp_c):
        return twr_temp_c - (
                self.__tower_capacity_fraction_free_convection_regime__ * (twr_temp_c - tws_temp_at_max_fan_c)
        )

    def get_tws_temp_and_fr_air(
            self,
            fr_water,
            tws_temp_at_max_fan_c,
            tws_temp_free_convection_c,
            tws_temp_setpoint_c,
            wetbulb_c,
            range_c=None
    ):
        def __solve_fr_air__(fr_air_estimate):
            calc_approach_temp = self.__get_approach_temp__(
                fr_water=fr_water,
                fr_air=fr_air_estimate,
                wetbulb_c=wetbulb_c,
                range_c=range_c
            )
            calc_tws_temp_c = wetbulb_c + calc_approach_temp
            return abs(tws_temp_setpoint_c - calc_tws_temp_c)

        range_c = range_c if range_c else self.design_range_c

        if tws_temp_at_max_fan_c > tws_temp_setpoint_c:
            return tws_temp_at_max_fan_c, 1.0

        elif tws_temp_free_convection_c <= tws_temp_setpoint_c:
            return tws_temp_setpoint_c, 0.0

        else:
            fr_air = optimize.minimize_scalar(
                __solve_fr_air__,
                bounds=(self.__minimum_air_flowrate_ratio__, self.__maximum_air_flowrate_ratio__),
                method='bounded'
            ).x
            approach_temp_c = self.__get_approach_temp__(
                fr_water=fr_water,
                fr_air=fr_air,
                wetbulb_c=wetbulb_c,
                range_c=range_c
            )
            return wetbulb_c + approach_temp_c, fr_air

    def get_fan_power(self, fr_air):
        return self.design_fan_power_kw * fr_air ** 3

    def get_makeup_water_usage(
            self,
            drybulb_c,
            humidity_ratio_kgh2o_kgair,
            pressure_pa,
            specific_volume_moist_air,
            air_flowrate_m3_hr,
            water_flowrate_m3_s,
            fr_air,
            unit_system: str = 'SI'
    ):
        def calculate_evaporation():

            if unit_system == 'SI':
                psychrolib.SetUnitSystem(psychrolib.SI)
            elif unit_system == 'IP':
                psychrolib.SetUnitSystem(psychrolib.IP)
            else:
                raise ValueError(f"`unit_system` parameter must be one of: `SI` or `IP`, not {unit_system}")

            air_mass_flowrate_kg_hr = air_flowrate_m3_hr / specific_volume_moist_air
            air_mass_flowrate_kg_s = air_mass_flowrate_kg_hr / 3600

            saturated_humidity_ratio_kgh2o_kgair = psychrolib.GetSatHumRatio(TDryBulb=drybulb_c, Pressure=pressure_pa)

            return max(
                air_mass_flowrate_kg_s * (saturated_humidity_ratio_kgh2o_kgair - humidity_ratio_kgh2o_kgair),
                0
            ) / utils.STANDARD_DENSITY_OF_WATER_KG_M3

        def calculate_drift():
            """
            Drift is water loss due to the entrainment of small water droplets in the air stream
            passing through the tower.
            :return:
            """
            return max(
                water_flowrate_m3_s * (self.operating_percent_of_water_loss_to_drift / 100) * fr_air,
                0
            )

        def calculate_blowdown(flowrate_evaporation_m3_s, flowrate_drift_m3_s):
            """
            Blowdown is water flushed from the basin on a periodic basis to purge the
            concentration of mineral scale or other contaminants.
            :param flowrate_evaporation_m3_s: calculated evaporation flowrate [m^3/s]
            :param flowrate_drift_m3_s: calculated drift flowrate [m^3/s]
            :return: float: blowdown flowrate [m^3/s]
            """
            return max(
                flowrate_evaporation_m3_s / (self.operating_cycles_of_concentration - 1) - flowrate_drift_m3_s,
                0
            )

        makeup_flowrate_evaporation_m3_s = calculate_evaporation()
        makeup_flowrate_drift_m3_s = calculate_drift()
        makeup_flowrate_blowdown_m3_s = calculate_blowdown(
            flowrate_evaporation_m3_s=makeup_flowrate_evaporation_m3_s,
            flowrate_drift_m3_s=makeup_flowrate_drift_m3_s
        )

        makeup_flowrate_total_m3_s = \
            makeup_flowrate_evaporation_m3_s + makeup_flowrate_drift_m3_s + makeup_flowrate_blowdown_m3_s

        return makeup_flowrate_evaporation_m3_s, makeup_flowrate_drift_m3_s, \
            makeup_flowrate_blowdown_m3_s, makeup_flowrate_total_m3_s


@dataclass
class Chiller:
    design_cop: float
    design_cooling_capacity_kw: float
    count: int = 1
    design_chw_supply_temperature_c: float = 5.0
    min_load_percentage: float = 0.2
    max_load_percentage: float = 1.0
    __curve_reference_cop__: float = 6.04
    """
    EnergyPlus curve for Chiller Cooling Capacity Ratio [-] as a function of 
    Leaving Chilled Water Temperature [C] (x) and 
    Entering Condenser Water Temperature [C] (y).
    Selected chiller: `Carrier 19XR 1407kW/6.04COP/VSD`
    See: https://github.com/NREL/EnergyPlus/blob/develop/datasets/Chillers.idf
    """
    __curve_cooling_capacity_ratio_function_of_temperature__: CurveBiquadratic = CurveBiquadratic(
        constant=1.042261E+00,
        x=2.644821E-03,
        x2=-1.468026E-03,
        y=1.366256E-02,
        y2=-8.302334E-04,
        xy=1.573579E-03,
        x_min=4.44,
        x_max=10.0,
        y_min=12.78,
        y_max=32.22
    )
    """
    EnergyPlus curve for Chiller Energy Input [W] to Cooling Output [W] Ratio [W/W] as a function of 
    Leaving Chilled Water Temperature [C] (x) and 
    Entering Condenser Water Temperature [C] (y).
    Selected chiller: `Carrier 19XR 1407kW/6.04COP/VSD`
    See: https://github.com/NREL/EnergyPlus/blob/develop/datasets/Chillers.idf
    """
    __curve_energy_input_to_cooling_output_ratio_function_of_temperature__: CurveBiquadratic = CurveBiquadratic(
        constant=1.026340E+00,
        x=-1.612819E-02,
        x2=-1.092591E-03,
        y=-1.784393E-02,
        y2=7.961842E-04,
        xy=-9.586049E-05,
        x_min=4.44,
        x_max=10.0,
        y_min=12.78,
        y_max=32.22
    )
    """
    EnergyPlus curve for Chiller Energy Input [W] to Cooling Output [W] Ratio [W/W] as a function of
    Part Load Ratio (x) [-] [load/capacity]. 
    Selected chiller: `Carrier 19XR 1407kW/6.04COP/VSD`
    See: https://github.com/NREL/EnergyPlus/blob/develop/datasets/Chillers.idf
    """
    __curve_energy_input_to_cooling_output_ratio_function_of_part_load_ratio__: CurveQuadratic = CurveQuadratic(
        constant=1.188880E-01,
        x=6.723542E-01,
        x2=2.068754E-01,
        x_min=0.2,
        x_max=1.04
    )

    def __get_eir_function_of_part_load_ratio__(self, part_load_ratio):

        c = self.__curve_energy_input_to_cooling_output_ratio_function_of_part_load_ratio__

        if part_load_ratio < c.x_min or part_load_ratio > c.x_max:
            if part_load_ratio > c.x_max:
                upsize = round(self.design_cooling_capacity_kw * part_load_ratio * 1.2, -2)
                upsize_text = f" Consider up-sizing your chiller cooling capacity from " \
                              f"{self.design_cooling_capacity_kw} [kW] to {upsize} [kW] or greater."
                streamlit.write(upsize_text)
            else:
                upsize_text = ''
            raise ValueError(
                f"Part Load Ratio out of bounds. `part_load_ratio` must be between "
                f"({c.x_min}, {c.x_max}), but received {part_load_ratio}.{upsize_text}"
            )

        return \
            c.constant + \
            c.x * part_load_ratio + \
            c.x2 * part_load_ratio ** 2

    def __get_eir_function_of_temperatures__(self, chw_leaving_temp_c, cw_entering_temp_c):

        c = self.__curve_energy_input_to_cooling_output_ratio_function_of_temperature__

        # if chw_leaving_temp_c < c.x_min or chw_leaving_temp_c > c.x_max:
        #     raise ValueError(
        #         f"Temperature out of bounds. `chw_leaving_temp_c` must be between "
        #         f"({c.x_min}, {c.x_max}), but received {chw_leaving_temp_c}."
        #     )
        # if cw_entering_temp_c < c.y_min or cw_entering_temp_c > c.y_max:
        #     raise ValueError(
        #         f"Temperature out of bounds. `cw_entering_temp_c` must be between "
        #         f"({c.y_min}, {c.y_max}), but received {cw_entering_temp_c}."
        #     )

        chw_leaving_temp_c = c.x_min if chw_leaving_temp_c < c.x_min else chw_leaving_temp_c
        chw_leaving_temp_c = c.x_max if chw_leaving_temp_c > c.x_max else chw_leaving_temp_c

        cw_entering_temp_c = c.y_min if cw_entering_temp_c < c.y_min else cw_entering_temp_c
        cw_entering_temp_c = c.y_max if cw_entering_temp_c > c.y_max else cw_entering_temp_c

        return \
            c.constant + \
            c.x * chw_leaving_temp_c + \
            c.x2 * chw_leaving_temp_c ** 2 + \
            c.y * cw_entering_temp_c + \
            c.y2 * cw_entering_temp_c ** 2 + \
            c.xy * chw_leaving_temp_c * cw_entering_temp_c

    def get_cooling_capacity(self, chw_leaving_temp_c, cw_entering_temp_c):

        c = self.__curve_cooling_capacity_ratio_function_of_temperature__

        # if chw_leaving_temp_c < c.x_min or chw_leaving_temp_c > c.x_max:
        #     raise ValueError(
        #         f"Temperature out of bounds. `chw_leaving_temp_c` must be between "
        #         f"({c.x_min}, {c.x_max}), but received {chw_leaving_temp_c}."
        #     )
        # if cw_entering_temp_c < c.y_min or cw_entering_temp_c > c.y_max:
        #     raise ValueError(
        #         f"Temperature out of bounds. `cw_entering_temp_c` must be between "
        #         f"({c.y_min}, {c.y_max}), but received {cw_entering_temp_c}."
        #     )

        chw_leaving_temp_c = c.x_min if chw_leaving_temp_c < c.x_min else chw_leaving_temp_c
        chw_leaving_temp_c = c.x_max if chw_leaving_temp_c > c.x_max else chw_leaving_temp_c

        cw_entering_temp_c = c.y_min if cw_entering_temp_c < c.y_min else cw_entering_temp_c
        cw_entering_temp_c = c.y_max if cw_entering_temp_c > c.y_max else cw_entering_temp_c

        cooling_capacity_ratio = \
            c.constant + \
            c.x * chw_leaving_temp_c + \
            c.x2 * chw_leaving_temp_c ** 2 + \
            c.y * cw_entering_temp_c + \
            c.y2 * cw_entering_temp_c ** 2 + \
            c.xy * chw_leaving_temp_c * cw_entering_temp_c

        return cooling_capacity_ratio * self.design_cooling_capacity_kw

    def get_power(self, chw_leaving_temp_c, cw_entering_temp_c, cooling_output_kw):

        cooling_capacity_kw = self.get_cooling_capacity(
            chw_leaving_temp_c=chw_leaving_temp_c,
            cw_entering_temp_c=cw_entering_temp_c
        )

        part_load_ratio = cooling_output_kw / cooling_capacity_kw

        eir_function_of_part_load_ratio = self.__get_eir_function_of_part_load_ratio__(
            part_load_ratio=part_load_ratio
        )

        eir_function_of_temperatures = self.__get_eir_function_of_temperatures__(
            chw_leaving_temp_c=chw_leaving_temp_c,
            cw_entering_temp_c=cw_entering_temp_c
        )

        energy_input_ratio = eir_function_of_part_load_ratio * eir_function_of_temperatures
        reference_power = cooling_output_kw / self.design_cop

        return reference_power * energy_input_ratio, eir_function_of_part_load_ratio, eir_function_of_temperatures
