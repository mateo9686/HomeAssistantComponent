import logging
from datetime import datetime, timedelta
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import requests
import datetime
import time
from homeassistant.helpers.event import track_time_interval
from time import sleep

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)


# Domain and component constants and validation
DOMAIN = 'open_sense_contribute'
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_LAT = "latitude"
CONF_LON = "longitude"
CONF_MEASURANDS = "measurands"
CONF_SENSOR_IDS = "sensor_ids"
CONF_TOKEN = "token"
CONF_UNITS = "units"
CONF_LICENSE = "license"
CONF_ACCURACY = "accuracy"
CONF_ALTITUDE_ABOVE_GROUND = "altitude_above_ground"
CONF_DIRECTION_VERTICAL = "direction_vertical"
CONF_DIRECTION_HORIZONTAL = "direction_horizontal"

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_LAT): cv.latitude,
        vol.Required(CONF_LON): cv.longitude,
        vol.Required(CONF_MEASURANDS): cv.string,
        vol.Required(CONF_SENSOR_IDS): cv.string,
        vol.Required(CONF_TOKEN): cv.string,
        vol.Required(CONF_UNITS): cv.string,
        vol.Required(CONF_LICENSE): cv.string,
        vol.Required(CONF_ALTITUDE_ABOVE_GROUND): cv.string,
        vol.Required(CONF_DIRECTION_VERTICAL): cv.string,
        vol.Required(CONF_DIRECTION_HORIZONTAL): cv.string,
        vol.Required(CONF_ACCURACY): cv.string
    }),
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """ setup OpenSense domain """

    config = config.get(DOMAIN)

    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    lat = config.get(CONF_LAT)
    lon = config.get(CONF_LON)
    measurands = config.get(CONF_MEASURANDS)
    token = config.get(CONF_TOKEN)
    units = config.get(CONF_UNITS)
    sensor_ids = config.get(CONF_SENSOR_IDS)
    sensor_license = config.get(CONF_LICENSE)
    altitude_above_ground = config.get(CONF_ALTITUDE_ABOVE_GROUND)
    direction_vertical = config.get(CONF_DIRECTION_VERTICAL)
    direction_horizontal = config.get(CONF_DIRECTION_HORIZONTAL)
    accuracy = config.get(CONF_ACCURACY)
    if units is not None:
        units = units.replace(" ", "").split(',')

    sensors = create_sensors_for_given_measurands(username, password, token, measurands, sensor_ids, lat, lon, hass,
                                                  units, sensor_license, altitude_above_ground, direction_vertical,
                                                  direction_horizontal, accuracy)

    for sensor in sensors:
        sensor.set_state()

    def refresh(event_time):
        _LOGGER.debug("Updating...")
        for sensor in sensors:
            sensor.update()

    track_time_interval(hass, refresh, MIN_TIME_BETWEEN_UPDATES)

    return True


class Sensor:

    def __init__(self, os_sensor_id, sensor_id, measurand_id, unit_id, lat, lon, license_id, altitude_above_ground,
                 direction_vertical, direction_horizontal, sensor_model, accuracy, attribution_text, attribution_url,
                 token, hass):
        """Initialize the sensor"""
        self.id = os_sensor_id
        self.hass = hass
        self.sensor_id = sensor_id
        self.measurand_id = measurand_id
        self.unit_id = unit_id
        self.lat = lat
        self.lon = lon
        self.license_id = license_id
        self.altitude_above_ground = altitude_above_ground
        self.direction_vertical = direction_vertical
        self.direction_horizontal = direction_horizontal
        self.sensor_model = sensor_model
        self.accuracy = accuracy
        self.attribution_text = attribution_text
        self.attribution_url = attribution_url
        self.last_update = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        self.value = 21 #self.get_last_value()
        self.token = token
        self.attributes = {
            "OpenSense id": self.id,
            "last update": self.last_update
        }

    @property
    def get_token(self):
        return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiIzZmU1ODc3M2FmMzg0NjM5YTA0YThjNzcxNWMwZWRlMyIsImlhdCI6MTU0ODc5NzMwNywiZXhwIjoxODY0MTU3MzA3fQ.ZwVYjPuMInraeO6g6bboI20S6MqvXcK5MPzWn9Bt4pI"

    @property
    def get_id(self):
        return self.id

    @property
    def get_sensor_id(self):
        return self.sensor_id

    @property
    def get_measurand_id(self):
        return self.measurand_id

    @property
    def get_unit_id(self):
        return self.unit_id

    @property
    def get_value(self):
        return self.value

    @property
    def get_latitude(self):
        return self.lat

    @property
    def get_longitude(self):
        return self.lon

    @property
    def get_license_id(self):
        return self.license_id

    @property
    def get_altitude_above_ground(self):
        return self.altitude_above_ground

    @property
    def get_sensor_model(self):
        return self.sensor_model

    @property
    def get_accuracy(self):
        return self.accuracy

    @property
    def get_attribution_text(self):
        return self.attribution_text

    @property
    def get_attribution_url(self):
        return self.attribution_url

    @property
    def get_attributes(self):
        return self.attributes

    @property
    def get_last_update(self):
        return self.last_update

    def set_state(self):
        self.hass.states.set("Contribute.netatmo_aussen_temperature", "True", self.get_attributes)

    """def get_last_value(self):
        link = "http://localhost:8123/api/states/{0}".format(self.get_sensor_id)
        headers = \
            {
                "Authorization": "Bearer {0}".format(self.get_token)
            }
        r = requests.get(link, headers=headers)
        data = r.json()
        sleep(5)
        return data['state']"""

    def update(self):
        self.last_update = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        # self.value = self.get_last_value()
        self.attributes = {
            "OpenSense id": self.id,
            "last update": self.last_update
        }
        self.set_state()
        OpenSense.post_value_to_sensor(self.get_id, self.get_value)



class OpenSense:

    @staticmethod
    def get_measurand_name_from_measurand_id(measurand_id):
        link = "https://www.opensense.network/progprak/beta/api/v1.0/measurands/{0}".format(measurand_id)
        r = requests.get(link)
        data = r.json()
        return data['name']

    @staticmethod
    def get_measurand_id_from_measurand_name(measurand_name):
        link = "https://www.opensense.network/progprak/beta/api/v1.0/measurands?name={0}".format(measurand_name)
        r = requests.get(link)
        data = r.json()
        return data[0]['id']

    @staticmethod
    def create_sensor(measurand_id, unit_id, lat, lon, license_id, altitude_above_ground, direction_vertical,
                      direction_horizontal, sensor_model, accuracy, attribution_text, attribution_url):
        link = "https://www.opensense.network/progprak/beta/api/v1.0/sensors/addSensor"
        json_data = \
            {
                "measurandId": measurand_id,
                "unitId": unit_id,
                "location":
                    {
                        "lat": lat,
                        "lng": lon
                    },
                "licenseId": license_id,
                "altitudeAboveGround": altitude_above_ground,
                "directionVertical": direction_vertical,
                "directionHorizontal": direction_horizontal,
                "sensorModel": sensor_model,
                "accuracy": accuracy,
                "attributionText": attribution_text,
                "attributionURL": attribution_url
            }
        headers = \
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": OpenSense.get_api_key()
            }
        r = requests.post(link, headers=headers, json=json_data)
        data = r.json()
        return data['id']

    @staticmethod
    def get_api_key(username="smarthome", password="8KO9koE+"):
        link = "https://www.opensense.network/progprak/beta/api/v1.0/users/login"
        json_data = \
            {
                "username": username,
                "password": password
            }
        r = requests.post(link, json=json_data)
        if r.status_code != 200:
            return -1
        return r.json()['id']

    @staticmethod
    def get_unit_name_from_unit_id(unit_id):
        link = "https://www.opensense.network/progprak/beta/api/v1.0/units/{0}".format(unit_id)
        r = requests.get(link)
        data = r.json()
        return data['name']

    @staticmethod
    def get_unit_id_from_unit_name(unit_name):
        link = "https://www.opensense.network/progprak/beta/api/v1.0/units?name={0}".format(unit_name)
        r = requests.get(link)
        data = r.json()
        return data[0]['id']

    @staticmethod
    def post_value_to_sensor(sensor_id, value, timestamp=-1):
        link = "https://www.opensense.network/progprak/beta/api/v1.0/sensors/addValue"
        if timestamp == -1:
            timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]

        json_data = \
            {
                "sensorId": sensor_id,
                "timestamp": timestamp,
                "numberValue": value
            }

        headers = \
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": OpenSense.get_api_key()
            }

        r = requests.post(link, headers=headers, json=json_data)
        return r.status_code

    @staticmethod
    def collapsed_post_to_sensor(sensor_ids, values, timestamps):
        link = "https://www.opensense.network/progprak/beta/api/v1.0/sensors/addMultipleValues"

        collapsed_messages = []

        for i in range(len(values)):
            json_value = \
                {
                    "sensorId": sensor_ids[i],
                    "timestamp": timestamps[i],
                    "numberValue": values[i]
                }
            collapsed_messages.append(json_value)

        message = \
            {
                "collapsedMessages": collapsed_messages
            }

        headers = \
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": OpenSense.get_api_key()
            }

        r = requests.post(link, headers=headers, json=message)
        return r.status_code


    @staticmethod
    def includes_sensor(measurand, lat, lon):
        link = "https://www.opensense.network/progprak/beta/api/v1.0/sensors/mysensors"

        headers = \
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": OpenSense.get_api_key()
            }

        """_init__(self, os_sensor_id, sensor_id, measurand_id, unit_id, lat, lon, license_id, altitude_above_ground,
                 direction_vertical, direction_horizontal, sensor_model, accuracy, attribution_text, attribution_url,
                 token, hass):"""

        r = requests.get(link, headers=headers)
        data = r.json()
        measurand_id = OpenSense.get_measurand_id_from_measurand_name(measurand)
        for sensor in data:
            if sensor['measurandId'] == measurand_id and sensor['location']['lat'] == lat and \
                    sensor['location']['lng'] == lon:
                return sensor['id']
        return -1


def create_sensors_for_given_measurands(username, password, token, measurands, sensor_ids, lat, lon, hass, units,
                                        sensor_license, altitude_above_ground, direction_vertical,
                                        direction_horizontal, accuracy):

    measurands = measurands.replace(" ", "").split(',')
    sensor_ids = sensor_ids.replace(" ", "").split(',')

    sensors = []
    for i in range(len(measurands)):
        measurand = measurands[i]
        ha_sensor_id = sensor_ids[i]
        unit = units[i]
        unit_id = OpenSense.get_unit_id_from_unit_name(unit)
        measurand_id = OpenSense.get_measurand_id_from_measurand_name(measurand)
        sensor_id = OpenSense.includes_sensor(measurand, lat, lon)
        if sensor_id == -1:
            sensor_id = OpenSense.create_sensor(measurand_id, unit_id, lat, lon, sensor_license, altitude_above_ground,
                                    direction_vertical, direction_horizontal, ha_sensor_id, accuracy, "", "")

        sensors.append(Sensor(sensor_id, ha_sensor_id, measurand_id, unit_id, lat, lon, sensor_license,
                              altitude_above_ground, direction_vertical, direction_horizontal, "",
                              accuracy, ha_sensor_id, "", token, hass))

    return sensors

print(OpenSense.get_api_key())

