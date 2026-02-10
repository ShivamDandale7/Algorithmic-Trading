from pyotp import TOTP

otp_secret = "BMPIURKWQHGV2CVOIZGNKWG4D6VDWOYH"
token = TOTP(otp_secret).now()
print("OTP: ",token)