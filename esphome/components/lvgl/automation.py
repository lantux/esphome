from typing import Any, Callable

from esphome import automation
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.const import CONF_ACTION, CONF_GROUP, CONF_ID, CONF_TIMEOUT
from esphome.cpp_generator import get_variable
from esphome.cpp_types import nullptr

from .defines import (
    CONF_BOTTOM_LAYER,
    CONF_EDITING,
    CONF_FREEZE,
    CONF_LVGL_ID,
    CONF_MAIN,
    CONF_OBJ,
    CONF_SCROLLBAR,
    CONF_SHOW_SNOW,
    CONF_TOP_LAYER,
    StaticCastExpression,
)
from .lv_validation import lv_bool
from .lvcode import (
    LVGL_COMP_ARG,
    UPDATE_EVENT,
    LambdaContext,
    LocalVariable,
    LvglComponent,
    ReturnStatement,
    add_line_marks,
    lv,
    lv_add,
    lv_expr,
    lv_obj,
    lvgl_comp,
)
from .schemas import LIST_ACTION_SCHEMA, LVGL_SCHEMA, part_schema
from .types import (
    LV_STATE,
    LvglAction,
    LvglCondition,
    ObjUpdateAction,
    WidgetType,
    lv_group_t,
    lv_obj_t,
    lv_pseudo_button_t,
)
from .widgets import (
    Widget,
    add_widgets,
    get_scr_act,
    get_widgets,
    set_obj_properties,
    wait_for_widgets,
)

# Record widgets that are used in a focused action here
focused_widgets = set()


async def layers_to_code(lv_component, config):
    if top_conf := config.get(CONF_TOP_LAYER):
        top_layer = lv_expr.display_get_layer_top(lv_component.get_disp())
        with LocalVariable("top_layer", lv_obj_t, top_layer) as top_layer_obj:
            top_w = Widget(top_layer_obj, layer_spec, top_conf)
            await set_obj_properties(top_w, top_conf)
            await add_widgets(top_w, top_conf)
    if bottom_conf := config.get(CONF_BOTTOM_LAYER):
        bottom_layer = lv_expr.display_get_layer_bottom(lv_component.get_disp())
        with LocalVariable("bottom_layer", lv_obj_t, bottom_layer) as bottom_layer_obj:
            bottom_w = Widget(bottom_layer_obj, layer_spec, bottom_conf)
            await set_obj_properties(bottom_w, bottom_conf)
            await add_widgets(bottom_w, bottom_conf)


async def action_to_code(
    widgets: list[Widget],
    action: Callable[[Widget], Any],
    action_id,
    template_arg,
    args,
):
    await wait_for_widgets()
    async with LambdaContext(parameters=args, where=action_id) as context:
        for widget in widgets:
            await action(widget)
    var = cg.new_Pvariable(action_id, template_arg, await context.get_lambda())
    return var


async def update_to_code(config, action_id, template_arg, args):
    async def do_update(widget: Widget):
        await set_obj_properties(widget, config)
        await widget.type.to_code(widget, config)
        if (
            widget.type.w_type.value_property is not None
            and widget.type.w_type.value_property in config
        ):
            lv.obj_send_event(widget.obj, UPDATE_EVENT, nullptr)

    widgets = await get_widgets(config[CONF_ID])
    return await action_to_code(widgets, do_update, action_id, template_arg, args)


@automation.register_condition(
    "lvgl.is_paused",
    LvglCondition,
    LVGL_SCHEMA,
)
async def lvgl_is_paused(config, condition_id, template_arg, args):
    lvgl = config[CONF_LVGL_ID]
    async with LambdaContext(LVGL_COMP_ARG, return_type=cg.bool_) as context:
        lv_add(ReturnStatement(lvgl_comp.is_paused()))
    var = cg.new_Pvariable(condition_id, template_arg, await context.get_lambda())
    await cg.register_parented(var, lvgl)
    return var


@automation.register_condition(
    "lvgl.is_idle",
    LvglCondition,
    LVGL_SCHEMA.extend(
        {
            cv.Required(CONF_TIMEOUT): cv.templatable(
                cv.positive_time_period_milliseconds
            )
        }
    ),
)
async def lvgl_is_idle(config, condition_id, template_arg, args):
    lvgl = config[CONF_LVGL_ID]
    timeout = await cg.templatable(config[CONF_TIMEOUT], [], cg.uint32)
    async with LambdaContext(LVGL_COMP_ARG, return_type=cg.bool_) as context:
        lv_add(ReturnStatement(lvgl_comp.is_idle(timeout)))
    var = cg.new_Pvariable(condition_id, template_arg, await context.get_lambda())
    await cg.register_parented(var, lvgl)
    return var


@automation.register_action(
    "lvgl.widget.redraw",
    ObjUpdateAction,
    cv.Any(
        cv.maybe_simple_value(
            {
                cv.Required(CONF_ID): cv.use_id(lv_obj_t),
            },
            key=CONF_ID,
        ),
        LVGL_SCHEMA,
    ),
)
async def obj_invalidate_to_code(config, action_id, template_arg, args):
    if CONF_LVGL_ID in config:
        lv_comp = await cg.get_variable(config[CONF_LVGL_ID])
        widgets = [get_scr_act(lv_comp)]
    else:
        widgets = await get_widgets(config)

    async def do_invalidate(widget: Widget):
        lv_obj.invalidate(widget.obj)

    return await action_to_code(widgets, do_invalidate, action_id, template_arg, args)


layer_spec = WidgetType(CONF_OBJ, lv_obj_t, (CONF_MAIN, CONF_SCROLLBAR))


@automation.register_action(
    "lvgl.update",
    LvglAction,
    part_schema(layer_spec)
    .extend(LVGL_SCHEMA)
    .extend(
        {
            cv.GenerateID(): cv.use_id(LvglComponent),
            cv.Optional(CONF_TOP_LAYER): part_schema(layer_spec),
            cv.Optional(CONF_BOTTOM_LAYER): part_schema(layer_spec),
        }
    ),
)
async def lvgl_update_to_code(config, action_id, template_arg, args):
    lv_component = await cg.get_variable(config[CONF_LVGL_ID])
    async with LambdaContext(LVGL_COMP_ARG, where=action_id) as context:
        await layers_to_code(lv_component, config)
    var = cg.new_Pvariable(action_id, template_arg, await context.get_lambda())
    await cg.register_parented(var, lv_component)
    return var


@automation.register_action(
    "lvgl.pause",
    LvglAction,
    LVGL_SCHEMA.extend(
        {
            cv.Optional(CONF_SHOW_SNOW, default=False): lv_bool,
        }
    ),
)
async def pause_action_to_code(config, action_id, template_arg, args):
    lv_comp = await cg.get_variable(config[CONF_LVGL_ID])
    async with LambdaContext(LVGL_COMP_ARG) as context:
        add_line_marks(where=action_id)
        lv_add(lvgl_comp.set_paused(True, config[CONF_SHOW_SNOW]))
    var = cg.new_Pvariable(action_id, template_arg, await context.get_lambda())
    await cg.register_parented(var, lv_comp)
    return var


@automation.register_action(
    "lvgl.resume",
    LvglAction,
    LVGL_SCHEMA,
)
async def resume_action_to_code(config, action_id, template_arg, args):
    lv_comp = await cg.get_variable(config[CONF_LVGL_ID])
    async with LambdaContext(LVGL_COMP_ARG, where=action_id) as context:
        lv_add(lvgl_comp.set_paused(False, False))
    var = cg.new_Pvariable(action_id, template_arg, await context.get_lambda())
    await cg.register_parented(var, lv_comp)
    return var


@automation.register_action("lvgl.widget.disable", ObjUpdateAction, LIST_ACTION_SCHEMA)
async def obj_disable_to_code(config, action_id, template_arg, args):
    async def do_disable(widget: Widget):
        widget.add_state(LV_STATE.DISABLED)

    return await action_to_code(
        await get_widgets(config), do_disable, action_id, template_arg, args
    )


@automation.register_action("lvgl.widget.enable", ObjUpdateAction, LIST_ACTION_SCHEMA)
async def obj_enable_to_code(config, action_id, template_arg, args):
    async def do_enable(widget: Widget):
        widget.clear_state(LV_STATE.DISABLED)

    return await action_to_code(
        await get_widgets(config), do_enable, action_id, template_arg, args
    )


@automation.register_action("lvgl.widget.hide", ObjUpdateAction, LIST_ACTION_SCHEMA)
async def obj_hide_to_code(config, action_id, template_arg, args):
    async def do_hide(widget: Widget):
        widget.add_flag("LV_OBJ_FLAG_HIDDEN")

    widgets = [
        widget.outer if widget.outer else widget for widget in await get_widgets(config)
    ]
    return await action_to_code(widgets, do_hide, action_id, template_arg, args)


@automation.register_action("lvgl.widget.show", ObjUpdateAction, LIST_ACTION_SCHEMA)
async def obj_show_to_code(config, action_id, template_arg, args):
    async def do_show(widget: Widget):
        widget.clear_flag("LV_OBJ_FLAG_HIDDEN")
        if widget.move_to_foreground:
            lv_obj.move_foreground(widget.obj)

    widgets = [
        widget.outer if widget.outer else widget for widget in await get_widgets(config)
    ]
    return await action_to_code(widgets, do_show, action_id, template_arg, args)


def focused_id(value):
    value = cv.use_id(lv_pseudo_button_t)(value)
    focused_widgets.add(value)
    return value


@automation.register_action(
    "lvgl.widget.focus",
    ObjUpdateAction,
    cv.Any(
        cv.maybe_simple_value(
            LVGL_SCHEMA.extend(
                {
                    cv.Optional(CONF_GROUP): cv.use_id(lv_group_t),
                    cv.Required(CONF_ACTION): cv.one_of(
                        "MARK", "RESTORE", "NEXT", "PREVIOUS", upper=True
                    ),
                    cv.Optional(CONF_FREEZE, default=False): cv.boolean,
                }
            ),
            key=CONF_ACTION,
        ),
        cv.maybe_simple_value(
            {
                cv.Required(CONF_ID): focused_id,
                cv.Optional(CONF_FREEZE, default=False): cv.boolean,
                cv.Optional(CONF_EDITING, default=False): cv.boolean,
            },
            key=CONF_ID,
        ),
    ),
)
async def widget_focus(config, action_id, template_arg, args):
    widget = await get_widgets(config)
    if widget:
        widget = widget[0]
        group = StaticCastExpression(
            lv_group_t.operator("ptr"), lv_expr.obj_get_group(widget.obj)
        )
    elif group := config.get(CONF_GROUP):
        group = await get_variable(group)
    else:
        group = lv_expr.group_get_default()

    async with LambdaContext(parameters=args, where=action_id) as context:
        if widget:
            lv.group_focus_freeze(group, False)
            lv.group_focus_obj(widget.obj)
            if config[CONF_EDITING]:
                lv.group_set_editing(group, True)
        else:
            action = config[CONF_ACTION]
            lv_comp = await get_variable(config[CONF_LVGL_ID])
            if action == "MARK":
                context.add(lv_comp.set_focus_mark(group))
            else:
                lv.group_focus_freeze(group, False)
                if action == "RESTORE":
                    context.add(lv_comp.restore_focus_mark(group))
                elif action == "NEXT":
                    lv.group_focus_next(group)
                else:
                    lv.group_focus_prev(group)

        if config[CONF_FREEZE]:
            lv.group_focus_freeze(group, True)
        var = cg.new_Pvariable(action_id, template_arg, await context.get_lambda())
        return var
