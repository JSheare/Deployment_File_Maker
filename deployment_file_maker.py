import pandas as pd
import numpy as np
import requests
import os.path
import json
# requires: pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


def get_google_sheet_df(headers, sheet_id, sheet_name, column_range):
    # column_range is in A1 notation (i.e. A:I returns all rows for columns A to I)
    url = f'https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{sheet_name}!{column_range}'
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    values = r.json()['values']
    df = pd.DataFrame(values[1:])
    df.columns = values[0]
    df = df.apply(lambda x: x.str.strip()).replace('', np.nan)
    return df


def get_token(SCOPES):
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
        return info['token']


def make_file(row_dict):
    # Renaming the columns to be a little more programmer-friendly
    row_dict['location'] = str(row_dict.pop('Location'))
    row_dict['instrument'] = str(row_dict.pop('Instrument').upper())
    row_dict['start_date'] = str(row_dict.pop('Start date'))
    row_dict['end_date'] = str(row_dict.pop('End date'))
    row_dict['utc_to_local'] = float(row_dict.pop('UTC conversion to local time'))
    dst_in_region = str(row_dict.pop('Daylight savings?')).upper()
    row_dict['dst_in_region'] = True if dst_in_region in ['YES', 'Y', 'TRUE'] else False
    row_dict['weather_station'] = str(row_dict.pop('Nearest weather station'))
    row_dict['sounding_station'] = str(row_dict.pop('Nearest sounding station'))
    row_dict['latitude'] = float(row_dict.pop('Latitude (N)'))
    row_dict['longitude'] = float(row_dict.pop('Longitude (E, 0-360)'))
    row_dict['altitude'] = float(row_dict.pop('Altitude (km)'))
    row_dict['notes'] = str(row_dict.pop('Notes'))

    # Exporting the json file
    if not os.path.exists('Deployment Files'):
        os.mkdir('Deployment Files')

    file_name = f'{row_dict["instrument"]}_deployment_{row_dict["start_date"]}_{row_dict["end_date"]}'
    with open(f'Deployment Files/{file_name}.json', 'w') as file:
        json.dump(row_dict, file)


def main():
    # If modifying these scopes here and in the Google dev console, delete the file token.json
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    access_token = get_token(SCOPES)

    headers = {'authorization': f'Bearer {access_token}',
               'Content-Type': 'application/vnd.api+json'}

    # Google sheet id is in the url, between spreadsheets/d/ and /edit
    google_sheet_id = '1B5ElU3eaeqGJ6gGzR0WePk9q-mMiou7T3FOqge3VDD4'
    sheet_name = 'Sheet1'
    sample_range = 'A:L'

    # Gets the sheet from the api and converts it into a pandas dataframe
    df = get_google_sheet_df(headers, google_sheet_id, sheet_name, sample_range)
    for row_dict in df.to_dict(orient='records'):
        make_file(row_dict)


if __name__ == '__main__':
    main()
