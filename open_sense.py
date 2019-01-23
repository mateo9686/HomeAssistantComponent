import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import requests
import geopy.distance
import datetime
import time

_LOGGER = logging.getLogger(__name__)

# Domain and component constants and validation
# DOMAIN = 'open'
DOMAIN = 'open_sense'
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_LAT = "latitude"
CONF_LON = "longitude"
CONF_MEASURANDS = "measurands"

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Required(CONF_LAT): cv.latitude,
        vol.Required(CONF_LON): cv.longitude,
        vol.Required(CONF_MEASURANDS): cv.string,
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

    # Attempt to login
    """api_key = get_api_key()
    if api_key == -1:
        _LOGGER.error("OpenSense login failed.")
        return False"""
    if measurands == "all":
        set_states_for_all_measurands(lat, lon, hass)
    else:
        set_states_for_given_measurands(measurands, lat, lon, hass)

    return True


def set_states_for_given_measurands(measurands, lat, lon, hass):
    measurands = measurands.replace(" ", "").split(',')

    for measurand in measurands:
        measurand_id = get_measurand_id_from_measurand_name(measurand)
        sensor_id = get_id_of_closest_sensor(lat, lon, measurand_id)
        if sensor_id == -1:
            hass.states.set("openSense.{0}".format(measurand), "no sensors")
        else:
            value = get_last_value(sensor_id)
            hass.states.set("openSense.{0}".format(measurand), "%.2f" % value)


def set_states_for_all_measurands(lat, lon, hass):
    link = "https://www.opensense.network/progprak/beta/api/v1.0/measurands"
    r = requests.get(link)
    data = r.json()
    number_of_measurands = len(data)
    for i in range(number_of_measurands):
        measurand_id = i + 1
        measurand = get_measurand_name_from_measurand_id(measurand_id)
        sensor_id = get_id_of_closest_sensor(lat, lon, measurand_id)
        if sensor_id == -1:
            hass.states.set("openSense.{0}".format(measurand), "no sensors")
        else:
            value = get_last_value(sensor_id)
            hass.states.set("openSense.{0}".format(measurand), "%.2f" % value)


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
            if get_last_value(json['id']) is not None:
                min_dist = dist
                sensor_id = json['id']
    return sensor_id


def get_id_of_closest_sensor(lat, lon, measurand_id):
    dist = 100
    data = []
    while (len(data) <= 1 or len(data) > 15)  and dist < 51000:
        link = "https://www.opensense.network/progprak/beta/api/v1.0/sensors?measurandId={0}&refPoint={1}, {2}&maxDistance={3}" \
            .format(measurand_id, lat, lon, dist)
        r = requests.get(link)
        data = r.json()
        if len(data) == 1:
            if get_last_value(data[0]['id']) is not None:
                return data[0]['id']
        if len(data) > 15:
            dist = dist / 2 + 100
        else:
            dist *= 2
    if len(data) == 0:
        return -1
    if len(data) == 1:
        return -1
    return find_closest_sensor(data, lat, lon)


def get_last_value(sensor_id):
    link = "https://www.opensense.network/progprak/beta/api/v1.0/sensors/{0}/values".format(sensor_id)
    r = requests.get(link)
    data = r.json()
    last_index = len(data['values']) - 1
    if last_index == -1:
        return None
    return data['values'][last_index]['numberValue']


def get_measurand_id_from_sensor(sensor_id):
    link = "https://www.opensense.network/progprak/beta/api/v1.0/sensors/{0}".format(sensor_id)
    r = requests.get(link)
    data = r.json()
    return data['measurandId']


def get_measurand_name_from_measurand_id(measurand_id):
    link = "https://www.opensense.network/progprak/beta/api/v1.0/measurands/{0}".format(measurand_id)
    r = requests.get(link)
    data = r.json()
    return data['name']


def get_measurand_id_from_measurand_name(measurand_name):
    link = "https://www.opensense.network/progprak/beta/api/v1.0/measurands?name={0}".format(measurand_name)
    r = requests.get(link)
    data = r.json()
    return data[0]['id']


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
            "Authorization": get_api_key()
        }
    r = requests.post(link, headers=headers, json=json_data)
    data = r.json()
    return data['id']


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
            "Authorization": get_api_key()
        }

    r = requests.post(link, headers=headers, json=json_data)
    return r.status_code


print(get_id_of_closest_sensor(52.507334, 13.332367, 11))
print(get_last_value(26422))
