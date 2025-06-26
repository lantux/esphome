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
/**
 * Using voltage thresholds to adjust the charge state. This resynchronises
 */
void BatteryGaugeSensor::on_voltage_(float value) {
  // don't use voltage to adjust when under heavy charge or discharge
  if (std::abs(this->last_current_) > this->capacity_ / 5)
    return;
  if (!std::isfinite(this->last_voltage_)) {
    this->last_voltage_ = value;
    return;
  }
  // if the voltage crossed a threshold, set the charge state according to that data point
  for (auto &pair : this->charge_map_) {
    if (value >= pair.first && this->last_voltage_ < pair.first) {
      auto new_state = pair.second * this->capacity_ / 1000.0f;  // convert to Ah
      this->publish_(new_state);
      ESP_LOGD(TAG, "Charging: Voltage %f, charge percentage: %.1f", value, this->charge_percentage_ / 10.0);
      this->last_voltage_ = value;
      return;
    }
  }
  // If the voltage is decreasing, check the discharge map
  for (auto &pair : this->discharge_map_) {
    if (value <= pair.first && this->last_voltage_ > pair.first) {
      auto new_state = pair.second * this->capacity_ / 1000.0f;  // convert to Ah
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

void BatteryGaugeSensor::reset_soc_from_voltage() {
  if (!std::isfinite(this->last_voltage_)) {
    ESP_LOGW(TAG, "No voltage reading available");
    return;
  }

  // Combine both charge and discharge maps
  std::map<float, int> combined_map;

  // First add all discharge map entries
  for (const auto &[voltage, percentage] : this->discharge_map_) {
    combined_map[voltage] = percentage;
  }

  // Then add or update with charge map entries (this will override discharge values at the same voltage)
  for (const auto &[voltage, percentage] : this->charge_map_) {
    combined_map[voltage] = percentage;
  }

  if (combined_map.empty()) {
    ESP_LOGE(TAG, "No voltage-SoC mapping available");
    return;
  }

  // Find the two closest voltage points for interpolation
  auto it = combined_map.lower_bound(this->last_voltage_);

  // Handle edge cases
  if (it == combined_map.begin()) {
    // Voltage is below the lowest point in the map
    this->charge_percentage_ = it->second;
  } else if (it == combined_map.end()) {
    // Voltage is above the highest point in the map
    this->charge_percentage_ = combined_map.rbegin()->second;
  } else {
    // We're between two points, perform linear interpolation
    auto upper = it;
    auto lower = std::prev(it);

    float voltage_ratio = (this->last_voltage_ - lower->first) / (upper->first - lower->first);
    this->charge_percentage_ = lower->second + (upper->second - lower->second) * voltage_ratio;
  }

  // Update the charge state in Ah
  this->charge_state_ = this->charge_percentage_ / 1000.0f * this->capacity_;

  // Save the new percentage
  this->saved_percentage_.save(&this->charge_percentage_);

  ESP_LOGD(TAG, "Reset SoC from voltage: %.2fV -> %.1f%%", this->last_voltage_, this->charge_percentage_ / 10.0f);
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
      ESP_LOGCONFIG(TAG, "    %.1f V: %.1f%%", pair.first, pair.second / 10.0f);
    }
  }
  if (!this->discharge_map_.empty()) {
    ESP_LOGCONFIG(TAG, "  Discharge map:");
    for (const auto &pair : this->discharge_map_) {
      ESP_LOGCONFIG(TAG, "    %.1f V: %.1f%%", pair.first, pair.second / 10.0f);
    }
  }
}
}  // namespace battery_gauge
}  // namespace esphome
