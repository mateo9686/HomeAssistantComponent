import requests
import geopy.distance
import datetime
import time


def find_closest_sensor(data, lat, lon):
    min_dist = float("inf")
    sensor_id = -1
    location = (lat, lon)
    for json in data:
        j_lat = json['location']['lat']
        j_lon = json['location']['lng']
        location2 = (j_lat, j_lon)
        dist = geopy.distance.vincenty(location, location2).m
        if dist < min_dist:
            min_dist = dist
            sensor_id = json['id']
    return sensor_id


def get_id_of_closest_sensor(lat, lon, measurand):
    dist = 5
    data = []
    while len(data) == 0:
        link = "https://www.opensense.network/progprak/beta/api/v1.0/sensors?measurandId={0}&refPoint={1}, {2}&maxDistance={3}" \
            .format(measurand, lat, lon, dist)
        r = requests.get(link)
        data = r.json()
        dist *= 10
    return find_closest_sensor(data, lat, lon)


def get_last_value(sensor_id):
    link = "https://www.opensense.network/progprak/beta/api/v1.0/sensors/{0}/values".format(sensor_id)
    r = requests.get(link)
    data = r.json()
    last_index = len(data['values']) - 1
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


print(post_value_to_sensor(161438, 12))
