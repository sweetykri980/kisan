import json
import os
from config import settings # To get file paths

def load_json_data(file_path):
    """
    Loads data from a JSON file.
    Args:
        file_path (str): The absolute path to the JSON file.
    Returns:
        dict or list: The data loaded from the JSON file, or None if an error occurs.
    """
    if not os.path.exists(file_path):
        if settings.DEBUG_MODE:
            print(f"Data Loader Error: File not found at {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        if settings.DEBUG_MODE:
            print(f"Data Loader Error: Could not decode JSON from {file_path}. Error: {e}")
        return None
    except Exception as e:
        if settings.DEBUG_MODE:
            print(f"Data Loader Error: An unexpected error occurred while loading {file_path}. Error: {e}")
        return None

def get_crop_data():
    """
    Loads the crop advisory data from the predefined JSON file.
    Returns:
        dict: The crop advisory data, or None if loading fails.
    """
    return load_json_data(settings.CROP_ADVISORY_FILE)

def get_mandi_price_data():
    """
    Loads the Mandi price data from the predefined JSON file.
    Returns:
        dict: The Mandi price data, or None if loading fails.
    """
    return load_json_data(settings.MANDI_PRICES_FILE)

def get_schemes_data():
    """
    Loads the schemes and advisory data from the predefined JSON file.
    Returns:
        list: The schemes and advisory data (expected to be a list of scheme objects), 
              or None if loading fails or file doesn't exist.
    """
    return load_json_data(settings.SCHEMES_ADVISORY_FILE)


if __name__ == '__main__':
    print("Testing Data Loaders...")
    print("-" * 30)
    crop_data = get_crop_data()
    if crop_data:
        print(f"Crop data loaded successfully! Found {len(crop_data)} crops.")
        # Example check, assuming 'गेहूं' exists and has new fields
        if "गेहूं" in crop_data and "irrigation" in crop_data["गेहूं"]:
            print("  गेहूं की सिंचाई जानकारी (नमूना):", crop_data["गेहूं"]["irrigation"])
        elif "गेहूं" in crop_data:
             print("  गेहूं की जानकारी मिली, पर 'irrigation' फ़ील्ड नहीं।")
        else:
            print("  गेहूं की जानकारी नहीं मिली।")
    else:
        print("फसल सलाहकार डेटा लोड करने में विफल।")

    print("-" * 30)
    mandi_data = get_mandi_price_data()
    if mandi_data:
        print(f"Mandi price data loaded successfully! Found {len(mandi_data)} mandis.")
        if "कानपुर मंडी" in mandi_data and "गेहूं" in mandi_data["कानपुर मंडी"]:
            print("  कानपुर मंडी में गेहूं का भाव:", mandi_data["कानपुर मंडी"]["गेहूं"])
        else:
            print("  कानपुर मंडी में गेहूं की जानकारी डेटा में नहीं मिली या फाइल सही नहीं है।")
    else:
        print("मंडी भाव डेटा लोड करने में विफल।")

    print("-" * 30)
    schemes_data = get_schemes_data()
    if schemes_data:
        print("Schemes advisory data loaded successfully!")
        if isinstance(schemes_data, list) and len(schemes_data) > 0:
            print(f"  Number of schemes/advisories loaded: {len(schemes_data)}")
            print(f"  Example first scheme name: {schemes_data[0].get('name', 'N/A')}")
        elif schemes_data is not None: # It loaded something, but not a non-empty list
             print("  Schemes data loaded, but it's empty or not in the expected list format.")
        # No 'else' here because load_json_data returns None on failure, caught by the 'if schemes_data:'
    else:
        print("योजनाओं की सलाह का डेटा लोड करने में विफल।")