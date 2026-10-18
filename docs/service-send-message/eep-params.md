# EEP parameters for the Send Message service

Generated from the [manifest-pinned bertel2020 library](https://github.com/bertel2020/eltako14bus/archive/76d0dba36311bbd7c2e2813133eaf4ca341d7ca1.zip)
(package version 1.2).
Regenerate with `python -m tools.generate_eep_params` after installing `requirements.txt`.

These are constructor parameter names, not a guarantee that every profile can be sent.
The service fills omitted parameters with **0**, even when the constructor has another default.
Supply all values needed by your device. This service uses `encode_message`,
whereas the custom climate controller uses its own `encode_message2` path.

## Profiles excluded by the existing service documentation

- `A5-09-0C`
- `A5-38-08`

A5-09-04 receives CO2 correctly, but its current outgoing encoder references
`learn_button`, which its constructor does not provide. Do not use that profile
for sending until separately corrected and validated.

A5-10-06 currently expects Python enum objects for `mode` and `priority`.
The service does not convert JSON/YAML values into those enums, so ordinary
service calls for this profile are not supported. This is separate from
the custom climate controller, whose existing send path is unchanged.

## Constructor parameters

- `A5-04-01`: humidity, learn_button, temp_availability, temperature
- `A5-04-02`: humidity, learn_button, supply_voltage, temperature
- `A5-04-03`: humidity, learn_button, telegram_type, temperature
- `A5-06-01`: day_light, illumination, twilight
- `A5-07-01`: learn_button, pir_status, pir_status_on, support_volrage_availability, support_voltage
- `A5-08-01`: illumination, learn_button, occupancy_button, pir_status, supply_voltage, temperature
- `A5-09-04`: concentration, humidity, temperature
- `A5-10-03`: current_temp, target_temp
- `A5-10-06`: current_temp, mode, priority, target_temp
- `A5-10-12`: current_temperature, humidity, target_temperature
- `A5-12-01`: data_type, divisor, learn_button, measurement_channel, meter_reading
- `A5-12-02`: data_type, divisor, learn_button, measurement_channel, meter_reading
- `A5-12-03`: data_type, divisor, learn_button, measurement_channel, meter_reading
- `A5-13-01`: dawn_sensor, day_night, hemisphere, identifier, learn_button, rain_indication, sun_east, sun_south, sun_west, temperature, wind_speed
- `A5-30-01`: battery_status, contact_status, learn_button
- `A5-30-03`: digital_input_0, digital_input_1, digital_input_2, digital_input_3, learn_button, status_of_wake, temperature
- `D5-00-01`: contact, learn_button
- `F6-01-01`: button_pushed
- `F6-02-01`: energy_bow, rocker_first_action, rocker_second_action, second_action
- `F6-02-02`: energy_bow, rocker_first_action, rocker_second_action, second_action
- `F6-10-00`: handle_position, movement
- `G5-3F-7F`: direction, state, time
- `H5-3F-7F`: command, learn_button, time
- `M5-38-08`: state
