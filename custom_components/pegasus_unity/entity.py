"""Base entity for the Pegasus Astro Unity integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import PegasusUnityCoordinator


class PegasusUnityEntity(CoordinatorEntity[PegasusUnityCoordinator]):
    """Base class wiring device info and availability for Unity entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PegasusUnityCoordinator,
        device_id: str,
        full_name: str,
        firmware: str,
    ) -> None:
        """Store the device id and build a static device info snapshot."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            manufacturer=MANUFACTURER,
            model=full_name,
            name=full_name,
            sw_version=firmware,
            serial_number=device_id,
        )

    @property
    def available(self) -> bool:
        """Return True only while the device is present in coordinator data."""
        return super().available and self._device_id in self.coordinator.data
