"""
LED Controller Classes for different LED systems
"""

import requests
import json
from abc import ABC, abstractmethod


class LEDController(ABC):
    """Abstract base class for LED controllers"""
    
    @abstractmethod
    def turn_on(self) -> bool:
        """Turn the LED device on"""
        pass
    
    @abstractmethod
    def turn_off(self) -> bool:
        """Turn the LED device off"""
        pass
    
    @abstractmethod
    def set_color(self, color: str) -> bool:
        """Set the LED color (hex format like #FF0000)"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the controller can connect to the device"""
        pass


class WLEDController(LEDController):
    """Controller for WLED devices"""
    
    def __init__(self, ip: str):
        self.ip = ip
        self.base_url = f"http://{ip}/json/state"
    
    def turn_on(self) -> bool:
        try:
            response = requests.post(self.base_url, json={"on": True}, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def turn_off(self) -> bool:
        try:
            response = requests.post(self.base_url, json={"on": False}, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def set_color(self, color: str) -> bool:
        try:
            hex_color = color.lstrip("#")
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            payload = {"on": True, "seg": [{"col": [[r, g, b]]}]}
            response = requests.post(self.base_url, json=payload, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def set_preset(self, preset_id: int) -> bool:
        try:
            response = requests.post(self.base_url, json={"ps": preset_id}, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def set_effect(self, effect_id: int) -> bool:
        try:
            payload = {"on": True, "seg": [{"fx": effect_id}]}
            response = requests.post(self.base_url, json=payload, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def set_brightness(self, brightness: int) -> bool:
        try:
            payload = {"on": True, "bri": brightness}
            response = requests.post(self.base_url, json=payload, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_connection(self) -> bool:
        try:
            response = requests.get(self.base_url, timeout=5)
            return response.status_code == 200
        except:
            return False


class GoveeController(LEDController):
    """Controller for Govee devices"""
    
    def __init__(self, api_key: str, device_id: str, model: str):
        self.api_key = api_key
        self.device_id = device_id
        self.model = model
        self.base_url = "https://developer-api.govee.com/v1/devices/control"
        self.headers = {"Govee-API-Key": api_key}
    
    def _send_command(self, command: dict) -> bool:
        try:
            payload = {
                "device": self.device_id,
                "model": self.model,
                "cmd": command
            }
            response = requests.put(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def turn_on(self) -> bool:
        return self._send_command({"name": "turn", "value": "on"})
    
    def turn_off(self) -> bool:
        return self._send_command({"name": "turn", "value": "off"})
    
    def set_color(self, color: str) -> bool:
        hex_color = color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return self._send_command({
            "name": "color",
            "value": {"r": r, "g": g, "b": b}
        })
    
    def set_brightness(self, brightness: int) -> bool:
        return self._send_command({"name": "brightness", "value": brightness})

    def set_scene(self, scene_id: int) -> bool:
        """Set a Govee scene by numeric id (value is passed through as-is)."""
        return self._send_command({"name": "scene", "value": scene_id})
    
    def test_connection(self) -> bool:
        try:
            response = requests.get(
                "https://developer-api.govee.com/v1/devices",
                headers=self.headers,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False


class HueController(LEDController):
    """Controller for Philips Hue lights"""
    
    def __init__(self, bridge_ip: str, username: str, light_id: int = 1):
        self.bridge_ip = bridge_ip
        self.username = username
        self.light_id = light_id
        self.base_url = f"http://{bridge_ip}/api/{username}/lights/{light_id}"
    
    def _send_command(self, command: dict) -> bool:
        try:
            response = requests.put(
                f"{self.base_url}/state",
                json=command,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def turn_on(self) -> bool:
        return self._send_command({"on": True})
    
    def turn_off(self) -> bool:
        return self._send_command({"on": False})
    
    def set_color(self, color: str) -> bool:
        # Convert hex to Hue's hue/sat/bri format
        hex_color = color.lstrip("#")
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        
        # Simple RGB to HSV conversion
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        diff = max_val - min_val
        
        if max_val == min_val:
            hue = 0
        elif max_val == r:
            hue = (60 * ((g - b) / diff) + 360) % 360
        elif max_val == g:
            hue = (60 * ((b - r) / diff) + 120) % 360
        else:
            hue = (60 * ((r - g) / diff) + 240) % 360
        
        sat = 0 if max_val == 0 else (diff / max_val)
        
        # Hue uses 0-65535 for hue, 0-254 for sat/bri
        hue_value = int((hue / 360.0) * 65535)
        sat_value = int(sat * 254)
        bri_value = int(max_val * 254)
        
        return self._send_command({
            "on": True,
            "hue": hue_value,
            "sat": sat_value,
            "bri": bri_value
        })
    
    def test_connection(self) -> bool:
        try:
            response = requests.get(self.base_url, timeout=5)
            return response.status_code == 200
        except:
            return False
