import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

SMS_API_KEY = os.getenv("SMS_API_KEY")
SMS_TEMPLATE_ID = os.getenv("SMS_TEMPLATE_ID")

def send_otp_sms(phone_number: str, otp_code: str):
    """
    Sends a verification OTP using the api.sms.ir service and a template.
    """
    if not SMS_API_KEY or not SMS_TEMPLATE_ID:
        print("ERROR: SMS_API_KEY or SMS_TEMPLATE_ID is not set in the .env file.")
        return False

    print(f"--- Sending real SMS via api.sms.ir (verify endpoint) ---")
    print(f"Sending OTP {otp_code} to {phone_number} using template {SMS_TEMPLATE_ID}")

    url = "https://api.sms.ir/v1/send/verify"

    payload = {
        "mobile": phone_number,
        "templateId": int(SMS_TEMPLATE_ID),
        "parameters": [
            {
                "name": "TITLE", 
                "value": otp_code
            }
        ]
    }

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'text/plain',
        'x-api-key': SMS_API_KEY
    }

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        
        response_data = response.json()
        print(f"SMS API Response: {response_data}")

        if response_data.get("status") == 1:
            return True
        else:
            print(f"SMS API returned an error: {response_data.get('message')}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while sending the SMS request: {e}")
        return False
    except json.JSONDecodeError:
        print(f"Failed to decode JSON response from SMS API. Response text: {response.text}")
        return False