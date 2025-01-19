import os
import requests
from opencage.geocoder import OpenCageGeocode
from app.db import supabase
DEFAULT_CITY = os.getenv('DEFAULT_CITY')
DEFAULT_COUNTRY = os.getenv('DEFAULT_COUNTRY')

OPENCAGE_API_KEY = os.getenv('OPENCAGE_API_KEY')

NOMINATUM_URL = os.getenv('NOMINATUM_URL')

def get_coordinates(address):

    # if address doesn't contain Tallinn or Estonia then add to it "Tallinn, Estonia". Make sure Tallinn and/or Estonia are not displayed twice 
    if DEFAULT_CITY not in address and DEFAULT_COUNTRY not in address:
        address = f"{address}, {DEFAULT_CITY}, {DEFAULT_COUNTRY}"

    # if address doesn't contain "Tallinn" then add to it "Tallinn"
    if DEFAULT_CITY not in address:
        address = f"{address}, {DEFAULT_CITY}"

    # if address doesn't contain "Estonia" then add to it "Estonia"
    if DEFAULT_COUNTRY not in address:
        address = f"{address}, {DEFAULT_COUNTRY}"


    # Check if address is already registered in dictionary and return coordinates
    dictionary_response = supabase.table("address_directory").select("*").eq("address", address).execute()
    if dictionary_response.data:
        # print address retrieved from dictionary with all parameters printed one by one
        print(f"Address {address} already registered in dictionary table address_directory")
        print(f"Address retrieved from dictionary: {dictionary_response.data[0]}")
        print(f"Latitude: {dictionary_response.data[0]['latitude']}")
        print(f"Longitude: {dictionary_response.data[0]['longitude']}")

        return dictionary_response.data[0]["latitude"], dictionary_response.data[0]["longitude"]

    # Otherwise return getNominatumCoordinates(address)
    return getOpenCageCoordinates(address)

def getOpenCageCoordinates(address):
    geocoder = OpenCageGeocode(key=OPENCAGE_API_KEY)
    results = geocoder.geocode(address)
    if results:
        return results[0]['geometry']['lat'], results[0]['geometry']['lng']
    return None, None

# Глобальная переменная для токена
cached_token = None
cached_token_expiration = None


def getNominatumCoordinates(address):
    # if not, get coordinates from nominatum
    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "Estonians888/1.0 (zeya.metsapuu@gmail.com)"
    }
    try:
        response = requests.get(NOMINATUM_URL, params=params, headers=headers)
        print(f"Response status: {response.status_code}, Response content: {response.text}")
        if response.status_code == 200 and response.json():
            data = response.json()[0]
            # insert address into dictionary table address_directory
            supabase.table("address_directory").insert({
                "address": address,
                "latitude": data["lat"],
                "longitude": data["lon"],
                "city": DEFAULT_CITY,
                "country": DEFAULT_COUNTRY
            }).execute()
            return float(data["lat"]), float(data["lon"])
        return None, None
    except Exception as e:
        print(f"Error getting coordinates: {e}")
        return None, None