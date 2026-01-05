"""
LED Controller Classes for different LED systems (WLED, Govee, Philips Hue)
"""

import requests
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple


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
        """Set the LED color (hex format like #FFFFFF)"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the controller can connect to the device"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict:
        """Get current device status"""
        pass


class WLEDController(LEDController):
    """Controller for WLED devices"""
    
    def __init__(self, ip: str):
        self.ip = ip
        self.base_url = f"http://{ip}/json/state"
    
    def turn_on(self) -> bool:
        """Turn WLED on"""
        try:
            payload = {"on": True}
            response = requests.post(self.base_url, json=payload, timeout=5)
            print(f"[WLED] Turning ON -> {self.base_url}")
            return response.status_code == 200
        except Exception as e:
            print(f"[WLED ERROR] Failed to turn on: {e}")
            return False
    
    def turn_off(self) -> bool:
        """Turn WLED off"""
        try:
            payload = {"on": False}
            response = requests.post(self.base_url, json=payload, timeout=5)
            print(f"[WLED] Turning OFF -> {self.base_url}")
            return response.status_code == 200
        except Exception as e:
            print(f"[WLED ERROR] Failed to turn off: {e}")
            return False
    
    def set_color(self, color: str) -> bool:
        """Set WLED color"""
        try:
            hex_color = color.lstrip("#")
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            payload = {"on": True, "seg": [{"col": [[r, g, b]]}]}
            response = requests.post(self.base_url, json=payload, timeout=5)
            print(f"[WLED] Setting color RGB({r},{g},{b}) -> {self.base_url}")
            return response.status_code == 200
        except Exception as e:
            print(f"[WLED ERROR] Failed to set color: {e}")
            return False
    
    def set_effect(self, effect_id: int) -> bool:
        """Set WLED effect"""
        try:
            payload = {"on": True, "seg": [{"fx": effect_id}]}
            response = requests.post(self.base_url, json=payload, timeout=5)
            print(f"[WLED] Setting effect #{effect_id} -> {self.base_url}")
            return response.status_code == 200
        except Exception as e:
            print(f"[WLED ERROR] Failed to set effect: {e}")
            return False
    
    def set_preset(self, preset_id: int) -> bool:
        """Set WLED preset"""
        try:
            payload = {"ps": preset_id}
            response = requests.post(self.base_url, json=payload, timeout=5)
            print(f"[WLED] Running preset #{preset_id} -> {self.base_url}")
            return response.status_code == 200
        except Exception as e:
            print(f"[WLED ERROR] Failed to set preset: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test WLED connection"""
        try:
            response = requests.get(f"http://{self.ip}/json/info", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_status(self) -> Dict:
        """Get WLED status"""
        try:
            response = requests.get(self.base_url, timeout=5)
            return response.json() if response.status_code == 200 else {}
        except:
            return {}


class GoveeController(LEDController):
    """Controller for Govee devices"""
    
    def __init__(self, api_key: str, device_id: str, model: str):
        self.api_key = api_key
        self.device_id = device_id
        self.model = model
        self.base_url = "https://developer-api.govee.com/v1/devices"
        self.headers = {
            "Govee-API-Key": api_key,
            "Content-Type": "application/json"
        }
        self._scenes_cache = None
    
    def _make_control_request(self, capability: str, value: any) -> bool:
        """Make a control request to Govee API"""
        try:
            payload = {
                "device": self.device_id,
                "model": self.model,
                "cmd": {
                    "name": capability,
                    "value": value
                }
            }
            response = requests.put(f"{self.base_url}/control", 
                                  json=payload, headers=self.headers, timeout=10)
            print(f"[GOVEE] Control request {capability}: {value} -> Status: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            print(f"[GOVEE ERROR] Control request failed: {e}")
            return False
    
    def turn_on(self) -> bool:
        """Turn Govee device on"""
        return self._make_control_request("turn", "on")
    
    def turn_off(self) -> bool:
        """Turn Govee device off"""
        return self._make_control_request("turn", "off")
    
    def set_color(self, color: str) -> bool:
        """Set Govee color"""
        try:
            # Convert hex to RGB
            hex_color = color.lstrip("#")
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # Govee expects RGB values
            rgb_value = {"r": r, "g": g, "b": b}
            return self._make_control_request("color", rgb_value)
        except Exception as e:
            print(f"[GOVEE ERROR] Failed to set color: {e}")
            return False
    
    def set_brightness(self, brightness: int) -> bool:
        """Set Govee brightness (0-100)"""
        brightness = max(0, min(100, brightness))  # Clamp to valid range
        return self._make_control_request("brightness", brightness)
    
    def set_scene(self, scene_id: int) -> bool:
        """Set Govee scene"""
        scenes = self.get_scenes()
        if scenes and 0 <= scene_id < len(scenes):
            scene_code = scenes[scene_id].get("code", 0)
            return self._make_control_request("scene", scene_code)
        else:
            print(f"[GOVEE ERROR] Invalid scene ID: {scene_id}")
            return False
    
    def get_scenes(self) -> List[Dict]:
        """Get available Govee scenes"""
        if self._scenes_cache is not None:
            return self._scenes_cache
        
        try:
            params = {"device": self.device_id, "model": self.model}
            response = requests.get(f"{self.base_url}/scenes", 
                                  params=params, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self._scenes_cache = data.get("data", {}).get("scenes", [])
                print(f"[GOVEE] Loaded {len(self._scenes_cache)} scenes")
                return self._scenes_cache
            else:
                print(f"[GOVEE ERROR] Failed to get scenes: {response.status_code}")
                return []
        except Exception as e:
            print(f"[GOVEE ERROR] Failed to get scenes: {e}")
            return []
    
    def get_devices(self) -> List[Dict]:
        """Get available Govee devices"""
        try:
            response = requests.get(f"{self.base_url}/devices", 
                                  headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                devices = data.get("data", {}).get("devices", [])
                print(f"[GOVEE] Found {len(devices)} devices")
                return devices
            else:
                print(f"[GOVEE ERROR] Failed to get devices: {response.status_code}")
                return []
        except Exception as e:
            print(f"[GOVEE ERROR] Failed to get devices: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test Govee API connection"""
        try:
            devices = self.get_devices()
            # Check if our device is in the list
            for device in devices:
                if device.get("device") == self.device_id and device.get("model") == self.model:
                    return True
            return False
        except:
            return False
    
    def get_status(self) -> Dict:
        """Get Govee device status"""
        try:
            params = {"device": self.device_id, "model": self.model}
            response = requests.get(f"{self.base_url}/state", 
                                  params=params, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json().get("data", {})
            else:
                print(f"[GOVEE ERROR] Failed to get status: {response.status_code}")
                return {}
        except Exception as e:
            print(f"[GOVEE ERROR] Failed to get status: {e}")
            return {}


class PhilipsHueController(LEDController):
    """Controller for Philips Hue devices (placeholder for future implementation)"""
    
    def __init__(self, bridge_ip: str, username: str):
        self.bridge_ip = bridge_ip
        self.username = username
        self.base_url = f"http://{bridge_ip}/api/{username}"
    
    def turn_on(self) -> bool:
        """Turn Philips Hue lights on"""
        # TODO: Implement Philips Hue API calls
        print("[HUE] Turn on - Not implemented yet")
        return False
    
    def turn_off(self) -> bool:
        """Turn Philips Hue lights off"""
        # TODO: Implement Philips Hue API calls
        print("[HUE] Turn off - Not implemented yet")
        return False
    
    def set_color(self, color: str) -> bool:
        """Set Philips Hue color"""
        # TODO: Implement Philips Hue API calls
        print(f"[HUE] Set color {color} - Not implemented yet")
        return False
    
    def test_connection(self) -> bool:
        """Test Philips Hue connection"""
        # TODO: Implement Philips Hue API calls
        print("[HUE] Test connection - Not implemented yet")
        return False
    
    def get_status(self) -> Dict:
        """Get Philips Hue status"""
        # TODO: Implement Philips Hue API calls
        print("[HUE] Get status - Not implemented yet")
        return {}


def create_led_controller(led_type: str, config: Dict) -> Optional[LEDController]:
    """Factory function to create appropriate LED controller"""
    
    if led_type == "wled":
        ip = config.get("wled_ip", "")
        if not ip:
            print("[ERROR] WLED IP not configured")
            return None
        return WLEDController(ip)
    
    elif led_type == "govee":
        api_key = config.get("govee_api_key", "")
        device_id = config.get("govee_device_id", "")
        model = config.get("govee_model", "")
        
        if not all([api_key, device_id, model]):
            print("[ERROR] Govee API key, device ID, or model not configured")
            return None
        return GoveeController(api_key, device_id, model)
    
    elif led_type == "philips_hue":
        bridge_ip = config.get("hue_bridge_ip", "")
        username = config.get("hue_username", "")
        
        if not all([bridge_ip, username]):
            print("[ERROR] Philips Hue bridge IP or username not configured")
            return None
        return PhilipsHueController(bridge_ip, username)
    
    else:
        print(f"[ERROR] Unknown LED type: {led_type}")
        return None