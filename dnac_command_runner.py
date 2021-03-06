import requests
import json
import time
import pandas
from dnac_token import get_auth_token
from dnac_config import DNAC_IP

# Create a funtion to open the file, read the device IP and the configuration commands

token = get_auth_token()


def open_file(): 

    try: 
        file = input("Ingrese el nombre del archivo en formato .xlsx: ")
        flap = input("Ingrese el nombre de la solapa: ")
        name = input("Ingresa el nombre de la columna: ")
        device_commands = pandas.read_excel(file, sheet_name=flap)
        device_ip = device_commands[name].tolist()
        
    except FileNotFoundError:
        print('El archivo especificado no existe, por favor verifique el nombre y vuelva a intentarlo')

    return(device_ip)


def get_devices(devices):

    device_id = {}

    for ip in devices:

        try:
            url = "https://{}/dna/intent/api/v1/network-device/ip-address/{}".format(DNAC_IP, ip)
            hdr = {'x-auth-token': token, 'content-type': 'application/json'}
            resp = requests.get(url, verify=False, headers=hdr)
            device_det = resp.json()
            id = device_det['response']['id']
            dev = {ip: id}

        except (requests.ConnectionError, TimeoutError):
            print('Error en la solicitud, verifique la IP del servidor o si este se encuentra disponible')

        device_id.update(dev)
    return(device_id)


def cmd_runner(ids):

    global ios_cmd
    ios_cmd = "show interface"
    device_task = {}

    for ip, id in ids.items():
        device_id = id

        try: 
            print("executing ios command -->", ios_cmd, "to this device-->", id)
            param = {
                "name": "Show Command",
                "commands": [ios_cmd],
                "deviceUuids": [device_id]
            }
            url = "https://{}/api/v1/network-device-poller/cli/read-request".format(DNAC_IP)
            header = {'content-type': 'application/json', 'x-auth-token': token}
            response = requests.post(url, verify=False, data=json.dumps(param), headers=header)
            task_id = response.json()['response']['taskId']
            print("Command runner Initiated! Task ID --> ", task_id)
            print("Retrieving Path Trace Results.... ")
            dev_task = {ip: task_id}
        
        except (requests.ConnectionError, TimeoutError):
            print('Error en la solicitud, verifique la IP del servidor o si este se encuentra disponible')

        device_task.update(dev_task)

    return (device_task)
    

def get_fileid(taskid):

    device_file = {}

    for ip, task in taskid.items():
        for _ in range(5):

            try: 
                url = "https://{}/dna/intent/api/v1/task/{}".format(DNAC_IP, task)
                hdr = {'x-auth-token': token, 'content-type': 'application/json'}
                resp = requests.get(url, verify=False, headers=hdr)

                if resp.status_code == 200 and "endTime" in resp.json()['response']:
                    file_id = resp.json()['response']['progress']
                    file_id = json.loads(file_id)['fileId']
                    dev_file = {ip: file_id}

                else:
                    print("No response yet, please wait for a few seconds")
                    time.sleep(5)

            except (requests.ConnectionError, TimeoutError):
                print('Error en la solicitud, verifique la IP del servidor o si este se encuentra disponible')

        device_file.update(dev_file)
    return device_file


def save_file(files):

    for ip, file_id in files.items():

        url = "https://{}/dna/intent/api/v1/file/{}".format(DNAC_IP, file_id)
        hdr = {'x-auth-token': token, 'content-type': 'application/json'}
        resp = requests.get(url, verify=False, headers=hdr)
        print("The outputs of the device ", ip, resp.json()[0]['commandResponses']['SUCCESS'][ios_cmd])


def main():

    user = input('''Si deseas ingresar un rango de IPs presiona "X", 
    si deseas ingresar el nombre del archivo presiona "Y": ''')

    if user.upper() == "Y":
        devices = open_file()

    elif user.upper() == "X":
        devices = input("Ingrese el rango de Ips en el siguiente formato: FirstIP-FinalIP: ")
        devices = devices.split('-')
        # Define a new value of "device" with all the IPs inside the range

    else:
        print("Ha ingresado una opción invalida, intentelo nuevamente")

    ids = get_devices(devices)
    tasks = cmd_runner(ids)
    files = get_fileid(tasks)
    save_file(files)


if __name__ == "__main__":
    main()
