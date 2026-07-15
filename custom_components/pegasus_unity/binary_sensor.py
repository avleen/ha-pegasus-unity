"""Binary sensor platform for the Pegasus Astro Unity integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PegasusUnityConfigEntry
from .entity import PegasusUnityEntity
from .parser import DewPortData, PpbaData

if TYPE_CHECKING:
    from .coordinator import PegasusUnityCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class PegasusUnityBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Pegasus Unity binary sensor with a value function."""

    value_fn: Callable[[PpbaData], bool | None]


BINARY_SENSOR_DESCRIPTIONS: tuple[
    PegasusUnityBinarySensorEntityDescription, ...
] = (
    PegasusUnityBinarySensorEntityDescription(
        key="over_current",
        translation_key="over_current",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: data.is_over_current,
    ),
    PegasusUnityBinarySensorEntityDescription(
        key="quad_output",
        translation_key="quad_output",
        device_class=BinarySensorDeviceClass.POWER,
        value_fn=lambda data: data.power_hub_on,
    ),
    PegasusUnityBinarySensorEntityDescription(
        key="variable_output",
        translation_key="variable_output",
        device_class=BinarySensorDeviceClass.POWER,
        value_fn=lambda data: data.variable_port_on,
    ),
    PegasusUnityBinarySensorEntityDescription(
        key="usb2_hub",
        translation_key="usb2_hub",
        device_class=BinarySensorDeviceClass.POWER,
        value_fn=lambda data: data.dual_usb2_on,
    ),
    PegasusUnityBinarySensorEntityDescription(
        key="auto_dew",
        translation_key="auto_dew",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: data.auto_dew_on,
    ),
)


def _find_port(data: PpbaData, number: int) -> DewPortData | None:
    """Return the dew port with the given number, or None if absent."""
    for port in data.dew_ports:
        if port.number == number:
            return port
    return None


def _dew_over_current_description(
    number: int,
) -> PegasusUnityBinarySensorEntityDescription:
    """Build the description for a dew heater port over-current sensor."""
    return PegasusUnityBinarySensorEntityDescription(
        key=f"dew_over_current_{number}",
        translation_key="dew_over_current",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data, n=number: (
            port.is_over_current if (port := _find_port(data, n)) else None
        ),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PegasusUnityConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pegasus Unity binary sensors from the coordinator data."""
    coordinator = entry.runtime_data
    entities: list[PegasusUnityBinarySensor] = []

    for device_id, data in coordinator.data.items():
        for description in BINARY_SENSOR_DESCRIPTIONS:
            entities.append(
                PegasusUnityBinarySensor(
                    coordinator, device_id, data.full_name, data.firmware, description
                )
            )
        for port in data.dew_ports:
            entities.append(
                PegasusUnityBinarySensor(
                    coordinator,
                    device_id,
                    data.full_name,
                    data.firmware,
                    _dew_over_current_description(port.number),
                    {"port": str(port.number)},
                )
            )

    async_add_entities(entities)


class PegasusUnityBinarySensor(PegasusUnityEntity, BinarySensorEntity):
    """A single Pegasus Unity binary sensor entity."""

    entity_description: PegasusUnityBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: PegasusUnityCoordinator,
        device_id: str,
        full_name: str,
        firmware: str,
        description: PegasusUnityBinarySensorEntityDescription,
        translation_placeholders: dict[str, str] | None = None,
    ) -> None:
        """Initialise the binary sensor from its description."""
        super().__init__(coordinator, device_id, full_name, firmware)
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"
        if translation_placeholders is not None:
            self._attr_translation_placeholders = translation_placeholders

    @property
    def is_on(self) -> bool | None:
        """Return the boolean state from the description's value_fn."""
        data = self.coordinator.data.get(self._device_id)
        if data is None:
            return None
        return self.entity_description.value_fn(data)
