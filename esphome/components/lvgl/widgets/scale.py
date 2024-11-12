from esphome.components.lvgl.defines import CONF_RADIUS, CONF_STYLE, LV_SCALE_MODE
from esphome.components.lvgl.lvcode import lv
import esphome.config_validation as cv
from esphome.const import (
    CONF_ITEMS,
    CONF_MODE,
    CONF_RANGE_FROM,
    CONF_RANGE_TO,
    CONF_ROTATION,
)

from ..defines import CONF_ANGLE_RANGE, CONF_INDICATOR, CONF_MAIN
from ..lv_validation import lv_bool
from ..types import LvType, WidgetType, lv_style_t
from . import Widget

lv_scale_t = LvType("lv_scale_t")

CONF_SCALE = "scale"
CONF_DRAW_TICKS_ON_TOP = "draw_ticks_on_top"
CONF_LABEL_SHOW = "label_show"
CONF_TOTAL_TICK_COUNT = "total_tick_count"
CONF_MAJOR_TICK_EVERY = "major_tick_every"
CONF_SECTIONS = "sections"

SECTION_SCHEMA = cv.Schema(
    {
        cv.Required(CONF_RANGE_FROM): cv.float_,
        cv.Required(CONF_RANGE_TO): cv.float_,
        cv.Optional(CONF_STYLE): cv.use_id(lv_style_t),
    }
)


def mode_check(config):
    if CONF_RADIUS not in config and "ROUND" in config[CONF_MODE]:
        config[CONF_RADIUS] = "LV_RADIUS_CIRCLE"
    return config


SCALE_SCHEMA = cv.Schema(
    {
        cv.Optional(CONF_RANGE_FROM, default=0.0): cv.float_,
        cv.Optional(CONF_RANGE_TO, default=100.0): cv.float_,
        cv.Optional(CONF_ANGLE_RANGE): cv.int_range(0, 360),
        cv.Optional(CONF_ROTATION): cv.int_range(0, 360),
        cv.Optional(CONF_DRAW_TICKS_ON_TOP, default=False): lv_bool,
        cv.Optional(CONF_LABEL_SHOW, default=True): lv_bool,
        cv.Optional(CONF_TOTAL_TICK_COUNT, default=50): cv.int_range(1, 1000),
        cv.Optional(CONF_MAJOR_TICK_EVERY, default=10): cv.int_range(1, 1000),
        cv.Optional(CONF_SECTIONS): cv.ensure_list(SECTION_SCHEMA),
        cv.Optional(CONF_MODE, default="HORIZONTAL_TOP"): LV_SCALE_MODE.one_of,
    }
).add_extra(mode_check)


class ScaleType(WidgetType):
    def __init__(self):
        super().__init__(
            CONF_SCALE,
            lv_scale_t,
            (CONF_MAIN, CONF_ITEMS, CONF_INDICATOR),
            SCALE_SCHEMA,
        )

    async def to_code(self, w: Widget, config):
        mode = config[CONF_MODE]
        for prop in (
            CONF_ANGLE_RANGE,
            CONF_ROTATION,
            CONF_DRAW_TICKS_ON_TOP,
            CONF_LABEL_SHOW,
            CONF_TOTAL_TICK_COUNT,
            CONF_MAJOR_TICK_EVERY,
            CONF_MODE,
        ):
            await w.set_property(prop, config)
        lv.scale_set_range(w.obj, config[CONF_RANGE_FROM], config[CONF_RANGE_TO])


scale_spec = ScaleType()
