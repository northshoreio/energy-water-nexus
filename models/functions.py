import pandas as pd
import numpy as np
import math
from scipy.interpolate import interp1d


def chwDT(OutsideAirDryBulbTemperature_F=pd.DataFrame()):
    """
    Calculate delta T across CHW loop.
    Input: Outside Air Dry Bulb Temperature [F]
    Output: CHW Loop Delta T [F]
    """

    ##Curve
    DryBulb_F = np.array((0.0, 55.0, 95.0, 120.0,))
    chwDeltaT_F = np.array((8.0, 8.0, 16.0, 16.0))
    chwDeltaTcurve = interp1d(DryBulb_F, chwDeltaT_F, 'linear')
    return chwDeltaTcurve(OutsideAirDryBulbTemperature_F)


def get_chw_flowrate_gpm(chw_tonnage, chw_return_temp, chw_supply_temp):
    """
    Calculate flow rate of CHW loop.

    Input: chw_tonnage: CHW load [tons]
    Input: chw_return_temp: CHW return temperature [F]
    Input: chw_supply_temp: CHW supply temperature [F]
    Output: chw_flowrate_gpm: CHW flowrate [gpm]
    """
    return (chw_tonnage * 12000) / (500 * (chw_return_temp - chw_supply_temp))


def get_tonnage(flowrate_gpm, water_return_temp, water_supply_temp):
    """
    Calculate cooling tonnage.

    Input: flowrate_gpm: water flowrate [gpm]
    Input: water_return_temp: water return temperature [F]
    Input: water_return_temp: water supply temperature [F]
    Output: cooling tonnage [tons]
    """
    return (flowrate_gpm * 500 * (water_return_temp - water_supply_temp))/12000


def wbReset(approach, OutsideAirWetBulbTemperature_F=pd.DataFrame()):
    """
    Calculate target condenser water supply temperature
    based on a wet bulb reset control strategy.
    Input: Outside Air Wet Bulb Temperature [F]
    Output: CW Supply Temperature [F]
    """
    WetBulb_F = np.array((0.0, 55.0 - approach, 80.0 - approach, 120.0 - approach))
    CondenserWaterSupplyTemperature_F = np.array((55.0, 55.0, 80.0, 120.0))
    WBresetCurve = interp1d(WetBulb_F, CondenserWaterSupplyTemperature_F, 'linear')
    return WBresetCurve(OutsideAirWetBulbTemperature_F)


# Chilled water flow rate function
# based on the outside air temperature
def cwFlowRate():
    """
    Calculate flow rate of CW loop.
    Input:
    Output: CW Loop Flow Rate [gpm/ton]
    """
    # todo revisit with sam
    flowRate = 15000 / (500 * 10)
    return flowRate


def kw_to_tons(kw):
    return kw * 3.412142 / 12


def roundup(x, up):
    return int(math.ceil(x / up)) * up


def hp_to_kw(hp):
    return hp * 0.745700


def btu_to_w(btu):
    return btu / 3.412142


def fahrenheit_to_celsius(temperature_F):
    """
    Convert fahrenheit to celsius.
    Input: 	Temperature [F]
    Output: Temperature [C]
    """
    temperature_C = (temperature_F - 32) * 5 / 9
    return temperature_C


def delta_fahrenheit_to_delta_celsius(temperatureDelta_F):
    """
    Convert fahrenheit delta to celsius delta.
    Input: 	Temperature Delta [F]
    Output: Temperature Delta [C]
    """
    return temperatureDelta_F * 5 / 9


def delta_celsius_to_fahrenheit(temperatureDelta_C):
    """
    Convert celsius delta to fahrenheit delta.
    Input: 	Temperature Delta [C]
    Output: Temperature Delta [F]
    """
    return temperatureDelta_C * 9 / 5
