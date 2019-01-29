def collapsed_post_to_sensor(sensor_id, values, timestamps):
    link = "https://opensense.network/progprak/apidocs/#!/Values/post_api_v1_0_sensors_addMultipleValues"

    collapsedMessages = []

    for i in range(len(values)):
        jsonvalue = {"sensorId":None,
                 "timestamp":None,
                 "numberValue":None
                }
        jsonvalue ["sensor_id"] = value[i]
        jsonvalue ["timestamp"] = timestamps[i]
        jsonvalue ["sensorId"] = sensor_id
        collapsedMessages.append(jsonvalue)

    message = {"collapsedMessages":None}
    message ["collapsedMessages"] = collapsedMessages


    headers = \
    {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": get_api_key()
    }

    r = requests.post(link, headers=headers, json=message)
    return r.status_code

collapsed_post_to_sensor(289120,[2,3],["2019-01-29T19:42:32.639Z", "2019-01-29T19:42:52.639Z"])
