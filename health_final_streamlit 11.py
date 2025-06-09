import re
import os
import sqlite3
import time
import json
from dataclasses import dataclass
from typing import Dict, Any
from api import *
from utils import speech_to_text, text_to_speech1_english, redirecting_to_agent, message_website, call_openai, \
    extract_and_convert_to_json
from soap_api_number import extract_health_policy_numbers  , extract_motor_policy_numbers

from dateutil import parser
import re
import streamlit as st
import wave
from deep_update import handle_recording, play_audio

from utils import text_to_speech_azure_streamlit, speech_to_text_azure_streamlit
# from health_final_hindi import hindi_claim_intimation_flow
import requests
from utils import *
import re
import xml.etree.ElementTree as ET

from health_final_hindi import * 


def convert_to_dd_mm_yyyy(date_str):
    # Regular expression to match month and year formats (e.g., "February 2025")
    if re.match(r"^[A-Za-z]+ \d{4}$", date_str) or re.match(r"^\d{1,2}[a-z]{2} [A-Za-z]+$", date_str):
        return "date format is not correct"
    try:
        # Parse the input date string
        parsed_date = parser.parse(date_str)
        # Convert the parsed date to DD/MM/YYYY format
        formatted_date = parsed_date.strftime('%d/%m/%Y')
        return formatted_date

    except (ValueError, OverflowError):
        return "Invalid date format"
    
def remove_special_characters_except_comma(input_string):
    try:
        return re.sub(r'[^A-Za-z0-9,/ ]', ' ', input_string)
    except:
        return input_string
    

def calculate_length_of_audio():
    with wave.open(r"C:/Users/jatin/OneDrive/Desktop/today/health_insurance_project/audio/Bot/bot_response.wav", 'rb') as audio_file:
        frames = audio_file.getnframes()
        rate = audio_file.getframerate()
        duration = frames / float(rate)
        return duration + 0.5
    

def text_to_speech_func_english(message):
    text_to_speech_azure_streamlit(input_text=message)
    with st.chat_message("assistant"):
        st.write(message)
    play_audio()
    time.sleep(calculate_length_of_audio())  # handle time dynamically



def get_user_input_with_retries(record_duration: int = 5):
    message = "Sorry, I didn't catch that. Please say it again."
    max_attempts = 0
    # for attempt in range(max_attempts):
    while max_attempts < 2:
        max_attempts += 1
        text_to_speech_func_english(message=message)

        # Record user input
        with st.spinner("Recording..."):
            handle_recording(duration=record_duration)
        input_text = speech_to_text_azure_streamlit()

        # Validate and process input
        if input_text is not None:
            processed_text = str(input_text).strip().lower()
            if processed_text:
                with st.chat_message("user"):
                    st.write(processed_text)
                return processed_text

    return False  # All attempts failed


def handle_user_input(duration):
    with st.spinner("Recording..."):
        handle_recording(duration=duration)  # Assuming handle_recording is your recording function
    user_input = speech_to_text_azure_streamlit()
    if user_input is not None:
        user_input = remove_fullstop_from_input(user_input.strip().lower())
        with st.chat_message("user"):
            st.write(user_input)
    else:
        user_input = get_user_input_with_retries(record_duration=duration)

    if user_input is False:
        message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
        text_to_speech_func_english(message)
    return user_input


from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class ClaimSession:
    """Central data storage for health claim process"""
    selected_language: str = None
    auth_attempts: int = 0
    date_attempts: int = 0
    policy_number: str = None  
    mobile_number: str = None
    policy_details: List[Dict[str, Any]] = field(default_factory=list)
    caller_details: Dict[str, Any] = None
    claim_details: Dict[str, Any] = None
    transfer_reason: str = None



def fetch_health(pincode):
    # Get absolute database path
    db_path = os.path.abspath('C:/Users/jatin/OneDrive/Desktop/today/health_insurance_project/db.sqlite3')

    if not os.path.exists(db_path):
        print("Database file not found!")
        return []

    try:
        # Establishing connection to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Fetch Records
        query = f"SELECT * FROM FinalGarageMaster WHERE PinCode = '{pincode}';"
        cursor.execute(query)
        records = cursor.fetchall()
        return records

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

    finally:
        if conn:
            conn.close()




# *************************************************************************************************************


def validate_mobile_number(mobile_number):
    # Call the API validation function
    status, _ = validate_mobile_number_api_call(mobile_number)  # Unpack the response

    # Check if the response indicates a valid or invalid mobile number
    if status == "valid mobile number":
        return True
    elif status == "invalid mobile number":
        return False
    else:
        return False

# Test
# mobile_no = "8655904635"
# is_valid = validate_mobile_number(mobile_no)
# print(is_valid)  # Should print True if the number is valid


# print("this is my detail from getting bacend ",policy_details)
retry_count = 0
def handle_multiple_policies(session, ph_nu):
    """Handles different scenarios based on the number of policies dynamically and assigns the correct name."""

    global policy_details  # Ensure access to global policy details
    
    # List of product codes that require transferring to an agent
    restricted_product_codes = [
        2812, 2824, 2825, 2826, 2827, 2828, 2829, 2835, 2842, 2843, 2845, 2847, 
        2849, 2850, 2851, 2852, 2853, 2854, 2856, 2857, 2858, 2859, 2860, 2861, 
        2862, 2864, 2865, 2914, 2913, 2945, 2711, 3011, 3015, 2934, 2933, 2929, 
        2931, 2835, 2829, 2951, 2952, 2955, 2942, 2875, 2958
    ]
    
    import difflib

    def normalize_user_response(user_input):
        """Returns 'yes' or 'no' if close match is found, else returns None."""
        user_input = user_input.strip().lower().replace(".", "").replace(",", "")
        options = ["yes", "no"]
        match = difflib.get_close_matches(user_input, options, n=1, cutoff=0.8)
        return match[0] if match else None


    policies = extract_motor_policy_numbers(ph_nu)
    print(f"Extracted policies: {policies}") 

    if isinstance(policies, str):
        text_to_speech_func_english(policies)
        text_to_speech_func_english("Transferring you to an agent.")
        return False

    policy_count = len(policies)
    
#   check this condition if else   *********************************************
    if policy_count == 1:
        session.policy_number = policies[0]
        selected_policy = next((p for p in policy_details if p["policy_number"] == session.policy_number), None)
        
        if selected_policy:
            session.policy_details = [selected_policy]
            session.mobile_number = selected_policy["mobile_number"]
            selected_name = selected_policy.get("name", "Customer")
            
            # Check if the product code requires transfer
            if selected_policy.get("product_code") and int(selected_policy["product_code"]) in restricted_product_codes:
                text_to_speech_func_english("Your policy type requires assistance. Transferring you to an agent.")
                return False
            
        else:
            selected_name = "Customer"

        text_to_speech_func_english(f"I have identified your policy. I'll take you to the correct queue based on your policy type.")
        text_to_speech_func_english(f"Your policy {session.policy_number} is selected. Proceeding with intimation.")
        text_to_speech_func_english(f"Thank you, {selected_name}. Your mobile number is {session.mobile_number}.")
        return True

    elif 2 <= policy_count <= 3:
        message = "You have multiple policies. I will read the last 7 digits of each policy one by one. Please confirm."
        text_to_speech_func_english(message)
        selected_policy = None 

        for policy_no in policies:
            last_7_digits = policy_no[-7:]
            text_to_speech_func_english(f"Does your policy number end with {last_7_digits}? Please say 'yes' or 'no'.")
            # user_input = handle_user_input(duration=5).replace(" ", "").replace(".", "").lower()
            
            user_input = handle_user_input(duration=5)
            # user_input = "yes"
            user_input = user_input.replace(" ", "").replace(".", "").lower() if user_input else ""
            
            
            if not user_input or not isinstance(user_input, str):
                #    text_to_speech_func_english("No input detected. Disconnecting the call.")
                   return False  # <-- Stop execution if the user stays silent.
            user_input = user_input.strip().lower() if isinstance(user_input, str) and user_input in ["yes", "no", "confirm"] else ""
            
            # user_input ="yes"
            user_input = normalize_user_response(user_input)

            if user_input in ["yes", "confirm"]:
                session.policy_number = policy_no
                selected_policy = next((p for p in policy_details if p["policy_number"] == session.policy_number), None)
 
                if selected_policy:
                    session.policy_details = [selected_policy]
                    session.mobile_number = selected_policy["mobile_number"]
                    selected_name = selected_policy.get("name", "Customer")
                    
                    # Check if the product code requires transfer
                    if selected_policy.get("product_code") and int(selected_policy["product_code"]) in restricted_product_codes:
                        text_to_speech_func_english("Your policy type requires assistance. Transferring you to an agent.")
                        return False

                else:
                    selected_name = "Customer"

                text_to_speech_func_english(f"You selected policy {session.policy_number} and your name is {selected_name}")
                text_to_speech_func_english(f"Thank you, {selected_name}. Your mobile number is {session.mobile_number}.")
                return True  
            
            elif user_input in ["no"]:
                text_to_speech_func_english("Okay, let's check the next policy.")
                continue  
            
            else:
                text_to_speech_func_english("Invalid response. ")
                continue

        # text_to_speech_func_english("No policy was confirmed. Transferring you to an agent.")
        if not  selected_policy:
            text_to_speech_func_english(".Sorry, I haven’t received correct input from you, so I’ll be disconnecting the call now.")
            return False
#  in this if user give something out put like i dont know so i need to  give retry 2 times then disconnect the call 

    
    elif policy_count >= 4:
       for attempt in range(3): 
        text_to_speech_func_english("You have multiple policies. Please say the last 7 digits of the policy number.")
        user_input = handle_user_input(duration=7)
        extracted_number = re.findall(r"\b\d{7}\b", user_input)
        
        # Check if user input is not a number or contains no number
        if user_input in ["i don't know", "dont know", "don't know"] or not re.search(r"\d", user_input):
            text_to_speech_func_english(f"Invalid input or you said you don't know. Attempt {attempt + 1} of 3.")
            if attempt == 2:
                text_to_speech_func_english("Multiple unsuccessful attempts. Disconnecting the call.")
                return False
            continue

        if not extracted_number:
            text_to_speech_func_english("Invalid input. Please provide exactly 7 digits.")
            continue
        
        user_input = extracted_number[0]
        selected_policy = next((p for p in policy_details if user_input in p["policy_number"]), None)

        if selected_policy:
            session.policy_number = selected_policy["policy_number"]
            session.policy_details = [selected_policy]
            session.mobile_number = selected_policy["mobile_number"]
            selected_name = selected_policy.get("name", "Customer")

            # Check if the product code requires transfer
            if selected_policy.get("product_code") and int(selected_policy["product_code"]) in restricted_product_codes:
                text_to_speech_func_english("Your policy type requires assistance. Transferring you to an agent.")
                return False

            text_to_speech_func_english(f"Policy {session.policy_number} selected. Proceeding with intimation.")
            text_to_speech_func_english(f"Thank you, {selected_name}.")
            return True
        text_to_speech_func_english("Policy not found. Please try again.")
       text_to_speech_func_english("Multiple unsuccessful attempts. Disconnecting the call.")
       return False
        # text_to_speech_func_english("Policy not found. Transferring to an agent.")
        # return False

    else:
        text_to_speech_func_english("No policies found. Transferring to an agent.")
        return False


# ***** step 3 logic about retail and corporate **************************************
def fetch_policy_details(policy_no):
    url = f'http://mservices.brobotinsurance.co.in/ldapauth/api/corporateportalapi/getpolicyclassificationforpolicy?policyno={policy_no}'
    headers = {"Authorization": "Basic UkdJQ29ycDpWQGxpZEB0ZQ=="}
    response = requests.get(url, headers=headers)
    return response.json()


def process_policy(policy_no):
    if not policy_no:
        return False

    policy_details = fetch_policy_details(policy_no)
    if 'Output' not in policy_details:
        return False

    classification = policy_details['Output']

    if classification == 'Retail':
        message = "Could you provide patient U H I D"
        text_to_speech_func_english(message)

        for attempt in range(2):
            
            
            # uhid_confirmation =  handle_user_input(duration=12).replace(" ", "").replace(".", "").upper()
            uhid_confirmation = re.sub(r'\D', '', (handle_user_input(duration=12) or "").upper().strip())
            # uhid_confirmation =130592329291010982
            res1 = uhid_retail_confirmation(uhid_confirmation, policy_no)

            if res1 == True:
                return True
            elif attempt == 0 and res1 == "second":
                message = "Could you please provide the correct U-H-I-D of the patient?"
                text_to_speech_func_english(message)
            else:
                break

        message = "Limit Exceeded! I am disconnecting the call now."
        text_to_speech_func_english(message)
        return False


    elif classification == 'Corporate':
        message = "Please share your employee code"
        text_to_speech_func_english(message)

        for emp_attempt in range(2):
            
            # user_input = "10000003"
            
            user_input = handle_user_input(duration=10)

            
            if user_input:
                emp_code_confirmation = re.sub(r'\D', '', user_input.upper().strip())
            else:
                emp_code_confirmation = ""
                
            if not isinstance(emp_code_confirmation, str) or not emp_code_confirmation.strip():
                return False
            
            res = empid_corporate_details(emp_code_confirmation, policy_no)

            if res == True:
                # Proceed to UHID confirmation
                for uhid_attempt in range(2):
                    message = "Could you confirm patient U-H-I-D"
                    text_to_speech_func_english(message)
                    
                    #
                    
                    # uhid_confirmation = re.sub(r'[^A-Za-z0-9]', '', handle_user_input(duration=12).upper())
                    
                    user_input = handle_user_input(duration=12)
                    # user_input = "RSP0223000100"
                    if user_input:
                       uhid_confirmation = re.sub(r'[^A-Za-z0-9]', '', user_input.upper().strip())
                    else:
                       uhid_confirmation = ""

                    if not isinstance(uhid_confirmation, str) or not uhid_confirmation.strip():
                        return False

                    res2 = uhid_corporate_confirmation(emp_code_confirmation, policy_no, uhid_confirmation)

                    if res2 == True:
                        return True
                    elif uhid_attempt == 0 and res2 == "seconduhid":
                        message = "Could you please provide the correct U-H-I-D of the patient?"
                        text_to_speech_func_english(message)
                    else:
                        break

                message = "Unfortunately, the details provided do not match our records. I am disconnecting the call now."
                text_to_speech_func_english(message)
                return False

            elif emp_attempt == 0 and res == "second_emp":
                message = "No employee found. Please share correct employee code."
                text_to_speech_func_english(message)
            else:
                break

        message = "Unfortunately, the details provided do not match our records. I am disconnecting the call now."
        text_to_speech_func_english(message)
        return False

    else:
        message = "Error verifying policy classification. I have to end the call."
        text_to_speech_func_english(message)
        return False


# Function to call the second API with the provided data
def uhid_retail_confirmation(uhid_confirmation, policy_no_confirmation):
    data = {
        "EmployeeId": "0",
        "PolicyClassification": "Retail",
        "PolicyNo": policy_no_confirmation
            }
    url = 'http://mservices.brobotinsurance.com/ldapauth/api/corporateportalapi/GetPolicyMemberDetailsForPolicy'  # Replace with the actual endpoint
    headers = {'Authorization': 'Basic UkdJQ29ycDpWQGxpZEB0ZQ==', 'Content-Type': 'application/json'}
    response = requests.post(url, json=data, headers=headers)
    result = response.json()
    
    # Check if the output list exists and contains at least one element
    if "Output" in result and isinstance(result["Output"], list):
        if result["Output"]:
            # Output is non-empty; get the returned UHID
            returned_uhid = result["Output"][0].get("UHID")
            if returned_uhid == uhid_confirmation:
                print("MATCHED  this one")
                message = "U-H-I-D MATCHED"
                text_to_speech_func_english(message)
                # ask_admission_date(session=)
                return True
            elif returned_uhid != uhid_confirmation:
                message = "Could you please provide the correct U-H-ID of the patient?"
                text_to_speech_func_english(message)
                return "second"
            else:
                message = "U-H-I-D does not match the UCS data"
                text_to_speech_func_english(message)
                return False
        else:
            # "Output" is an empty list—treat as a mismatch
            message = "U-H-I-D does not match the UCS data"
            text_to_speech_func_english(message)
            return False
    else:
        print("Error in response or no data returned")
        return "Error in response or no data returned"



def empid_corporate_details(emp_code_confirmation, policy_no_confirmation):
    print(f'emp: {type(emp_code_confirmation)}, policy: {type(policy_no_confirmation)}')
    data = {
        "EmployeeId": emp_code_confirmation,
        "PolicyClassification": "Corporate",
        "PolicyNo": policy_no_confirmation
    }
    url = 'http://mservices.brobotinsurance.com/ldapauth/api/corporateportalapi/GetPolicyMemberDetailsForPolicy'
    headers = {'Authorization': 'Basic UkdJQ29ycDpWQGxpZEB0ZQ==', 'Content-Type': 'application/json'}
    response = requests.post(url, json=data, headers=headers)
    result = response.json()
    # st.write(result)
    
    # Check if the output list exists and contains data
    if "Output" in result and isinstance(result["Output"], list):
        if result["Output"]:
            returned_emp_id = result["Output"][0].get("EmployeeId")
            print("returned id", type(returned_emp_id))
            # Check if the returned Employee ID matches the input
            if returned_emp_id == str(emp_code_confirmation):
                print("ID MATCHED")
                message = "Employee ID Matched"
                text_to_speech_func_english(message)
                return True
            else:
                # Employee ID mismatch, allow retry
                message = "Employee ID does not match. Please try again."
                text_to_speech_func_english(message)
                return "second_emp"
        else:
            # Empty output list, allow retry
            return "second_emp"
    else:
        print("Error in response or no data returned")
        return False



def uhid_corporate_confirmation(emp_code_confirmation, policy_no_confirmation, uhid_confirmation):
    data = {
        "EmployeeId": emp_code_confirmation,
        "PolicyClassification": "Corporate",
        "PolicyNo": policy_no_confirmation
    }
    url = 'http://mservices.brobotinsurance.com/ldapauth/api/corporateportalapi/GetPolicyMemberDetailsForPolicy'
    headers = {
        'Authorization': 'Basic UkdJQ29ycDpWQGxpZEB0ZQ==',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        result = response.json()
    except Exception as e:
        print("API request failed:", e)
        return False

    if "Output" in result and isinstance(result["Output"], list) and result["Output"]:
        returned_uhid = result["Output"][0].get("UHID")
        print("Returned UHID:", returned_uhid)

        if returned_uhid == str(uhid_confirmation):
            return True
        else:
            return "seconduhid"
    else:
        return False






# ************    new logic for date checking *****************************************************

# *****************      new logic end here *******************************************************
from dateutil import parser
from datetime import datetime



def format_date(user_input):
    try:
        parsed_date = parser.parse(user_input, fuzzy=True)
        formatted_date = parsed_date.strftime("%d/%m/%Y")  # Matches your validation
        return formatted_date
    except ValueError:
        return user_input




#  give retry for both like if date is outside the time period or invalid or empty ************************************
def ask_admission_date(session):
    """
    Ask the user for the hospital admission date, validate it against the policy period, and store it.
    If the date is not within the policy period or invalid, transfer the call to an agent.
    """
    max_attempts = 2  # Allow only two tries
    attempts = 0

    # Fetch policy details from the session
    policy_details = session.policy_details[0]
    policy_start_date = policy_details.get("policy_start_date", "")
    policy_end_date = policy_details.get("policy_end_date", "")

    # Check if policy_start_date and policy_end_date are present
    if not policy_start_date or not policy_end_date:
        session.transfer_reason = "Missing policy dates"
        text_to_speech_func_english("The policy details are missing or invalid. I’ll transfer you to an agent for further assistance.")
        return False

    # Ensure the start date and end date are formatted correctly
    try:
        policy_start_date = policy_start_date.split(" ")[0]  # Take only the date part, ignore time
        policy_start_date = datetime.strptime(policy_start_date, "%m/%d/%Y").date()

        policy_end_date = datetime.strptime(policy_end_date, "%d %b %Y").date()

    except ValueError as e:
        session.transfer_reason = "Invalid Policy Dates"
        text_to_speech_func_english(f"The policy dates seem to be invalid. Error: {e}. I'll transfer you to an agent for further assistance.")
        return False

    while attempts < max_attempts:
        message = "Could you please share the date when you were admitted to the hospital?"
        text_to_speech_func_english(message)

        admission_date = handle_user_input(duration=6)  
        
        # admission_date = "16 april 2024"
        
        if not admission_date:
            session.transfer_reason = "No input received"
            text_to_speech_func_english("Sorry, I didn’t receive any input from you. I’ll be disconnecting the call now.")
            return False

        admission_date = format_date(admission_date)  # Format using improved formatter

        try:
            formatted_admission_date = datetime.strptime(admission_date, "%d/%m/%Y").date()
        except ValueError:
            attempts += 1
            if attempts < max_attempts:
                text_to_speech_func_english("The date you provided seems to be invalid. Please try again.")
                continue
            else:
                session.transfer_reason = "Invalid Date Format"
                text_to_speech_func_english("The date you provided is invalid. I’ll transfer you to an agent for further assistance. Please hold.")
                return False

        # Validate admission date against policy period
        if policy_start_date <= formatted_admission_date <= policy_end_date:
            session.claim_details = session.claim_details or {}  # Initialize dict
            session.claim_details["admission_date"] = admission_date

            insured_name = policy_details.get("name", "Unknown")
            confirmation_message = f"Dear {insured_name}, your date of admission is {admission_date}."
            text_to_speech_func_english(confirmation_message)
            return True
        else:
            session.transfer_reason = "Admission Date Outside Policy Period"
            text_to_speech_func_english(
                "The Date of Admission is outside the policy period, so we are unable to process your request. Thank you for reaching out to us."
            )
            return False

    return False

# ******* step 3 end here ***********************************************************

#**** Step 4 logic for Type Of claim  ************************************************
from datetime import datetime
import re



# **********************************  testing ********************************************************************************




def clean_date_input(date_str):
    """
    Cleans up date strings by removing ordinal suffixes and extra whitespace.
    Capitalizes the month for better parsing.
    """
    date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str, flags=re.IGNORECASE)  # Remove suffix
    date_str = re.sub(r'\s+', ' ', date_str).strip()  # Normalize spaces
    return date_str.title()  # Capitalize month
 
def try_parse_date(date_str):
    """
    Tries to parse a date string using multiple expected formats.
    """
    for fmt in ("%d %B %Y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None
 
#  in this only cashless we give default amount 25000 not in reimbursement ( in this we need to give amount )*********************
#  in reimbursement if user did not give amount then give 2 retry and also -------------------------------------------
# def determine_claim_type(session):
#     """Determines the type of claim based on user input and proceeds accordingly."""
#     text_to_speech_func_english("Please let me know the type of claim you are registering. Is it for: "
#                                 "1. OPD, 2. Reimbursement, or 3. Cashless? "
#                                 "For example, say 'OPD claim' or 'Reimbursement claim'.")
 
#     while True:
#         # user_input = handle_user_input(duration=5).strip().lower()
        
#         raw_input = handle_user_input(duration=5)
#         user_input = raw_input.strip().lower() if raw_input else ""
#         # user_input = "reimbursement"
 
#         # ✅ CASE 1: OPD Claim → Transfer to Agent
#         if "opd" in user_input:
#             text_to_speech_func_english("Thank you for confirming. Since this is an OPD claim, I will transfer you to a live agent for further assistance. Please hold.")
#             session.transfer_reason = "OPD claim - Transfer to Agent"
#             return False  # Ends here, transfers to agent
 
#         # ✅ CASE 2: Reimbursement Claim → Ask for Date of Discharge
#         elif "reimbursement" in user_input:
#             text_to_speech_func_english("Could you please provide the Date of Discharge from the hospital? "
#                                         "For example, say '15 April 2025'.")
 
#             session.claim_details = session.claim_details or {}
#             static_admission_date_str = session.claim_details.get("admission_date")
 
#             if not static_admission_date_str:
#                 text_to_speech_func_english("Admission date is missing. Please provide it before giving discharge date.")
#                 session.transfer_reason = "Missing Admission Date"
#                 return False
 
#             try:
#                 admission_date = try_parse_date(clean_date_input(static_admission_date_str))
#             except Exception as e:
#                 text_to_speech_func_english("Admission date format is incorrect. Cannot proceed.")
#                 session.transfer_reason = "Invalid Admission Date Format"
#                 return False
 
#             while True:
#                 discharge_date_str = handle_user_input(duration=5)
#                 # discharge_date_str= "20 April 2024"
                
#                 cleaned_discharge_date = clean_date_input(discharge_date_str)
 
#                 discharge_date = try_parse_date(cleaned_discharge_date)
 
#                 if discharge_date:
#                     if discharge_date < admission_date:
#                         text_to_speech_func_english(f"Date of Discharge is before the Date of Admission ({admission_date.strftime('%d %B %Y')}). Please provide a correct Date of Discharge.")
#                         continue
 
#                     session.claim_details["discharge_date"] = discharge_date.strftime("%d %B %Y")
#                     text_to_speech_func_english(f"Thank you. You have provided {discharge_date.strftime('%d %B %Y')} as the Date of Discharge.")
#                     return True
#                 else:
#                     text_to_speech_func_english("I'm sorry, the date format is incorrect. Please say the date like '15 October 2024' or '15/10/2024'.")
 
#         # ✅ CASE 3: Cashless Claim → Store and Proceed
#         elif "cashless" in user_input:
#             session.claim_details = session.claim_details or {}
#             session.claim_details["claim_type"] = "cashless"
 
#             text_to_speech_func_english("Thank you for confirming. We have registered your claim as a Cashless claim.")
#             return True
 
#         else:
#             text_to_speech_func_english("I didn't understand that. Please say 'OPD claim', 'Reimbursement claim', or 'Cashless claim'.")
            
            
            
# def determine_claim_type(session):
#     """Determines the type of claim based on user input (max 2 attempts)"""
#     max_attempts = 2
#     attempts = 0
    
#     # Initial prompt
#     text_to_speech_func_english("Please let me know the type of claim you are registering. Is it: "
#                              "1. OPD, 2. Reimbursement, or 3. Cashless? "
#                              "For example, say 'OPD claim' or 'Reimbursement claim'.")

#     while attempts < max_attempts:
#         attempts += 1
        
#         # Get user input with error handling
#         # raw_input = handle_user_input(duration=5)
#         raw_input = "Reimbursement"
        
        
#         if raw_input is False:  # Input failed completely
#             return False
            
#         user_input = raw_input.strip().lower() if raw_input else ""
        
#         with st.chat_message("user"):
#             st.write(user_input if user_input else "No input")

#         # Case 1: OPD Claim
#         if "opd" in user_input:
#             text_to_speech_func_english("Thank you for confirming. Since this is an OPD claim, I'm transferring you to a live agent for further assistance. Please stay on the line.")
#             session.transfer_reason = "OPD claim - Transfer to agent"
#             return False

#         # Case 2: Reimbursement Claim
#         elif "reimbursement" in user_input:
#             text_to_speech_func_english("Thank you. We've registered your claim as a Reimbursement claim.")
#             text_to_speech_func_english("Please provide the date of discharge from the hospital")

#             session.claim_details = session.claim_details or {}
#             # static_admission_date_str = session.claim_details.get("admission_date")
            
            
#             static_admission_date_str = "18 April 2024"
            
#             if not static_admission_date_str:
#                 text_to_speech_func_english("Admission date is missing. Please provide it first, then give the discharge date.")
#                 session.transfer_reason = "Missing admission date"
#                 return False

#             try:
#                 admission_date = try_parse_date(clean_date_input(static_admission_date_str))
#             except Exception as e:
#                 text_to_speech_func_english("The admission date format is incorrect. Cannot proceed.")
#                 session.transfer_reason = "Invalid admission date format"
#                 return False

#             # Get discharge date with 2 attempts
#             discharge_attempts = 0
#             while discharge_attempts < 2:
#                 discharge_attempts += 1
#                 discharge_date_str = handle_user_input(duration=5)
                
#                 # with st.chat_message("user"):
#                 #     st.write(discharge_date_str)     
                
#                 cleaned_discharge_date = clean_date_input(discharge_date_str)
#                 discharge_date = try_parse_date(cleaned_discharge_date)

#                 if discharge_date:
#                     if discharge_date < admission_date:
#                         text_to_speech_func_english(f"Discharge date is before admission date ({admission_date.strftime('%d %B %Y')}). Please provide the correct discharge date.")
#                         continue

#                     session.claim_details["discharge_date"] = discharge_date.strftime("%d %B %Y")
#                     text_to_speech_func_english(f"Thank you. You've provided {discharge_date.strftime('%d %B %Y')} as the discharge date.")
#                     return True
#                 else:
#                     if discharge_attempts < 2:
#                         text_to_speech_func_english("I'm sorry, the date format is incorrect. Please say the date like '15 October 2024' or '15/10/2024'.")
#                     else:
#                         text_to_speech_func_english("Sorry, I couldn't understand the discharge date. Please try again later.")
#                         return False

#         # Case 3: Cashless Claim
#         elif "cashless" in user_input:
#             session.claim_details = session.claim_details or {}
#             session.claim_details["claim_type"] = "cashless"
#             text_to_speech_func_english("Thank you. We've registered your claim as a Cashless claim.")
#             return True

#         # Invalid input handling
#         if attempts < max_attempts:
#             if not user_input:
#                 text_to_speech_func_english("Sorry, I didn't hear you. Please say it again.")
#             else:
#                 text_to_speech_func_english("I didn't understand that. Please say 'OPD claim', 'Reimbursement claim', or 'Cashless claim'.")
#         else:
#             break

#     # Max attempts reached
#     text_to_speech_func_english("Sorry, I couldn't determine your claim type. Please try again later. I'm ending the call now.")
#     session.transfer_reason = "Could not determine claim type"
#     return False


def determine_claim_type(session):
    """Determines the type of claim based on user input (max 2 attempts)"""
    max_attempts = 2
    attempts = 0
    
    # Initial prompt
    text_to_speech_func_english("Please let me know the type of claim you are registering. Is it: "
                             "1. OPD, 2. Reimbursement, or 3. Cashless? "
                             "For example, say 'OPD claim' or 'Reimbursement claim'.")

    while attempts < max_attempts:
        attempts += 1
        
        # Get user input with error handling
        raw_input = handle_user_input(duration=5)
        
        # raw_input = "reimbursement"
        
        if raw_input is False:  # Input failed completely
            return False
            
        user_input = raw_input.strip().lower() if raw_input else ""
        
        # with st.chat_message("user"):
        #     st.write(user_input if user_input else "No input")

        # Case 1: OPD Claim
        if "opd" in user_input:
            text_to_speech_func_english("Thank you for confirming. Since this is an OPD claim, I'm transferring you to a live agent for further assistance. Please stay on the line.")
            session.transfer_reason = "OPD claim - Transfer to agent"
            return False

        # Case 2: Reimbursement Claim
        elif "reimbursement" in user_input:
            text_to_speech_func_english("Thank you. We've registered your claim as a Reimbursement claim.")
            
            session.claim_details = session.claim_details or {}
            session.claim_details["claim_type"] = "reimbursement" 
            static_admission_date_str = session.claim_details.get("admission_date")
            # static_admission_date_str = "15 April 2024"

            if not static_admission_date_str:
                text_to_speech_func_english("Admission date is missing. Please provide it first, then give the discharge date.")
                session.transfer_reason = "Missing admission date"
                return False

            try:
                admission_date = try_parse_date(clean_date_input(static_admission_date_str))
            except Exception as e:
                text_to_speech_func_english("The admission date format is incorrect. Cannot proceed.")
                session.transfer_reason = "Invalid admission date format"
                return False

            # Get discharge date with 2 dedicated attempts
            discharge_attempts = 0
            while discharge_attempts < 2:
                text_to_speech_func_english("Please provide the date of discharge from the hospital (e.g., '15 January 2024')")
                discharge_date_str = handle_user_input(duration=5)
                discharge_attempts += 1
                
                # Clean and normalize the date input
                cleaned_input = clean_date_input(discharge_date_str)
                cleaned_input = cleaned_input.replace("th", "").replace("st", "").replace("nd", "").replace("rd", "").replace(".", "")
                
                # with st.chat_message("user"):
                #     st.write(discharge_date_str)     
                
                discharge_date = try_parse_date(cleaned_input)

                if discharge_date:
                    if discharge_date < admission_date:
                        if discharge_attempts < 2:
                            text_to_speech_func_english(f"Discharge date ({discharge_date.strftime('%d %B %Y')}) is before admission date ({admission_date.strftime('%d %B %Y')}). Please try again.")
                            continue
                        else:
                            text_to_speech_func_english(f"Discharge date is still before admission date. I'll need to transfer you to an agent for assistance.")
                            session.transfer_reason = "Discharge date before admission date"
                            return False

                    session.claim_details["discharge_date"] = discharge_date.strftime("%d %B %Y")
                    text_to_speech_func_english(f"Thank you. You've provided {discharge_date.strftime('%d %B %Y')} as the discharge date.")
                    return True
                else:
                    if discharge_attempts < 2:
                        text_to_speech_func_english("I'm sorry, the date format is incorrect. Please say the date like '15 October 2024'")
                    else:
                        text_to_speech_func_english("Sorry, I couldn't understand the discharge date. I'll need to transfer you to an agent.")
                        session.transfer_reason = "Could not understand discharge date"
                        return False

            # This point should never be reached because of the return statements above
            return False

        # Case 3: Cashless Claim
        elif "cashless" in user_input:
            session.claim_details = session.claim_details or {}
            session.claim_details["claim_type"] = "cashless"
            text_to_speech_func_english("Thank you. We've registered your claim as a Cashless claim.")
            return True

        # Invalid input handling for claim type
        if attempts < max_attempts:
            if not user_input:
                text_to_speech_func_english("Sorry, I didn't hear you. Please say it again.")
            else:
                text_to_speech_func_english("I didn't understand that. Please say 'OPD claim', 'Reimbursement claim', or 'Cashless claim'.")
        else:
            break

    # Max attempts reached for claim type
    text_to_speech_func_english("Sorry, I couldn't determine your claim type. Please try again later. I'm ending the call now.")
    session.transfer_reason = "Could not determine claim type"
    return False


#  ****************************Step 4 end here****************************************


# **********    Step 5 logic for verify_insured_details  ******************************
# def verify_insured_details(session):
#         """Verifies insured details and collects additional information if required."""

#     # 🔹 Step 1: Ask if the customer is the insured person
#     # session.policy_details = [selected_policy]
#     # session.mobile_number = selected_policy["mobile_number"]
#     # selected_name = selected_policy.get("name", "Customer")
  
#         insured_name =  session.policy_details[0].get("name", "Unknown")  # Placeholder for insured name (Fetch from actual policy later)
#         # 
#     # print("this is the yashnaibcihsdbihbv",insured_name)
#         text_to_speech_func_english(f"As per our record, the patient’s {insured_name} name is . Could you please confirm if you are the insured?")
    
    
#         # user_input = handle_user_input(duration=5).strip().lower()
    
#         # raw_input = "23123"
#         raw_input = handle_user_input(duration=5)
#         user_input = re.sub(r'[^a-zA-Z]', '', raw_input.strip()) if raw_input else ""
#         # user_input = "yes"

#         if user_input in ["yes", "i am", "confirm"]:
#             text_to_speech_func_english("Thank you for confirming. Let's proceed with the next step.")
#             session.claim_details["intimator_details"] = {
#                 "name": insured_name,
#                 "relationship": "Self"
#             }
#             return True  # Proceed with the next step

#         elif user_input in ["no", "not me"]:
#             # 🔹 Step 2: Ask for relationship
#             text_to_speech_func_english("Could you please let us know your relationship with the insured person?")
#             relationship = handle_user_input(duration=5).strip()
            
#             # 🔹 Step 3: Ask for Name
#             text_to_speech_func_english("Could you please confirm your Name?")
#             intimator_name = handle_user_input(duration=5).strip()
#             name_match = re.findall(r"[A-Za-z]+", intimator_name)
#             intimator_name = " ".join(name_match).title()
            
#             # 🔹 Step 4: Ask for Mobile Number
#             text_to_speech_func_english("Could you please confirm your Mobile Number?")
#             mobile_number = handle_user_input(duration=5).strip()
#             mobile_match = re.findall(r"\d+", mobile_number)
#             mobile_number = "".join(mobile_match)[-10:] if mobile_match else ""
            
#             # ✅ **Convert mobile number to digit-by-digit speech**
#             mobile_digits = " ".join(mobile_number)  # Converts "7206166156" → "Seven Two Zero Six One Six Six One Five Six"
#             text_to_speech_func_english(f"Your mobile number is: {mobile_digits}.")

#             # 🔹 Step 5: Ask for Email ID
#             text_to_speech_func_english("Could you please confirm your Email ID?")
#             email_id = handle_user_input(duration=5).strip()

#             # Store details in session
#             session.claim_details["intimator_details"] = {
#                 "name": intimator_name,
#                 "relationship": relationship,
#                 "mobile": mobile_number,
#                 "email": email_id
#             }
            
#             mobile_number=str(mobile_number)
#             mobile_number = ' '.join(mobile_number)  # This will make "8655904635" -> "8 6 5 5 9 0 4 6 3 5"
#             # 🔹 Step 6: Confirm the details with the customer
#             text_to_speech_func_english(
#                 f"Let me confirm the details you provided: "
#                 f"Your name is {intimator_name}, "
#                 f"Your relationship with the insured person is {relationship}, "
#                 f"Your Mobile Number is {mobile_number}, "
#                 f"Your Email Address is {email_id}. "
#                 "Are these details correct?"
#             )
# #  need to remove while true its not needed **************************************
#             for attempts in range(2):
#                 # confirm_input = handle_user_input(duration=5)
                
#                 raw_input = handle_user_input(duration=5)
#                 confirm_input = raw_input.strip().lower() if raw_input else ""
                
                
                
#                 if confirm_input in ["yes", "correct", "confirm"]:
#                     text_to_speech_func_english("Thank you for these details. Let's continue with Doctor’s name, Diagnosis details, and Claim amount.")
#                     return True  # Proceed with the flow
#                 elif confirm_input in ["no", "incorrect"]:
#                     text_to_speech_func_english("Sorry for your inconvenience. We have to get your details again.")
#                     return verify_insured_details(session)  # Restart the process
                
#                 elif not confirm_input:  # If the input is empty, restart the input prompt
#                     text_to_speech_func_english("Sorry, I didn't catch that. Please say 'Yes' or 'No'.")
#                     continue
#                 else:
#                     text_to_speech_func_english("Please say 'Yes' if the details are correct or 'No' if they need to be updated.")

#         else:
#             return False
#             # text_to_speech_func_english("I didn't understand that. Please say 'Yes' or 'No'.")



def verify_insured_details(session):
    """Verifies insured details and collects additional information if required."""
    insured_name = session.policy_details[0].get("name", "Unknown")

    # Step 1: Ask if the customer is the insured person
    text_to_speech_func_english(f"As per our records, the patient's name is {insured_name}. Could you please confirm if you are the insured person?")
    attempts = 0

    while attempts < 2:
        raw_input = handle_user_input(duration=5)
        
        # raw_input="yes"
        
        if raw_input is False:
            return False
        
        user_input = raw_input.strip().lower().replace(".", "").replace(",", "") if raw_input else ""
        
        # with st.chat_message("user"):
        #     st.write(user_input if user_input else "No input")

        if user_input in ["yes", "i am", "confirm"]:
            text_to_speech_func_english("Thank you for confirming. Let's proceed to the next step.")
            session.claim_details["intimator_details"] = {
                "name": insured_name,
                "relationship": "Self"
            }
            return True

        elif user_input in ["no", "not me"]:
            # Step 2: Ask for relationship
            text_to_speech_func_english("Could you please tell us your relationship with the insured person?")
            raw_relationship = handle_user_input(duration=5)
            
            # raw_relationship = "Brother"
            
            if raw_relationship is False:
                return False
            relationship = re.sub(r"[,\<\./\|\?]", "", raw_relationship.strip()) if raw_relationship else ""
            
            # with st.chat_message("user"):
            #     st.write(relationship)
            text_to_speech_func_english(f"Your relationship with the insured is: {relationship}")
            
            # Step 3: Ask for Name
            text_to_speech_func_english("Could you please tell us your name?")
            raw_intimator_name = handle_user_input(duration=5)
            
            # raw_intimator_name = "Yash"
            
            if raw_intimator_name is False:
                return False
            
            intimator_name = re.sub(r"[,\<\./\|\?]", "", raw_intimator_name.strip()) if raw_intimator_name else ""
            
            # with st.chat_message("user"):
            #     st.write(intimator_name)
                    
            # Step 4: Ask for Mobile Number
            # text_to_speech_func_english("Could you please provide your mobile number?")
            # mobile_number = handle_user_input(duration=5)
            # # mobile_number = "jknjnjnjn"
            
            # if mobile_number is False:
            #     return False
            
            # mobile_match = re.findall(r"\d+", mobile_number)
            # mobile_number = "".join(mobile_match)[-10:] if mobile_match else ""

            # mobile_digits = " ".join(mobile_number)
            # with st.chat_message("user"):
            #     st.write(mobile_digits)
                    
            # text_to_speech_func_english(f"Your mobile number is: {mobile_digits}.")
            text_to_speech_func_english("Could you please provide your mobile number?")
            retry_count = 0
            max_retries = 2
            valid_number = False

            while retry_count <= max_retries and not valid_number:
              mobile_number = handle_user_input(duration=5)
            #   mobile_number = '7206166156'
              if mobile_number is False:
               return False
    
              mobile_match = re.findall(r"\d+", mobile_number)
              mobile_number = "".join(mobile_match)[-10:] if mobile_match else ""
    
            # Check if we have exactly 10 digits
              if len(mobile_number) == 10:
                valid_number = True
              else:
                retry_count += 1
                if retry_count <= max_retries:
                    text_to_speech_func_english(f"That doesn't appear to be a valid 10-digit number. Please try again. You have {max_retries - retry_count + 1} attempts remaining.")
                else:
                    text_to_speech_func_english("Sorry, you've exceeded the maximum number of attempts.")
                    return False

            # If we got here, we have a valid 10-digit number
            mobile_digits = " ".join(mobile_number)
            # with st.chat_message("user"):
            #     st.write(mobile_digits)
    
            # text_to_speech_func_english(f"Your mobile number is: {mobile_digits}.")
            
            # Step 5: Ask for Email ID
            
            text_to_speech_func_english("Could you please provide your email address?")
            email_id = handle_user_input(duration=5)
            # email_id="yashshddfsd121"
            
            
            def normalize_email(speech_input: str) -> str:
                replacements = {
                    " at the rate ": "@",
                    " at ": "@",
                    " dot ": ".",
                    " dotcom": ".com",
                    " dot com": ".com",
                    " underscore ": "_",
                    " dash ": "-",
                    " space ": "",
                    " comma ": ",",
                }
                for spoken, symbol in replacements.items():
                    speech_input = speech_input.replace(spoken, symbol)
                return speech_input.strip()
            
            email_id = normalize_email(email_id)
            
            # with st.chat_message("user"):
            #     st.write(email_id)
                    
            # Store details
            session.claim_details["intimator_details"] = {
                "name": intimator_name,
                "relationship": relationship,
                "mobile": mobile_number,
                "email": email_id
            }

            mobile_number = ' '.join(mobile_number)
            
            # Step 6: Confirm the details
            text_to_speech_func_english(
                f"Let me confirm the details you provided: "
                f"Your name is {intimator_name}, "
                f"Your relationship with the insured is: {relationship}, "
                f"Your mobile number is: {mobile_number}, "
                f"and your email address is: {email_id}. "
                "Are all these details correct?"
            )

            confirm_attempts = 0
            while confirm_attempts < 2:
                raw_input = handle_user_input(duration=5)
                
                if raw_input is False:
                    return False
               
                confirm_input = raw_input.strip().lower().replace(".", "").replace(",", "") if raw_input else ""
                
                # with st.chat_message("user"):
                #     st.write(confirm_input)
                    
                if confirm_input in ["yes", "correct", "confirm"]:
                    text_to_speech_func_english("Thank you for providing the information. Let's now proceed with the doctor's name, diagnosis details and claim amount.")
                    return True
                elif confirm_input in ["no", "incorrect"]:
                    text_to_speech_func_english("We apologize for the inconvenience. We'll need to collect your information again.")
                    return verify_insured_details(session)
                else:
                    confirm_attempts += 1
                    if confirm_attempts < 2:
                        text_to_speech_func_english("Please say 'Yes' if the information is correct or 'No' if it needs to be updated.")
                    else:
                        text_to_speech_func_english("Sorry, you've exceeded the maximum number of attempts.")
                        return False

        else:
            attempts += 1
            if attempts < 2:
                text_to_speech_func_english("Sorry, I didn't understand that. Could you please say it again?")
            else:
                text_to_speech_func_english("I'm sorry, I couldn't understand your response. Please try again later. I'm ending the call now..")
                
                return False
# *******************Step 5 end here **************************************************


def ask_for_mobile_number(session: ClaimSession):
    """
    Ask the user for their 10-digit mobile number and validate it.
    If valid, store it in the session; otherwise, transfer to an agent.
    """
    try:
        for attempt in range(2):  # Allow 2 attempts
            message = "The mobile number you called from is not your registered mobile number. Please share your 10-digit registered mobile number?"
            text_to_speech_func_english(message)
            # st.write(message)

            user_input = handle_user_input(duration=10)
            if user_input is False:
                session.transfer_reason = "Exceeded input limit"
                return redirecting_to_agent(session.transfer_reason)

            cleaned_number = re.sub(r"[^\d]", "", user_input)  # Keep only digits

            if len(cleaned_number) == 10 and validate_mobile_number(cleaned_number):
                session.mobile_number = cleaned_number
                
                print("this is session mobile ",  session.mobile_number)
                
                text_to_speech_func_english("Thank you. I am now validating the information you provided. Please wait a moment.")
                st.write("Thank you. I am now validating the information you provided. Please wait a moment.")

                # if not get_policy_details(session):
                #     print(session.__dict__)
                #     return redirecting_to_agent(session.transfer_reason)
                return True  # Successfully validated

            else:
                if attempt == 0:
                    message = "I'm sorry, the information you shared does not match our records. Can you please try again?"
                else:
                    session.transfer_reason = "Maximum authentication attempts exceeded"
                    message = "Sorry, we are unable to verify your information. Transferring you to an agent."
                
                text_to_speech_func_english(message)
                st.write(message)

                if session.transfer_reason:
                    return redirecting_to_agent(session.transfer_reason)
                    
        return False  # If validation fails

    except Exception as e:
        session.transfer_reason = f"Mobile number validation error: {str(e)}"
        message = "I'm sorry, due to a system issue, I'm connecting you to an agent who can assist you further. Please wait."
        text_to_speech_func_english(message)
        return redirecting_to_agent(session.transfer_reason)




    
def text_to_speech_func_english(message):
    text_to_speech_azure_streamlit(input_text=message)
    with st.chat_message("assistant"):
        st.write(message)
    play_audio()
    time.sleep(calculate_length_of_audio())  # handle time dynamically


# **********            Step 6 for hospital detials and patient details ******************************************
import requests
import json

from word2number import w2n  # Install this package if not already: pip install word2number

def extract_amount_from_input(text):
    # Try to extract direct digits first
    digit_match = re.findall(r"\d+", text)
    if digit_match:
        return "".join(digit_match)

    # Try to convert number words to digits
    try:
        amount = w2n.word_to_num(text.lower())
        return str(amount)
    except:
        return None




import difflib

import re

def normalize_name(name):
    """Remove punctuation and convert to lowercase for better matching."""
    return re.sub(r"[^\w\s]", "", name).lower()

# def fetch_hospital_and_patient_details(session):
#     """Collects doctor details, diagnosis, claim amount, and hospital information."""

#     if not hasattr(session, "claim_details") or session.claim_details is None:
#         session.claim_details = {}

#     # Step 1: Ask for Doctor's Name
#     text_to_speech_func_english("Could you please share the name of the doctor who is treating you or consulting you at the hospital?")
#     # doctor_name = handle_user_input(duration=5).strip()
#     doctor_name = "mohiy"
    
#     # Step 2: Ask for Diagnosis Details
#     text_to_speech_func_english("Could you kindly share the diagnosis details or the medical condition that has been diagnosed?")
#     # diagnosis_details = handle_user_input(duration=5).strip()
#     diagnosis_details = "cancer"


# # i need to create logic for cashless and reimbursement for amount **************************************** 
#     import re
#     # Step 3: Ask for Claim Amount
#     text_to_speech_func_english("Thank you for providing those details. Now, could you please let me know the estimated claim amount?")
#     # claim_amount = handle_user_input(duration=5).strip().replace(",", "").lower() 
#     claim_amount=""
     
#     if isinstance(claim_amount, str):
#         claim_amount = claim_amount.strip().replace(",", "").lower()
#     else:
#         claim_amount = ""
#     if not claim_amount:
#         # text_to_speech_func_english(" we will set a default claim amount of 25000 rupees.")
#         claim_amount = "25000"
        
    
#     # Extract numbers using regex
#     numbers = re.findall(r'\d+', claim_amount)


#     if numbers:
#     # If number is found, take the first number
#       claim_amount = numbers[0]
    
#     else:
#     # If user says no amount or unclear text, default to 25000
#       claim_amount = "25000"


# #  in cashless if user give amount then we need to announce otherwise we dont need to announce the amount because if default 25000********  
#     # Confirm Details with Customer
#     text_to_speech_func_english(
#         f"Let me confirm the details you provided: "
#         f"Your doctor’s name is {doctor_name}, "
#         f"Details of your diagnosis are {diagnosis_details}, "
#         f"Amount asked for claim is {claim_amount}. "
#         "Are these details correct?"
#     )

# #  need to remove ********************************
#     while True:
#         # confirm_input = handle_user_input(duration=5).strip()
#         confirm_input = "yes"
#         if confirm_input in ["yes", "correct", "confirm"]:
#             text_to_speech_func_english("Thank you for the details. Let’s continue with Hospital details.")
#             break
#         elif confirm_input in ["no", "incorrect"]:
#             text_to_speech_func_english("Sorry for your inconvenience. We have to get your details again.")
#             return fetch_hospital_and_patient_details(session)
#         else:
#             text_to_speech_func_english("Please say 'Yes' if the details are correct or 'No' if they need to be updated.")

#     # retry_count = 0
#     # while retry_count < 2:
#     for attempt in range(2):   
#         # Step 4: Ask for Hospital Pin Code
        
#         #  need to provide regex for extract the pincode no if not then give retry ***************************************
        
#         text_to_speech_func_english("Could you also please share the pin code of this hospital?")
#         # hospital_pin_code =  handle_user_input(duration=5).strip()
#         # hospital_pin_code =  handle_user_input(duration=5).strip()
#         hospital_pin_code = "127021"
        
#         if not re.match(r"^\d{6}$", hospital_pin_code):
#           text_to_speech_func_english(f"Invalid pin code entered. Please provide a valid 6-digit pin code. Attempt {retry_count + 1} of 2.")
#           retry_count += 1
#           continue
#         hospital_list = fetch_hospitals_by_pincode(hospital_pin_code)or []
        
#         if not hospital_list:
#           text_to_speech_func_english(f"No hospitals found for the entered pin code. Attempt {retry_count + 1} of 2.")
#           retry_count += 1
#           continue
      
#         # Step 5: Ask for Hospital Name
#         text_to_speech_func_english("Could you kindly share the name of the hospital where patient is seeking treatment?")
#         # hospital_name_input = handle_user_input(duration=5).strip()
#         hospital_name_input = "namkin hospital"
        
#          # Validate PIN code using regex (must be a 6-digit number)
       

#         # Normalize user input
#         normalized_input = normalize_name(hospital_name_input)

        

#         normalized_names_map = {
#             normalize_name(hospital.get("HospitalName", "")): hospital
#             for hospital in hospital_list
#         }

#         close_matches = difflib.get_close_matches(normalized_input, normalized_names_map.keys(), n=1, cutoff=0.6)

#         matched_hospital = None
#         if close_matches:
#             best_match_key = close_matches[0]
#             hospital = normalized_names_map[best_match_key]
#             matched_hospital = {
#                 "name": hospital.get("HospitalName", "Unknown"),
#                 "location": hospital.get("Address1", "Unknown"),
#                 "address2": hospital.get("Address2", ""),
#                 "city": hospital.get("City", "Unknown"),
#                 "district": hospital.get("District", "Unknown"),
#                 "state": hospital.get("State", "Unknown"),
#                 "country": hospital.get("Country", "Unknown"),
#                 "pincode": hospital.get("Pincode", "Unknown"),
#                 "city_id": hospital.get("CityID"),
#                 "area_id": hospital.get("AreaID"),
#                 "district_id": hospital.get("DistrictID"),
#                 "state_id": hospital.get("StateID"),
#                 "contact_person": hospital.get("ContactPerson", "Unknown"),
#                 "phone": hospital.get("PhoneNo", "Unknown"),
#                 "mobile": hospital.get("MobileNo", "Unknown"),
#                 "email": hospital.get("EmailID", "Unknown"),
#                 "network": hospital.get("lstNetwork", "Unknown"),
#                 "unique_id": hospital.get("UniqueId"),
#                 "hospital_id": hospital.get("HospitalId"),
#                 "status": "confirmed"
#             }

#         if matched_hospital:
#             text_to_speech_func_english(
#                 f"We found a match: {matched_hospital['name']} at {matched_hospital['location']}. Proceeding with this hospital."
#             )
#             session.claim_details["hospital_details"] = matched_hospital
#             break
#         else:
#             text_to_speech_func_english(
#                 "We couldn’t find this hospital name for the given pin code. "
#                 "Would you still like to proceed with your hospital details for the claim?"
#             )

#             # user_input = handle_user_input(duration=4).strip()
#             user_input = "yes"
#             if user_input in ["yes", "okay", "proceed"]:
#                 text_to_speech_func_english("Proceeding with your provided hospital details.")
#                 session.claim_details["hospital_details"] = {
#                     "name": hospital_name_input,
#                     "pincode": hospital_pin_code,
#                     "location": "Unknown",
#                     "address2": "",
#                     "city": "Unknown",
#                     "district": "Unknown",
#                     "state": "Unknown",
#                     "country": "Unknown",
#                     "city_id": None,
#                     "area_id": None,
#                     "district_id": None,
#                     "state_id": None,
#                     "contact_person": "Pending",
#                     "phone": "Pending",
#                     "mobile": "Pending",
#                     "email": "Pending",
#                     "network": "Unknown",
#                     "unique_id": None,
#                     "hospital_id": 0,
#                     "status": "user_confirmed_unlisted"
#                 }
#                 break
#             elif user_input in ["no", "cancel"]:
#                 retry_count += 1
#                 if retry_count < 2:
#                     text_to_speech_func_english("Okay, let’s try entering the hospital details again.")
#                 else:
#                     text_to_speech_func_english("We could not proceed further. Please try again later or contact support.")
#                     return False
#             else:
#                 text_to_speech_func_english("Please say 'Yes' to proceed or 'No' to cancel.")

#     # Save other details
#     session.claim_details.update({
#         "doctor_name": doctor_name,
#         "diagnosis": diagnosis_details,
#         "claim_amount": claim_amount
#     })

#     return True

import re
import difflib

# def fetch_hospital_and_patient_details(session):
#     """Collects doctor details, diagnosis, claim amount, and hospital information."""

#     if not hasattr(session, "claim_details") or session.claim_details is None:
#         session.claim_details = {}

#     # Step 1: Ask for Doctor's Name
#     text_to_speech_func_english("Could you please share the name of the doctor who is treating you or consulting you at the hospital?")
#     # doctor_name = "mohiy"  
#     doctor_name=handle_user_input(duration=5).strip()
    
#     # Step 2: Ask for Diagnosis Details
#     text_to_speech_func_english("Could you kindly share the diagnosis details or the medical condition that has been diagnosed?")
#     # diagnosis_details = "cancer" 
#     diagnosis_details =handle_user_input(duration=5).strip()
#     import re
#     # Step 3: Ask for Claim Amount
#     text_to_speech_func_english("Thank you for providing those details. Now, could you please let me know the estimated claim amount?")
#     claim_amount = handle_user_input(duration=5).strip().replace(",", "").lower() 
    
    
#     # claim_amount='85858'
     
#     if isinstance(claim_amount, str):
#         claim_amount = claim_amount.strip().replace(",", "").lower()
#     else:
#         claim_amount = ""
#     if not claim_amount:
#         # text_to_speech_func_english(" we will set a default claim amount of 25000 rupees.")
#         claim_amount = "25000"
        
    
#     # Extract numbers using regex
#     numbers = re.findall(r'\d+', claim_amount)
   

#     if numbers:
#     # If number is found, take the first number
#       claim_amount = numbers[0]
#       text_to_speech_func_english(
#         f"Let me confirm the details you provided: "
#         f"Your doctor’s name is {doctor_name}, "
#         f"Details of your diagnosis are {diagnosis_details}, "
#         f"Amount asked for claim is {claim_amount}. "
#         "Are these details correct?"
#        )
      
    
#     else:
#     # If user says no amount or unclear text, default to 25000
#       claim_amount = "25000"
#       text_to_speech_func_english(
#         f"Let me confirm the details you provided: "
#         f"Your doctor’s name is {doctor_name}, "
#         f"Details of your diagnosis are {diagnosis_details}"
#         "Are these details correct?"
#        )

   
# #  in cashless if user give amount then we need to announce otherwise we dont need to announce the amount because if default 25000********  
#     # Confirm Details with Customer
    
    
    
#     raw_input = handle_user_input(duration=5)
    
    
#     # raw_input = "yes231"
    
#     confirm_input = re.sub(r'[^a-zA-Z]', '', raw_input.strip()) if raw_input else ""
#     if confirm_input in ["yes", "correct", "confirm"]:
#             text_to_speech_func_english("Thank you for the details. Let’s continue with Hospital details.")
            
#     elif confirm_input in ["no", "incorrect"]:
#             text_to_speech_func_english("Sorry for your inconvenience. We have to get your details again.")
#             return fetch_hospital_and_patient_details(session)
#     else:
#             text_to_speech_func_english("Please say 'Yes' if the details are correct or 'No' if they need to be updated.")

#     # confirm_input = "yes"  # Replace with: handle_user_input(duration=5).strip().lower()
#     # if confirm_input not in ["yes", "correct", "confirm"]:
#     #     text_to_speech_func_english("Sorry for your inconvenience. We will collect your details again.")
#     #     return fetch_hospital_and_patient_details(session)

#     # Retry for PIN Code and Hospital Details
#     for attempt in range(2):
#         text_to_speech_func_english("Could you please share the pin code of this hospital?")
#         # hospital_pin_code = "127021"  # Replace with: handle_user_input(duration=5).strip()
#         hospital_pin_code1 = handle_user_input(duration=8)
        
#         # hospital_pin_code1 = "127021!"
#         hospital_pin_code = re.sub(r"[^\d]", '', hospital_pin_code1.strip()) if hospital_pin_code1 else ""
        
#         if not hospital_pin_code:
#            text_to_speech_func_english("No input received. Unable to proceed with the claim.")
#            return False
        
        
#          # Ensure hospital_pin_code is a string
#         if isinstance(hospital_pin_code, bool):
#            text_to_speech_func_english("Invalid input. Please provide a valid 6-digit pin code.")
#            continue
       
#         hospital_pin_code = str(hospital_pin_code).strip()
        
#         if not re.match(r"^\d{6}$", hospital_pin_code):
#             text_to_speech_func_english(f"Invalid pin code entered. Please provide a valid 6-digit pin code. Attempt {attempt + 1} of 2.")
#             continue

#         hospital_list = fetch_hospitals_by_pincode(hospital_pin_code) or []

#         if not hospital_list:
#             text_to_speech_func_english(f"No hospitals found for the entered pin code. Attempt {attempt + 1} of 2.")
#             continue

#         # Step 5: Ask for Hospital Name
#         text_to_speech_func_english("Could you kindly share the name of the hospital where the patient is seeking treatment?")
#         # hospital_name_input = "rohtak pgi" 
#         hospital_name_input =handle_user_input(duration=5).strip()
#     #    ************************************************************


#     # **************************************************************
#         normalized_input = normalize_name(hospital_name_input)
#         normalized_names_map = {
#             normalize_name(hospital.get("HospitalName", "")): hospital
#             for hospital in hospital_list
#         }

#         close_matches = difflib.get_close_matches(normalized_input, normalized_names_map.keys(), n=1, cutoff=0.6)
#         matched_hospital = None

#         if close_matches:
#             best_match_key = close_matches[0]
#             hospital = normalized_names_map[best_match_key]
#             matched_hospital = {
#                 "name": hospital.get("HospitalName", "Unknown"),
#                 "location": hospital.get("Address1", "Unknown"),
#                 "address2": hospital.get("Address2", ""),
#                 "city": hospital.get("City", "Unknown"),
#                 "district": hospital.get("District", "Unknown"),
#                 "state": hospital.get("State", "Unknown"),
#                 "country": hospital.get("Country", "Unknown"),
#                 "pincode": hospital.get("Pincode", "Unknown"),
#                 "city_id": hospital.get("CityID"),
#                 "area_id": hospital.get("AreaID"),
#                 "district_id": hospital.get("DistrictID"),
#                 "state_id": hospital.get("StateID"),
#                 "contact_person": hospital.get("ContactPerson", "Unknown"),
#                 "phone": hospital.get("PhoneNo", "Unknown"),
#                 "mobile": hospital.get("MobileNo", "Unknown"),
#                 "email": hospital.get("EmailID", "Unknown"),
#                 "network": hospital.get("lstNetwork", "Unknown"),
#                 "unique_id": hospital.get("UniqueId"),
#                 "hospital_id": hospital.get("HospitalId"),
#                 "status": "confirmed"
#             }
            
#         if matched_hospital:
#             text_to_speech_func_english(
#                 f"We found a match: {matched_hospital['name']} at {matched_hospital['location']}. Proceeding with this hospital."
#             )
#             session.claim_details["hospital_details"] = matched_hospital
#             break
#         else:
#             text_to_speech_func_english(
#                 "We couldn’t find this hospital name for the given pin code. "
#                 "Would you still like to proceed with your hospital details for the claim?"
#             )
            
    
#             # user_input = handle_user_input(duration=4).strip()# Example input
#             raw_input = handle_user_input(duration=1)
#             user_input = raw_input.strip().lower() if raw_input else ""
            
#             if user_input in ["yes", "okay", "proceed"]:
#                 text_to_speech_func_english("Proceeding with your provided hospital details.")
#                 session.claim_details["hospital_details"] = {
#                     "name": hospital_name_input,
#                     "pincode": hospital_pin_code,
#                     "location": "Unknown",
#                     "address2": "",
#                     "city": "Unknown",
#                     "district": "Unknown",
#                     "state": "Unknown",
#                     "country": "Unknown",
#                     "city_id": None,
#                     "area_id": None,
#                     "district_id": None,
#                     "state_id": None,
#                     "contact_person": "Pending",
#                     "phone": "Pending",
#                     "mobile": "Pending",
#                     "email": "Pending",
#                     "network": "Unknown",
#                     "unique_id": None,
#                     "hospital_id": 0,
#                     "status": "user_confirmed_unlisted"
#                 }
#                 break
#             elif user_input in ["no", "cancel"]:
#                 retry_count += 1
#                 if retry_count < 2:
#                     text_to_speech_func_english("Okay, let’s try entering the hospital details again.")
#                 else:
#                     text_to_speech_func_english("We could not proceed further. Please try again later or contact support.")
#                     return False
                
                

#     else:
#         text_to_speech_func_english("We could not proceed further. Please try again later or contact support.")
#         return False

#     # Save details in session
#     session.claim_details.update({
#         "doctor_name": doctor_name,
#         "diagnosis": diagnosis_details,
#         "claim_amount": claim_amount
#     })

#     text_to_speech_func_english("Thank you for providing all the necessary information. Let's proceed with the claim.")
#     return True






def fetch_hospital_and_patient_details(session):
        # Debug: Check if claim_type exists in session
    print("Current session.claim_details:", session.claim_details)  # Debug print
    print("Claim type in session:", session.claim_details.get("claim_type"))  # Debug print

    """Collects doctor details, diagnosis, claim amount, and hospital information."""

    if not hasattr(session, "claim_details") or session.claim_details is None:
        session.claim_details = {}

    # Step 1: Ask for Doctor's Name
    text_to_speech_func_english("Could you please share the name of the doctor who is treating you or consulting you at the hospital?")
    raw_doctor_name = handle_user_input(duration=5)
    # raw_doctor_name ="mohit"
    
    if raw_doctor_name is False:
        return False
        
    doctor_name = re.sub(r"[,\<\./\|\?]", "", raw_doctor_name.strip()) if raw_doctor_name else ""
    
    # with st.chat_message("user"):
    #     st.write(doctor_name)

    # Step 2: Ask for Diagnosis Details
    text_to_speech_func_english("Could you kindly share the diagnosis details or the medical condition that has been diagnosed?")
    raw_diagnosis_details = handle_user_input(duration=5)
    # raw_diagnosis_details="cancer"
    
    if raw_diagnosis_details is False:
        return False
    
    diagnosis_details = re.sub(r"[,\<\./\|\?]", "", raw_diagnosis_details.strip()) if raw_diagnosis_details else ""
    
    # with st.chat_message("user"):
    #     st.write(diagnosis_details)

    # Step 3: Ask for Claim Amount
    
    if session.claim_details.get("claim_type", "").lower() == "reimbursement":
        text_to_speech_func_english("Thank you for providing those details. Now, could you please let me know the estimated claim amount?")
        # For reimbursement, we strictly require the claim amount with 2 attempts
        # text_to_speech_func_english("You have selected reimbursement. Please provide the estimated claim amount in rupees.")
        
        claim_amount = None
        for attempt in range(2):
            raw_claim_amount = handle_user_input(duration=6)
            
            if raw_claim_amount is False:
                return False
                
            if isinstance(raw_claim_amount, str):
                # Clean the input and look for numbers
                cleaned_input = raw_claim_amount.strip().replace(",", "").lower()
                numbers = re.findall(r'\d+', cleaned_input)
                
                if numbers:
                    claim_amount = numbers[0]
                    break  # valid numeric input received
                else:
                    # Handle non-numeric responses ("I don't know", etc.)
                    if attempt == 0:
                        text_to_speech_func_english("For reimbursement claims, we need an estimated amount. Please say the amount in numbers, like '50000 rupees'.")
                    else:
                        text_to_speech_func_english("Sorry, I still didn't get a valid amount. Since this is a reimbursement claim, I'll need to transfer you to an agent for assistance.")
                        session.transfer_reason = "Could not get claim amount for reimbursement"
                        return False
            else:
                # No input received
                if attempt == 0:
                    text_to_speech_func_english("I didn't hear the claim amount. Please say the estimated amount in rupees.")
                else:
                    text_to_speech_func_english("Sorry, I didn't receive any claim amount. Since this is a reimbursement claim, I'll need to transfer you to an agent.")
                    session.transfer_reason = "No claim amount provided for reimbursement"
                    return False
        
        # Confirm all details including claim amount
        text_to_speech_func_english(
            f"Let me confirm the details you provided: "
            f"Your doctor's name is {doctor_name}, "
            f"Details of your diagnosis are {diagnosis_details}, "
            f"Amount asked for claim is {claim_amount} rupees. "
            "Are these details correct?"
        )
    else:
        # For non-reimbursement claims (cashless), keep the original flow
        text_to_speech_func_english("Thank you for providing those details. Now, could you please let me know the estimated claim amount?")
        raw_claim_amount = handle_user_input(duration=5)
        
        if raw_claim_amount is False:
            return False
        
        claim_amount = re.sub(r"[,\<\./\|\?]", "", raw_claim_amount.strip().replace(",", "").lower()) if raw_claim_amount else ""
        
        if isinstance(claim_amount, str):
            claim_amount = claim_amount.strip().replace(",", "").lower()
        else:
            claim_amount = ""
            
        if not claim_amount:
            claim_amount = "25000"

        numbers = re.findall(r'\d+', claim_amount)

        if numbers:
            claim_amount = numbers[0]
            text_to_speech_func_english(
                f"Let me confirm the details you provided: "
                f"Your doctor's name is {doctor_name}, "
                f"Details of your diagnosis are {diagnosis_details}, "
                f"Amount asked for claim is {claim_amount} rupees. "
                "Are these details correct?"
            )
        else:
            claim_amount = "25000"
            text_to_speech_func_english(
                f"Let me confirm the details you provided: "
                f"Your doctor's name is {doctor_name}, "
                f"Details of your diagnosis are {diagnosis_details}. "
                "Are these details correct?"
            )


    # Confirmation with retry logic
    attempts = 0
    while attempts < 2:
        raw_input = handle_user_input(duration=5)
        # raw_input="yes"
        
        if raw_input is False:
            return False 
        
        confirm_input = raw_input.strip().lower().replace(".", "").replace(",", "") if raw_input else ""
        
        # with st.chat_message("user"):
        #     st.write(confirm_input)
            
        if confirm_input in ["yes", "correct", "confirm", "yeah", "yep", "yup", "sure"]:
            text_to_speech_func_english("Thank you for the details. Let's continue with Hospital details.")
            break
        elif confirm_input in ["no", "incorrect", "nope", "nah"]:
            text_to_speech_func_english("Sorry for your inconvenience. We have to get your details again.")
            return fetch_hospital_and_patient_details(session)
        else:
            attempts += 1
            if attempts < 2:
                text_to_speech_func_english("Sorry, I didn't understand that. Could you please say 'yes' if the details are correct or 'no' if they need to be updated?")
            else:
                text_to_speech_func_english("We could not proceed further. Please try again later.")
                return False

    # Hospital details with retry logic
    retry_count = 0
    while retry_count < 2:
        # Step 4: Ask for Hospital Pin Code
        text_to_speech_func_english("Could you please share the pin code of this hospital?")
        raw_hospital_pin_code = handle_user_input(duration=8)
        # raw_hospital_pin_code='127021'
        
        if raw_hospital_pin_code is False:
            return False
            
        hospital_pin_code = re.sub(r"[^\d]", '', raw_hospital_pin_code.strip()) if raw_hospital_pin_code else ""
        
        if not hospital_pin_code:
            text_to_speech_func_english("No input received. Please provide a valid 6-digit pin code.")
            retry_count += 1
            continue
        
        if not re.match(r"^\d{6}$", hospital_pin_code):
            text_to_speech_func_english(f"Invalid pin code entered. Please provide a valid 6-digit pin code. Attempt {retry_count + 1} of 2.")
            retry_count += 1
            continue

        hospital_list = fetch_hospitals_by_pincode(hospital_pin_code) or []

        if not hospital_list:
            text_to_speech_func_english(f"No hospitals found for the entered pin code. Attempt {retry_count + 1} of 2.")
            retry_count += 1
            continue

        # Step 5: Ask for Hospital Name
        text_to_speech_func_english("Could you kindly share the name of the hospital where the patient is seeking treatment?")
        raw_hospital_name_input = handle_user_input(duration=5)
        # raw_hospital_name_input= "dddddddd hospital"
        
        if raw_hospital_name_input is False:
            return False
            
        hospital_name_input = raw_hospital_name_input.strip()
        
        normalized_input = normalize_name(hospital_name_input)
        normalized_names_map = {
            normalize_name(hospital.get("HospitalName", "")): hospital
            for hospital in hospital_list
        }

        close_matches = difflib.get_close_matches(normalized_input, normalized_names_map.keys(), n=1, cutoff=0.8)
        matched_hospital = None

        if close_matches:
            best_match_key = close_matches[0]
            hospital = normalized_names_map[best_match_key]
            matched_hospital = {
                
                "name": hospital.get("HospitalName", "Unknown"),
                "location": hospital.get("Address1", "Unknown"),
                "address2": hospital.get("Address2", ""),
                "city": hospital.get("City", "Unknown"),
                "district": hospital.get("District", "Unknown"),
                "state": hospital.get("State", "Unknown"),
                "country": hospital.get("Country", "Unknown"),
                "pincode": hospital.get("Pincode", "Unknown"),
                "city_id": hospital.get("CityID"),
                "area_id": hospital.get("AreaID"),
                "district_id": hospital.get("DistrictID"),
                "state_id": hospital.get("StateID"),
                "contact_person": hospital.get("ContactPerson", "Unknown"),
                "phone": hospital.get("PhoneNo", "Unknown"),
                "mobile": hospital.get("MobileNo", "Unknown"),
                "email": hospital.get("EmailID", "Unknown"),
                "network": hospital.get("lstNetwork", "Unknown"),
                "unique_id": hospital.get("UniqueId"),
                "hospital_id": hospital.get("HospitalId"),
                "status": "confirmed"
            }
            
            # Confirm matched hospital
            text_to_speech_func_english(
                f"We found a match: {matched_hospital['name']} at {matched_hospital['location']}. "
                "Please confirm if this is the correct hospital."
            )
            
            # Get confirmation with retry logic
            confirm_attempts = 0
            while confirm_attempts < 2:
                raw_confirm = handle_user_input(duration=5)
                # raw_confirm="yes"
                
                if raw_confirm is False:
                    return False
                    
                confirm_input = raw_confirm.strip().lower().replace(".", "").replace(",", "") if raw_confirm else ""
                
                if confirm_input in ["yes", "correct", "confirm", "yeah", "yep"]:
                    session.claim_details["hospital_details"] = matched_hospital
                    break
                elif confirm_input in ["no", "incorrect", "nope", "nah"]:
                    text_to_speech_func_english("Let me try to find another match.")
                    matched_hospital = None
                    break
                else:
                    confirm_attempts += 1
                    if confirm_attempts < 2:
                        text_to_speech_func_english("Sorry, I didn't understand. Please say 'yes' if this is the correct hospital or 'no' if it's not.")
                    else:
                        text_to_speech_func_english("We'll proceed with the hospital details you provided earlier.")
                        matched_hospital = None
                        break
            
            if matched_hospital:
                break

        if not matched_hospital:
            text_to_speech_func_english(
                "We couldn't find this hospital name for the given pin code. "
                "Would you still like to proceed with your hospital details for the claim?"
            )
            
            raw_user_input = handle_user_input(duration=4)
            # raw_user_input='yes'
            user_input = raw_user_input.strip().lower() if raw_user_input else ""
            
            if user_input in ["yes", "proceed", "yeah", "yep"]:
                text_to_speech_func_english("Proceeding with your provided hospital details.")
                session.claim_details["hospital_details"] = {
                    
                    "name": hospital_name_input,
                    "pincode": hospital_pin_code,
                    "location": "Unknown",
                    "address2": "",
                    "city": "Unknown",
                    "district": "Unknown",
                    "state": "Unknown",
                    "country": "Unknown",
                    "city_id": None,
                    "area_id": None,
                    "district_id": None,
                    "state_id": None,
                    "contact_person": "Pending",
                    "phone": "Pending",
                    "mobile": "Pending",
                    "email": "Pending",
                    "network": "Unknown",
                    "unique_id": None,
                    "hospital_id": 0,
                    "status": "user_confirmed_unlisted"
                }
                break
            elif user_input in ["no", "cancel", "nope"]:
                retry_count += 1
                if retry_count < 2:
                    text_to_speech_func_english("Okay, let's try entering the hospital details again.")
                else:
                    text_to_speech_func_english("We could not proceed further. Please try again later.")
                    return False
            else:
                retry_count += 1
                if retry_count < 2:
                    text_to_speech_func_english("Please say 'yes' to proceed or 'no' to try again.")
                else:
                    text_to_speech_func_english("We could not proceed further. Please try again later .")
                    return False

    # Save details in session
    session.claim_details.update({
        "doctor_name": doctor_name,
        "diagnosis": diagnosis_details,
        "claim_amount": claim_amount
    })

    # text_to_speech_func_english("Thank you for providing all the necessary information. Let's proceed with the claim.")
    return True




# def fetch_hospital_and_patient_details(session):
#     # Debug: Check if claim_type exists in session
#     print("Current session.claim_details:", session.claim_details)  # Debug print
#     print("Claim type in session:", session.claim_details.get("claim_type"))  # Debug print

#     """Collects doctor details, diagnosis, claim amount, and hospital information."""

#     if not hasattr(session, "claim_details") or session.claim_details is None:
#         session.claim_details = {}

#     # Step 1: Ask for Doctor's Name
#     text_to_speech_func_english("Could you please share the name of the doctor who is treating you or consulting you at the hospital?")
#     # raw_doctor_name = handle_user_input(duration=5)
#     raw_doctor_name ="mohit"
    
#     if raw_doctor_name is False:
#         return False
        
#     doctor_name = re.sub(r"[,\<\./\|\?]", "", raw_doctor_name.strip()) if raw_doctor_name else ""
    
#     # Step 2: Ask for Diagnosis Details
#     text_to_speech_func_english("Could you kindly share the diagnosis details or the medical condition that has been diagnosed?")
#     # raw_diagnosis_details = handle_user_input(duration=5)
#     raw_diagnosis_details="cancer"
    
#     if raw_diagnosis_details is False:
#         return False
    
#     diagnosis_details = re.sub(r"[,\<\./\|\?]", "", raw_diagnosis_details.strip()) if raw_diagnosis_details else ""

#     # Handle claim amount differently based on claim type
#     if session.claim_details.get("claim_type", "").lower() == "reimbursement":
#         # For reimbursement, we require the claim amount with 2 attempts
#         text_to_speech_func_english("You have selected reimbursement. Please provide the estimated claim amount.")
        
#         claim_amount = None
#         for attempt in range(2):
#             raw_claim_amount = handle_user_input(duration=6)
            
#             if raw_claim_amount is False:
#                 return False
                
#             if isinstance(raw_claim_amount, str):
#                 claim_amount = raw_claim_amount.strip().replace(",", "").lower()
            
#             if claim_amount:
#                 # Extract numbers from input
#                 numbers = re.findall(r'\d+', claim_amount)
#                 if numbers:
#                     claim_amount = numbers[0]
#                     break  # valid input received
#                 else:
#                     if attempt == 0:
#                         text_to_speech_func_english("I didn't get a valid amount. Please say the amount clearly, like '50000 rupees'.")
#                     claim_amount = None
#             else:
#                 if attempt == 0:
#                     text_to_speech_func_english("I didn't get the claim amount. Please say the amount clearly.")
#                 else:
#                     text_to_speech_func_english("Sorry, I haven't received any claim amount. I'll be disconnecting the call now.")
#                     return False  # disconnect the call / end flow
        
#         # Confirm all details including claim amount
#         text_to_speech_func_english(
#             f"Let me confirm the details you provided: "
#             f"Your doctor's name is {doctor_name}, "
#             f"Details of your diagnosis are {diagnosis_details}, "
#             f"Amount asked for claim is {claim_amount} rupees. "
#             "Are these details correct?"
#         )
#     else:
#         # For non-reimbursement claims (cashless), keep the original flow
#         text_to_speech_func_english("Thank you for providing those details. Now, could you please let me know the estimated claim amount?")
#         raw_claim_amount = handle_user_input(duration=5)
        
#         if raw_claim_amount is False:
#             return False
        
#         claim_amount = re.sub(r"[,\<\./\|\?]", "", raw_claim_amount.strip().replace(",", "").lower()) if raw_claim_amount else ""
        
#         if isinstance(claim_amount, str):
#             claim_amount = claim_amount.strip().replace(",", "").lower()
#         else:
#             claim_amount = ""
            
#         if not claim_amount:
#             claim_amount = "25000"

#         numbers = re.findall(r'\d+', claim_amount)

#         if numbers:
#             claim_amount = numbers[0]
#             text_to_speech_func_english(
#                 f"Let me confirm the details you provided: "
#                 f"Your doctor's name is {doctor_name}, "
#                 f"Details of your diagnosis are {diagnosis_details}, "
#                 f"Amount asked for claim is {claim_amount} rupees. "
#                 "Are these details correct?"
#             )
#         else:
#             claim_amount = "25000"
#             text_to_speech_func_english(
#                 f"Let me confirm the details you provided: "
#                 f"Your doctor's name is {doctor_name}, "
#                 f"Details of your diagnosis are {diagnosis_details}. "
#                 "Are these details correct?"
#             )

#     # Store all collected details in session
#     session.claim_details.update({
#         "doctor_name": doctor_name,
#         "diagnosis_details": diagnosis_details,
#         "claim_amount": claim_amount
#     })

#     return True


# def fetch_hospital_and_patient_details(session):
#     # Debug: Check if claim_type exists in session
#     print("Current session.claim_details:", session.claim_details)  # Debug print
#     print("Claim type in session:", session.claim_details.get("claim_type"))  # Debug print

#     """Collects doctor details, diagnosis, claim amount, and hospital information."""

#     if not hasattr(session, "claim_details") or session.claim_details is None:
#         session.claim_details = {}

#     # Step 1: Ask for Doctor's Name
#     text_to_speech_func_english("Could you please share the name of the doctor who is treating you or consulting you at the hospital?")
#     # raw_doctor_name = handle_user_input(duration=5)
#     raw_doctor_name ="mohit"  # For testing
    
#     if raw_doctor_name is False:
#         return False
        
#     doctor_name = re.sub(r"[,\<\./\|\?]", "", raw_doctor_name.strip()) if raw_doctor_name else ""
    
#     # Step 2: Ask for Diagnosis Details
#     text_to_speech_func_english("Could you kindly share the diagnosis details or the medical condition that has been diagnosed?")
#     # raw_diagnosis_details = handle_user_input(duration=5)
#     raw_diagnosis_details="cancer"  # For testing
    
#     if raw_diagnosis_details is False:
#         return False
    
#     diagnosis_details = re.sub(r"[,\<\./\|\?]", "", raw_diagnosis_details.strip()) if raw_diagnosis_details else ""

#     # Handle claim amount differently based on claim type
#     if session.claim_details.get("claim_type", "").lower() == "reimbursement":
#         # For reimbursement, we strictly require the claim amount with 2 attempts
#         text_to_speech_func_english("You have selected reimbursement. Please provide the estimated claim amount in rupees.")
        
#         claim_amount = None
#         for attempt in range(2):
#             raw_claim_amount = handle_user_input(duration=6)
            
#             if raw_claim_amount is False:
#                 return False
                
#             if isinstance(raw_claim_amount, str):
#                 # Clean the input and look for numbers
#                 cleaned_input = raw_claim_amount.strip().replace(",", "").lower()
#                 numbers = re.findall(r'\d+', cleaned_input)
                
#                 if numbers:
#                     claim_amount = numbers[0]
#                     break  # valid numeric input received
#                 else:
#                     # Handle non-numeric responses ("I don't know", etc.)
#                     if attempt == 0:
#                         text_to_speech_func_english("For reimbursement claims, we need an estimated amount. Please say the amount in numbers, like '50000 rupees'.")
#                     else:
#                         text_to_speech_func_english("Sorry, I still didn't get a valid amount. Since this is a reimbursement claim, I'll need to transfer you to an agent for assistance.")
#                         session.transfer_reason = "Could not get claim amount for reimbursement"
#                         return False
#             else:
#                 # No input received
#                 if attempt == 0:
#                     text_to_speech_func_english("I didn't hear the claim amount. Please say the estimated amount in rupees.")
#                 else:
#                     text_to_speech_func_english("Sorry, I didn't receive any claim amount. Since this is a reimbursement claim, I'll need to transfer you to an agent.")
#                     session.transfer_reason = "No claim amount provided for reimbursement"
#                     return False
        
#         # Confirm all details including claim amount
#         text_to_speech_func_english(
#             f"Let me confirm the details you provided: "
#             f"Your doctor's name is {doctor_name}, "
#             f"Details of your diagnosis are {diagnosis_details}, "
#             f"Amount asked for claim is {claim_amount} rupees. "
#             "Are these details correct?"
#         )
#     else:
#         # For non-reimbursement claims (cashless), keep the original flow
#         text_to_speech_func_english("Thank you for providing those details. Now, could you please let me know the estimated claim amount?")
#         raw_claim_amount = handle_user_input(duration=5)
        
#         if raw_claim_amount is False:
#             return False
        
#         claim_amount = re.sub(r"[,\<\./\|\?]", "", raw_claim_amount.strip().replace(",", "").lower()) if raw_claim_amount else ""
        
#         if isinstance(claim_amount, str):
#             claim_amount = claim_amount.strip().replace(",", "").lower()
#         else:
#             claim_amount = ""
            
#         if not claim_amount:
#             claim_amount = "25000"

#         numbers = re.findall(r'\d+', claim_amount)

#         if numbers:
#             claim_amount = numbers[0]
#             text_to_speech_func_english(
#                 f"Let me confirm the details you provided: "
#                 f"Your doctor's name is {doctor_name}, "
#                 f"Details of your diagnosis are {diagnosis_details}, "
#                 f"Amount asked for claim is {claim_amount} rupees. "
#                 "Are these details correct?"
#             )
#         else:
#             claim_amount = "25000"
#             text_to_speech_func_english(
#                 f"Let me confirm the details you provided: "
#                 f"Your doctor's name is {doctor_name}, "
#                 f"Details of your diagnosis are {diagnosis_details}. "
#                 "Are these details correct?"
#             )

#     # Store all collected details in session
#     session.claim_details.update({
#         "doctor_name": doctor_name,
#         "diagnosis_details": diagnosis_details,
#         "claim_amount": claim_amount
#     })

#     return True

def fetch_hospitals_by_pincode(hospital_pin_code):
    
    
    """Fetch all hospitals for a given pincode."""
    url = "http://mservices.brobotinsurance.com/ldapauth/api/corporateportalapi/HospitalSearchList"
    headers = {
        "Authorization": "Basic UkdJQ29ycDpWQGxpZEB0ZQ==",
        "Content-Type": "application/json"
    }
    payload = json.dumps({
        "HospitalName": "",  # Empty to fetch all in the pincode
        "PinCode": str(hospital_pin_code),
        "Cityid": 0
    })

    try:
        response = requests.post(url, headers=headers, data=payload)
        response_data = response.json()
        if response.status_code == 200 and "Output" in response_data:
            return response_data["Output"]
        else:
            return []
    except Exception as e:
        print(f"Error fetching hospital list: {e}")
        return []


# Test the function
print("this is my test case *************************",fetch_hospitals_by_pincode(127021))


# *******************************************************************************************************************

def  get_policy_details(session: ClaimSession):
    """
    Fetch policy details using only the mobile number.
    - If policies exist, confirm insured details with the user.
    - If no policies are found, transfer to an agent.
    """

    try:
        if not getattr(session, 'mobile_number', None):
            session.transfer_reason = "Mobile number not provided"
            message = "We need a registered mobile number to proceed. Transferring you to an agent."
            text_to_speech_func_english(message)
            return False

        mobile_number = session.mobile_number
        policy_details = fetch_policy_details_via_phone_number(mobile_number)

        if not policy_details:
            session.transfer_reason = "No policies found for the provided mobile number"
            message = "We couldn't locate any policies linked to your mobile number. Let me connect you with an agent."
            text_to_speech_func_english(message)
            return False

        session.policy_details = policy_details
        insured_name = session.policy_details.get("insured_name", "the insured person")
        policy_number = session.policy_details.get("policyno", "your registered policy")

        # Confirm insured details
        message = (
            f"Please confirm: Your registered policy is {policy_number}, "
            f"and the insured name is {insured_name}. Is this correct?"
        )
        text_to_speech_func_english(message)

        user_input = handle_user_input(duration=5)
        if user_input is False:
            session.transfer_reason = "Exceeded input limit"
            message = "Sorry, I haven’t received any input from you. Transferring you to an agent."
            text_to_speech_func_english(message)
            return False

        if "yes" in user_input.lower() or "confirm" in user_input.lower():
            message = "Thank you. Just a moment while I retrieve your policy details."
            text_to_speech_func_english(message)
            return True
        else:
            session.transfer_reason = "User did not confirm insured details"
            message = "I'm sorry, I couldn't confirm your details. Transferring you to an agent for further assistance."
            text_to_speech_func_english(message)
            return False

    except Exception as e:
        session.transfer_reason = f"Policy details retrieval error: {str(e)}"
        message = "I'm sorry, due to a system issue, I'm connecting you to an agent for further assistance."
        text_to_speech_func_english(message)
        return False


#  ****************************   Step 7 ****************************************************************************
import requests


def create_service_request(session):
    print("Executing create_service_request...*****************************************************")

    url = "https://leadservices.brobotinsurance.com/rgiChatbot/ChatbotIntegrationWrapper.asmx"
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://tempuri.org/CreateSRForChatbotWrap"
    }

    # Extracting dynamic values from session
    session_dict = session.__dict__
    policy_info = session_dict.get('policy_details', [{}])[0]
    policy_number = policy_info.get('policy_number')
    phone_number = policy_info.get('mobile_number')
    product_code = policy_info.get('product_code')
    caller_name = policy_info.get('name', 'Unknown')

    # Constructing SOAP body
    body = f"""<?xml version="1.0" encoding="utf-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
       <soapenv:Header/>
       <soapenv:Body>
          <tem:CreateSRForChatbotWrap>
             <tem:XML><![CDATA[
                <EndorsementRequests>
                    <EndorsementRequest>
                        <CallerUserID>WhatsApp</CallerUserID>
                        <Password>WhatsApp@123</Password>
                        <CallerAppId>293</CallerAppId>
                        <UniqueRefNo>92707</UniqueRefNo>
                        <LOB>3</LOB>
                        <PolicyNo>{policy_number}</PolicyNo>
                        <ProductCode>{product_code}</ProductCode>
                        <SrvcCallType>7</SrvcCallType>
                        <SrvcCallSubType>4</SrvcCallSubType>
                        <SrvcReqType>54</SrvcReqType>
                        <CallerName>{caller_name}</CallerName>
                        <IsDocumentPendingCase>Y</IsDocumentPendingCase>
                        <CallerType>5</CallerType>
                        <Gender></Gender>
                        <Date_Of_Birth></Date_Of_Birth>
                        <Address1></Address1>
                        <Address2></Address2>
                        <City></City>
                        <District></District>
                        <State></State>
                        <Pincode></Pincode>
                        <TelephoneNo></TelephoneNo>
                        <CallReceivedFromNo>{phone_number}</CallReceivedFromNo>
                        <InsuredNo></InsuredNo>
                        <EmailId>kore@gmail.com</EmailId>
                        <CustomerRemark>Kore Catbot Test</CustomerRemark>
                        <AdditionalFields>
                            <ClaimFields/>
                            <SalesFields/>
                            <EndorsementFields/>
                            <PolicyFields/>
                        </AdditionalFields>
                    </EndorsementRequest>
                </EndorsementRequests>
             ]]></tem:XML>
          </tem:CreateSRForChatbotWrap>
       </soapenv:Body>
    </soapenv:Envelope>"""

    # Send request
    try:
        response = requests.post(url, data=body, headers=headers)
        if response.status_code == 200:
            print("✅ Service request successfully created.")
            return True
        else:
            print("❌ Failed to create service request. Status code:", response.status_code)
            return False
    except Exception as e:
        print("❌ Error occurred while sending request:", str(e))
        return False


#  if something get wrong or error the we need to transfer the call not mention to the user ********************************

# def initialize_claim(session):
#     """Step 7 & 8: Initializes the claim with collected details and handles response with conclusion message."""

#     text_to_speech_func_english("Thank you for providing all the necessary information. Let's proceed with the claim.")

#     try:
#         # Extract necessary details from session
#         policy = session.policy_details[0]
#         hospital = session.claim_details.get("hospital_details", {})
#         doctor_name = session.claim_details.get("doctor_name", "Unknown")
#         diagnosis = session.claim_details.get("diagnosis", "Not Provided")
#         claim_amount = str(session.claim_details.get("claim_amount", "25000"))
#         intimator = session.claim_details.get("intimator_details", {})

#         # Prepare request body
#         payload = {
#             "ProposerName": policy.get("name", ""),
#             "AdmissionDate": "",
#             "DischargeDate": "",
#             "DoctorName": doctor_name,
#             "DiagnosisDetails": diagnosis,
#             "ClDetailId": "",
#             "HospitalName": hospital.get("name", ""),
#             "DocumentList": [],
#             "MobileNumber": f"91-{policy.get('mobile_number', '')}",
#             "ReceivedMode": "Sbot",
#             "IntimatorRelationship": intimator.get("relationship", ""),
#             "PatientMobileNo": f"91-{policy.get('mobile_number', '')}",
#             "InsuredName": policy.get("name", ""),
#             "EmployeeID": policy.get("employee_id", ""),
#             "EmailID": intimator.get("email", "test@example.com"),
#             "Age": policy.get("age", "30"),
#             "RelationShip": policy.get("relationship", ""),
#             "PatientName": policy.get("name", ""),
#             "UHIDNumber": policy.get("uhid", ""),
#             "PatientUHID": policy.get("uhid", ""),
#             "PolicyName": policy.get("policy_name", ""),
#             "PolicyNumber": policy.get("policy_number", ""),
#             "PolicyStartDate": policy.get("policy_start_date", ""),
#             "PolicyEndDate": policy.get("policy_end_date", ""),
#             "IntimationType": "CLOPD",
#             "ServiceCode": policy.get("service_code", ""),
#             "ServiceType": policy.get("service_type", "3"),
#             "HospitalId": hospital.get("hospital_id", ""),
#             "Address1": hospital.get("location", ""),
#             "Address2": hospital.get("address2", ""),
#             "Address3": "",
#             "State": hospital.get("state", ""),
#             "City": hospital.get("city", ""),
#             "District": hospital.get("district", ""),
#             "Pincode": hospital.get("pincode", ""),
#             "ClaimAmount": claim_amount,
#             "IntimatorName": intimator.get("name", ""),
#             "IntimatorMobileNo": f"{intimator.get('mobile', '')}",
#             "ProductTypeId": "",
#             "ProductType": "",
#             "TypeofLossID": "",
#             "TypeofLoss": "",
#             "BenefitTypeID": "",
#             "BenefitType": "",
#             "LossDate": "",
#             "LossTime": "",
#             "IncidentDate": "",
#             "LossDescription": "",
#             "Whatsapp_Consent": "",
#             "PatientABHAId": "",
#             "PatientABHAAddress": "",
#             "InsuredABHAId": "",
#             "InsuredABHAAddress": "",
#             "BenefitInsuredOccupation": ""
#         }

#         headers = {
#             "Content-Type": "application/json",
#             "Authorization": "Basic UkdJQ29ycDpWQGxpZEB0ZQ=="  # ← same as in Postman
#         }

#         response = requests.post(
#             "http://mservices.brobotinsurance.co.in/ldapauth/api/corporateportalapi/IntimateHealthClaim",
#             json=payload,
#             headers=headers,
#             timeout=10
#         )

#         print("📄 Raw Response Text:", response.text)
#         response_json = response.json()
#         print("📨 Response from API:", response_json)

#         # Check for success
#         if response_json.get("Message", "").lower() == "success" and response_json.get("ClaimNumber"):
#             claim_number = response_json["ClaimNumber"]
#             claim_id = response_json["ClaimNumberId"]

#             # ✅ Save claim number & ID in session
#             session.claim_details["claim_number"] = claim_number
#             session.claim_details["claim_id"] = claim_id

#             # ✅ Step 7 response
#             text_to_speech_func_english(
#                 f"Your claim intimation ID has been successfully generated. "
#                 f"I have sent this ID via SMS to the mobile number associated with this claim. "
#                 # f"Your ID is {claim_number}."
#             )
            
#             #  here i need to call the service request ***************************************************************
#             create_service_request(session)
#             result = create_service_request(session)
#             print("Status Code:", result["status_code"])
#             print("Response Text:", result["response_text"])
            
#             # ✅ Step 8: Conclusion
#             text_to_speech_func_english(
#                 f"Claim Intimation done. Kindly note your claim intimation number {claim_number}. "
#                 "Post receipt of the documents, the claim will be processed within 15 days as per policy terms and conditions. "
#                 "Kindly submit the documents on our email ID: services@Indusindinsurance.com, "
#                 "and please mention your claim intimation number in the subject line."
#             )

#             return True
#         else:
#             # Extract and print error message if claim number not returned
#             error_msg = response_json.get("Error", "Unknown error occurred.")
#             print("⚠️ API Error Message:", error_msg)

#             text_to_speech_func_english(
#                 f"I could not generate your claim intimation ID. "
#                 f"The reason is: {error_msg}. "
#                 "I will transfer you to an agent for further assistance. Please hold."
#             )
            
#             # text_to_speech_func_english(
#             #     "I'm sorry, due to a system issue, I'm connecting you to an agent who can assist you further. Please wait."
#             # )
#             return False

#     except Exception as e:
#         print("❌ Exception during claim initialization:", str(e))
#         text_to_speech_func_english(
#             "I'm sorry, due to a system issue, I'm connecting you to an agent who can assist you further. Please wait."
#         )
#         return False


def initialize_claim(session):
    """Step 7 & 8: Initializes the claim with collected details and handles response with conclusion message."""

    text_to_speech_func_english("Thank you for providing all the necessary information. Let's proceed with the claim.")

    try:
        # Extract necessary details from session
        policy = session.policy_details[0]
        hospital = session.claim_details.get("hospital_details", {})
        doctor_name = session.claim_details.get("doctor_name", "Unknown")
        diagnosis = session.claim_details.get("diagnosis", "Not Provided")
        claim_amount = str(session.claim_details.get("claim_amount", "25000"))
        intimator = session.claim_details.get("intimator_details", {})

        # Prepare request body
        payload = {
            "ProposerName": policy.get("name", ""),
            "AdmissionDate": "",
            "DischargeDate": "",
            "DoctorName": doctor_name,
            "DiagnosisDetails": diagnosis,
            "ClDetailId": "",
            "HospitalName": hospital.get("name", ""),
            "DocumentList": [],
            "MobileNumber": f"91-{policy.get('mobile_number', '')}",
            "ReceivedMode": "Sbot",
            "IntimatorRelationship": intimator.get("relationship", ""),
            "PatientMobileNo": f"91-{policy.get('mobile_number', '')}",
            "InsuredName": policy.get("name", ""),
            "EmployeeID": policy.get("employee_id", ""),
            "EmailID": intimator.get("email", "test@example.com"),
            "Age": policy.get("age", "30"),
            "RelationShip": policy.get("relationship", ""),
            "PatientName": policy.get("name", ""),
            "UHIDNumber": policy.get("uhid", ""),
            "PatientUHID": policy.get("uhid", ""),
            "PolicyName": policy.get("policy_name", ""),
            "PolicyNumber": policy.get("policy_number", ""),
            "PolicyStartDate": policy.get("policy_start_date", ""),
            "PolicyEndDate": policy.get("policy_end_date", ""),
            "IntimationType": "CLOPD",
            "ServiceCode": policy.get("service_code", ""),
            "ServiceType": policy.get("service_type", "3"),
            "HospitalId": hospital.get("hospital_id", ""),
            "Address1": hospital.get("location", ""),
            "Address2": hospital.get("address2", ""),
            "Address3": "",
            "State": hospital.get("state", ""),
            "City": hospital.get("city", ""),
            "District": hospital.get("district", ""),
            "Pincode": hospital.get("pincode", ""),
            "ClaimAmount": claim_amount,
            "IntimatorName": intimator.get("name", ""),
            "IntimatorMobileNo": f"{intimator.get('mobile', '')}",
            "ProductTypeId": "",
            "ProductType": "",
            "TypeofLossID": "",
            "TypeofLoss": "",
            "BenefitTypeID": "",
            "BenefitType": "",
            "LossDate": "",
            "LossTime": "",
            "IncidentDate": "",
            "LossDescription": "",
            "Whatsapp_Consent": "",
            "PatientABHAId": "",
            "PatientABHAAddress": "",
            "InsuredABHAId": "",
            "InsuredABHAAddress": "",
            "BenefitInsuredOccupation": ""
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Basic UkdJQ29ycDpWQGxpZEB0ZQ=="  # ← same as in Postman
        }

        response = requests.post(
            "http://mservices.brobotinsurance.co.in/ldapauth/api/corporateportalapi/IntimateHealthClaim",
            json=payload,
            headers=headers,
            timeout=10
        )

        print("📄 Raw Response Text:", response.text)
        response_json = response.json()
        print("📨 Response from API:", response_json)

        # Check for success
        if response_json.get("Message", "").lower() == "success" and response_json.get("ClaimNumber"):
            claim_number = response_json["ClaimNumber"]
            claim_id = response_json["ClaimNumberId"]

            # ✅ Save claim number & ID in session
            session.claim_details["claim_number"] = claim_number
            session.claim_details["claim_id"] = claim_id

            # ✅ Step 7 response
            text_to_speech_func_english(
                f"Your claim intimation ID has been successfully generated. "
                f"I have sent this ID via SMS to the mobile number associated with this claim. "
                # f"Your ID is {claim_number}."
            )
            
            #  here i need to call the service request ***************************************************************

            # ✅ Step 8: Conclusion
            text_to_speech_func_english(
                f"Claim Intimation done. Kindly note your claim intimation number {claim_number}. "
                "Post receipt of the documents, the claim will be processed within 15 days as per policy terms and conditions. "
                "Kindly submit the documents on our email ID: R G I C L .services @relianceADA.com, "
                "and please mention your claim intimation number in the subject line."
            )

            return True
        else:
            # Extract and print error message if claim number not returned
            error_msg = response_json.get("Error", "Unknown error occurred.")
            print("⚠️ API Error Message:", error_msg)

            text_to_speech_func_english(
                f"I could not generate your claim intimation ID. "
                f"The reason is: {error_msg}. "
                "I will transfer you to an agent for further assistance. Please hold."
            )
            return False

    except Exception as e:
        print("❌ Exception during claim initialization:", str(e))
        text_to_speech_func_english(
            "I am sorry, I am having trouble generating your claim intimation ID. "
            "I will transfer you to an agent who can help you further. Please hold."
        )
        return False


def test_initialize_claim_with_static_data():
    """Hits the real API using static test data to verify claim generation."""
    print("🚀 [LIVE TEST] Sending static claim data to real API...")

    # Static test data
    payload = {
  "ProposerName": "MEENA PATIL",
  "AdmissionDate": "2024-03-06",
  "DischargeDate": "",
  "DoctorName": "fsfdgdf",
  "DiagnosisDetails": "gdfsf",
  "ClDetailId": "",
  "HospitalName": "Apex Citi Hospital (A Unit Of Siddharth Health Care Pvt. Ltd.)",
  "DocumentList": [],
  "MobileNumber": "91-9100000008",
  "ReceivedMode": "Sbot",
  "IntimatorRelationship": "",
  "PatientMobileNo": "91-9100000008",
  "InsuredName": "MEENA PATIL",
  "EmployeeID": "70310111",
  "EmailID": "test@sp.com",
  "Age": "39",
  "RelationShip": "SPOUSE",
  "PatientName": "MEENA PATIL",
  "UHIDNumber": "RMDDG23000001B1",
  "PatientUHID": "RMDDG23000001B1",
  "PolicyName": "SPENCERS RETAIL LIMITED",
  "PolicyNumber": "202232812000033005",
  "PolicyStartDate": "01-Jan-2023",
  "PolicyEndDate": "31-Dec-2023",
  "IntimationType": "CLOPD",
  "ServiceCode": "",
  "ServiceType": "3",
  "HospitalId": "99434",
  "Address1": "D-44, West Vinod Nagar, I.P Extn.",
  "Address2": "Shop No 5, Plot No 266 Narmada Apartment, Sector 23, Next To HDFC ATM, Juinagar",
  "Address3": "",
  "State": "DELHI",
  "City": "DELHI EAST",
  "District": "EAST DELHI",
  "Pincode": "110092",
  "ClaimAmount": "465",
  "IntimatorName": "MEENA PATIL",
  "IntimatorMobileNo": "",
  "ProductTypeId": "",
  "ProductType": "",
  "TypeofLossID": "",
  "TypeofLoss": "",
  "BenefitTypeID": "",
  "BenefitType": "",
  "LossDate": "",
  "LossTime": "",
  "IncidentDate": "",
  "LossDescription": "",
  "Whatsapp_Consent": "",
  "PatientABHAId": "",
  "PatientABHAAddress": "",
  "InsuredABHAId": "",
  "InsuredABHAAddress": "",
  "BenefitInsuredOccupation": ""
}
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Basic UkdJQ29ycDpWQGxpZEB0ZQ=="  # ← same as in Postman
    }

    try:
        response = requests.post(
            "http://mservices.brobotinsurance.co.in/ldapauth/api/corporateportalapi/IntimateHealthClaim",
            json=payload,
            headers=headers,  # ← use headers!
            timeout=10
        )
        print("📄 Raw Response Text:", response.text)
        response_json = response.json()
        print("📨 API Response:", response_json)

        if response_json.get("Message", "").lower() == "success" and response_json.get("ClaimNumber"):
            print("✅ Claim generated successfully!")
            print("🆔 Claim Number:", response_json.get("ClaimNumber"))
        else:
            print("⚠️ Claim not generated.")
            print("❗ Error Message:", response_json.get("Error", "Unknown error."))

    except Exception as e:
        print("❌ Exception while calling API:", str(e))
print(test_initialize_claim_with_static_data())

# *********************************Step 7 end here ******************************************************************



# *******************************    Sr API logic start here ********************************************************


#  in this i need to print the response in terminal ****************************************************************
import requests


def handle_language_selection(duration=5):
    max_attempts = 2  # Allow two attempts for language selection
    attempt = 0

    while attempt < max_attempts:
        with st.spinner("Recording..."):
            handle_recording(duration=duration)  # Assuming handle_recording is your recording function
        
        user_input = speech_to_text_azure_streamlit()
        
        if user_input:
            user_input = remove_fullstop_from_input(user_input.strip().lower())
            with st.chat_message("user"):
                st.write(user_input)
            
            # Check for valid language options
            if user_input in ["hindi", "english", "हिंदी", "अंग्रेजी"]:
                return user_input  # Valid language input confirmed
            else:
                text_to_speech_func_english("Sorry, I didn’t understand. Please say 'Hindi' or 'English'.")
                text_to_speech_func_hindi("माफ़ कीजिए, मुझे समझ नहीं आया। कृपया 'हिंदी' या 'अंग्रेजी' कहें।")
        else:
            text_to_speech_func_english("Sorry, I didn’t catch that. Can you please repeat?")
            text_to_speech_func_hindi("माफ़ कीजिए, मुझे वो समझ नहीं आया। क्या आप कृपया इसे फिर से कह सकते हैं?")
        
        attempt += 1

    # If all attempts are used
    message = "Sorry, I haven’t received a valid input from you, so I’ll be disconnecting the call now."
    text_to_speech_func_english(message)
    text_to_speech_func_hindi("मुझे आपसे कोई मान्य इनपुट नहीं मिला है, इसलिए मैं कॉल को समाप्त कर रहा हूँ।")
    return None



# result = create_service_request(session)
# print("Status Code:", result["status_code"])
# print("Response Text:", result["response_text"])

# *******************************    Sr API logic end here   ********************************************************
from health_final_hindi import *

# def claim_intimation_flow(mobile_number=8655904635):
#     session = ClaimSession()
    

#     # Step 1: Greet the User & Ask for Language
    
    
#     welcome_message = "Namaste! Welcome to our health claim helpline. Would you prefer to continue in Hindi or English?"
#     text_to_speech_func_english(welcome_message)
#     welcome_message = "नमस्ते! हमारी क्लेम हेल्पलाइन पर आपका स्वागत है। क्या आप हिंदी या अंग्रेजी में आगे बढ़ना पसंद करेंगे?"
#     text_to_speech_func_hindi(welcome_message)
    
#     st.write(welcome_message)

#     language_confirmation = handle_user_input(duration=1)
#     # language_confirmation = "english"
    
#     if language_confirmation is False:
#         session.transfer_reason = "Exceed the input limit"
#         return False

#     if 'hindi' in language_confirmation.lower():
#         session.selected_language = "Hindi"
#         confirmation_message = "अपनी भाषा चुनने के लिए धन्यवाद।"
#         text_to_speech_func_hindi(confirmation_message)
        
#         if validate_mobile_number(mobile_number):
#             registered_mobile_no = "आपने रजिस्टर्ड मोबाइल नंबर से कॉल किया है, कृपया प्रतीक्षा करें, मैं विवरण प्रदान कर रहा हूँ।"
#             text_to_speech_func_hindi(registered_mobile_no)
#             session.mobile_number = mobile_number
            
#             if not handle_multiple_policies_hindi(session, mobile_number):
#                 print(session.__dict__)
#                 return redirecting_to_agent(session.transfer_reason)
        
#         else:
#             if not ask_mobile_number_hindi(session):
                
#                 return redirecting_to_agent(session.transfer_reason)
 
#             if session.mobile_number:
#                 if not handle_multiple_policies_hindi(session, session.mobile_number):
#                     print(session.__dict__)
#                     return redirecting_to_agent(session.transfer_reason)
                
                
#         #   ✅ Step 3: Process Policy (sample corporate number used)
#         if not process_policy_hindi(202232812000002305):
#             return redirecting_to_agent(session.transfer_reason)
        
#         # st.write("Session Details:", session.__dict__)
        
#         if not ask_admission_date_hindi(session):
#             return redirecting_to_agent(session.transfer_reason)
 
        
 
#         if not determine_claim_type_hindi(session):
#             return redirecting_to_agent(session.transfer_reason)
 
#         if not verify_insured_details_hindi(session):
#             return redirecting_to_agent(session.transfer_reason)
 
#         if not fetch_hospital_and_patient_details_hindi(session):
#             return redirecting_to_agent(session.transfer_reason)
        
#         if not initialize_claim_hindi(session):
#             return redirecting_to_agent(session.transfer_reason)
        
#         if not create_service_request(session):
#             return redirecting_to_agent(session.transfer_reason)
                
#     elif 'english' in language_confirmation.lower():
#         session.selected_language = "English"
        
#         confirmation_message = "Thank you for choosing your language."
#         text_to_speech_func_english(confirmation_message)
        
#         if validate_mobile_number(mobile_number):
#             registered_mobile_no ="you have called through the registered mobile number,let me provide the details "
#             text_to_speech_func_english(registered_mobile_no)
#             session.mobile_number = mobile_number
            
#             if not handle_multiple_policies(session, mobile_number):
#                 # print(session.__dict__) 
#                 return redirecting_to_agent(session.transfer_reason)
                
#         else:
#             if not ask_for_mobile_number(session):
#                 # print(session.__dict__)    
#                 return redirecting_to_agent(session.transfer_reason)
        
#             if session.mobile_number:
#                 if not handle_multiple_policies(session, session.mobile_number):
#                     print(session.__dict__)
#                     return redirecting_to_agent(session.transfer_reason)
                
#                   # 202232812000002305      corporate number   
#                   # 130592329291010982      retail number
                      
#         # ✅ Step 3: retail and corporate 
#         if not  process_policy(202232812000002305):
#              return redirecting_to_agent(session.transfer_reason)
 
#         if not ask_admission_date(session):
#             return redirecting_to_agent(session.transfer_reason) 
        
#         # print(session.claim_details.get("admission_date"))
        
#         # ✅ Step 4: Determine Claim Type
#         if not determine_claim_type(session):
#             return redirecting_to_agent(session.transfer_reason)

#         # ✅ Step 5: Insured & Member Details Verification
#         if not verify_insured_details(session):
#             return redirecting_to_agent(session.transfer_reason)
        
#         # ✅ Step 6: Insured & Member Details Verification
#         if not fetch_hospital_and_patient_details(session):
#             return redirecting_to_agent(session.transfer_reason)
        
#         if not initialize_claim(session):
#             return redirecting_to_agent(session.transfer_reason)
        
#         # if not create_service_request(session):
#         #     return redirecting_to_agent(session.transfer_reason)

#     # st.write("Session Details:", session.__dict__)

# st.title("Health Claim 🏥")
# st.markdown("Welcome to the RGI Health Claim App! Click below to start the claim flow.")

# if st.button("Start flow"):
#     claim_intimation_flow()
    

def claim_intimation_flow(mobile_number=8655904635):
    session = ClaimSession()
    language_attempts = 0
    max_attempts = 2

    # Language Selection with 2 Attempts
    while language_attempts < max_attempts:
        language_attempts += 1
        
        # Greet user in both languages
        welcome_message_eng = "Namaste! Welcome to our health claim helpline. Would you prefer to continue in Hindi or English?"
        welcome_message_hin = "नमस्ते! हमारी क्लेम हेल्पलाइन पर आपका स्वागत है। क्या आप हिंदी या अंग्रेजी में आगे बढ़ना पसंद करेंगे?"
        
        text_to_speech_func_english(welcome_message_eng)
        text_to_speech_func_hindi(welcome_message_hin)
        # st.write(welcome_message_eng + "\n\n" + welcome_message_hin)

        language_confirmation = handle_user_input(duration=5)
        # language_confirmation ="english"
        
        if language_confirmation is False:
            session.transfer_reason = "Exceed the input limit"
            return False

        if 'hindi' in language_confirmation.lower():
            session.selected_language = "Hindi"
            text_to_speech_func_hindi("अपनी भाषा चुनने के लिए धन्यवाद।")
            break
            
        elif 'english' in language_confirmation.lower():
            session.selected_language = "English"
            text_to_speech_func_english("Thank you for choosing your language.")
            break
            
        else:
            if language_attempts < max_attempts:
                retry_msg = "Please choose either Hindi or English. You have 1 more attempt."
                text_to_speech_func_english(retry_msg)
                retry_msg = "कृपया हिंदी या अंग्रेजी में चुनें। आपके पास 1 और प्रयास शेष है।"
                text_to_speech_func_hindi(retry_msg)
            else:
                session.transfer_reason = "Language not selected properly"
                
                retry_msg = "आपकी सीमा पर हो गई है, कॉल समाप्त की जा रही है"
                text_to_speech_func_hindi(retry_msg)
                retry_msg = "Your limit has been reached, the call is being terminated"
                text_to_speech_func_english(retry_msg)
                return redirecting_to_agent(session.transfer_reason)

    # Hindi Flow
    if session.selected_language == "Hindi":
        # Mobile Number Validation
        if validate_mobile_number(mobile_number):
            registered_msg = "आपने रजिस्टर्ड मोबाइल नंबर से कॉल किया है, कृपया प्रतीक्षा करें, मैं विवरण प्रदान कर रहा हूँ।"
            text_to_speech_func_hindi(registered_msg)
            session.mobile_number = mobile_number
            
            if not handle_multiple_policies_hindi(session, mobile_number):
                return redirecting_to_agent(session.transfer_reason)
        else:
            if not ask_mobile_number_hindi(session):
                return redirecting_to_agent(session.transfer_reason)
 
            if session.mobile_number:
                if not handle_multiple_policies_hindi(session, session.mobile_number):
                    return redirecting_to_agent(session.transfer_reason)
        
        # Process each step separately
        if not process_policy_hindi(202232812000002305):
            return redirecting_to_agent(session.transfer_reason)
        
        if not ask_admission_date_hindi(session):
            return redirecting_to_agent(session.transfer_reason)
 
        if not determine_claim_type_hindi(session):
            return redirecting_to_agent(session.transfer_reason)
 
        if not verify_insured_details_hindi(session):
            return redirecting_to_agent(session.transfer_reason)
 
        if not fetch_hospital_and_patient_details_hindi(session):
            return redirecting_to_agent(session.transfer_reason)
        
        if not initialize_claim_hindi(session):
            return redirecting_to_agent(session.transfer_reason)
        
        if not create_service_request(session):
            return redirecting_to_agent(session.transfer_reason)
    # English Flow
    elif session.selected_language == "English":
        if validate_mobile_number(mobile_number):
            registered_msg = "You have called through the registered mobile number, let me provide the details."
            text_to_speech_func_english(registered_msg)
            session.mobile_number = mobile_number
            
            if not handle_multiple_policies(session, mobile_number):
                return redirecting_to_agent(session.transfer_reason)
        else:
            if not ask_for_mobile_number(session):
                return redirecting_to_agent(session.transfer_reason)
        
            if session.mobile_number:
                if not handle_multiple_policies(session, session.mobile_number):
                    return redirecting_to_agent(session.transfer_reason)
                
        # Process each step separately
        if not process_policy(202232812000002305):
            return redirecting_to_agent(session.transfer_reason)
 
        if not ask_admission_date(session):
            return redirecting_to_agent(session.transfer_reason)
        
        if not determine_claim_type(session):
            return redirecting_to_agent(session.transfer_reason)

        if not verify_insured_details(session):
            return redirecting_to_agent(session.transfer_reason)
        
        if not fetch_hospital_and_patient_details(session):
            return redirecting_to_agent(session.transfer_reason)
        
        if not initialize_claim(session):
            return redirecting_to_agent(session.transfer_reason)
        
        if not create_service_request(session):
            return redirecting_to_agent(session.transfer_reason)

    return True

# UI Components
st.title("Collections 🏥")
st.markdown("Welcome to the Collections App! Click below to start the claim flow.")

if st.button("Start flow"):
    claim_intimation_flow()




    
# Unfortunately, the details provided do not match our records. I am disconnecting the call now.