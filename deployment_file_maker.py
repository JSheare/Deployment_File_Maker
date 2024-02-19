import pandas as pd
import numpy as np
import requests
import os.path
import json
# requires: pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


def get_google_sheet_df(headers, google_sheet_id, sheet_name, _range):
    """_range is in A1 notation (i.e. A:I returns all rows for columns A to I)"""

    url = f'https://sheets.googleapis.com/v4/spreadsheets/{google_sheet_id}/values/{sheet_name}!{_range}'
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    values = r.json()['values']
    df = pd.DataFrame(values[1:])
    df.columns = values[0]
    df = df.apply(lambda x: x.str.strip()).replace('', np.nan)
    return df


def get_file_loc(detector):
    detector = detector.upper()
    if detector == 'GODOT':
        return '/media/AllDetectorData/Detectors/GODOT'
    elif detector == 'HAWC':
        return '/media/AllDetectorData/Detectors/HAWC'
    elif 'MINITHOR' in detector:
        return '/media/AllDetectorData/Detectors/MINITHOR1'
    elif detector == 'SANTIS':
        return '/media/AllDetectorData/Detectors/SANTIS'
    elif 'THOR' in detector:
        return '/media/AllDetectorData/Detectors/THOR'

    return ''


# If modifying these scopes here and in the Google dev console, delete the file token.json
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

creds = None
# Imports api access token and refresh token (if they exist)
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)

# Otherwise asks the user to authorize
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        # Note: you need to change the name of the file you get from Google's dev console to 'credentials.json'
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)

    # Now save the valid credentials
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

# Get the api access token
with open('token.json', 'r') as token:
    info = json.load(token)
    access_token = info['token']

headers = {'authorization': f'Bearer {access_token}',
           'Content-Type': 'application/vnd.api+json'}

# Google sheet id is in the url, between spreadsheets/d/ and /edit
google_sheet_id = '1B5ElU3eaeqGJ6gGzR0WePk9q-mMiou7T3FOqge3VDD4'
sheet_name = 'Sheet1'
sample_range = 'A:L'

# Gets the sheet from the api and converts it into a pandas dataframe
df = get_google_sheet_df(headers, google_sheet_id, sheet_name, sample_range)
deployments_dictionary = df.to_dict(orient='records')

# Reads/writes deployment files
for entry in deployments_dictionary:
    file_path = (f'{get_file_loc(entry["Instrument"])}/'
                 f'{entry["Instrument"].lower()}_{entry["Start date"]}_{entry["End date"]}')
    # Checks to see if existing files are up-to-date
    if os.path.exists(file_path):
        file = open(file_path, 'r')
        deployment_info = json.load(file)
        file.close()
        if deployment_info != entry:
            with open(file_path, 'w') as file:
                json.dump(entry, file)
    # Otherwise makes a new file
    else:
        with open(file_path, 'w') as file:
            json.dump(entry, file)
