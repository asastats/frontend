"""Django settings module used for NFT model training."""

from pathlib import Path

from .base import *

DATA_PATH = Path("/home/ipaleka/asa/") / "data"

NFT_DATA_SERVER = "192.99.167.63"
NFT_DATA_SERVER_USER = "asastats"
NFT_DATA_SERVER_DATA_PATH = "/var/www/asastats.com/data"

ASASTATS_API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzI1Mjk2NzcxLCJpYXQiOjE2OTM3NjA3NzEsImp0aSI6IjZlMjY0ZGNhZjgxOTRiODZhZWMwYzAxMzNkNjE1NTE3IiwidXNlcl9pZCI6MTR9.dsxMTUVOTPmbSbegO5Sa6-kiBK_2RLyXrr6H6aiIKOs"
