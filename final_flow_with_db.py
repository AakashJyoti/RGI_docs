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
from soap_api_number import extract_motor_policy_numbers
from dateutil import parser
import re
# import streamlit as st
import wave
from deep_update import handle_recording, play_audio

from utils import text_to_speech_azure_streamlit, speech_to_text_azure_streamlit
from RGI_Motor_Hindi_1 import hindi_claim_intimation_flow
import django

import wave
from asgiref.sync import sync_to_async

os.environ['DJANGO_SETTINGS_MODULE'] = 'rgi_motor_websocket_test.settings'
django.setup()

from websocket_testing.models import UserDetails

DB_Object =UserDetails()

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

# # audio file time duration calculation
def calculate_length_of_audio():
    base_path = os.path.dirname(os.path.abspath(__file__))  # Get the current script's directory
    parent_directory = os.path.dirname(base_path)  # Go up one directory
    audio_path = os.path.join(parent_directory, "audio", "Bot", "bot_response.wav")


    with wave.open(audio_path, 'rb') as audio_file:
        frames = audio_file.getnframes()
        rate = audio_file.getframerate()
        duration = frames / float(rate)
        return duration + 0.5

# def text_to_speech_func_english(message):
#     text_to_speech_azure_streamlit(input_text=message)
#
#     with st.chat_message("assistant"):
#         st.write(message)
#     play_audio()
#     time.sleep(calculate_length_of_audio())  # handle time dynamically


# def text_to_speech_func_english(message):
#     """
#     Convert text to speech, generate a WAV file, and return its filename.
#     Here we generate a dummy silent WAV file.
#     """
#     print(f"TTS (English): {message}")


    # filename = "tts_response.wav"
    # try:
    #     with wave.open(filename, "w") as wf:
    #         wf.setnchannels(1)
    #         wf.setsampwidth(2)
    #         wf.setframerate(16000)
    #         # 1 second of silence (16000 frames)
    #         silence = b'\x00\x00' * 16000
    #         wf.writeframes(silence)
    # except Exception as e:
    #     print("Error generating TTS audio:", e)
    # return filename


# def get_user_input_with_retries(record_duration: int = 5):
#     message = "Sorry, I didn't catch that. Please say it again."
#     max_attempts = 0
#     # for attempt in range(max_attempts):
#     while max_attempts < 2:
#         max_attempts += 1
#         text_to_speech_func_english(message=message)
#
#         # Record user input
#         with st.spinner("Recording..."):
#             handle_recording(duration=record_duration)
#         input_text = speech_to_text_azure_streamlit()
#
#         # Validate and process input
#         if input_text is not None:
#             processed_text = str(input_text).strip().lower()
#             if processed_text:
#                 with st.chat_message("user"):
#                     st.write(processed_text)
#                 return processed_text
#
#     return False  # All attempts failed


# def handle_user_input(duration):
#     with st.spinner("Recording..."):
#         handle_recording(duration=duration)  # Assuming handle_recording is your recording function
#     user_input = speech_to_text_azure_streamlit()
#     if user_input is not None:
#         user_input = remove_fullstop_from_input(user_input.strip().lower())
#         with st.chat_message("user"):
#             st.write(user_input)
#     else:
#         user_input = get_user_input_with_retries(record_duration=duration)
#
#     if user_input is False:
#         message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
#         text_to_speech_func_english(message)
#     return user_input

#for terminal testing

def text_to_speech_func_english(message):
    """
    Convert text to speech, generate a WAV file, and return its filename.
    Here we generate a dummy silent WAV file.
    """
    print(f"TTS (English): {message}")

    text_to_speech_azure_streamlit(message)

def get_user_input_with_retries(record_duration: int = 5):
    message = "Sorry, I didn't catch that. Please say it again."
    max_attempts = 0
    # for attempt in range(max_attempts):
    while max_attempts < 2:
        max_attempts += 1
        text_to_speech_func_english(message)

        # Record user input
        # with st.spinner("Recording..."):
        handle_recording(duration=record_duration)
        input_text = speech_to_text_azure_streamlit()

        # Validate and process input
        if input_text is not None:
            processed_text = str(input_text).strip().lower()
            if processed_text:
                # with st.chat_message("user"):
                #     st.write(processed_text)
                print(processed_text)
                return processed_text

    return False  # All attempts failed


def handle_user_input(duration):
    # with st.spinner("Recording..."):
    handle_recording(duration=duration)  # Assuming handle_recording is your recording function
    user_input = speech_to_text_azure_streamlit()
    if user_input is not None:
        user_input = remove_fullstop_from_input(user_input.strip().lower())
        print(user_input)
        # with st.chat_message("user"):
        #     st.write(user_input)
    else:
        user_input = get_user_input_with_retries(record_duration=duration)

    if user_input is False:
        message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
        text_to_speech_func_english(message)
    return user_input




@dataclass
class ClaimSession:
    """Central data storage for claim process"""
    selected_language: str = None
    auth_attempts: int = 0
    date_attempts: int = 0
    policy_number: str = None
    mobile_number: str = None
    policy_details: Dict[str, Any] = None
    caller_details: Dict[str, Any] = None
    claim_details: Dict[str, Any] = None
    garage_details: Dict[str, Any] = None
    transfer_reason: str = None


def fetch_garage(pincode):
    # Get absolute database path
    base_path = os.path.dirname(os.path.abspath(__file__))  # Get the current script's directory
    parent_directory = os.path.dirname(base_path)  # Go up one directory
    db_path = os.path.join(parent_directory, "db.sqlite3")

    # db_path = os.path.abspath('D:/reliance/claim_agent/db.sqlite3')

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


def validate_mobile_number(mobile_number):
    # Mock validation logic
    validate_number = validate_mobile_number_api_call(mobile_number)

    # Check if the response indicates a valid or invalid mobile number
    if validate_number == "valid mobile number":
        return True
    elif validate_number == "invalid mobile number":
        return False
    else:
        return False


def ask_mobile_or_policy_number(session: ClaimSession):
    try:
        while session.auth_attempts < 2:
            message = "can you please share your 16 or 18 digit policy number or 10 digit registered mobile number?"
            text_to_speech_func_english(message=message)


            user_input = handle_user_input(duration=10)
            if user_input is False:
                session.transfer_reason = "Exceed the input limit"
                return False

            cleaned_number = re.sub(r"[^\d]", "", user_input)  # Keep only digits, remove anything else

            if len(cleaned_number) == 10 and validate_mobile_number(cleaned_number):
                session.mobile_number = cleaned_number
                return True

            elif len(cleaned_number) in [16, 18]:
                session.policy_number = cleaned_number
                return True
            else:
                session.auth_attempts += 1
                if session.auth_attempts < 2:
                    message = "I'm sorry, the information you share does not match with our records. Let's try again"
                    text_to_speech_func_english(message)
        DB_Object.mobile_number=session.mobile_number
        DB_Object.save()
        session.transfer_reason = "Maximum authentication attempts exceeded"

        # streamlit UI
        message = "I'm sorry, we've exceeded the maximum attempts. Goodbye!"
        text_to_speech_func_english(message)
        return False
    except Exception as e:
        session.transfer_reason = f"Ask for mobile or policy number error: {str(e)}"
        # streamlit UI
        message = "I'm sorry, due to a system issue, I'm connecting you to an agent who can assist you further. Please wait."
        text_to_speech_func_english(message)
        return False


def get_policy_details(session: ClaimSession):
    """
    This function obtains policy details based on the inputs stored in the session, with enhanced confirmation and retry logic.

    - If a policy number is already provided, it fetches details and confirms with the user.
    - If a mobile number is available, it retrieves linked policies, confirms one, and then confirms the details.
    - Users have two chances to correct their policy number if initial confirmations fail.
    """

    try:
        # CASE 1: Direct policy number provided in session
        if getattr(session, 'policy_number', None):
            policy_number = session.policy_number
            session.policy_details = fetch_policy_details_via_phone_number(policy_number)
            DB_Object.policy_number=policy_number
            DB_Object.save()
            if session.policy_details:
                # Confirm policy details with user
                message = (
                    f"Please confirm your policy number {session.policy_details['policyno']} "
                    f"and insured name is {session.policy_details['insured_name']}. "
                    "Is this correct? Please say 'yes' or 'no'."
                )

                # streamlit UI
                text_to_speech_func_english(message)

                user_input = handle_user_input(duration=5)
                if user_input is False:
                    session.transfer_reason = "Exceed the input limit"
                    message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
                    text_to_speech_func_english(message)
                    return False


                if "yes" in user_input or "confirm" in user_input:
                    # if user_response in ['yes', 'confirm']:
                    # text_to_speech1_english("Just a moment, let me pull up your policy details.")
                    # streamlit UI
                    message = "Just a moment, let me pull up your policy details."
                    text_to_speech_func_english(message)
                    return True
                else:
                    # Handle retries for direct policy number case
                    return handle_policy_retries(session)
            else:
                session.transfer_reason = "Policy details not found for the provided policy number"
                # text_to_speech1_english("The policy details could not be found. Let me connect you with an agent.")
                # streamlit UI
                message = "The policy details could not be found. Let me connect you with an agent."
                text_to_speech_func_english(message)
                return False

        # CASE 2: Mobile number available
        elif getattr(session, 'mobile_number', None):
            mobile_number = session.mobile_number
            policy_numbers = extract_motor_policy_numbers(mobile_number)

            if not policy_numbers:
                session.transfer_reason = "No policy numbers found linked to the provided mobile number"
                # text_to_speech1_english("We could not locate any policies linked with your mobile number.")
                # streamlit UI
                message = "We could not locate any policies linked with your mobile number. Let me connect you with an agent."
                text_to_speech_func_english(message)
                return False

            confirmed_policy = None
            if len(policy_numbers) > 1:
                message = "There are multiple policies with this number. Let me confirm each one: "
                text_to_speech_func_english(message)

            for policy in policy_numbers:
                # text_to_speech1_english(f"Is your policy number {policy}? Please say 'yes' or 'confirm' if correct.")
                # streamlit UI
                message = f"Is your policy number {policy}? Please say 'yes' or 'confirm' if correct."
                text_to_speech_func_english(message)

                # user_reply = remove_fullstop_from_input(speech_to_text().strip().lower())
                # with st.spinner("Recording..."):
                #     handle_recording(duration=4)  # Assuming handle_recording is your recording function
                # user_input = remove_fullstop_from_input(speech_to_text_azure_streamlit().strip().lower())
                # with st.chat_message("user"):
                #     st.write(user_input)
                user_input = handle_user_input(duration=5)
                if user_input is False:
                    session.transfer_reason = "Exceed the input limit"
                    message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
                    text_to_speech_func_english(message)
                    return False


                if "yes" in user_input or "confirm" in user_input:
                    # if user_reply in ['yes', 'confirm']:
                    confirmed_policy = policy
                    session.policy_number = policy
                    DB_Object.policy_number=session.policy_number
                    DB_Object.save()

                    break

            if not confirmed_policy:
                session.transfer_reason = "No policy number confirmed by the user"
                # text_to_speech1_english("I couldn't confirm any policy number. Let me connect you with an agent.")
                # streamlit UI
                message = "I couldn't confirm any policy number. Let me connect you with an agent."
                text_to_speech_func_english(message)
                return False

            # Fetch and confirm details
            session.policy_details = fetch_policy_details_via_phone_number(confirmed_policy)
            if session.policy_details:
                message = (
                    f"Please confirm: Policy Number {session.policy_details['policyno']}, "
                    f"Insured Name {session.policy_details['insured_name']}. Is this correct?"
                )
                text_to_speech_func_english(message)

                # user_response = remove_fullstop_from_input(speech_to_text().strip().lower())
                # with st.spinner("Recording..."):
                #     handle_recording(duration=4)  # Assuming handle_recording is your recording function
                # user_input = remove_fullstop_from_input(speech_to_text_azure_streamlit().strip().lower())
                # with st.chat_message("user"):
                #     st.write(user_input)
                user_input = handle_user_input(duration=5)
                if user_input is False:
                    session.transfer_reason = "Exceed the input limit"
                    message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
                    text_to_speech_func_english(message)
                    return False


                if "yes" in user_input or "confirm" in user_input:
                    # text_to_speech1_english("Just a moment, let me pull up your policy details.")
                    # streamlit UI
                    message = "Just a moment, let me pull up your policy details."
                    text_to_speech_func_english(message)

                    return True
                else:
                    # Handle retries for mobile-derived policy number
                    return handle_policy_retries(session)
            else:
                session.transfer_reason = "Policy details not found for the confirmed policy number"
                # text_to_speech1_english("The policy details could not be found. Let me connect you with an agent.")
                # streamlit UI
                message = "The policy details could not be found. Let me connect you with an agent."
                text_to_speech_func_english(message)
                return False

        # CASE 3: No relevant information
        else:
            session.transfer_reason = "No policy or mobile number provided"
            # text_to_speech1_english("We need either a policy number or mobile number to proceed. Transferring you to an agent.")
            # streamlit UI
            message = "We need either a policy number or mobile number to proceed. Transferring you to an agent."
            text_to_speech_func_english(message)
            return False

    except Exception as e:
        session.transfer_reason = f"get policy details error: {str(e)}"
        # streamlit UI
        message = "I'm sorry, due to a system issue, I'm connecting you to an agent who can assist you further. Please wait."
        text_to_speech_func_english(message)
        return False


def handle_policy_retries(session: ClaimSession) -> bool:
    try:
        """Handles up to 2 retries for policy confirmation"""
        for attempt in range(2):
            # text_to_speech1_english("Please provide your policy number again.")
            # streamlit UI
            message = "Please provide your policy number again."
            text_to_speech_func_english(message)

            # new_policy = remove_fullstop_from_input(speech_to_text().strip().lower())
            # with st.spinner("Recording..."):
            #     handle_recording(duration=10)  # Assuming handle_recording is your recording function
            # new_policy = remove_fullstop_from_input(speech_to_text_azure_streamlit().strip().lower())
            # with st.chat_message("user"):
            #     st.write(new_policy)
            new_policy = handle_user_input(duration=10)
            if new_policy is False:
                session.transfer_reason = "Exceed the input limit"
                message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
                text_to_speech_func_english(message)
                return False

            # Fetch fresh details
            policy_details = fetch_policy_details_via_phone_number(new_policy)
            if not policy_details:
                # text_to_speech1_english("No policy found with that number. Please try again.")
                # streamlit UI
                message = "No policy found with that number. Please try again."
                text_to_speech_func_english(message)
                continue

            # Confirm new details
            message = (
                f"Please confirm: Policy Number {policy_details['policyno']}, "
                f"Insured Name {policy_details['insured_name']}. Is this correct?"
            )
            text_to_speech_func_english(message)

            # user_response = remove_fullstop_from_input(speech_to_text().strip().lower())
            # with st.spinner("Recording..."):
            #     handle_recording(duration=4)  # Assuming handle_recording is your recording function
            # user_input = remove_fullstop_from_input(speech_to_text_azure_streamlit().strip().lower())
            # with st.chat_message("user"):
            #     st.write(user_input)
            user_input = handle_user_input(duration=5)
            if user_input is False:
                session.transfer_reason = "Exceed the input limit"
                message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
                text_to_speech_func_english(message)
                return False

            if "yes" in user_input or "confirm" in user_input:
                session.policy_details = policy_details
                session.policy_number = new_policy
                # text_to_speech1_english("Just a moment, let me pull up your policy details.")
                # streamlit UI
                message = "Just a moment, let me pull up your policy details."
                text_to_speech_func_english(message)
                return True

            if attempt < 1:
                # text_to_speech1_english("Let's try one more time.")
                # streamlit UI
                message = "Let's try one more time."
                text_to_speech_func_english(message)

        # All retries exhausted
        session.transfer_reason = "Failed policy confirmation after 2 attempts"
        # text_to_speech1_english("We couldn't verify your policy. Transferring you to an agent.")
        # streamlit UI
        message = "We couldn't verify your policy. Transferring you to an agent."
        text_to_speech_func_english(message)
        return False

    except Exception as e:
        session.transfer_reason = f"Handle policy retries error: {str(e)}"
        # streamlit UI
        message = "I'm sorry, due to a system issue, I'm connecting you to an agent who can assist you further. Please wait."
        text_to_speech_func_english(message)
        return False


def insured_confirmation(session: ClaimSession):
    try:
        session.caller_details = {}
        # if policy_details:
        message = "Thank you. could you please confirm if you are the insured?"
        text_to_speech_func_english(message)

        # confirm_insured_or_not = str(speech_to_text()).strip().lower()
        # with st.spinner("Recording..."):
        #     handle_recording(duration=4)  # Assuming handle_recording is your recording function
        # confirm_insured_or_not = str(speech_to_text_azure_streamlit().strip().lower())
        # with st.chat_message("user"):
        #     st.write(confirm_insured_or_not)
        confirm_insured_or_not = handle_user_input(duration=5)
        if confirm_insured_or_not is False:
            session.transfer_reason = "Exceed the input limit"
            message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
            text_to_speech_func_english(message)
            return False

        if 'yes' in confirm_insured_or_not:
            session.caller_details["is_insured"] = True
            # text_to_speech1_english(f"Thank you for confirming, {session.policy_details['insured_name']}. Let's proceed with your claim.")
            # streamlit UI
            message = f"Thank you for confirming, {session.policy_details['insured_name']}. Let's proceed with your claim."
            text_to_speech_func_english(message)
            DB_Object.insured_name=session.policy_details['insured_name']
            DB_Object.is_insured=True
            DB_Object.save()
        else:
            session.caller_details["is_insured"] = False
            DB_Object.is_insured = False
            DB_Object.save()
            # text_to_speech1_english("I understand that you're not the insured. I will need to collect some information from you.")
            # streamlit UI
            message = "I understand that you're not the insured. I will need to collect some information from you."
            text_to_speech_func_english(message)

            # text_to_speech1_english("Could you please confirm your relationship with the insured?")
            # streamlit UI
            message = "Could you please confirm your relationship with the insured?"
            text_to_speech_func_english(message)

            # with st.spinner("Recording..."):
            #     handle_recording(duration=5)  # Assuming handle_recording is your recording function
            # relationship_with_insured = str(speech_to_text_azure_streamlit().strip().lower())
            # session.caller_details['relationship'] = relationship_with_insured
            # with st.chat_message("user"):
            #     st.write(relationship_with_insured)
            relationship_with_insured = handle_user_input(duration=5)
            if relationship_with_insured is False:
                session.transfer_reason = "Exceed the input limit"
                message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
                text_to_speech_func_english(message)
                return False

            session.caller_details['relationship'] = relationship_with_insured
            DB_Object.relationship=session.caller_details['relationship']
            DB_Object.save()

            # text_to_speech1_english("Please help us with your full name.")
            # streamlit UI
            message = "Please help us with your full name."
            text_to_speech_func_english(message)

            # session.caller_details['name'] = str(speech_to_text()).strip().lower()
            # with st.spinner("Recording..."):
            #     handle_recording(duration=5)  # Assuming handle_recording is your recording function
            # name_of_caller = str(speech_to_text_azure_streamlit().strip().lower())
            # session.caller_details['name'] = name_of_caller
            # with st.chat_message("user"):
            #     st.write(name_of_caller)
            name_of_caller = handle_user_input(duration=5)
            if name_of_caller is False:
                session.transfer_reason = "Exceed the input limit"
                message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
                text_to_speech_func_english(message)
                return False
            session.caller_details['name'] = name_of_caller
            DB_Object.caller_name=session.caller_details['name']
            DB_Object.save()

            # text_to_speech1_english("Please provide your mobile number.")
            # streamlit UI
            message = "Please provide your mobile number."
            text_to_speech_func_english(message)

            # mobile_number = str(speech_to_text()).strip().lower()
            # session.caller_details['mobile'] = remove_fullstop_from_input(mobile_number)

            # with st.spinner("Recording..."):
            #     handle_recording(duration=6)  # Assuming handle_recording is your recording function
            # caller_number = str(speech_to_text_azure_streamlit().strip().lower())
            # session.caller_details['mobile'] = remove_fullstop_from_input(caller_number)
            # with st.chat_message("user"):
            #     st.write(caller_number)
            caller_number = handle_user_input(duration=5)
            if caller_number is False:
                session.transfer_reason = "Exceed the input limit"
                message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
                text_to_speech_func_english(message)
                return False
            session.caller_details['mobile'] = caller_number
            DB_Object.caller_mobile=session.caller_details['mobile']
            DB_Object.save()


    except Exception as e:
        session.transfer_reason = f"Insured confirmation error: {str(e)}"
        # streamlit UI
        message = "I'm sorry, due to a system issue, I'm connecting you to an agent who can assist you further. Please wait."
        text_to_speech_func_english(message)
        return False


def claim_type(session: ClaimSession):
    try:
        session.claim_details = {}

        # text_to_speech1_english("Please confirm whether this claim is for an accident or theft.")
        # streamlit UI
        message = "Please confirm whether this claim is for an accident or theft."
        text_to_speech_func_english(message)

        # claim_type_response = str(speech_to_text()).strip().lower()
        # with st.spinner("Recording..."):
        #     handle_recording(duration=6)  # Assuming handle_recording is your recording function
        # claim_type_response = str(speech_to_text_azure_streamlit().strip().lower())
        # with st.chat_message("user"):
        #     st.write(claim_type_response)
        claim_type_response = handle_user_input(duration=5)
        if claim_type_response is False:
            session.transfer_reason = "Exceed the input limit"
            message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
            text_to_speech_func_english(message)
            return False

        prompt = f"""
        You are a claim type classifier. Your task is to strictly identify whether the given details represent an accident or theft.

        IMPORTANT RULES:
        - You MUST return ONLY ONE claim type: either "accident" or "theft".
        - If the details do NOT clearly indicate either accident or theft, respond with None.
        - Return the result in strict JSON format.
        - Do NOT provide multiple claim types or any additional explanations.

        Input Details: {claim_type_response}

        Expected Output Format:
        {{
            "claim_type": "accident" OR "claim_type": "theft"
        }}
        """

        claim_type_detail = extract_and_convert_to_json(call_openai(prompt))

        if 'theft' in claim_type_detail.get('claim_type'):
            DB_Object.claim_type="Theft"
            DB_Object.save()
            session.transfer_reason = "Theft claim requires specialist handling"
            # text_to_speech1_english(
            #     "I understand this is a theft claim. I'll need to transfer you to a specialized agent for further assistance. Please hold.")
            # streamlit UI
            message = "I understand this is a theft claim. I'll need to transfer you to a specialized agent for further assistance. Please hold."
            text_to_speech_func_english(message)

            session.claim_details['claim_type'] = 'theft'
            return False

        elif 'accident' in claim_type_detail.get('claim_type'):
            DB_Object.claim_type = "Accident"
            DB_Object.save()
            session.claim_details['claim_type'] = 'accident'
            # text_to_speech1_english("I'm sorry to hear about the accident. Have you reported the vehicle to a garage?")
            # streamlit UI
            message = "I'm sorry to hear about the accident. Have you reported the vehicle to a garage?"
            text_to_speech_func_english(message)

            # response = str(speech_to_text()).strip().lower()
            # with st.spinner("Recording..."):
            #     handle_recording(duration=6)  # Assuming handle_recording is your recording function
            # response = str(speech_to_text_azure_streamlit().strip().lower())
            # with st.chat_message("user"):
            #     st.write(response)
            response = handle_user_input(duration=5)
            if response is False:
                session.transfer_reason = "Exceed the input limit"
                message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
                text_to_speech_func_english(message)
                return False

            if 'no' in response or 'not' in response or "haven't" in response:
                session.transfer_reason = "Vehicle not reported to garage"
                # text_to_speech1_english(
                #     "Since the vehicle hasn't been reported to a garage yet, I will transfer you to an agent for further guidance on the next steps. Please hold.")
                # streamlit UI
                message = "Since the vehicle hasn't been reported to a garage yet, I will transfer you to an agent for further guidance on the next steps. Please hold."
                text_to_speech_func_english(message)

                return False

            # text_to_speech1_english(
            #     "Thank you for reporting the vehicle. I will need some details about the accident. Let's go through them one by one.")
            # streamlit UI
            message = "Thank you for reporting the vehicle. I will need some details about the accident. Let's go through them one by one."
            text_to_speech_func_english(message)

            # Collect Accident Details
            # text_to_speech1_english("Please provide the date of the accident, using the format: day, month, and year.")
            # streamlit UI
            message = "Please provide the date of the accident, using the format: date, month, and year."
            text_to_speech_func_english(message)

            # with st.spinner("Recording..."):
            #     handle_recording(duration=6)  # Assuming handle_recording is your recording function
            # accident_date = str(speech_to_text_azure_streamlit().strip().lower())
            # accident_date = convert_to_dd_mm_yyyy(accident_date)
            # with st.chat_message("user"):
            #     st.write(accident_date)
            accident_date = handle_user_input(duration=6)
            if accident_date is False:
                session.transfer_reason = "Exceed the input limit"
                message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
                text_to_speech_func_english(message)
                return False

            accident_date = convert_to_dd_mm_yyyy(accident_date)
            DB_Object.accident_date=accident_date
            DB_Object.save()

            policy_end_date = session.policy_details.get('policy_end_date')
            policy_start_date = session.policy_details.get('policy_start_date')

            policy_end_date = datetime.strptime(policy_end_date, "%d-%m-%Y")
            policy_start_date = datetime.strptime(policy_start_date, "%d-%m-%Y")

            DB_Object.policy_end_date = policy_end_date
            DB_Object.policy_start_date=policy_start_date
            DB_Object.save()

            formatted_accident_date = datetime.strptime(accident_date, "%d/%m/%Y")
            if policy_start_date < formatted_accident_date < policy_end_date:
                session.claim_details['accident_date'] = accident_date
            # else:
            #     message = "Date of loss should be within policy period. I'll transfer you to an agent for further details. Please hold."
            #     text_to_speech_azure_streamlit(input_text=message)
            #     with st.chat_message("assistant"):
            #         st.write(message)
            #     play_audio()
            #     time.sleep(calculate_length_of_audio())  # handle time dynamically
            #     session.transfer_reason = "Policy is Expired."
            #     return False
            else:
                # message = "Date of loss should be within policy period. Let's"
                message = "Please ensure the date of loss falls within the policy period. Let’s give it another try. Kindly share the date again."
                text_to_speech_func_english(message)

                accident_date = handle_user_input(duration=6)
                if accident_date is False:
                    session.transfer_reason = "Exceed the input limit"
                    message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
                    text_to_speech_func_english(message)
                    return False

                accident_date = convert_to_dd_mm_yyyy(accident_date)
                formatted_accident_date = datetime.strptime(accident_date, "%d/%m/%Y")

                if policy_start_date < formatted_accident_date < policy_end_date:
                    session.claim_details['accident_date'] = accident_date
                else:
                    message = "Date of loss should be within policy period. I'll transfer you to an agent for further details. Please hold."
                    text_to_speech_func_english(message)
                    session.transfer_reason = "Policy is Expired."
                    return False



            # text_to_speech1_english("Please provide the time of the accident.")
            # streamlit UI
            message = "Please provide the time of the accident."
            text_to_speech_func_english(message)

            # accident_time = str(speech_to_text()).strip().lower()
            # with st.spinner("Recording..."):
            #     handle_recording(duration=6)  # Assuming handle_recording is your recording function
            # accident_time = str(speech_to_text_azure_streamlit().strip().lower())
            # with st.chat_message("user"):
            #     st.write(accident_time)
            accident_time = handle_user_input(duration=5)
            if accident_time is False:
                session.transfer_reason = "Exceed the input limit"
                message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
                text_to_speech_func_english(message)
                return False


            if accident_time:
                prompt = f"""
                   You are a time modifier. Your task is to modify the time as per below given rules.

                   IMPORTANT RULES:
                   - You MUST return ONLY modified time.
                    Ex.:    '02:30 PM' should be converted to "HourOfLoss": "14", "MinOfLoss": "30"
                            '8 in the morning' should be converted to "HourOfLoss": "08", "MinOfLoss": "00"
                   - Return the result in strict JSON format.

                   Input Details: {accident_time}

                   Expected Output Format:
                   {{
                       "HourOfLoss": "Hour",
                       "MinOfLoss": "Minute"
                   }}
                   """

                hour_and_minute = extract_and_convert_to_json(call_openai(prompt))
                session.claim_details['HourOfLoss'] = hour_and_minute['HourOfLoss']
                DB_Object.HourOfLoss=session.claim_details['HourOfLoss']
                session.claim_details['MinOfLoss'] = hour_and_minute['MinOfLoss']
                DB_Object.MinOfLoss=session.claim_details['MinOfLoss']
                DB_Object.save()

            # text_to_speech1_english("Please provide the location of the accident.")
            # streamlit UI
            message = "Please provide the location of the accident."
            text_to_speech_func_english(message)

            # with st.spinner("Recording..."):
            #     handle_recording(duration=6)  # Assuming handle_recording is your recording function
            # accident_location = str(speech_to_text_azure_streamlit().strip().lower())
            # session.claim_details['accident_location'] = accident_location
            # with st.chat_message("user"):
            #     st.write(accident_location)
            accident_location = handle_user_input(duration=5)
            if accident_location is False:
                session.transfer_reason = "Exceed the input limit"
                message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
                text_to_speech_func_english(message)
                return False

            session.claim_details['accident_location'] = accident_location

            DB_Object.accident_location=session.claim_details['accident_location']
            DB_Object.save()

            message = "Please provide the driver Name."
            text_to_speech_func_english(message)

            # with st.spinner("Recording..."):
            #     handle_recording(duration=6)  # Assuming handle_recording is your recording function
            # driver_info = str(speech_to_text_azure_streamlit().strip().lower())
            # session.claim_details['driver_info'] = driver_info
            # with st.chat_message("user"):
            #     st.write(driver_info)
            driver_info = handle_user_input(duration=5)
            if driver_info is False:
                session.transfer_reason = "Exceed the input limit"
                message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
                text_to_speech_func_english(message)
                return False

            session.claim_details['driver_info'] = driver_info
            DB_Object.driver_info=session.claim_details['driver_info']
            DB_Object.save()

            # text_to_speech1_english("Please provide some information about the accident.")
            # streamlit UI
            message = "Please provide some information about the accident."
            text_to_speech_func_english(message)

            # with st.spinner("Recording..."):
            #     handle_recording(duration=10)  # Assuming handle_recording is your recording function
            # accident_info = str(speech_to_text_azure_streamlit().strip().lower())
            # session.claim_details['accident_info'] = accident_info
            # with st.chat_message("user"):
            #     st.write(accident_info)
            accident_info = handle_user_input(duration=10)
            if accident_info is False:
                session.transfer_reason = "Exceed the input limit"
                message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
                text_to_speech_func_english(message)
                return False

            session.claim_details['accident_info'] = accident_info

            DB_Object.accident_info=session.claim_details['accident_info']
            DB_Object.save()

            return True

    except Exception as e:
        session.transfer_reason = f"Claim type error: {str(e)}"
        # streamlit UI
        message = "I'm sorry, due to a system issue, I'm connecting you to an agent who can assist you further. Please wait."
        text_to_speech_func_english(message)

        return False


def garage_validation(session: ClaimSession):
    try:
        session.garage_details = {}

        # Step 1: Ask for pincode
        # text_to_speech1_english("Please provide the pincode of the garage.")
        # streamlit UI
        message = "Please provide the pincode of the garage."
        text_to_speech_func_english(message)

        # with st.spinner("Recording..."):
        #     handle_recording(duration=5)  # Assuming handle_recording is your recording function
        # pincode_input = str(speech_to_text_azure_streamlit().strip().lower())
        # with st.chat_message("user"):
        #     st.write(pincode_input)
        pincode_input = handle_user_input(duration=5)
        if pincode_input is False:
            session.transfer_reason = "Exceed the input limit"
            message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
            text_to_speech_func_english(message)
            return False

        pincode = re.sub(r"[.-]", "", pincode_input)
        DB_Object.Garage_Pincode=pincode
        DB_Object.save()

        # text_to_speech1_english("Thank you for providing the pincode. I'm now checking our records for that pincode.")
        # streamlit UI
        message = "Thank you for providing the pincode. I'm now checking our records for that pincode."
        text_to_speech_func_english(message)

        # # Step 2: Query database
        records = fetch_garage(pincode=pincode)

        # Step 3: Handle no garages found
        if len(records) == 0:
            session.transfer_reason = "No garages found in pincode"
            # text_to_speech1_english(
            #     "No garages were found in that pincode. I will now transfer you to an agent for further assistance. Please hold.")
            # streamlit UI
            message = "No garages were found in that pincode. I will now transfer you to an agent for further assistance. Please hold."
            text_to_speech_func_english(message)
            return False

        # Step 4: Single garage found
        elif len(records) == 1:
            garage = {
                'GarageID': records[0][0],
                'GarageName': records[0][4],
                'Address': records[0][5],
                'Pincode': records[0][6]
            }

            # confirm_message = f"We found the garage {garage['GarageName']} located at {garage['Address']}. Is this correct?"
            # text_to_speech1_english(confirm_message)
            # streamlit UI
            message = f"We found the garage {garage['GarageName']} located at {remove_special_characters_except_comma(garage['Address'])}. Is this correct?"
            text_to_speech_func_english(message)

            # confirmation = str(speech_to_text()).strip().lower()
            # with st.spinner("Recording..."):
            #     handle_recording(duration=5)  # Assuming handle_recording is your recording function
            # confirmation = str(speech_to_text_azure_streamlit().strip().lower())
            # with st.chat_message("user"):
            #     st.write(confirmation)
            confirmation = handle_user_input(duration=5)
            if confirmation is False:
                session.transfer_reason = "Exceed the input limit"
                message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
                text_to_speech_func_english(message)
                return False

            if 'yes' in confirmation or 'correct' in confirmation:
                # text_to_speech1_english("The garage has been verified in our system. Let's proceed with the claim.")
                # streamlit UI
                message = "The garage has been verified in our system. Let's proceed with the claim."
                text_to_speech_func_english(message)

                session.garage_details = garage
                return True
            else:
                session.transfer_reason = "User rejected single garage match"
                message = "Please hold while I transfer you to an agent for further assistance."
                text_to_speech_func_english(message)
                return False

        # Step 5: Multiple garages found
        else:
            # Multiple garages found, ask for garage name
            message = "We found multiple garages in that pincode. Please provide the name of the garage."
            text_to_speech_func_english(message)

            # garage_name_input = str(speech_to_text()).strip().lower()
            # with st.spinner("Recording..."):
            #     handle_recording(duration=5)  # Assuming handle_recording is your recording function
            # garage_name_input = str(speech_to_text_azure_streamlit().strip().lower())
            # with st.chat_message("user"):
            #     st.write(garage_name_input)
            garage_name_input = handle_user_input(duration=5)
            if garage_name_input is False:
                session.transfer_reason = "Exceed the input limit"
                message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
                text_to_speech_func_english(message)
                return False


            garage_name = re.sub(r"[.-]", "", garage_name_input)

            # Filter records by garage name (case-insensitive partial match)
            matching_garages = []
            for record in records:
                if garage_name in record[4].lower():
                    matching_garages.append({
                        'GarageID': record[0],
                        'GarageName': record[4],
                        'Address': record[5],
                        'Pincode': record[6]
                    })
            # No name matches
            if len(matching_garages) == 0:
                # text_to_speech1_english("No exact matches found. Let me list all garages in this pincode for confirmation:")
                # streamlit UI
                message = "No exact matches found. Let me list all garages in this pincode for confirmation:"
                text_to_speech_func_english(message)
                selected_garage = None

                # List all garages in the pincode for confirmation
                for record in records:
                    garage = {
                        'GarageID': record[0],
                        'GarageName': record[4],
                        'Address': record[5],
                        'Pincode': record[6]
                    }
                    # confirm_msg = f"Did you mean {garage['GarageName']} located at {garage['Address']}?"
                    # text_to_speech1_english(confirm_msg)
                    # streamlit UI
                    message = f"Did you mean {garage['GarageName']} located at {remove_special_characters_except_comma(garage['Address'])}?"
                    text_to_speech_func_english(message)

                    # response = str(speech_to_text()).strip().lower()
                    # with st.spinner("Recording..."):
                    #     handle_recording(duration=5)  # Assuming handle_recording is your recording function
                    # response = str(speech_to_text_azure_streamlit().strip().lower())
                    # with st.chat_message("user"):
                    #     st.write(response)
                    response = handle_user_input(duration=5)
                    if response is False:
                        session.transfer_reason = "Exceed the input limit"
                        message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
                        text_to_speech_func_english(message)
                        return False

                    if 'yes' in response or 'correct' in response:
                        selected_garage = garage
                        break

                if selected_garage:
                    # text_to_speech1_english(
                    #     f"Confirmed {selected_garage['GarageName']}. The garage has been verified. Let's proceed with the claim.")
                    # streamlit UI
                    message = f"Confirmed {selected_garage['GarageName']}. The garage has been verified. Let's proceed with the claim."
                    text_to_speech_func_english(message)
                    session.garage_details = selected_garage
                    DB_Object.GarageName=selected_garage['GarageName']
                    DB_Object.save()
                    return True
                else:
                    session.transfer_reason = "No garage selected from multiple options"
                    message = "None of the garages matched your request. Please hold while I transfer you to an agent for further assistance."
                    text_to_speech_func_english(message)
                    return False

            # Single name match
            elif len(matching_garages) == 1:
                garage = matching_garages[0]
                # confirm_message = f"We found {garage['GarageName']} located at {garage['Address']}. Is this correct?"
                # text_to_speech1_english(confirm_message)
                # streamlit UI
                message = f"We found {garage['GarageName']} located at {remove_special_characters_except_comma(garage['Address'])}. Is this correct?"
                text_to_speech_func_english(message)

                # confirmation = str(speech_to_text()).strip().lower()
                # with st.spinner("Recording..."):
                #     handle_recording(duration=5)  # Assuming handle_recording is your recording function
                # confirmation = str(speech_to_text_azure_streamlit().strip().lower())
                # with st.chat_message("user"):
                #     st.write(confirmation)
                confirmation = handle_user_input(duration=5)
                if confirmation is False:
                    session.transfer_reason = "Exceed the input limit"
                    message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
                    text_to_speech_func_english(message)
                    return False

                if 'yes' in confirmation or 'correct' in confirmation:
                    # text_to_speech1_english("The garage has been verified in our system. Let's proceed with the claim.")
                    # streamlit UI
                    message = "The garage has been verified in our system. Let's proceed with the claim."
                    text_to_speech_func_english(message)
                    session.garage_details = garage
                    return True
                else:
                    session.transfer_reason = "User rejected single name-matched garage"
                    # text_to_speech1_english("Please hold while I transfer you to an agent for further assistance.")
                    # streamlit UI
                    message = "Please hold while I transfer you to an agent for further assistance."
                    text_to_speech_func_english(message)
                    return False

            # Multiple name matches
            else:
                message = "There are multiple garages with that name. Let me confirm each one:"
                text_to_speech_func_english(message)
                selected_garage = None

                for garage in matching_garages:
                    # confirm_msg = f"Is it {garage['GarageName']} located at {garage['Address']}?"
                    # text_to_speech1_english(confirm_msg)
                    # streamlit UI
                    message = f"Is it {garage['GarageName']} located at {remove_special_characters_except_comma(garage['Address'])}?"
                    text_to_speech_func_english(message)

                    # response = str(speech_to_text()).strip().lower()
                    # with st.spinner("Recording..."):
                    #     handle_recording(duration=5)  # Assuming handle_recording is your recording function
                    # response = str(speech_to_text_azure_streamlit().strip().lower())
                    # with st.chat_message("user"):
                    #     st.write(response)
                    response = handle_user_input(duration=5)
                    if response is False:
                        session.transfer_reason = "Exceed the input limit"
                        message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
                        text_to_speech_func_english(message)
                        return False

                    if 'yes' in response or 'correct' in response:
                        selected_garage = garage
                        break

                if selected_garage:
                    # text_to_speech1_english(
                    #     f"You have confirmed {selected_garage['GarageName']}. The garage has been verified. Let's proceed with the claim.")
                    # streamlit UI
                    message = f"You have confirmed {selected_garage['GarageName']} located at {remove_special_characters_except_comma(selected_garage['Address'])}. The garage has been verified. Let's proceed with the claim."
                    text_to_speech_func_english(message)
                    session.garage_details = selected_garage
                    DB_Object.GarageName = selected_garage['GarageName']
                    DB_Object.Garage_Address=selected_garage['Address']
                    DB_Object.save()
                    return True
                else:
                    session.transfer_reason = "No garage selected from multiple name matches"
                    message = "None of the garages were selected. I will now transfer you to an agent. Please hold."
                    text_to_speech_func_english(message)
                    return False
    except Exception as e:
        session.transfer_reason = f"Garage Validation error: {str(e)}"
        # streamlit UI
        message = "I'm sorry, due to a system issue, I'm connecting you to an agent who can assist you further. Please wait."
        text_to_speech_func_english(message)
        return False


def proceed_with_claim(session):
    try:
        # Prepare API payload
        payload = {
            "PolicyNo": '160221923730000221',
            "IntimaterName": session.caller_details.get('name', session.policy_details.get('insured_name')),
            "MinOfLoss": session.claim_details.get('MinOfLoss', "57"),
            "CreatedBy": "3539",
            "IntimaterMobileNo": session.caller_details.get('mobile', session.mobile_number),
            "InsuredName": session.policy_details.get('insured_name', 'JALPAN R SHAH'),
            "LOSSDATE": session.claim_details.get('accident_date', 'N/A'),
            "DescriptionOfLoss": session.claim_details.get("accident_info", 'N/A'),
            "DriverName": session.claim_details.get('driver_info', 'Unknown'),
            "HourOfLoss": session.claim_details.get('HourOfLoss', "12"),
            "RequestSource": "4708",
            "InsuredMobileNumber": session.policy_details.get('CONTACTNO_MOBILE', '9876543210'),
            "ReasonForDelayInIntimation": "1",
            "InsuredWhatsappNumber": session.policy_details.get('CONTACTNO_MOBILE', '9876543210'),
            "InsuredEmailId": session.policy_details.get('EmailID', "a@b.com"),
            "InsuredWhatsappConsent": "True",
            "EstimatedLoss": "1",
            "GarageID": session.garage_details.get('GarageID', '0000')
        }
        DB_Object.GarageID=session.garage_details.get('GarageID', ' ')
        DB_Object.save()
        # Confirm details with user
        message = (
            "Please confirm if all details are correct: "
            f"Policy Number: {session.policy_details.get('policyno')},"
            f"Insured Name: {payload['InsuredName']}, "
            f"Accident Date: {payload['LOSSDATE']}, "
            f"Location: {session.claim_details.get('accident_location', 'N/A')}, "
            f"Driver: {payload['DriverName']}, "
            "Is this correct?"
        )
        text_to_speech_func_english(message)

        # with st.spinner("Recording..."):
        #     handle_recording(duration=5)  # Assuming handle_recording is your recording function
        # confirmation = str(speech_to_text_azure_streamlit().strip().lower())
        # with st.chat_message("user"):
        #     st.write(confirmation)
        confirmation = handle_user_input(duration=5)
        if confirmation is False:
            session.transfer_reason = "Exceed the input limit"
            message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
            text_to_speech_func_english(message)
            return False

        if 'yes' in confirmation or 'correct' in confirmation:
            message = "I'll now generate your claim intimation ID. Please wait a moment while I process this."
            text_to_speech_func_english(message)

            # API call
            response = requests.post(
                "http://mplusuat.reliancegeneral.co.in:9443/VAPTMobile/claims.svc/GETCLAIMNO_GARAGEAPP", json=payload)

            # Handle API failure
            if not response or response.status_code != 200:
                session.transfer_reason = "Claim API failure"
                message = "I'm sorry, I'm having trouble generating your claim intimation ID due to a system issue. I will transfer you to an agent who can help you further. Please hold."
                text_to_speech_func_english(message)
                return False

            # Parse the JSON response
            response_data = response.json()

            # if response_data.get("Result") and len(response_data["Result"]) > 0:
            #     session.claim_details['claim_no'] = response_data['Result'][0].get('ClaimNo', 'Unknown')
            if response_data.get("Result") and len(response_data["Result"]) > 0:
                first_result = response_data["Result"][0]
                status = first_result.get("Status")

                if status == "Success":
                    # Success case: Store ClaimNo in claim_details
                    session.claim_details['claim_no'] = first_result.get('ClaimNo', 'Unknown')
                elif status == "Failure":
                    # Failure case: Store error in transfer_reason and return False
                    error_response = first_result.get("Errorresponse", "")
                    session.transfer_reason = error_response
                    message = f"There is some technical issues, I'll transfer you to an agent for further details. Please hold."
                    text_to_speech_func_english(message)
                    return False
                else:
                    # Handle unexpected status
                    session.transfer_reason = f"Unexpected status: {status}"
                    # text_to_speech1_english("System error occurred. Transferring to agent. Please hold.")
                    # streamlit UI
                    message = "System error occurred. Transferring to agent. Please hold."
                    text_to_speech_func_english(message)
                    return False
            else:
                # Handle missing or empty Result
                session.transfer_reason = "No result data found in the response."
                # text_to_speech1_english("No result data found in the response.. Transferring to agent. Please hold.")
                # streamlit UI
                message = "No result data found in the response.. Transferring to agent. Please hold."
                text_to_speech_func_english(message)
                return False

            message = ("Claim successfully registered! Your claim intimation number is " +
                       " ".join(session.claim_details['claim_no']) +
                       ". We'll send SMS confirmation shortly.")
            text_to_speech_func_english(message)
            DB_Object.claim_no=session.claim_details['claim_no']
            DB_Object.save()
            return True

        else:
            session.transfer_reason = "User requested details correction"
            message = "I'll transfer you to an agent to correct the details. Please hold."
            text_to_speech_func_english(message)
            return False

    except Exception as e:
        session.transfer_reason = f"Claim processing error: {str(e)}"
        message = "I'm sorry, due to a system issue, I'm connecting you to an agent who can assist you further. Please wait."
        text_to_speech_func_english(message)
        return False


def conclusion_step(session):
    try:
        # streamlit UI
        message = "Thank you for contacting our claim intimation helpline. If you have any further questions or concerns, feel free to call us back or visit our website. Have a great day!"
        text_to_speech_func_english(message)
    except Exception as e:
        session.transfer_reason = f"Conclusion step error: {str(e)}"
        message = "I'm sorry, due to a system issue, I'm connecting you to an agent who can assist you further. Please wait."
        text_to_speech_func_english(message)

def claim_intimation_flow(mobile_number="8697745125"):
    session = ClaimSession()

    DB_Object =UserDetails()
    session_d="1234"
    DB_Object.session_id=session_d
    call_sid="12345678"
    DB_Object.call_sid=call_sid
    # DB_Object.mobile_number = mobile_number
    DB_Object.save()


    welcome_message = "Namaste! Welcome to our claim helpline. Would you prefer to continue in Hindi or English?"
    text_to_speech_func_english(welcome_message)
    # text_to_speech_func_english(welcome_message)

    # language_confirmation = handle_user_input(duration=5)
    language_confirmation =handle_user_input(duration=5)


    if language_confirmation is False:
        session.transfer_reason = "Exceed the input limit"
        message = "Sorry, I haven’t received any input from you, so I’ll be disconnecting the call now."
        text_to_speech_func_english(message)
        DB_Object.transfer_reason=message
        DB_Object.save()
        return False

    if 'hindi' in language_confirmation.lower():

        session.selected_language = "Hindi"
        DB_Object.selected_language = session.selected_language
        DB_Object.save()
        hindi_claim_intimation_flow(session, mobile_number)
    elif 'english' in language_confirmation.lower():
        session.selected_language = "English"
        DB_Object.selected_language = session.selected_language
        DB_Object.save()
        if validate_mobile_number(mobile_number):
            session.mobile_number = mobile_number
            DB_Object.mobile_number = session.mobile_number
            DB_Object.save()
            if not get_policy_details(session):
                print(session.__dict__)
                return redirecting_to_agent(session.transfer_reason)
        else:
            if not ask_mobile_or_policy_number(session):
                print(session.__dict__)
                return redirecting_to_agent(session.transfer_reason)
            if session.mobile_number or session.policy_number:
                if not get_policy_details(session):
                    print(session.__dict__)
                    return redirecting_to_agent(session.transfer_reason)
        if not insured_confirmation(session):
            return redirecting_to_agent(session.__dict__)
        # insured_confirmation(session)

        if not claim_type(session):
            print(session.__dict__)
            return redirecting_to_agent(session.transfer_reason)

        if not garage_validation(session):
            print(session.__dict__)
            return redirecting_to_agent(session.transfer_reason)

        if not proceed_with_claim(session):
            print(session.__dict__)
            return redirecting_to_agent(session.transfer_reason)

        conclusion_step(session)

    print(session.__dict__)


if __name__ == "__main__":
    claim_intimation_flow()