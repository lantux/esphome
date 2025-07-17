import esphome.codegen as cg
from esphome.components import sensor
import esphome.config_validation as cv
from esphome.const import (
    CONF_CAPACITY,
    CONF_INITIAL_STATE,
    CONF_VOLTAGE,
    DEVICE_CLASS_ENERGY,
    STATE_CLASS_TOTAL,
    UNIT_PERCENT,
)

from .. import battery_gauge_ns

BatteryGaugeSensor = battery_gauge_ns.class_(
    "BatteryGaugeSensor", sensor.Sensor, cg.Component
)

CONF_CURRENT_SOURCE = "current_source"
CONF_MAX_CHARGE_VOLTAGE = "max_charge_voltage"
CONF_PERCENTAGE = "percentage"
CONF_VOLTAGE_SOURCE = "voltage_source"


def shorthand(value):
    if isinstance(value, dict) and len(value) == 1:
        voltage = cv.float_(float(list(value.keys())[0]))
        percentage = cv.percentage(list(value.values())[0])
        value = {CONF_VOLTAGE: voltage, CONF_PERCENTAGE: percentage}
    return cv.Schema(
        {
            cv.Required(CONF_VOLTAGE): cv.float_,
            cv.Required(CONF_PERCENTAGE): cv.All(
                cv.percentage_int,
                cv.Range(min=0, max=100),
            ),
        }
    )(value)


capacity = cv.float_with_unit("capacity", "(ah|AH|Ah|aH)?")

CONFIG_SCHEMA = (
    sensor.sensor_schema(
        BatteryGaugeSensor,
        unit_of_measurement=UNIT_PERCENT,
        state_class=STATE_CLASS_TOTAL,
        device_class=DEVICE_CLASS_ENERGY,
        accuracy_decimals=1,
    )
    .extend(
        {
            cv.Required(CONF_VOLTAGE_SOURCE): cv.use_id(sensor.Sensor),
            cv.Required(CONF_CURRENT_SOURCE): cv.use_id(sensor.Sensor),
            cv.Required(CONF_CAPACITY): capacity,
            cv.Required(CONF_MAX_CHARGE_VOLTAGE): cv.voltage,
            cv.Optional(CONF_INITIAL_STATE): cv.All(
                cv.percentage, cv.Range(min=0, max=1.0)
            ),
        }
    )
    .extend(cv.COMPONENT_SCHEMA)
)


async def to_code(config):
    voltage_source = await cg.get_variable(config[CONF_VOLTAGE_SOURCE])
    current_source = await cg.get_variable(config[CONF_CURRENT_SOURCE])
    capacity = config[CONF_CAPACITY]
    var = await sensor.new_sensor(
        config,
        voltage_source,
        current_source,
        capacity,
        config[CONF_MAX_CHARGE_VOLTAGE],
    )
    if initial_state := config.get(CONF_INITIAL_STATE):
        cg.add(var.set_initial_state(initial_state))
    await cg.register_component(var, config)
