from apscheduler.schedulers.blocking import BlockingScheduler
import datetime
import time
import requests
import json
import re
from dnac_token import get_auth_token
from dnac_config import DNAC_IP

token = get_auth_token()
currentTime = datetime.datetime.now()


def get_device_list():

    device_id = {}

    try: 
        url = "https://{}/api/v1/network-device".format(DNAC_IP)
        hdr = {'x-auth-token': token, 'content-type': 'application/json'}
        resp = requests.get(url, verify=False, headers=hdr)
        device_list = resp.json()

        for device in device_list['response']:
            if device['family'] != 'Unified AP':
                hostname = device['hostname']
                id = device['id']
                dev = {hostname: id}
            else:
                continue
            device_id.update(dev)

    except (requests.ConnectionError, TimeoutError):
        print('Error en la solicitud, verifique la IP del servidor o si este se encuentra disponible')

    return (device_id)


def cmd_runner(ids):

    global ios_cmd
    ios_cmd = "show running-config"
    device_task = {}

    for host, id in ids.items():
        device_id = id

        try:
            print("executing ios command -->",
                  ios_cmd, "to this device-->", id)
            param = {
                "name": "Show Command",
                "commands": [ios_cmd],
                "deviceUuids": [device_id]
            }
            url = "https://{}/api/v1/network-device-poller/cli/read-request".format(DNAC_IP)
            header = {'content-type': 'application/json','x-auth-token': token}
            response = requests.post(url, verify=False, data=json.dumps(param), headers=header)
            task_id = response.json()['response']['taskId']
            print("Command runner Initiated! Task ID --> ", task_id)
            print("Retrieving Path Trace Results.... ")
            dev_task = {host: task_id}

        except (requests.ConnectionError, TimeoutError):
            print(
                'Error en la solicitud, verifique la IP del servidor o si este se encuentra disponible')

        device_task.update(dev_task)

    return (device_task)


def get_fileid(taskid):

    device_file = {}

    for host, task in taskid.items():
        for _ in range(5):

            try:
                url = "https://{}/dna/intent/api/v1/task/{}".format(
                    DNAC_IP, task)
                hdr = {'x-auth-token': token,
                       'content-type': 'application/json'}
                resp = requests.get(url, verify=False, headers=hdr)

                if resp.status_code == 200 and "endTime" in resp.json()['response']:
                    file_id = resp.json()['response']['progress']
                    file_id = json.loads(file_id)['fileId']
                    dev_file = {host: file_id}

                else:
                    print("No response yet, please wait for a few seconds")
                    time.sleep(5)

            except (requests.ConnectionError, TimeoutError):
                print(
                    'Error en la solicitud, verifique la IP del servidor o si este se encuentra disponible')

        device_file.update(dev_file)
    return device_file


def save_file(files):

    for host, file_id in files.items():

        url = "https://{}/dna/intent/api/v1/file/{}".format(DNAC_IP, file_id)
        hdr = {'x-auth-token': token, 'content-type': 'application/json'}
        resp = requests.get(url, verify=False, headers=hdr)
        file = resp.json()[0]['commandResponses']['SUCCESS'][ios_cmd]
        time = currentTime.strftime("%Y-%m-%d %H:%M:%S")
        time = re.sub('[:]', '', time)
        f = open('{}_{}.txt'.format(host, time), 'w')
        f.write(file)
        f.close()
        

def main():

    ids = get_device_list()
    tasks = cmd_runner(ids)
    files = get_fileid(tasks)
    save_file(files)


scheduler = BlockingScheduler()
scheduler.add_job(main, 'cron', hour=10, minute=00)
scheduler.start()
