from esphome import automation

from ..automation import update_to_code
from ..defines import CONF_MAIN, CONF_OBJ, CONF_SCROLLBAR
from ..schemas import create_modify_schema
from ..types import ObjUpdateAction, WidgetType, lv_obj_t

obj_spec = WidgetType(CONF_OBJ, lv_obj_t, (CONF_MAIN, CONF_SCROLLBAR))


@automation.register_action(
    "lvgl.widget.update", ObjUpdateAction, create_modify_schema(obj_spec)
)
async def obj_update_to_code(config, action_id, template_arg, args):
    return await update_to_code(config, action_id, template_arg, args)
