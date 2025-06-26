#pragma once

#include "esphome/core/component.h"
#include "esphome/components/sensor/sensor.h"
#include <map>

namespace esphome {
namespace battery_gauge {

class BatteryGaugeSensor : public sensor::Sensor, public Component {
 public:
  BatteryGaugeSensor(sensor::Sensor *voltage_source, sensor::Sensor *current_source, float capacity,
                     std::map<float, int> discharge_map, std::map<float, int> charge_map)
      : voltage_source_(voltage_source),
        current_source_(current_source),
        capacity_(capacity),
        discharge_map_(std::move(discharge_map)),
        charge_map_(std::move(charge_map)),
        saved_percentage_(global_preferences->make_preference<unsigned>(this->object_id_hash_)) {}
  void setup() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::DATA; }
  void set_initial_state(float initial_state) { initial_state_ = initial_state; }
  void reset_soc_from_voltage();

 protected:
  void publish_(float new_state);
  Sensor *voltage_source_;
  Sensor *current_source_;
  float capacity_;
  void on_current_(float value);
  void on_voltage_(float value);
  float charge_state_{};                // charge state in Ah
  unsigned charge_percentage_{0};       // charge percentage * 10
  std::map<float, int> discharge_map_;  // map of volts to charge percentage * 10
  std::map<float, int> charge_map_;     // map of volts to charge percentage * 10
  float initial_state_{0};
  uint32_t last_time_{0};
  float last_voltage_{NAN};
  float last_current_{NAN};
  ESPPreferenceObject saved_percentage_;
};

}  // namespace battery_gauge
}  // namespace esphome
