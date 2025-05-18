import requests
import json
from datetime import datetime

# --- Global Constants ---
# URL for the login endpoint (from login_request.py)
LOGIN_URL = "http://poudelanish17.com.np:9002/api/v1/auth/login"
# Default base URL for other API endpoints (from request.py)
DEFAULT_API_BASE_URL = 'http://poudelanish17.com.np:9002/api/v1'

# --- Login Function (adapted from login_request.py) ---
def attempt_login(email, password):
    """
    Attempts to log in to the specified API endpoint.
    Uses the provided email and password arguments.

    Args:
        email (str): The email for login.
        password (str): The password for login.

    Returns:
        tuple: (success_boolean, response_data_or_error_message)
               - If successful (HTTP status 2xx): (True, response.json() or response.text)
               - If failed: (False, error_json or error_text or error_message_string)
    """
    payload = {
        "email": "developer@developer1.com",  # Using the passed email argument
        "password": "developer1"  # Using the passed password argument
    }
    headers = {
        "Content-Type": "application/json"
    }

    print(f"Attempting login to: {LOGIN_URL}")
    print(f"Login Payload: {json.dumps(payload)}")

    try:
        response = requests.post(LOGIN_URL, json=payload, headers=headers, timeout=10)

        print(f"Login Status Code: {response.status_code}")

        if 200 <= response.status_code < 300:
            print("Login successful!")
            try:
                response_data = response.json()
                print("Login Response JSON:")
                print(json.dumps(response_data, indent=2))
                return True, response_data
            except json.JSONDecodeError:
                print("Login Response was not valid JSON.")
                print(f"Login Raw Response: {response.text}")
                return True, response.text
        else:
            print(f"Login failed. Status code: {response.status_code}")
            try:
                error_data = response.json()
                print("Login Error Response JSON:")
                print(json.dumps(error_data, indent=2))
                return False, error_data
            except json.JSONDecodeError:
                print(f"Login Error Response (not JSON): {response.text}")
                return False, response.text

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the login request: {e}")
        return False, str(e)
    except Exception as e:
        print(f"An unexpected error occurred during login: {e}")
        return False, str(e)

# --- Generic API Request Function (from request.py) ---
def send_api_request(url, method='POST', payload=None, headers=None, timeout=10):
    """
    Sends an API request to the specified URL.

    Args:
        url (str): The full URL of the API endpoint.
        method (str): HTTP method to use (e.g., 'GET', 'POST', 'PUT', 'DELETE').
        payload (dict, str, optional): Data for the request body or query params.
        headers (dict, optional): Custom headers for the request.
        timeout (int): Request timeout in seconds.

    Returns:
        tuple: (success_boolean, response_data_or_error_message)
    """
    if not url:
        error_msg = "API Error: URL cannot be empty."
        print(error_msg)
        return False, error_msg

    effective_headers = {}
    is_json_payload = False

    # Determine if payload should be sent as JSON and set Content-Type if needed
    if isinstance(payload, dict) and method.upper() in ['POST', 'PUT', 'PATCH']:
        # If headers are provided and Content-Type is already set, respect it.
        # Otherwise, default to application/json for dict payloads.
        if not (headers and 'Content-Type' in headers):
            effective_headers['Content-Type'] = 'application/json'
            is_json_payload = True
        elif headers and headers.get('Content-Type', '').lower() == 'application/json':
            is_json_payload = True
    
    if headers:
        effective_headers.update(headers) # Add any other headers, like Authorization

    print(f"API: Initiating {method} request to {url}")
    if payload:
        # Display payload appropriately
        payload_display = json.dumps(payload, indent=2) if is_json_payload and isinstance(payload, dict) else str(payload)
        print(f"API: Payload: {payload_display}")
    if effective_headers:
        print(f"API: Headers: {effective_headers}")

    try:
        if method.upper() == 'GET':
            response = requests.get(url, params=payload, headers=effective_headers, timeout=timeout)
        elif method.upper() == 'POST':
            if is_json_payload:
                response = requests.post(url, json=payload, headers=effective_headers, timeout=timeout)
            else:
                response = requests.post(url, data=payload, headers=effective_headers, timeout=timeout)
        elif method.upper() == 'PUT':
            if is_json_payload:
                response = requests.put(url, json=payload, headers=effective_headers, timeout=timeout)
            else:
                response = requests.put(url, data=payload, headers=effective_headers, timeout=timeout)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=effective_headers, timeout=timeout)
        else:
            error_msg = f"API Error: Unsupported HTTP method: {method}"
            print(error_msg)
            return False, error_msg

        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

        print(f"API: Request successful. Status Code: {response.status_code}")
        try:
            response_data = response.json()
            # print(f"API: Response JSON: {json.dumps(response_data, indent=2)}") # Verbose, uncomment if needed
        except json.JSONDecodeError:
            response_data = response.text
            # if response_data:
            #     print(f"API: Response was not JSON. Response text: {response_data}")
            # else:
            #     print("API: Response was not JSON and had no text content (e.g. 204 No Content).")
        
        return True, response_data

    except requests.exceptions.HTTPError as http_err:
        error_message = f"HTTP error occurred: {http_err}"
        if hasattr(http_err, 'response') and http_err.response is not None:
            error_message += f" | Status Code: {http_err.response.status_code} | Response: {http_err.response.text}"
        print(f"API: {error_message}")
        return False, error_message
    except requests.exceptions.ConnectionError as conn_err:
        error_message = f"Connection error occurred: {conn_err} (Could not connect to {url})"
        print(f"API: {error_message}")
        return False, error_message
    except requests.exceptions.Timeout as timeout_err:
        error_message = f"Timeout error occurred: {timeout_err} (Request to {url} timed out after {timeout}s)"
        print(f"API: {error_message}")
        return False, error_message
    except requests.exceptions.RequestException as req_err:
        error_message = f"An unexpected error occurred during the API request: {req_err}"
        print(f"API: {error_message}")
        return False, error_message
    except Exception as e:
        error_message = f"An unexpected error occurred in send_api_request: {e}"
        print(f"API: {error_message}")
        return False, error_message

# --- Number Plate Alert Function (adapted from request.py, now uses auth_token) ---
def send_number_plate_detection_alert(number_plate_text_extracted, auth_token=None):
    """
    Sends the detected number plate text to the OCR API endpoint,
    including an authorization token if provided.

    Args:
        number_plate_text_extracted (str): The extracted number plate text.
        auth_token (str, optional): The authentication token (Bearer token).

    Returns:
        tuple: (success_boolean, response_data_or_error_message) from send_api_request.
    """
    if not number_plate_text_extracted:
        print("API_ALERT: No number plate text provided to send.")
        return False, "No number plate text provided"

    ocr_api_url = f'{DEFAULT_API_BASE_URL}/OCR'  # e.g., http://poudelanish17.com.np:9002/api/v1/OCR
    
    payload = {
        'number_plate': number_plate_text_extracted,
        'timestamp': datetime.now().isoformat(),
        'source_module': 'combined_alert_system_v1' # Updated source module name
    }
    
    request_headers = {}
    if auth_token:
        request_headers['Authorization'] = f'Bearer {auth_token}'
        # Content-Type for JSON payload will be handled by send_api_request

    print(f"\n--- Sending Number Plate Alert for: '{number_plate_text_extracted}' ---")
    if auth_token:
        print(f"Using Authorization Token: Bearer {auth_token[:20]}...") # Print part of token for confirmation
        
    success, response_or_error = send_api_request(
        url=ocr_api_url,
        method='POST',
        payload=payload,
        headers=request_headers if request_headers else None # Pass headers if they exist
    )

    if success:
        # Assuming response_or_error could be JSON, try to pretty print
        try:
            response_display = json.dumps(response_or_error, indent=2)
        except (TypeError, json.JSONDecodeError): # Handle cases where it's not dict/list or already string
            response_display = response_or_error
        print(f"API_ALERT: Successfully sent number plate '{number_plate_text_extracted}'. Response: {response_display}")
    else:
        print(f"API_ALERT: Failed to send number plate '{number_plate_text_extracted}'. Error: {response_or_error}")
    
    return success, response_or_error

import csv

def send_latest_plate_from_csv(csv_path, auth_token=None):
    """
    Reads the latest row from the given CSV and sends it as JSON to the API.
    """
    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = list(csv.DictReader(csvfile))
            if not reader:
                print("CSV is empty.")
                return False, "CSV is empty"
            latest_row = reader[-1]
    except Exception as e:
        print(f"Failed to read CSV: {e}")
        return False, str(e)

    # Send the latest row as JSON
    print(f"Sending latest row from CSV: {latest_row}")
    # You can change the endpoint as needed; here we use the OCR endpoint as in your alert function
    ocr_api_url = f'{DEFAULT_API_BASE_URL}/OCR'
    request_headers = {}
    if auth_token:
        request_headers['Authorization'] = f'Bearer {auth_token}'
    success, response_or_error = send_api_request(
        url=ocr_api_url,
        method='POST',
        payload=latest_row,
        headers=request_headers if request_headers else None
    )
    if success:
        print("Successfully sent latest plate row.")
    else:
        print(f"Failed to send latest plate row: {response_or_error}")
    return success, response_or_error

# --- Vehicle Detection Alert Function ---
def send_vehicle_detection_alert(auth_token=None):
    """
    Sends an alert that a vehicle has been detected
    """
    api_url = f'{DEFAULT_API_BASE_URL}/vehicle-detection'
    
    payload = {
        'timestamp': datetime.now().isoformat(),
        'event': 'vehicle_detected',
        'source_module': 'vehicle_detection_v1'
    }
    
    request_headers = {}
    if auth_token:
        request_headers['Authorization'] = f'Bearer {auth_token}'
    
    return send_api_request(
        url=api_url,
        method='POST',
        payload=payload,
        headers=request_headers if request_headers else None
    )

# Export commonly used functions
__all__ = ['attempt_login', 'send_number_plate_detection_alert', 'send_vehicle_detection_alert']

# --- Main Execution Block ---
if __name__ == "__main__":
    # 1. Attempt Login to get the authentication token
    # Using credentials expected to yield a token based on the problem description.
    login_email = "developer@developer1.com"
    login_password = "developer1" # This should be the correct password for the developer email
    
    print(f"--- Main: Attempting Login for user: {login_email} ---")
    login_success, login_response_content = attempt_login(login_email, login_password)

    auth_token = None
    if login_success:
        print("\nMain: Login attempt was successful (HTTP 2xx).")
        if isinstance(login_response_content, dict) and "token" in login_response_content:
            auth_token = login_response_content["token"]
            print(f"Main: Successfully received token: {auth_token[:30]}...") # Print only a part of the token
        else:
            print("Main: Login successful, but no 'token' key found in the response.")
            print(f"Main: Login response content was: {login_response_content}")
    else:
        print("\nMain: Login attempt failed.")
        print(f"Main: Login failure response: {login_response_content}")

    # 2. If login was successful and token was obtained, send the number plate alert
    if auth_token:
        print("\n--- Main: Proceeding to send Number Plate Alert with authentication token ---")
        
        # Send the latest row from the CSV file
        csv_path = r"e:\My Files\Elytra Solutions\MadeshPradesh\nmp\database\license_plates_2025-05-13.csv"
        send_latest_plate_from_csv(csv_path, auth_token)
        
        print("Ready to send actual plate text from extraction pipeline using send_number_plate_detection_alert().")
    else:
        print("\n--- Main: Skipping Number Plate Alert because no authentication token was obtained. ---")

    print("\n--- Main: Script execution finished. ---")


def send_plate_data_bulk(plate_data_list, auth_token=None):
    """
    Sends the full plate data list to the API endpoint.
    Args:
        plate_data_list (list): List of plate data dictionaries.
        auth_token (str, optional): Bearer token for authentication.
    Returns:
        tuple: (success_boolean, response_data_or_error_message)
    """
    if not plate_data_list:
        print("API_BULK: No plate data to send.")
        return False, "No plate data provided"

    api_url = f'{DEFAULT_API_BASE_URL}/plate-data-bulk'  # Adjust endpoint as needed

    payload = {
        'plate_data': plate_data_list,
        'timestamp': datetime.now().isoformat(),
        'source_module': 'text_extraction_bulk_v1'
    }

    request_headers = {}
    if auth_token:
        request_headers['Authorization'] = f'Bearer {auth_token}'

    print(f"\n--- Sending Bulk Plate Data ({len(plate_data_list)} records) ---")
    success, response_or_error = send_api_request(
        url=api_url,
        method='POST',
        payload=payload,
        headers=request_headers if request_headers else None
    )

    if success:
        try:
            response_display = json.dumps(response_or_error, indent=2)
        except (TypeError, json.JSONDecodeError):
            response_display = response_or_error
        print(f"API_BULK: Successfully sent plate data. Response: {response_display}")
    else:
        print(f"API_BULK: Failed to send plate data. Error: {response_or_error}")

    return success, response_or_error
