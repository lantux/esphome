#include "lvgl_esphome.h"

#ifdef USE_LVGL_FONT
namespace esphome {
namespace lvgl {

static const uint8_t opa4_table[16] = {0, 17, 34, 51, 68, 85, 102, 119, 136, 153, 170, 187, 204, 221, 238, 255};

static const uint8_t opa2_table[4] = {0, 85, 170, 255};

static const void *get_glyph_bitmap(lv_font_glyph_dsc_t *dsc, lv_draw_buf_t *draw_buf) {
  const auto font = dsc->resolved_font;
  auto *const fe = (FontEngine *) font->dsc;

  const auto *gd = fe->get_glyph_data(dsc->gid.index);
  if (gd == nullptr)
    return nullptr;

  const uint8_t *bitmap_in = gd->data;
  uint8_t *bitmap_out_tmp = draw_buf->data;
  int32_t i = 0;
  int32_t x, y;
  uint32_t stride = lv_draw_buf_width_to_stride(gd->width, LV_COLOR_FORMAT_A8);

  if (fe->bpp == 1) {
    for (y = 0; y != gd->height; y++) {
      for (x = 0; x != gd->width; x++) {
        bitmap_out_tmp[x] = ((*bitmap_in++) << (x & 7) & 0x80) ? 0xff : 0x00;
      }
      bitmap_out_tmp += stride;
    }
  } else if (fe->bpp == 2) {
    for (y = 0; y < gd->height; y++) {
      for (x = 0; x < gd->width; x++, i++) {
        i = i & 0x3;
        if (i == 0)
          bitmap_out_tmp[x] = opa2_table[(*bitmap_in) >> 6];
        else if (i == 1)
          bitmap_out_tmp[x] = opa2_table[((*bitmap_in) >> 4) & 0x3];
        else if (i == 2)
          bitmap_out_tmp[x] = opa2_table[((*bitmap_in) >> 2) & 0x3];
        else if (i == 3) {
          bitmap_out_tmp[x] = opa2_table[((*bitmap_in) >> 0) & 0x3];
          bitmap_in++;
        }
      }
      bitmap_out_tmp += stride;
    }

  } else if (fe->bpp == 4) {
    for (y = 0; y < gd->height; y++) {
      for (x = 0; x < gd->width; x++, i++) {
        i = i & 0x1;
        if (i == 0) {
          bitmap_out_tmp[x] = opa4_table[(*bitmap_in) >> 4];
        } else if (i == 1) {
          bitmap_out_tmp[x] = opa4_table[(*bitmap_in) & 0xF];
          bitmap_in++;
        }
      }
      bitmap_out_tmp += stride;
    }
  }
  return draw_buf;
}

static bool get_glyph_dsc_cb(const lv_font_t *font, lv_font_glyph_dsc_t *dsc, uint32_t unicode_letter, uint32_t next) {
  auto *fe = (FontEngine *) font->dsc;
  const auto *gd = fe->get_glyph_data(unicode_letter);
  if (gd == nullptr)
    return false;
  dsc->adv_w = gd->offset_x + gd->width;
  dsc->ofs_x = gd->offset_x;
  dsc->ofs_y = fe->height - gd->height - gd->offset_y - fe->baseline;
  dsc->box_w = gd->width;
  dsc->box_h = gd->height;
  dsc->is_placeholder = 0;
  dsc->format = (lv_font_glyph_format_t) fe->bpp;
  dsc->gid.index = unicode_letter;
  return true;
}

FontEngine::FontEngine(font::Font *esp_font) : font_(esp_font) {
  this->bpp = esp_font->get_bpp();
  this->lv_font_.dsc = this;
  this->lv_font_.line_height = this->height = esp_font->get_height();
  this->lv_font_.base_line = this->baseline = this->lv_font_.line_height - esp_font->get_baseline();
  this->lv_font_.get_glyph_dsc = get_glyph_dsc_cb;
  this->lv_font_.get_glyph_bitmap = get_glyph_bitmap;
  this->lv_font_.subpx = LV_FONT_SUBPX_NONE;
  this->lv_font_.underline_position = -1;
  this->lv_font_.underline_thickness = 1;
}

const lv_font_t *FontEngine::get_lv_font() { return &this->lv_font_; }

const font::GlyphData *FontEngine::get_glyph_data(uint32_t unicode_letter) {
  if (unicode_letter == last_letter_)
    return this->last_data_;
  uint8_t unicode[5];
  memset(unicode, 0, sizeof unicode);
  if (unicode_letter > 0xFFFF) {
    unicode[0] = 0xF0 + ((unicode_letter >> 18) & 0x7);
    unicode[1] = 0x80 + ((unicode_letter >> 12) & 0x3F);
    unicode[2] = 0x80 + ((unicode_letter >> 6) & 0x3F);
    unicode[3] = 0x80 + (unicode_letter & 0x3F);
  } else if (unicode_letter > 0x7FF) {
    unicode[0] = 0xE0 + ((unicode_letter >> 12) & 0xF);
    unicode[1] = 0x80 + ((unicode_letter >> 6) & 0x3F);
    unicode[2] = 0x80 + (unicode_letter & 0x3F);
  } else if (unicode_letter > 0x7F) {
    unicode[0] = 0xC0 + ((unicode_letter >> 6) & 0x1F);
    unicode[1] = 0x80 + (unicode_letter & 0x3F);
  } else {
    unicode[0] = unicode_letter;
  }
  int match_length;
  int glyph_n = this->font_->match_next_glyph(unicode, &match_length);
  if (glyph_n < 0) {
    return nullptr;
  }
  this->last_data_ = this->font_->get_glyphs()[glyph_n].get_glyph_data();
  this->last_letter_ = unicode_letter;
  return this->last_data_;
}
}  // namespace lvgl
}  // namespace esphome
#endif  // USE_LVGL_FONT
