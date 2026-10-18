"""Isolated lifecycle regressions, runnable without a Home Assistant installation.

Execute the production lifecycle methods with small HA doubles. AST extraction
avoids importing unrelated platform/dependency code; these are not HA integration
tests. Run with: python3 -m unittest discover -s tests -v
"""
import ast
import asyncio
from contextlib import suppress
import logging
from pathlib import Path
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock


ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "eltako"


def load_methods(filename, class_name, names, namespace, base=None):
    tree = ast.parse((ROOT / filename).read_text())
    if class_name:
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
        cls.body = [n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in names]
        cls.bases = [ast.Name(id="Base", ctx=ast.Load())] if base else []
        cls.decorator_list = []
        namespace["Base"] = base
        nodes = [cls]
    else:
        nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in names]
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *nodes], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(ROOT / filename), "exec"), namespace)
    return namespace[class_name] if class_name else namespace


class EntityBase:
    async def async_added_to_hass(self):
        self.added = True

    async def async_will_remove_from_hass(self):
        self.removed = True

    def async_on_remove(self, callback):
        self.remove_callbacks.append(callback)


class LifecycleTests(unittest.IsolatedAsyncioTestCase):
    def integration(self, gateway, unload_ok):
        platforms = ["climate", "sensor"]
        other = object()
        data = {"other": other, "config": {"keep": True}}
        hass = SimpleNamespace(
            data={"eltako": data},
            config_entries=SimpleNamespace(async_unload_platforms=AsyncMock(return_value=unload_ok)),
        )
        ns = load_methods("eltako_integration_init.py", None, {"async_unload_entry"}, {
            "get_gateway_from_hass": lambda hass, entry: gateway,
            "LOGGER": logging.getLogger("test"), "PLATFORMS": platforms, "DATA_ELTAKO": "eltako",
        })
        return ns["async_unload_entry"], hass, data, other, platforms

    async def test_unload_stops_gateway_only_after_platforms_and_keeps_shared_data(self):
        gateway = SimpleNamespace(dev_name="gateway")
        unload, hass, data, other, platforms = self.integration(gateway, True)
        entry = object()

        async def stop_gateway():
            hass.config_entries.async_unload_platforms.assert_awaited_once_with(entry, platforms)

        gateway.async_unload = AsyncMock(side_effect=stop_gateway)
        self.assertTrue(await unload(hass, entry))
        gateway.async_unload.assert_awaited_once()
        self.assertEqual(data, {"other": other, "config": {"keep": True}})

    async def test_failed_platform_unload_preserves_gateway(self):
        gateway = SimpleNamespace(dev_name="gateway", async_unload=AsyncMock())
        unload, hass, data, _, _ = self.integration(gateway, False)
        before = data.copy()
        self.assertFalse(await unload(hass, object()))
        gateway.async_unload.assert_not_awaited()
        self.assertEqual(data, before)

    async def test_gateway_stops_in_worker_and_removes_service_and_dispatcher(self):
        cls = load_methods("gateway.py", "EnOceanGateway", {"async_unload", "_stop_bus"}, {
            "DOMAIN": "eltako", "LOGGER": logging.getLogger("test"),
        })
        gateway = cls()
        gateway.dev_id = gateway._attr_dev_id = 7
        main_thread = threading.get_ident()
        calls = []
        gateway._bus = SimpleNamespace(
            stop=lambda: calls.append(("stop", threading.get_ident())),
            join=lambda: calls.append(("join", threading.get_ident())),
        )
        gateway.hass = SimpleNamespace(
            services=SimpleNamespace(async_remove=Mock()),
            async_add_executor_job=asyncio.to_thread,
        )
        disconnect = Mock()
        gateway.dispatcher_disconnect_handle = disconnect
        gateway._last_message_received_handler = Mock()
        gateway._connection_state_handler = Mock()
        gateway._received_message_count_handler = Mock()
        await gateway.async_unload()
        gateway.hass.services.async_remove.assert_called_once_with("eltako", "gateway_7_send_message")
        disconnect.assert_called_once()
        self.assertIsNone(gateway.dispatcher_disconnect_handle)
        self.assertTrue(all(t != main_thread for _, t in calls))
        self.assertEqual([name for name, _ in calls], ["stop", "join"])
        self.assertIsNone(gateway._last_message_received_handler)
        self.assertIsNone(gateway._connection_state_handler)
        self.assertIsNone(gateway._received_message_count_handler)
        # Bus stopping must not depend on whether a dispatcher was registered.
        await gateway.async_unload()
        disconnect.assert_called_once()
        self.assertEqual(len(calls), 4)

    def climate(self, cooling=False):
        cls = load_methods("climate.py", "ClimateController", {
            "async_added_to_hass", "async_will_remove_from_hass", "_wrapped_update",
        }, {
            "asyncio": asyncio, "suppress": suppress,
            "EVENT_BUTTON_PRESSED": "btn_pressed", "CONF_SWITCH_BUTTON": "button",
            "LOGGER": logging.getLogger("test"),
            "config_helpers": SimpleNamespace(
                get_bus_event_type=lambda *args: "cooling_event",
                convert_button_pos_from_hex_to_str=lambda value: "LT",
            ),
        }, base=EntityBase)
        entity = cls()
        entity._update_task = None
        entity.remove_callbacks = []
        entity.cooling_switch = SimpleNamespace(id="switch", get=lambda key: 0x30) if cooling else None
        entity.async_handle_event = AsyncMock()
        entity.unique_id = "test_climate"
        entity.thermostat = None
        entity._actuator_mode = "heat"
        entity.target_temperature = 21
        entity._update_frequency = 0.001
        entity._async_send_command = AsyncMock()
        entity._async_check_if_cooling_is_activated = AsyncMock()
        entity._async_send_mode_cooling = AsyncMock()
        entity.listener_count = 0
        entity.tasks = []

        def listen(event_id, callback):
            entity.listener_count += 1

            def unsubscribe():
                entity.listener_count -= 1

            return unsubscribe

        def background(hass, coro, name):
            self.assertTrue(entity.added)
            task = asyncio.create_task(coro, name=name)
            entity.tasks.append(task)
            return task

        entity.hass = SimpleNamespace(bus=SimpleNamespace(async_listen=Mock(side_effect=listen)))
        entity.gateway = SimpleNamespace(base_id="base", config_entry=SimpleNamespace(async_create_background_task=background))
        return entity

    async def remove_entity(self, entity):
        await entity.async_will_remove_from_hass()
        # HA runs registered removal callbacks as part of entity removal.
        for callback in entity.remove_callbacks:
            callback()
        entity.remove_callbacks.clear()

    async def test_three_reload_cycles_stop_old_senders_and_cooling_listeners(self):
        old = []
        for _ in range(3):
            entity = self.climate(cooling=True)
            await entity.async_added_to_hass()
            self.assertEqual(entity.listener_count, 1)
            await asyncio.wait_for(self.wait_for_send(entity), 1)
            self.assertEqual(len(entity.tasks), 1)
            for previous, count in old:
                self.assertEqual(previous._async_send_command.await_count, count)
                self.assertEqual(previous.listener_count, 0)
            await self.remove_entity(entity)
            self.assertTrue(entity.tasks[0].cancelled())
            self.assertIsNone(entity._update_task)
            self.assertEqual(entity.listener_count, 0)
            old.append((entity, entity._async_send_command.await_count))

    async def wait_for_send(self, entity):
        while not entity._async_send_command.await_count:
            await asyncio.sleep(0.001)

    async def test_no_cooling_listener_and_immediate_removal(self):
        entity = self.climate()
        await entity.async_added_to_hass()
        entity.hass.bus.async_listen.assert_not_called()
        await self.remove_entity(entity)
        entity._async_send_command.assert_not_awaited()

    async def test_remove_cancels_inflight_periodic_send(self):
        entity = self.climate()
        sending = asyncio.Event()
        stopped = asyncio.Event()

        async def blocked_send(*args):
            sending.set()
            try:
                await asyncio.Event().wait()
            finally:
                stopped.set()

        entity._async_send_command.side_effect = blocked_send
        await entity.async_added_to_hass()
        await asyncio.wait_for(sending.wait(), 1)
        await self.remove_entity(entity)
        self.assertTrue(stopped.is_set())
        self.assertTrue(entity.tasks[0].cancelled())


if __name__ == "__main__":
    unittest.main()
