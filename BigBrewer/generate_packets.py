import subprocess
import random
import time

for day in range(25, 30):
    for hour in range(0, 23, 2):
        for plant in range(1, 5):
            data = random.randrange(100)
            return_code = subprocess.call('curl --header "Content-Type: application/json" --request POST --data \''
                                          '{"metadata": {"time": "2018-06-' + str("%02d" % day) + 'T' + str(
                "%02d" % hour) + ':25:11.875464918Z"}, "app_id": "plantsensors", "port": 3,'
                                 ' "dev_id": "plant' + str(
                plant) + '", "downlink_url": "https://integrations.thethingsnetwork.org/ttn-eu/api/v2/down/plantsensors/plantsensors?key=ttn-account-v2.03DrO-vnpemZkrPkhp4xzt8yZfOEHDEAv9bPIHFXaOE", '
                         '"hardware_serial": "003C9E6CD0EB61F8", "payload_raw": "ZmZmZmZm", '
                         '"payload_fields": {"voltage": 26.214, "plantname": "test", "water": ' + str(
                data) + '}, "counter": 0}\' 127.0.0.1:5000/ttn/submit', shell=True)
            time.sleep(0.5)
            print(str("%02d" % day), str("%02d" % hour))
            print("post")
