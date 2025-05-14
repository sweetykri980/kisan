import os
from dotenv import load_dotenv, dotenv_values

# Determine the absolute path of the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# Construct the path to the .env file located in the project root
dotenv_path = os.path.join(PROJECT_ROOT, '.env')

# --- Developer/Debug Mode ---
# Set to False for a "cleaner" run without verbose debug messages in console
# Set to True during development to see more detailed logs.
DEBUG_MODE = True # You can toggle this

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path, override=True, verbose=False)
    if DEBUG_MODE:
        print(f"DEBUG_SETTINGS: .env file found and loaded from: {dotenv_path}")
else:
    if DEBUG_MODE:
        print(f"DEBUG_SETTINGS: Warning - .env file not found at {dotenv_path}.")

# --- API Keys (Loaded from .env) ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") # Retained for potential future use
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")

# --- API Base URLs ---
OPENWEATHERMAP_BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

# --- Language Settings ---
ASR_LANGUAGE = "hi-IN"
TTS_LANGUAGE = "hi"

# --- Paths to Data Files ---
CROP_ADVISORY_FILE = os.path.join(PROJECT_ROOT, "data", "knowledge_base", "crop_advisory.json")
MANDI_PRICES_FILE = os.path.join(PROJECT_ROOT, "data", "knowledge_base", "mandi_prices.json")
SCHEMES_ADVISORY_FILE = os.path.join(PROJECT_ROOT, "data", "knowledge_base", "schemes_advisory.json")
# WEATHER_STATIC_FILE = os.path.join(PROJECT_ROOT, "data", "knowledge_base", "weather_static.json") # If you plan to use it
# LOCATIONS_FILE = os.path.join(PROJECT_ROOT, "data", "predefined_data", "locations.json") # If you plan to use it

# --- Predefined Lists ---
KNOWN_LOCATIONS_FOR_WEATHER = [
    "दिल्ली", "मुंबई", "कानपुर", "लखनऊ", "पटना", "भोपाल", "जयपुर",
    "हैदराबाद", "रांची", "रायपुर", "चंडीगढ़", "अहमदाबाद", "पुणे",
    "नागपुर", "इंदौर", "लुधियाना", "आगरा", "वाराणसी", "मेरठ",
    # Jharkhand Districts (Ensure these are in Hindi and match user queries)
    "बोकारो", "चतरा", "देवघर", "धनबाद", "दुमका", "पूर्वी सिंहभूम", "गढ़वा",
    "गिरिडीह", "गोड्डा", "गुमला", "हजारीबाग", "जामताड़ा", "खूंटी", "कोडरमा",
    "लातेहार", "लोहरदगा", "पाकुड़", "पलामू", "रामगढ़", "साहेबगंज",
    "सरायकेला खरसावां", "सिमडेगा", "पश्चिमी सिंहभूम"
]

EXAMPLE_QUERIES = [
    "गेहूं की खेती कब करें?",
    "धान के बारे में बताओ।",
    "सरसों में कौन से कीट लगते हैं?",
    "मक्का के लिए खाद की जानकारी दें।",
    "आलू के लिए मिट्टी कैसी होनी चाहिए?",
    "टमाटर में सिंचाई कब करें?",
    "कानपुर में आज मौसम कैसा है?",
    "लखनऊ मंडी में गेहूं का भाव क्या है?",
    "किसानों के लिए सरकारी योजनाएं कौन सी हैं?",
    "पीएम किसान योजना क्या है?",
    "मदद"
]

# --- Audio Settings ---
AUDIO_RESPONSE_FILENAME = "response.mp3" # Temporary file for TTS output

if DEBUG_MODE:
    print(f"DEBUG_SETTINGS: DEBUG MODE IS ON (verified in settings.py)")
    if OPENWEATHERMAP_API_KEY and OPENWEATHERMAP_API_KEY != "YOUR_ACTUAL_OPENWEATHERMAP_API_KEY_HERE": # Check it's not the placeholder
        print("DEBUG_SETTINGS: OpenWeatherMap API Key is loaded.")
    else:
        print("DEBUG_SETTINGS: Warning - OpenWeatherMap API Key is NOT loaded or is placeholder.")