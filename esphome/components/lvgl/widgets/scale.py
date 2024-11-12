from esphome.components.lvgl.defines import CONF_STYLE
from esphome.components.lvgl.lvcode import lv
import esphome.config_validation as cv
from esphome.const import CONF_ITEMS, CONF_RANGE_FROM, CONF_RANGE_TO, CONF_ROTATION

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
    }
)


class ScaleType(WidgetType):
    def __init__(self):
        super().__init__(
            CONF_SCALE,
            lv_scale_t,
            (CONF_MAIN, CONF_ITEMS, CONF_INDICATOR),
            SCALE_SCHEMA,
        )

    async def to_code(self, w: Widget, config):
        await w.set_property(CONF_DRAW_TICKS_ON_TOP, config)
        await w.set_property(CONF_ROTATION, config)
        await w.set_property(CONF_ANGLE_RANGE, config)
        await w.set_property(CONF_LABEL_SHOW, config)
        await w.set_property(CONF_TOTAL_TICK_COUNT, config)
        await w.set_property(CONF_MAJOR_TICK_EVERY, config)
        lv.scale_set_range(w.obj, config[CONF_RANGE_FROM], config[CONF_RANGE_TO])


scale_spec = ScaleType()
