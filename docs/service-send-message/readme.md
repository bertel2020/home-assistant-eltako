# Send Message Service

This service is mainly inteded to combine none-EnOcean and EnOcean devices. Services which cannot communicate nativcely because they are based on different communication protocols, you can use automations in Home Assistant to e.g. receive trigger from an none-EnOcean sender and send a EnOcean message to an relay or sync states of a thermostat. ...

## Configuration

<img src="send_message_automation_screenshot.png" height="300"/>

Create an [automation](https://www.home-assistant.io/getting-started/automation/) in Home Assistant. Use the upper sections to react on anything you like, dependent on you sensor/sender. 

`Add Action` and search for `eltako`. It proposes a service to send messages for every available gateway. In addition you need to enter in the data section what to send. The fields `id` and `eep` must be specified. `id` stands for the sender address. (Keep in mind: bus gateways do not send in wireless network and wireless tranceivers do only have 128 hardcoded addresses to be used.) `eep` is the message format you what to use. Dependent on the eep specific information is put into the messages to be sent. You can either check in the [code](https://github.com/bertel2020/eltako14bus/blob/76d0dba36311bbd7c2e2813133eaf4ca341d7ca1/eltakobus/eep.py) or in this automatically generated [parameter list for EEPs](eep-params.md). In the logs you can see what parameters has been transferred and which will be set as default to 0. To fill the EEP paramters with values we use [templating of HA](https://www.home-assistant.io/docs/configuration/templating/). This gives us the posibility to read values from different sensors, modify them if required, and pass them to be sent.

<img src="send_message_logs_screenshot.png" />

The [parameter reference](eep-params.md) records the exact constructor names
and known sending limitations. In particular, the old A5-10-06 example is omitted:
this fork's generic service does not convert numeric `mode` and `priority` values
to the Python enums its encoder requires. The dedicated climate controller uses
a different, unchanged send path. Receiving A5-09-04 is supported, but sending it
also has an existing encoder limitation documented in the reference.

## This fork's service contract

Service names remain `eltako.gateway_<configured gateway id>_send_message`.
Existing entity IDs and button event names are unchanged by these maintenance backports.
See the [generated parameter reference](eep-params.md) for this fork's constructor
names. In particular A5-10-06 uses `priority`, not the old `stand_by` argument;
A5-04-02 also supports `supply_voltage`. Missing parameters are filled with zero
by the service, rather than with Python constructor defaults.

## Gateway connection diagnostics

For a LAN gateway, the existing **Serial Path** sensor also exposes `host` and
`port` attributes. Its state and entity ID stay unchanged. Transport setup details
are recorded at debug logging level. No new gateway configuration is required.
