# OpenSense for Home Assistant
Custom component for Home Assistant 

## Installation
Add the open_sense.py file to the custom_components directory in Home Assistant configuration folder. 
Then add following to configuration.yaml file.
```yaml
open_sense:
    username: <username>
    password: <password>
    latitude: <latitude>
    longitude: <longitude>
    measurands: <comma separated list of measurands> or all if you want to get all of them
```
