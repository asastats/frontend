import base64

from algosdk import encoding

from nameservice.anssdk import constants


def is_valid_address(address):
    return encoding.is_valid_address(address)


def decode_value(value):
    try:
        return base64.b64decode(value).decode()
    except Exception as e:
        return ""


def decode_address(address):
    return encoding.encode_address(base64.b64decode(address))


def is_valid_name(name):
    valid = True
    for letter in name:
        ascii_code = ord(letter)
        if (
            ascii_code >= constants.ASCII_LOWER_CASE_A
            and ascii_code <= constants.ASCII_LOWER_CASE_Z
        ):
            continue
        elif (
            ascii_code >= constants.ASCII_DIGIT_0
            and ascii_code <= constants.ASCII_DIGIT_9
        ):
            continue
        else:
            valid = False

    if valid is not True:
        raise Exception(
            "Invalid domain name. Domain names only have a character set a-z and 0-9"
        )

    return valid
