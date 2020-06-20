import requests
from requests.auth import HTTPBasicAuth
from dnac_config import DNAC_IP, DNAC_PORT, DNAC_USER, DNAC_PASSWORD

#Try to get a DNAC token if the request fails show the error cause

def get_auth_token():

    try: 
        """Building out Auth request. Using requests.post to make a call to the Auth Endpoint"""
        url = 'https://{}/dna/system/api/v1/auth/token'.format(DNAC_IP)       # Endpoint URL
        resp = requests.post(url, verify=False, auth=HTTPBasicAuth(DNAC_USER, DNAC_PASSWORD))  # Make the POST Request
        token = resp.json()['Token']    # Retrieve the Token from the returned JSON
        print('Token Retrieved: {}'.format(token))  # Print out the Token
        return token

    except (requests.ConnectionError, TimeoutError):
        print('Error en la solicitud, verifique la IP del servidor o si este se encuentra disponible')

    except KeyError:
        error = resp.json()['error']
        print(error)

if __name__ == "__main__":
    get_auth_token()
