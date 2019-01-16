import requests
import geopy.distance


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
        link = "https://www.opensense.network/progprak/beta/api/v1.0/sensors?measurandId={0}&refPoint={1}, {2}&maxDistance={3}"\
            .format(measurand, lat, lon, dist)
        r = requests.get(link)
        data = r.json()
        dist *= 10
    return find_closest_sensor(data, lat, lon)


def get_last_value(sensor_id):
    link = 'https://www.opensense.network/progprak/beta/api/v1.0/sensors/' + sensor_id + '/values'
    r = requests.get(link)
    data = r.json()
    last_index = len(data['values']) - 1
    return data['values'][last_index]['numberValue']

# def get_measurand_from_sensor():


print(get_last_value('43759'))
