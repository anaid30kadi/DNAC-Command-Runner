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

def get_device(devices):

    for ip in devices:
        
        try:
            url = "https://{}/dna/intent/api/v1/network-device/ip-address/{}".format(DNAC_IP, ip)
            hdr = {'x-auth-token': token, 'content-type': 'application/json'}
            resp = requests.get(url, verify=False, headers=hdr)
            device_det = resp.json()

        except (requests.ConnectionError, TimeoutError):
            print('Error en la solicitud, verifique la IP del servidor o si este se encuentra disponible')

        cmd_runner(device_det['response']['id'])


def cmd_runner(id):
    ios_cmd = "show interface"
    device_id = id
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

    get_task_info(task_id, token)

def main():

    user = input('Para ingresar un rango de IPs presiona "X", si deseas ingresar el nombre del archivo presiona "Y" ')

    if user.upper() == "Y":
        devices = open_file()

    elif user.upper() == "X":
        devices = input("Ingrese el rango de Ips en el siguiente formato: InitialIP-FinalIP: ")
        devices = devices.split('-')
        # Define a new value of "device" with all the IPs inside the range

    else:
        print("Ha ingresado una opción invalida, intentelo nuevamente")

    get_device(devices)

main()
