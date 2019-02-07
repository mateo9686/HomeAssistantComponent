import logging
from datetime import datetime, timedelta
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import requests
import geopy.distance
import datetime
import time
from homeassistant.helpers.event import track_time_interval
from random import randint

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)


# Domain and component constants and validation
DOMAIN = 'open_sense'
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_LAT = "latitude"
CONF_LON = "longitude"
CONF_MEASURANDS = "measurands"
CONF_TOKEN = "token"

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Required(CONF_LAT): cv.latitude,
        vol.Required(CONF_LON): cv.longitude,
        vol.Required(CONF_MEASURANDS): cv.string,
        vol.Required(CONF_TOKEN): cv.string,
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

    # Attempt to login
    """api_key = get_api_key()
    if api_key == -1:
        _LOGGER.error("OpenSense login failed.")
        return False"""
    if measurands == "all":
        sensors = get_sensors_for_all_measurands(lat, lon, hass)
    else:
        sensors = get_sensors_for_given_measurands(measurands, lat, lon, hass)

    for sensor in sensors:
        sensor.set_state()


    def refresh(event_time):
        _LOGGER.debug("Updating...")
        for sensor in sensors:
            sensor.update()

    track_time_interval(hass, refresh, MIN_TIME_BETWEEN_UPDATES)

    return True


class Sensor:

    def __init__(self, sensor_id, measurand, hass):
        """Initialize the sensor"""
        self.id = sensor_id
        self.hass = hass
        if sensor_id == -1:
            self.measurand = measurand
            self.latitude = ""
            self.longitude = ""
            self.altitude_above_ground = ""
            self.sensor_model = ""
            self.accuracy = ""
            self.attribution_text = ""
            self.value = "no sensors near"
            self.unit = ""
            self.last_update = ""
            self.attributes = {}
        else:
            link = "https://www.opensense.network/progprak/beta/api/v1.0/sensors/{0}".format(sensor_id)
            r = requests.get(link)
            data = r.json()
            self.measurand = measurand
            self.last_update = OpenSense.get_timestamp(sensor_id)
            self.latitude = data['location']['lat']
            self.longitude = data['location']['lng']
            self.altitude_above_ground = data['altitudeAboveGround']
            self.sensor_model = data['sensorModel']
            self.accuracy = data['accuracy']
            self.attribution_text = data['attributionText']
            self.value, self.unit = OpenSense.get_last_value(sensor_id)
            self.attributes = {
                "friendly name": "OpenSense {0}".format(self.measurand),
                "id": self.id,
                "position": "{0}; {1}".format("%.2f" % self.get_latitude, "%.2f" % self.get_longitude),
                "sensor model": self.get_sensor_model,
                "altitude above ground": self.get_altitude_above_ground,
                "accuracy": self.get_accuracy,
                "attribution text": self.get_attribution_text
            }

    @property
    def get_id(self):
        return self.id

    @property
    def get_measurand(self):
        return self.measurand

    @property
    def get_value(self):
        return self.value

    @property
    def get_latitude(self):
        return self.latitude

    @property
    def get_longitude(self):
        return self.longitude

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
    def get_unit(self):
        return self.unit

    @property
    def get_attributes(self):
        return self.attributes

    @property
    def get_last_update(self):
        return self.last_update

    def set_state(self):
        if self.get_id == -1:
            self.hass.states.set("OpenSense.{0}".format(self.get_measurand), self.get_value, self.get_attributes)
        else:
            self.hass.states.set("OpenSense.{0}".format(self.get_measurand), "{0} {1}".format("%.2f" % self.get_value,
                                                                                         self.get_unit),
                            self.get_attributes)

    def update(self):
        if self.get_id != -1:
            self.last_update = OpenSense.get_timestamp(self.get_id)
            self.value, self.unit = OpenSense.get_last_value(self.get_id)
            #self.value = randint(0, 100)
            self.attributes = {
                "friendly name": "OpenSense {0}".format(self.measurand),
                "id": self.id,
                "position": "{0}; {1}".format("%.2f" % self.get_latitude, "%.2f" % self.get_longitude),
                "sensor model": self.get_sensor_model,
                "altitude above ground": self.get_altitude_above_ground,
                "accuracy": self.get_accuracy,
                "attribution text": self.get_attribution_text
            }
        self.set_state()


class OpenSense:

    @staticmethod
    def find_closest_sensor(data, lat, lon):
        min_dist = float("inf")
        sensor_id = -1
        location = (lat, lon)
        for json in data:
            j_lat = json['location']['lat']
            j_lon = json['location']['lng']
            location2 = (j_lat, j_lon)
            dist = geopy.distance.geodesic(location, location2).m
            if dist < min_dist:
                if OpenSense.get_last_value(json['id'])[0] is not None:
                    min_dist = dist
                    sensor_id = json['id']
        return sensor_id

    @staticmethod
    def get_id_of_closest_sensor(lat, lon, measurand_id):
        dist = 100
        data = []
        while len(data) <= 1 and dist < 10000:
            link = "https://www.opensense.network/progprak/beta/api/v1.0/sensors?measurandId={0}&refPoint={1}, " \
                   "{2}&maxDistance={3}" \
                .format(measurand_id, lat, lon, dist)
            r = requests.get(link)
            data = r.json()
            if len(data) == 1:
                if OpenSense.get_last_value(data[0]['id'])[0] is not None:
                    return data[0]['id']
            dist += 200
        if len(data) == 0:
            return -1
        if len(data) == 1:
            return -1
        return OpenSense.find_closest_sensor(data, lat, lon)

    @staticmethod
    def get_last_value(sensor_id):
        link = "https://www.opensense.network/progprak/beta/api/v1.0/sensors/{0}/values".format(sensor_id)
        r = requests.get(link)
        data = r.json()
        last_index = len(data['values']) - 1
        if last_index == -1:
            return None, None
        return data['values'][last_index]['numberValue'], OpenSense.get_unit_name_from_unit_id(data['unitId'])

    @staticmethod
    def get_measurand_id_from_sensor(sensor_id):
        link = "https://www.opensense.network/progprak/beta/api/v1.0/sensors/{0}".format(sensor_id)
        r = requests.get(link)
        data = r.json()
        return data['measurandId']

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
    def collapsed_post_to_sensor(sensor_id, values, timestamps):
        link = "https://www.opensense.network/progprak/beta/api/v1.0/sensors/addMultipleValues"

        collapsed_messages = []

        for i in range(len(values)):
            json_value = \
                {
                    "sensorId": sensor_id,
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
    def get_timestamp(sensor_id):
        link = "https://www.opensense.network/progprak/beta/api/v1.0/sensors/{0}/values".format(sensor_id)
        r = requests.get(link)
        data = r.json()
        last_index = len(data['values']) - 1
        if last_index == -1:
            return None, None
        return data['values'][last_index]['timestamp']



def get_sensors_for_all_measurands(lat, lon, hass):
    link = "https://www.opensense.network/progprak/beta/api/v1.0/measurands"
    r = requests.get(link)
    data = r.json()
    number_of_measurands = len(data)
    sensors = []
    for i in range(number_of_measurands):
        measurand_id = i + 1
        measurand_name = OpenSense.get_measurand_name_from_measurand_id(measurand_id)
        sensor_id = OpenSense.get_id_of_closest_sensor(lat, lon, measurand_id)
        sensors.append(Sensor(sensor_id, measurand_name, hass))
    return sensors


def get_sensors_for_given_measurands(measurands, lat, lon, hass):
    measurands = measurands.replace(" ", "").split(',')

    sensors = []
    for measurand in measurands:
        measurand_id = OpenSense.get_measurand_id_from_measurand_name(measurand)
        sensor_id = OpenSense.get_id_of_closest_sensor(lat, lon, measurand_id)
        sensors.append(Sensor(sensor_id, measurand, hass))
    return sensors


print(OpenSense.get_api_key())