from esphome.const import CONF_BUTTON

from ..defines import CONF_MAIN
from ..types import LvBoolean, WidgetType

lv_button_t = LvBoolean("lv_button_t")


button_spec = WidgetType(
    CONF_BUTTON,
    lv_button_t,
    (CONF_MAIN,),
)
