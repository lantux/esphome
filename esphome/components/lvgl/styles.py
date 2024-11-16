import esphome.codegen as cg
from esphome.const import CONF_ID
from esphome.core import ID

from .defines import CONF_STYLE_DEFINITIONS, CONF_THEME, LValidator, literal
from .helpers import add_lv_use
from .lvcode import lv
from .schemas import ALL_STYLES, collect_parts
from .types import lv_style_t
from .widgets import theme_widget_map


def has_style_props(config) -> bool:
    return any(prop in config for prop in ALL_STYLES)


async def create_style(style, id_name):
    style_id = ID(id_name, True, lv_style_t)
    svar = cg.new_Pvariable(style_id)
    lv.style_init(svar)
    for prop, validator in ALL_STYLES.items():
        if (value := style.get(prop)) is not None:
            if isinstance(validator, LValidator):
                value = await validator.process(value)
            if isinstance(value, list):
                value = "|".join(value)
            lv.call(f"style_set_{prop}", svar, literal(value))
    return svar


async def styles_to_code(config):
    """Convert styles to C__ code."""
    for style in config.get(CONF_STYLE_DEFINITIONS, ()):
        await create_style(style, style[CONF_ID].id)


async def theme_to_code(config):
    if theme := config.get(CONF_THEME):
        add_lv_use(CONF_THEME)
        for w_name, style in theme.items():
            styles = {
                part: await create_style(
                    props, "_lv_theme_style_" + w_name + "_" + part
                )
                for part, props in collect_parts(style).items()
            }
            theme_widget_map[w_name] = styles
