# from twilio.rest import Client

# # Your Twilio credentials (from https://www.twilio.com/console)
# account_sid = ""
# auth_token = ""
# twilio_number = ""  # Your Twilio phone number (E.164 format)

# # Initialize client
# client = Client(account_sid, auth_token)

# # Phone number to call (must be verified in Twilio if trial account)
# to_number = "+918709476349"  # Replace with recipient's phone number

# # Make the call
# call = client.calls.create(
#     to=to_number,
#     from_=twilio_number,
#     twiml='<Response><Say voice="alice">Hello! This is a test call from Twilio in Python.</Say></Response>'
# )

# print(f"Call initiated. SID: {call.sid}")
