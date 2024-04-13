import requests
import webbrowser
import json
import os
import sys
import logging
import subprocess

def show_dialog(title, message):
    script = f'''
    tell app "System Events"
        display dialog "{message}" with title "{title}"
    end tell
    '''
    subprocess.run(["osascript", "-e", script])

# Configure logging
logging.basicConfig(filename='mixcloud_upload.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
# Constants
CLIENT_ID = 'tUGfQ4HC9mBRf5YsYC'
CLIENT_SECRET = 'Lh3TGr92tkwu8u3QnrGmL3Gg5YJqUdFG'
REDIRECT_URI = 'google.com'  # This should match the redirect URI registered with Mixcloud
TOKEN_FILE = 'mixcloud_token.json'

def get_authorization_code():
    auth_url = f"https://www.mixcloud.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code"
    webbrowser.open_new(auth_url)

        # Use AppleScript to show a dialog box for the user to input the authorization code
    script = '''
    set theCode to text returned of (display dialog "Please paste the authorization code from your web browser:" default answer "" buttons {"OK"} default button 1)
    return theCode
    '''
    proc = subprocess.run(["osascript", "-e", script], text=True, capture_output=True)
    return proc.stdout.strip()
    print("Please authorize the application in the web browser.")
    redirected_url = input("Paste the full redirected URL here: ")
    code = redirected_url.split("code=")[-1]
    return code

def get_access_token(code):
    token_url = "https://www.mixcloud.com/oauth/access_token"
    payload = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code'
    }
    response = requests.post(token_url, data=payload)
    if response.status_code == 200:
        token_info = response.json()
        token_info['refresh_token'] = token_info.get('refresh_token', '')
        save_token(token_info)
        return token_info['access_token']
    else:
        logging.error("Failed to get access token: " + response.text)
        show_dialog("Authentication Error", "Failed to authenticate with Mixcloud.")
        return None

def save_token(token_info):
    with open(TOKEN_FILE, 'w') as file:
        json.dump(token_info, file)

def load_token():
    try:
        with open(TOKEN_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return None

def refresh_token(refresh_token):
    token_url = "https://www.mixcloud.com/oauth/access_token"
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    response = requests.post(token_url, data=payload)
    if response.status_code == 200:
        token_info = response.json()
        save_token(token_info)
        return token_info['access_token']
    else:
        logging.error("Failed to refresh token: " + response.text)
        show_dialog("Token Refresh Error", "Failed to refresh access token with Mixcloud.")
        return None
    
def check_and_load_access_token():
    token_info = load_token()
    if token_info and 'access_token' in token_info:
        access_token = token_info['access_token']
        # Optionally, test the token validity here with a simple API call and refresh if necessary
        return access_token
    else:
        code = get_authorization_code()
        return get_access_token(code)

def parse_metadata(file_path):
    """
    Parse metadata from a corresponding .json file.
    """
    base_path = os.path.splitext(file_path)[0]
    json_path = base_path + '.json'
    metadata = {'name': os.path.basename(base_path), 'description': '', 'tags': []}  # default metadata

    try:
        with open(json_path, 'r') as file:
            # Load metadata from JSON file
            metadata = json.load(file)
        logging.info(f"Metadata parsed successfully from {json_path}")
    except FileNotFoundError:
        logging.error(f"Metadata file not found: {json_path}")
        show_dialog("Metadata file not found", f"Failed to find metadata file {json_path}")
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON file: {e}")
        show_dialog("JSON Parsing Error", f"Error parsing the metadata file: {json_path}")

    return metadata
    
def upload_file(access_token, file_path, metadata):
    """
    Upload a single file to Mixcloud, including optional image, with the token as a query parameter.
    """
    # Add the access token directly in the query string
    url = f'https://api.mixcloud.com/upload/?access_token={access_token}'
    files = {'mp3': open(file_path, 'rb')}
    base_path = os.path.splitext(file_path)[0]
    image_path = base_path + '.jpg'
    
    if os.path.exists(image_path):
        files['picture'] = open(image_path, 'rb')
        logging.info(f"Including image {image_path} in upload")
            
    data = {'name': metadata['name'], 'description': metadata['description']}
    for i, tag in enumerate(metadata['tags']):
        data[f'tags-{i}-tag'] = tag

    response = requests.post(url, files=files, data=data)
    logging.info(f"Uploading {file_path} to Mixcloud")

    # Close file handlers
    for file in files.values():
        file.close()

    if response.status_code == 200:
        logging.info(f"Upload successful for {file_path}")
        show_dialog("Upload Success", f"Successfully uploaded {file_path}.")
    else:
        logging.error(f"Upload failed for {file_path}: {response.text}")
        show_dialog("Upload Error", f"Failed to upload {file_path}. Server said: {response.text}")

    return response.json()

def upload_files(access_token, file_paths):
    """
    Upload multiple files to Mixcloud with associated metadata and images.
    """
    for file_path in file_paths:
        if file_path.lower().endswith('.mp3'):
            logging.info(f"Processing file {file_path}")
            metadata = parse_metadata(file_path)
            result = upload_file(access_token, file_path, metadata)
            print("Uploaded:", file_path, "Result:", result)
            logging.info(f"Result for {file_path}: {result}")



if __name__ == "__main__":
    access_token = check_and_load_access_token()
    if access_token:
        logging.info("Access token retrieved")
        file_paths = sys.argv[1:]  # File paths from command line
        upload_files(access_token, file_paths)
        logging.info("All files processed")
    else:
        logging.error("Failed to obtain a valid access token.")
    file_paths = sys.argv[1:]
    upload_files(access_token, file_paths)
    logging.info("All files processed")

    # Upload the file
    # response = upload_file(access_token, file_path, name, description, tags)
    # print("Upload Response:", json.dumps(response, indent=4))
