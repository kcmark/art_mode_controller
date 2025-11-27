# art_mode_controller
Python script consolidated from work by donkthemagicllama
This script will monitor appletv and frametv to reset art mode when appletv is turned off. Frame TV does not handle this correctly.

Samsung The Frame TV Art Mode forcer - consolidated and rewritten fully in python from the original ruby version created by donkthemagicllama. 


Prerequisites

This requires installing 2 different python libraries:

https://github.com/postlund/pyatv 

https://github.com/NickWaterton/samsung-tv-ws-api

You should ensure your Frame TV has a static IP address and that you know what it is.

You'll need set up the Apple TV you plan to use with pyatv
run **atvremote wizard**
select your Apple TV and follow the prompts, note the MAC address

You'll need to create a token for your Frame TV using samsung-tv-ws-api
run python3 and execute the following

**from samsungtvws import SamsungTVWS**

**tv = SamsungTVWS(host='<frame_ip_address>', port=8002, token_file='frame_token.txt')**

**tv.shortcuts().power()** -- watch your TV, you should be required to accept a security prompt using your Frame remote

**quit()**
Customize Scripts Below

Update the AppleTV MAC and the IP of your TV and execute the python script. 
