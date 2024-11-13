from esphome.components.lvgl.lv_validation import lv_angle
import esphome.config_validation as cv

from ..defines import CONF_ARC_LENGTH, CONF_INDICATOR, CONF_MAIN, CONF_SPIN_TIME
from ..lvcode import lv
from ..types import LvType
from . import Widget, WidgetType
from .arc import CONF_ARC

CONF_SPINNER = "spinner"

SPINNER_SCHEMA = cv.Schema(
    {
        cv.Optional(CONF_ARC_LENGTH, default=60): lv_angle,
        cv.Optional(
            CONF_SPIN_TIME, default="1000ms"
        ): cv.positive_time_period_milliseconds,
    }
)

SPINNER_MODIFY_SCHEMA = cv.Schema(
    {
        cv.Optional(CONF_ARC_LENGTH): lv_angle,
        cv.Optional(CONF_SPIN_TIME): cv.positive_time_period_milliseconds,
    }
).add_extra(cv.has_none_or_all_keys)


class SpinnerType(WidgetType):
    def __init__(self):
        super().__init__(
            CONF_SPINNER,
            LvType("lv_spinner_t"),
            (CONF_MAIN, CONF_INDICATOR),
            SPINNER_SCHEMA,
            modify_schema=SPINNER_MODIFY_SCHEMA,
        )

    async def to_code(self, w: Widget, config):
        if CONF_ARC_LENGTH in config:
            lv.spinner_set_anim_params(
                w.obj,
                config[CONF_SPIN_TIME].total_milliseconds,
                config[CONF_ARC_LENGTH],
            )

    def get_uses(self):
        return (CONF_ARC,)


spinner_spec = SpinnerType()
