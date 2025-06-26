#include "battery_gauge_sensor.h"
#include "esphome/core/log.h"
#include "esphome/core/hal.h"

namespace esphome {
namespace battery_gauge {

static const char *const TAG = "battery_gauge.sensor";

void BatteryGaugeSensor::on_current_(float value) {
  if (!std::isfinite(value))
    return;  // ignore invalid values
  auto current = value;
  if (std::isfinite(this->last_current_)) {
    current += this->last_current_;
    current /= 2.0f;
  }
  this->last_current_ = value;
  auto now = millis();
  auto previous = this->last_time_;
  this->last_time_ = now;
  if (previous == 0)
    return;
  float interval = (now - previous) / 1000.0f / 3600.0f;
  auto delta = current * interval;
  ESP_LOGD(TAG, "current: %f, interval: %f, delta: %f, charge state: %f", current, interval, delta,
           this->charge_state_);
  this->publish_(this->charge_state_ + delta);
}

void BatteryGaugeSensor::publish_(float new_state) {
  this->charge_state_ = std::max(0.0f, std::min(new_state, this->capacity_));
  auto percentage = this->charge_state_ / this->capacity_ * 100.0f;
  this->publish_state(percentage);
  unsigned new_percentage = std::round(percentage * 10.0);
  if (new_percentage != this->charge_percentage_) {
    this->charge_percentage_ = new_percentage;
    ESP_LOGD(TAG, "Saving charge percentage: %u", this->charge_percentage_);
    this->saved_percentage_.save(&this->charge_percentage_);
  }
}
void BatteryGaugeSensor::on_voltage_(float value) {
  for (auto &pair : this->charge_map_) {
    if (value >= pair.first && (this->last_voltage_ < pair.first || this->charge_percentage_ < pair.second * 10)) {
      auto new_state = pair.second * this->capacity_ / 100.0f;  // convert to Ah
      this->publish_(new_state);
      ESP_LOGD(TAG, "Charging: Voltage %f, charge percentage: %.1f", value, this->charge_percentage_ / 10.0);
      this->last_voltage_ = value;
      return;
    }
  }
  // If the voltage is decreasing, we check the discharge map
  for (auto &pair : this->discharge_map_) {
    if (value <= pair.first && (this->last_voltage_ > pair.first || this->charge_percentage_ > pair.second * 10)) {
      auto new_state = pair.second * this->capacity_ / 100.0f;  // convert to Ah
      this->publish_(new_state);
      ESP_LOGD(TAG, "Discharging: Voltage %f, charge percentage: %.1f", value, this->charge_percentage_ / 10.0);
      this->last_voltage_ = value;
      return;
    }
  }
}

void BatteryGaugeSensor::setup() {
  this->current_source_->add_on_state_callback([this](float value) { this->on_current_(value); });
  this->voltage_source_->add_on_state_callback([this](float value) { this->on_voltage_(value); });
  this->last_time_ = millis();
  if (!this->saved_percentage_.load(&this->charge_percentage_) || this->charge_percentage_ == 0) {
    ESP_LOGD(TAG, "Setting initial charge state to %f", this->initial_state_);
    this->charge_percentage_ = this->initial_state_ * 1000.0f;
    this->saved_percentage_.save(&this->charge_percentage_);
  }
  this->charge_state_ = this->charge_percentage_ / 1000.0f * this->capacity_;
}

void BatteryGaugeSensor::dump_config() {
  LOG_SENSOR("", "Battery Gauge", this);
  ESP_LOGCONFIG(TAG, "  Capacity: %.0f", this->capacity_);
  unsigned saved_charge;
  if (this->saved_percentage_.load(&saved_charge)) {
    ESP_LOGCONFIG(TAG, "  Saved charge percentage: %.1f", saved_charge / 10.0f);
  }
  if (!this->charge_map_.empty()) {
    ESP_LOGCONFIG(TAG, "  Charge map:");
    for (const auto &pair : this->charge_map_) {
      ESP_LOGCONFIG(TAG, "    %.1f V: %d%%", pair.first, pair.second);
    }
  }
  if (!this->discharge_map_.empty()) {
    ESP_LOGCONFIG(TAG, "  Discharge map:");
    for (const auto &pair : this->discharge_map_) {
      ESP_LOGCONFIG(TAG, "    %.1f V: %d%%", pair.first, pair.second);
    }
  }
}
}  // namespace battery_gauge
}  // namespace esphome
