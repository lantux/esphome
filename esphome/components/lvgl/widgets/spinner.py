import esphome.config_validation as cv

from ..defines import CONF_ARC_LENGTH, CONF_INDICATOR, CONF_MAIN, CONF_SPIN_TIME
from ..lv_validation import angle
from ..lvcode import lv
from ..types import LvType
from . import Widget, WidgetType
from .arc import CONF_ARC

CONF_SPINNER = "spinner"

SPINNER_SCHEMA = cv.Schema(
    {
        cv.Required(CONF_ARC_LENGTH): angle,
        cv.Required(CONF_SPIN_TIME): cv.positive_time_period_milliseconds,
    }
)


class SpinnerType(WidgetType):
    def __init__(self):
        super().__init__(
            CONF_SPINNER,
            LvType("lv_spinner_t"),
            (CONF_MAIN, CONF_INDICATOR),
            SPINNER_SCHEMA,
        )

    async def to_code(self, w: Widget, config):
        lv.spinner_set_anim_params(
            w.obj,
            config[CONF_SPIN_TIME].total_milliseconds,
            config[CONF_ARC_LENGTH] // 10,
        )

    def get_uses(self):
        return (CONF_ARC,)


spinner_spec = SpinnerType()
