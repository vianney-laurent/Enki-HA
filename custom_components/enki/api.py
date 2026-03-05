"""Enki API."""

import aiohttp
from dataclasses import dataclass
from typing import Any
import time

from .const import (
    LOGGER,
    ENKI_OIDC_URL,
    ENKI_URL,
    ENKI_HOME_API_KEY,
    ENKI_BFF_API_KEY,
    ENKI_NODE_API_KEY,
    ENKI_REFERENTIEL_API_KEY,
    ENKI_LIGHTS_API_KEY)

proxy = None

@dataclass
class Device:
    """API device."""
    home_id: str
    device_id: str #device_id represents the type of device used (Hw reference)
    node_id: str #node_id represents the physical device (toke,)
    device_name: str

class API:
    """Class for Enki API."""

    def __init__(self, user: str, pwd: str) -> None:
        """Initialise."""
        self.user = user
        self.pwd = pwd

    @property
    def controller_name(self) -> str:
        """Return the name of the controller."""
        return self.user

    async def check_connected(self) -> bool:
        """Tell if token is still valid"""
        if not hasattr(self, '_access_token') or time.time()>self._tokenExpiresTime:
             await self.connect()
        return True

    async def connect(self) -> bool:
        """Connect to the Enki API."""
        try:
            async with aiohttp.ClientSession() as session, session.request(
                method="POST",
                url=ENKI_OIDC_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={"grant_type":"password",
                    "client_id": "enki-front",
                    "username": self.user,
                    "password": self.pwd},
                proxy=proxy,) as resp:

                    if resp.status == 200:
                        response = await resp.json()
                        LOGGER.debug("connect : %s", response)
                        self._access_token = response["access_token"]
                        self._refresh_token = response["refresh_token"]
                        self._token_type = response["token_type"]
                        tokenExpiresTime = time.time() + response["expires_in"]
                        self._tokenExpiresTime = tokenExpiresTime
                        return True
                    else:
                        error_text = await resp.text()
                        LOGGER.error("Enki API authentication failed! HTTP Status: %s, Response: %s", resp.status, error_text)
                        raise APIAuthError(f"Authentication failed with status {resp.status}")
        except aiohttp.ClientError as e:
            LOGGER.error("Enki API connection error during connect(): %s", e)
            raise APIConnectionError(f"Connection error: {e}")
        except Exception as e:
            LOGGER.error("Enki API unexpected error during connect(): %r", e)
            raise APIConnectionError(f"Unexpected error: {e}")

# *******************************************************
    async def get_homes(self):
        """Get list of homes."""
        await self.check_connected()
        homes = []
        async with aiohttp.ClientSession() as session, session.request(
             method="GET",
             url=f"{ENKI_URL}/api-enki-home-prod/v1/homes",
             headers={"Authorization": f"{self._token_type} {self._access_token}",
                      "X-Gateway-APIKey": ENKI_HOME_API_KEY},
             proxy=proxy,) as resp:

                if resp.status == 200:
                    response = await resp.json()
                    LOGGER.debug("get_homes : %s", response)
                    for home in response["items"]:
                        homes.append(home["id"])
                    return homes
                else:
                    error_text = await resp.text()
                    LOGGER.error("Error on get_homes. HTTP Status: %s, Response: %s", resp.status, error_text)
                    raise ValueError(f"Enki API get_homes error: {resp.status}")

    def merge_properties(self, device, properties):
         for prop in properties:
            if prop != "id":
                device[prop] = properties[prop]

    async def get_items_in_section_for_home(self, home_id) -> list[dict[str, Any]]:
            """Get sections in home."""
            await self.check_connected()
            async with aiohttp.ClientSession() as session, session.request(
             method="GET",
             url=f"{ENKI_URL}/api-enki-mobile-bff-prod/v1/dashboard/homes/{home_id}?hasGroups=true",
             headers={"Authorization": f"{self._token_type} {self._access_token}",
                      "X-Gateway-APIKey": ENKI_BFF_API_KEY},
             proxy=proxy,) as resp:
                devices = []
                if resp.status == 200:
                    response = await resp.json()
                    LOGGER.debug("get_items_in_section_for_home : %s", response)
                    for section in response["sections"]:
                        for item in section["items"]:
                            if 'deviceId' not in item["metadata"].keys():
                                continue
                            device = {
                                "homeId": home_id,
                                "deviceId": item["metadata"]["deviceId"],
                                "nodeId": item["metadata"]["nodeId"],
                                "deviceName": item["title"]["label"],
                                "state": item["state"],
                                "isEnabled": item["isEnabled"]
                            }
                            devices.append(device)

                            node_info = await self.get_node(home_id, device.get("nodeId"))
                            self.merge_properties(device, node_info)
                            
                            device_info = await self.get_device(device.get("deviceId"))
                            self.merge_properties(device, device_info)

                            await self.refresh_device(device)

                            LOGGER.debug("device : %r", device)
                    return devices
                  
                else:
                    error_text = await resp.text()
                    LOGGER.error("Error on get_items_in_section_for_home. HTTP Status: %s, Response: %s", resp.status, error_text)
                    raise ValueError(f"Enki API get_items_in_section_for_home error: {resp.status}")

    async def refresh_device(self, device): 
        """Update device details"""
        device_info = await self.get_device(device.get("deviceId"))
        self.merge_properties(device, device_info)
        if device.get("type") == "lights" and device.get("isEnabled"):
            try:
                # get lights details (on/off, brightness, temperature, etc)
                light_details = await self.get_light_details(device.get("homeId"), device.get("nodeId"))
                self.merge_properties(device, light_details)
            except ValueError as e:
                LOGGER.warning("Could not fetch light details for device %s (node %s): %s", 
                               device.get("deviceName"), device.get("nodeId"), e)
        return device

    async def get_node(self, home_id, node_id):
        """Get details on a node."""
        await self.check_connected()
        async with aiohttp.ClientSession() as session, session.request(
            method="GET",
            url=f"{ENKI_URL}/api-enki-node-agg-prod/v1/nodes/{node_id}",
            headers={"Authorization": f"{self._token_type} {self._access_token}",
                    "X-Gateway-APIKey": ENKI_NODE_API_KEY,
                    "homeId": f"{home_id}"},
            proxy=proxy,) as resp:

                if resp.status == 200:
                    response = await resp.json()
                    LOGGER.debug("get_node : %s", response)
                    return response

                else:
                    error_text = await resp.text()
                    LOGGER.error("Error on get_node. HTTP Status: %s, Response: %s", resp.status, error_text)
                    raise ValueError(f"Enki API get_node error: {resp.status}")

    async def get_device(self, id):
        """Get details on a device."""
        await self.check_connected()
        async with aiohttp.ClientSession() as session, session.request(
            method="GET",
            url=f"{ENKI_URL}/api-enki-referentiel-agg-prod/v1/devices/{id}?version=2.15.0",
            headers={"Authorization": f"{self._token_type} {self._access_token}",
                    "X-Gateway-APIKey": ENKI_REFERENTIEL_API_KEY},
            proxy=proxy,) as resp:

                if resp.status == 200:
                    response = await resp.json()
                    LOGGER.debug("get_device : %s", response)
                    return response

                else:
                    error_text = await resp.text()
                    LOGGER.error("Error on get_device. HTTP Status: %s, Response: %s", resp.status, error_text)
                    raise ValueError(f"Enki API get_device error: {resp.status}")

    async def get_light_details(self,home_id, node_id):
         """Get light state"""
         await self.check_connected()
         async with aiohttp.ClientSession() as session, session.request(
             method="GET",
             url=f"{ENKI_URL}/api-enki-lighting-prod/v1/lighting/{node_id}/check-light-state",
             headers={"Authorization": f"{self._token_type} {self._access_token}",
                      "homeId": home_id,
                      "X-Gateway-APIKey": ENKI_LIGHTS_API_KEY},
             proxy=proxy,) as resp:

                if resp.status == 200:
                    response = await resp.json()
                    LOGGER.debug("get_light_details : %s", response)
                    return response

                else:
                    error_text = await resp.text()
                    LOGGER.error("Error on get_light_details. HTTP Status: %s, Response: %s", resp.status, error_text)
                    raise ValueError(f"Enki API get_light_details error: {resp.status}")

    async def change_light_state(self, home_id, node_id, parameter, value):
        await self.check_connected()
        
        details = await self.get_light_details(home_id, node_id)
        if "lastReportedValue" not in details or not details["lastReportedValue"]:
            # If the API doesn't return lastReportedValue, initialize an empty payload
            data = {}
            LOGGER.warning("Enki API: No lastReportedValue found for node %s during state change. Sending partial payload.", node_id)
        else:
            data = details["lastReportedValue"]
            
        data[parameter] = value
        
        async with aiohttp.ClientSession() as session, session.request(
            method="POST",
            url=f"{ENKI_URL}/api-enki-lighting-prod/v1/lighting/{node_id}/change-light-state",
            headers={"Authorization": f"{self._token_type} {self._access_token}",
                    "homeId": home_id,
                    "X-Gateway-APIKey": ENKI_LIGHTS_API_KEY},
            proxy=proxy,
            json=data) as resp:

                if resp.status != 202:
                    error_text = await resp.text()
                    LOGGER.error("Error on change_light_state. HTTP Status: %s, Response: %s", resp.status, error_text)
                    raise ValueError(f"Enki API change_light_state error: {resp.status}")

# *******************************************************

    async def get_devices(self) -> list[dict[str, Any]]:
        """Get devices on api."""
        homes = await self.get_homes()
        devices = []
        for home in homes:
            devices.extend(await self.get_items_in_section_for_home(home))

        return devices

class APIAuthError(Exception):
    """Exception class for auth error."""

class APIConnectionError(Exception):
    """Exception class for connection error."""
