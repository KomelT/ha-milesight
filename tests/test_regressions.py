"""Small dependency-free regression tests for pure integration behavior."""

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from homeassistant.exceptions import HomeAssistantError
from homeassistant.components.http import KEY_HASS

from custom_components.milesight.binary_sensor import MilesightBinarySensor
from custom_components.milesight.config_flow import (
    _validate_downlink_template,
    _validate_topic_filter,
)
from custom_components.milesight.codecs.wt101.encode import setFreezeProtection
from custom_components.milesight.encoder import EncodeError, encode_payload
from custom_components.milesight.manager import MilesightDevice, MilesightManager
from custom_components.milesight.switches.freeze_protection import _freeze_threshold
from custom_components.milesight import (
    async_setup_entry,
    async_unload_entry,
)
from custom_components.milesight.const import DOMAIN
from custom_components.milesight.http_view import (
    MilesightDeviceActionView,
    MilesightDevicesView,
)


class EncoderTests(unittest.TestCase):
    def test_unknown_command_is_rejected(self):
        with self.assertRaises(EncodeError):
            encode_payload("wt101", {"not_a_command": 1})

    def test_empty_command_result_is_rejected(self):
        with self.assertRaises(EncodeError):
            encode_payload("wt101", {"reboot": 0})

    def test_invalid_fport_is_rejected(self):
        with self.assertRaises(EncodeError):
            encode_payload("wt101", {"reboot": 1, "fport": "not-an-int"})

    def test_freeze_threshold_rejects_bool_and_out_of_range(self):
        for threshold in (True, 0, 6):
            with self.assertRaises(ValueError):
                setFreezeProtection({"enable": 1, "temperature": threshold})

    def test_freeze_threshold_uses_configured_value_not_ambient_temperature(self):
        self.assertEqual(
            _freeze_threshold(
                {"temperature": 20, "freeze_protection_config": {"temperature": 2}}
            ),
            2,
        )
        self.assertEqual(_freeze_threshold({"temperature": 2}), 3)
        self.assertEqual(_freeze_threshold({"freeze_protection_config.temperature": 4}), 4)


class HelperTests(unittest.TestCase):
    def test_topic_validators_reject_embedded_plus(self):
        with self.assertRaises(Exception):
            _validate_topic_filter("milesight/foo+bar/+/uplink")
        with self.assertRaises(Exception):
            _validate_downlink_template("milesight/foo+bar/+/downlink")
        with self.assertRaises(Exception):
            _validate_downlink_template("milesight//+/+/downlink")
        self.assertEqual(
            _validate_downlink_template("milesight/{model}/{dev_eui}/downlink"),
            "milesight/{model}/{dev_eui}/downlink",
        )

    def test_topic_parser_checks_custom_literals(self):
        manager = MilesightManager(None, "entry", "custom/+/+/uplink")
        self.assertEqual(
            manager._parse_topic("custom/WT101/ABC/uplink"), ("ABC", "WT101")
        )
        self.assertEqual(manager._parse_topic("other/WT101/ABC/uplink"), (None, None))

    def test_get_device_normalizes_dev_eui(self):
        manager = MilesightManager(None, "entry", "custom/+/+/uplink")
        device = MilesightDevice("abc", "WT101")
        manager.devices["abc"] = device
        self.assertIs(manager.get_device(" ABC "), device)

    def test_boolean_conversion_is_safe(self):
        sensor = MilesightBinarySensor.__new__(MilesightBinarySensor)
        self.assertTrue(sensor._as_on("x", "true"))
        for value in ("enable", "open", "uninstalled", "triggered"):
            self.assertTrue(sensor._as_on("x", value))
        for value in ("disable", "normal", "installed"):
            self.assertFalse(sensor._as_on("x", value))
        self.assertTrue(sensor._as_on("x", 1))
        self.assertFalse(sensor._as_on("x", "unexpected"))


class MqttHandlerTests(unittest.IsolatedAsyncioTestCase):
    async def test_decoded_object_adds_and_updates_device(self):
        manager = MilesightManager(None, "entry", "milesight/+/+/uplink")
        message = SimpleNamespace(
            topic="milesight/WT101/AA-BB/uplink",
            payload='{"temperature": 21, "deviceName": "Hall"}',
        )
        with patch("custom_components.milesight.manager.async_dispatcher_send"):
            with patch.object(manager, "_async_sync_device_registry", new=AsyncMock()):
                await manager.async_handle_join_uplink(message)
                await manager.async_handle_join_uplink(
                    SimpleNamespace(
                        topic=message.topic,
                        payload='{"temperature": 22}',
                    )
                )
        device = manager.get_device("aa-bb")
        self.assertIsNotNone(device)
        self.assertEqual(device.name, "Hall")
        self.assertEqual(device.telemetry["temperature"], 22)

    async def test_invalid_payloads_and_topic_are_ignored(self):
        manager = MilesightManager(None, "entry", "milesight/+/+/uplink")
        messages = [
            ("milesight/WT101/AA/uplink", "[]"),
            ("milesight/WT101/BB/uplink", '"text"'),
            ("milesight/WT101/CC/uplink", "not-json"),
            ("other/WT101/DD/uplink", '{"temperature": 1}'),
        ]
        with patch("custom_components.milesight.manager.async_dispatcher_send"):
            with patch.object(manager, "_async_sync_device_registry", new=AsyncMock()):
                for topic, payload in messages:
                    await manager.async_handle_join_uplink(
                        SimpleNamespace(topic=topic, payload=payload)
                    )
        self.assertEqual(manager.devices, {})

    async def test_join_handler_can_use_different_filter(self):
        manager = MilesightManager(
            None, "entry", "custom/+/+/uplink", "custom/+/+/join"
        )
        with patch("custom_components.milesight.manager.async_dispatcher_send"):
            with patch.object(manager, "_async_sync_device_registry", new=AsyncMock()):
                await manager.async_handle_join_uplink(
                    SimpleNamespace(
                        topic="custom/WT101/AA/join", payload='{"battery": 90}'
                    ),
                    topic_filter=manager.join_topic,
                )
        self.assertIn("aa", manager.devices)


class LifecycleTests(unittest.IsolatedAsyncioTestCase):
    def _hass(self):
        services = SimpleNamespace(
            async_register=Mock(), async_remove=Mock(), has_service=Mock(return_value=True)
        )
        return SimpleNamespace(
            data={},
            http=SimpleNamespace(register_view=Mock()),
            services=services,
            config_entries=SimpleNamespace(
                async_forward_entry_setups=AsyncMock(), async_unload_platforms=AsyncMock()
            ),
        )

    def _entry(self):
        entry = SimpleNamespace(
            entry_id="entry",
            data={"join_topic": "join/+/+", "uplink_topic": "uplink/+/+"},
            async_on_unload=Mock(),
            add_update_listener=Mock(return_value=lambda: None),
        )
        return entry

    async def test_setup_subscribes_join_and_uplink_only_and_registers_services(self):
        hass = self._hass()
        entry = self._entry()
        unsub_join, unsub_uplink = Mock(), Mock()

        async def subscribe(_hass, topic, callback):
            self.assertIn(topic, ("join/+/+", "uplink/+/+"))
            return unsub_join if topic.startswith("join") else unsub_uplink

        with patch("custom_components.milesight.mqtt.async_subscribe", side_effect=subscribe):
            self.assertTrue(await async_setup_entry(hass, entry))
        self.assertEqual(hass.data[DOMAIN][entry.entry_id].join_topic, "join/+/+")
        self.assertEqual(hass.services.async_register.call_count, 2)
        entry.add_update_listener.assert_called_once()

    async def test_setup_second_subscription_failure_closes_first(self):
        hass = self._hass()
        entry = self._entry()
        first_unsub = Mock()

        async def subscribe(_hass, topic, callback):
            if topic.startswith("join"):
                return first_unsub
            raise HomeAssistantError("broker failure")

        with patch("custom_components.milesight.mqtt.async_subscribe", side_effect=subscribe):
            with self.assertRaises(Exception):
                await async_setup_entry(hass, entry)
        first_unsub.assert_called_once()
        self.assertNotIn(DOMAIN, hass.data)

    async def test_unload_failure_preserves_manager_and_services(self):
        hass = self._hass()
        entry = self._entry()
        manager = MilesightManager(hass, entry.entry_id, "uplink/+/+")
        manager.register_mqtt(Mock())
        hass.data[DOMAIN] = {entry.entry_id: manager}
        hass.config_entries.async_unload_platforms.return_value = False
        self.assertFalse(await async_unload_entry(hass, entry))
        self.assertIs(hass.data[DOMAIN][entry.entry_id], manager)

    async def test_successful_unload_closes_manager_and_removes_services(self):
        hass = self._hass()
        entry = self._entry()
        manager = MilesightManager(hass, entry.entry_id, "uplink/+/+")
        unsub = Mock()
        manager.register_mqtt(unsub)
        hass.data[DOMAIN] = {entry.entry_id: manager}
        self.assertTrue(await async_unload_entry(hass, entry))
        unsub.assert_called_once()
        self.assertNotIn(entry.entry_id, hass.data[DOMAIN])
        self.assertEqual(hass.services.async_remove.call_count, 2)


class HttpViewTests(unittest.IsolatedAsyncioTestCase):
    def _request(self, hass, body=None, error=None):
        request = SimpleNamespace(app={KEY_HASS: hass})
        if error is not None:
            request.json = AsyncMock(side_effect=error)
        else:
            request.json = AsyncMock(return_value=body)
        return request

    async def test_views_return_503_without_manager(self):
        hass = SimpleNamespace(data={})
        response = await MilesightDevicesView().get(self._request(hass))
        self.assertEqual(response.status, 503)
        response = await MilesightDeviceActionView().post(self._request(hass, {}))
        self.assertEqual(response.status, 503)

    async def test_action_validation_and_successful_delete(self):
        manager = Mock(spec=MilesightManager)
        manager.async_delete_device = AsyncMock(side_effect=[False, True])
        hass = SimpleNamespace(data={DOMAIN: {"entry": manager}})
        view = MilesightDeviceActionView()
        for body in (None, [], {"dev_eui": "x"}, {"dev_eui": "x", "action": "bad"}):
            response = await view.post(
                self._request(hass, body, ValueError("bad"))
                if body is None
                else self._request(hass, body)
            )
            self.assertEqual(response.status, 400)
        response = await view.post(self._request(hass, {"dev_eui": "unknown", "action": "delete"}))
        self.assertEqual(response.status, 404)
        response = await view.post(self._request(hass, {"dev_eui": "known", "action": "delete"}))
        self.assertEqual(response.status, 200)

    async def test_get_serializes_devices(self):
        manager = Mock(spec=MilesightManager)
        manager.serialize_devices.return_value = [{"dev_eui": "aa"}]
        hass = SimpleNamespace(data={DOMAIN: {"entry": manager}})
        response = await MilesightDevicesView().get(self._request(hass))
        self.assertEqual(response.status, 200)


class RegistryCleanupTests(unittest.IsolatedAsyncioTestCase):
    async def test_delete_removes_matching_entities_and_device(self):
        hass = object()
        manager = MilesightManager(hass, "entry", "uplink/+/+")
        manager.devices["aa"] = MilesightDevice("aa", "WT101")
        entity = SimpleNamespace(config_entry_id="entry", device_id="device-id", entity_id="sensor.aa")
        entity_registry = SimpleNamespace(entities={"sensor.aa": entity}, async_remove=Mock())
        device = SimpleNamespace(identifiers={(DOMAIN, "aa")}, id="device-id")
        device_registry = SimpleNamespace(
            async_get=Mock(return_value=device),
            async_get_device=Mock(return_value=device),
            async_remove_device=Mock(),
        )
        with patch("custom_components.milesight.manager.er.async_get", return_value=entity_registry):
            with patch("custom_components.milesight.manager.dr.async_get", return_value=device_registry):
                self.assertTrue(await manager.async_delete_device(" AA "))
        entity_registry.async_remove.assert_called_once_with("sensor.aa")
        device_registry.async_remove_device.assert_called_once_with("device-id")
