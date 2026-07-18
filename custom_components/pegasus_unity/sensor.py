"""Sensor platform for the Pegasus Astro Unity integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import PegasusUnityConfigEntry
from .entity import PegasusUnityEntity
from .parser import DewPortData, PpbaData

if TYPE_CHECKING:
    from .coordinator import PegasusUnityCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class PegasusUnitySensorEntityDescription(SensorEntityDescription):
    """Describes a Pegasus Unity sensor with a value extraction function."""

    value_fn: Callable[[PpbaData], StateType]


SENSOR_DESCRIPTIONS: tuple[PegasusUnitySensorEntityDescription, ...] = (
    PegasusUnitySensorEntityDescription(
        key="voltage",
        translation_key="voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        value_fn=lambda data: data.voltage,
    ),
    PegasusUnitySensorEntityDescription(
        key="current",
        translation_key="current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda data: data.current,
    ),
    PegasusUnitySensorEntityDescription(
        key="quad_current",
        translation_key="quad_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda data: data.quad_current,
    ),
    PegasusUnitySensorEntityDescription(
        key="power",
        translation_key="power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda data: data.power,
    ),
    PegasusUnitySensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=lambda data: data.temperature,
    ),
    PegasusUnitySensorEntityDescription(
        key="humidity",
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.humidity,
    ),
    PegasusUnitySensorEntityDescription(
        key="dew_point",
        translation_key="dew_point",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=lambda data: data.dew_point,
    ),
    PegasusUnitySensorEntityDescription(
        key="average_current",
        translation_key="average_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=2,
        value_fn=lambda data: data.average_amps,
    ),
    PegasusUnitySensorEntityDescription(
        key="amp_hours",
        translation_key="amp_hours",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="Ah",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=2,
        value_fn=lambda data: data.amp_hours,
    ),
    PegasusUnitySensorEntityDescription(
        key="energy",
        translation_key="energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_display_precision=1,
        value_fn=lambda data: data.watt_hours,
    ),
    PegasusUnitySensorEntityDescription(
        key="uptime",
        translation_key="uptime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.uptime_seconds,
    ),
    PegasusUnitySensorEntityDescription(
        key="auto_dew_aggressiveness",
        translation_key="auto_dew_aggressiveness",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.aggressiveness,
    ),
    PegasusUnitySensorEntityDescription(
        key="variable_voltage",
        translation_key="variable_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.variable_voltage,
    ),
)


def _find_port(data: PpbaData, number: int) -> DewPortData | None:
    """Return the dew port with the given number, or None if absent."""
    for port in data.dew_ports:
        if port.number == number:
            return port
    return None


def _dew_power_description(
    number: int,
) -> PegasusUnitySensorEntityDescription:
    """Build the description for a dew heater port power sensor."""
    return PegasusUnitySensorEntityDescription(
        key=f"dew_power_{number}",
        translation_key="dew_power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data, n=number: (
            port.power_pct if (port := _find_port(data, n)) else None
        ),
    )


def _dew_current_description(
    number: int,
) -> PegasusUnitySensorEntityDescription:
    """Build the description for a dew heater port current sensor."""
    return PegasusUnitySensorEntityDescription(
        key=f"dew_current_{number}",
        translation_key="dew_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda data, n=number: (
            port.current if (port := _find_port(data, n)) else None
        ),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PegasusUnityConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pegasus Unity sensors, adding devices as they appear."""
    coordinator = entry.runtime_data
    known_devices: set[str] = set()

    def _add_new_devices() -> None:
        entities: list[PegasusUnitySensor] = []
        for device_id, data in coordinator.data.items():
            if device_id in known_devices:
                continue
            known_devices.add(device_id)
            for description in SENSOR_DESCRIPTIONS:
                entities.append(
                    PegasusUnitySensor(
                        coordinator,
                        device_id,
                        data.full_name,
                        data.firmware,
                        description,
                    )
                )
            for port in data.dew_ports:
                placeholders = {"port": str(port.number)}
                entities.append(
                    PegasusUnitySensor(
                        coordinator,
                        device_id,
                        data.full_name,
                        data.firmware,
                        _dew_power_description(port.number),
                        placeholders,
                    )
                )
                entities.append(
                    PegasusUnitySensor(
                        coordinator,
                        device_id,
                        data.full_name,
                        data.firmware,
                        _dew_current_description(port.number),
                        placeholders,
                    )
                )
        if entities:
            async_add_entities(entities)

    _add_new_devices()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_devices))


class PegasusUnitySensor(PegasusUnityEntity, SensorEntity):
    """A single Pegasus Unity sensor entity."""

    entity_description: PegasusUnitySensorEntityDescription

    def __init__(
        self,
        coordinator: PegasusUnityCoordinator,
        device_id: str,
        full_name: str,
        firmware: str,
        description: PegasusUnitySensorEntityDescription,
        translation_placeholders: dict[str, str] | None = None,
    ) -> None:
        """Initialise the sensor from its description."""
        super().__init__(coordinator, device_id, full_name, firmware)
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"
        if translation_placeholders is not None:
            self._attr_translation_placeholders = translation_placeholders

    @property
    def native_value(self) -> StateType:
        """Return the current value produced by the description's value_fn."""
        data = self.coordinator.data.get(self._device_id)
        if data is None:
            return None
        return self.entity_description.value_fn(data)
