import time
import subprocess
import sys
import os
import logging
from datetime import datetime
import urllib3

# Suppress SSL warnings related to SamsungTVWS/urllib3 connection, matching original file practice
urllib3.disable_warnings()

# Ensure logging is configured
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CONFIGURATION ---
# Samsung Frame TV - UPDATE TV_IP and Apple TV MAC address
TV_IP = '10.0.1.17'
TV_POWER_PORT = 8002
FRAME_TOKEN_FILE = './frame_token.txt'
TV_DEFAULT_PORT = 8001  # Used for get_artmode

# Apple TV
ATV_ID = 'AA:AF:A1:A4:A3:AE' 

from samsungtvws import SamsungTVWS

# --- UTILITY & CONNECTION HELPERS ---

def get_tv_connection(use_auth=True):
    """Establishes the Samsung TV connection, using auth/port 8002 or default 8001"""
    if use_auth:
        # Used for power and set_artmode (requires token)
        return SamsungTVWS(TV_IP, port=TV_POWER_PORT, token_file=FRAME_TOKEN_FILE)
    else:
        # Used for get_artmode (often works without token on port 8001)
        return SamsungTVWS(TV_IP, port=TV_DEFAULT_PORT)

def _run_command(command_parts):
    """Utility to run an external command (atvremote) and return stripped stdout."""
    try:
        # Using subprocess.run to emulate Ruby's backticks (`)
        result = subprocess.run(
            command_parts,
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout.strip()
    except FileNotFoundError:
        logging.error(f"Command not found. Ensure '{command_parts[0]}' is installed and in your PATH.")
        return 'error'
    except Exception as e:
        logging.error(f"An unexpected error occurred during command execution: {e}")
        return 'error'

# --- TV / ATV STATE FUNCTIONS ---

def is_atv_on():
    """Checks if the Apple TV is on using the atvremote command line tool"""
    atv_state = 'empty'
    retries = 0
    # Ruby logic: loop until a recognizable state is returned
    while not atv_state.startswith('PowerState'):
        if atv_state != 'empty' and retries > 1:
            print(f"tv error, retrying {retries}")
        retries += 1
        time.sleep(1) if retries > 1 else None
        
        atv_state = _run_command(['atvremote', '-i', ATV_ID, 'power_state'])
        
    return atv_state == 'PowerState.On'

def get_tv_power_state():
    """Gets the power state of the Frame TV"""
    try:
        tv = get_tv_connection(use_auth=True)
        x = tv.rest_device_info()
        return x['device']['PowerState']
    except Exception as e:
        logging.warning(f"Error checking TV power status: {e}")
        return 'error'

def is_tv_standby():
    """Checks if the TV is in standby mode"""
    # Note: get_tv_power_state returns 'standby', 'on', or 'off'
    return get_tv_power_state() == 'standby'

def is_art_mode_on():
    """Checks if the Frame TV is currently in Art Mode."""
    time.sleep(0.5)
    art_mode = 'empty'
    retries = 0
    # Ruby logic: loop until status is 'on' or 'off'
    while art_mode not in ['on', 'off']:
        if art_mode != 'empty' and retries > 1:
            print(f"frame error, retrying {retries}")
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            print(f"... checking frame, status is {get_tv_power_state()}")
        retries += 1
        time.sleep(1) if retries > 1 else None
        
        try:
            # Use connection without full auth/port 8002, mimicking get_art_mode.py
            tv = get_tv_connection(use_auth=False)
            art_mode = tv.art().get_artmode()
        except Exception as e:
             logging.warning(f"Error checking Art Mode status: {e}")
             art_mode = 'error' # Force retry
        
    return art_mode == 'on'

def set_art_mode_on():
    """Turns on Art Mode"""
    try:
        tv = get_tv_connection(use_auth=True)
        tv.art().set_artmode('on')
        logging.info("Attempted to set Art Mode to 'on'.")
    except Exception as e:
        logging.error(f"Error turning Art Mode ON: {e}")

def toggle_tv_power():
    """Toggles TV power"""
    try:
        tv = get_tv_connection(use_auth=True)
        tv.shortcuts().power()
        logging.info("TV power toggled.")
    except Exception as e:
        logging.error(f"Error toggling TV power: {e}")

# --- MAIN LOOP ---

def main():
    atv_has_been_on = False
    tv_has_been_sleeping = False
    
    print("Starting Art Mode Controller. Monitoring Apple TV status...")

    while True:
        # Condition 1: Apple TV is ON and Frame TV is NOT in standby
        if is_atv_on() and not is_tv_standby():
            if not atv_has_been_on:
                print("tv turned on")
            atv_has_been_on = True
            time.sleep(1)

        # Condition 2: Apple TV is OFF
        elif not is_atv_on():
            # If Frame is already in Art Mode, just wait
            if is_art_mode_on():
                time.sleep(1)
            else:
                # Apple TV was ON previously, meaning it just turned off
                if atv_has_been_on:
                    print("tv off")
                    atv_has_been_on = False
                    print("turning frame back on")
                    toggle_tv_power()
                    print("enabling art mode\n")
                    time.sleep(0.5)
                    # Ruby logic: if Art Mode is still not on, toggle power again (forces TV to wake/change state)
                    if not is_art_mode_on():
                        toggle_tv_power()
                else:
                    # Apple TV is OFF, and was OFF before (script running, but nothing is on)
                    if is_atv_on() and is_tv_standby():
                        # This condition seems logically redundant but is retained from the Ruby script
                        print("tv on, but frame off, trying to turn on frame")
                        toggle_tv_power()
                    else:
                        # TV is likely just sleeping/off, and ATV is off
                        if not tv_has_been_sleeping:
                            print("tv appears to be sleeping")
                        tv_has_been_sleeping = True 
                        time.sleep(1)

if __name__ == "__main__":
    main()

