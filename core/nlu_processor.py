from utils.data_loaders import get_crop_data, get_mandi_price_data, get_schemes_data
from config import settings # To access KNOWN_LOCATIONS_FOR_WEATHER

# Load data at module level
CROP_DATA = get_crop_data()
KNOWN_CROPS = list(CROP_DATA.keys()) if CROP_DATA else []

MANDI_PRICE_DATA = get_mandi_price_data()
KNOWN_MANDIS = list(MANDI_PRICE_DATA.keys()) if MANDI_PRICE_DATA else []
KNOWN_MANDI_CORE_LOCATIONS = [m.replace("मंडी", "").strip() for m in KNOWN_MANDIS]

SCHEMES_DATA = get_schemes_data()
KNOWN_SCHEME_KEYWORDS_FROM_DATA = []
KNOWN_SCHEME_NAMES_FROM_DATA = [] # To store canonical scheme names
if isinstance(SCHEMES_DATA, list):
    for scheme in SCHEMES_DATA:
        if scheme and isinstance(scheme.get("keywords"), list): # Check if scheme is not None
            KNOWN_SCHEME_KEYWORDS_FROM_DATA.extend([k.lower() for k in scheme["keywords"]])
        if scheme and scheme.get("name"): # Check if scheme is not None
            KNOWN_SCHEME_NAMES_FROM_DATA.append(scheme.get("name").lower())
KNOWN_SCHEME_KEYWORDS_FROM_DATA = sorted(list(set(KNOWN_SCHEME_KEYWORDS_FROM_DATA)))
KNOWN_SCHEME_NAMES_FROM_DATA = sorted(list(set(KNOWN_SCHEME_NAMES_FROM_DATA)))


KNOWN_LOCATIONS_FOR_WEATHER = settings.KNOWN_LOCATIONS_FOR_WEATHER

# Keyword Lists
SOWING_TIME_KEYWORDS = [ # ... (no changes here from last full version) ...
    "कब करें", "कब करते हैं", "कब बोना", "का समय", "का सही समय",
    "बोने का समय", "लगाने का समय", "कब लगाया जाता है", "कब बोई जाती है"
]
GENERAL_INFO_KEYWORDS = [ # ... (no changes here from last full version) ...
    "के बारे में बताओ", "के बारे में जानकारी", "जानकारी दो", "क्या है",
    "कैसी फसल है", "कैसा होता है", "विवरण दें"
]
PEST_INFO_KEYWORDS = [ # ... (no changes here, ensure "बीमारी", "बीमारियां" (if needed) are there) ...
    "में कीट", "कौन से कीट", "के कीट", "कीट की समस्या", "कीट समस्या", 
    "कौन सी बीमारी", "बीमारी", "रोग", "के रोग", "में लगने वाले रोग" # "बीमारियां" could be added if "बीमारी" isn't catching it due to pluralization issues with ASR.
]
FERTILIZER_KEYWORDS = [
    "खाद", "कौन सी खाद", "खाद कब डालें", "उर्वरक", "फर्टिलाइजर", 
    "कितनी खाद", "खाद की मात्रा",
    "खाद कब और कितनी दें", "कितनी खाद दें" # Added
]
SOIL_TYPE_KEYWORDS = [ # ... (no changes here from last full version) ...
    "मिट्टी", "कैसी मिट्टी", "किस तरह की मिट्टी", "मिट्टी की जानकारी", "भूमि", "भूमि कैसी होनी चाहिए",
    "मिट्टी का प्रकार"
]
IRRIGATION_KEYWORDS = [
    "सिंचाई", "पानी कब दें", "पानी कब देना है", # Added "पानी कब देना है"
    "कितना पानी", "पानी की आवश्यकता", "पानी कैसे दें", "सिंचाई कैसे करें",
    "सिंचाई कब करनी चाहिए" # Added for more specific phrasing
]
HELP_KEYWORDS = [ # ... (no changes here from last full version) ...
    "मदद", "सहायता", "क्या कर सकते हो", "क्या कर सकता है", "क्या कर सकते हैं",
    "कैसे इस्तेमाल करूं", "हेल्प", "उदाहरण दो", "उदाहरण बताएं"
]
WEATHER_KEYWORDS = ["मौसम", "तापमान", "बारिश", "हवा", "कैसा है आज"]
MANDI_PRICE_KEYWORDS = ["भाव", "क्या भाव है", "क्या रेट है", "दाम क्या है", "कीमत क्या है", "मंडी में", "का रेट", "का भाव", "का दाम"]
CROP_KEYWORDS = ["की खेती", "की फसल", "की बुवाई", "फसल"] # General crop related, not for intent directly
SCHEME_KEYWORDS = ["योजना", "स्कीम", "सब्सिडी", "सरकारी मदद", "लोन", "ऋण", "कार्यक्रम", "सरकारी योजना", "सलाह"]


def process_query_rule_based(query_text):
    if not query_text: return {"intent": "unknown", "entities": {}}
    query_lower = query_text.lower()

    # Priority 1: Help
    for keyword in HELP_KEYWORDS:
        if keyword.lower() in query_lower: return {"intent": "get_help", "entities": {}}

    # Priority 2: Weather
    identified_loc_weather = None; is_weather_q = any(wk.lower() in query_lower for wk in WEATHER_KEYWORDS)
    if is_weather_q:
        for loc in KNOWN_LOCATIONS_FOR_WEATHER:
            if loc.lower() in query_lower: identified_loc_weather = loc; return {"intent": "get_weather", "entities": {"location": identified_loc_weather}}
        if identified_loc_weather is None and is_weather_q: return {"intent": "get_weather", "entities": {"location": None}}

    # Priority 3: Mandi Price
    is_mandi_q = any(mpk.lower() in query_lower for mpk in MANDI_PRICE_KEYWORDS)
    identified_mandi = None; identified_crop_mandi = None
    if is_mandi_q:
        for i, core_loc in enumerate(KNOWN_MANDI_CORE_LOCATIONS):
            if core_loc.lower() in query_lower: identified_mandi = KNOWN_MANDIS[i]; break
        if not identified_mandi:
            for mandi_name in KNOWN_MANDIS:
                if mandi_name.lower() in query_lower: identified_mandi = mandi_name; break
        for crop in KNOWN_CROPS: # Use KNOWN_CROPS for consistency
            if crop.lower() in query_lower: identified_crop_mandi = crop; break
        if identified_crop_mandi or identified_mandi:
            entities = {};
            if identified_crop_mandi: entities["crop_name"] = identified_crop_mandi
            if identified_mandi: entities["mandi_location"] = identified_mandi
            return {"intent": "get_mandi_price", "entities": entities}
        elif is_mandi_q: return {"intent": "get_mandi_price", "entities": {}}

    # Priority 4: Scheme Info
    is_scheme_q = any(sk.lower() in query_lower for sk in SCHEME_KEYWORDS) # General scheme keywords
    extracted_scheme_name = None # This will store the canonical name of the matched scheme

    if isinstance(SCHEMES_DATA, list): # Ensure SCHEMES_DATA is loaded and is a list
        for scheme in SCHEMES_DATA:
            if scheme: # Ensure scheme object is not None
                s_name = scheme.get("name", "").lower()
                s_keywords_from_json = [k.lower() for k in scheme.get("keywords", [])] # Keywords from JSON

                # Check if the query contains the scheme's main name (or part of it)
                if s_name and s_name in query_lower: # Check if full scheme name is in query
                    extracted_scheme_name = scheme.get("name") # Use the canonical name
                    break 
                # Check if the query contains any of the scheme's specific keywords from JSON
                for json_keyword in s_keywords_from_json:
                    if json_keyword in query_lower: # Check if a defined keyword is in the query
                        extracted_scheme_name = scheme.get("name") # Return the canonical name
                        break
            if extracted_scheme_name: # If found by its specific keywords or name, break outer loop
                break
    
    if is_scheme_q or extracted_scheme_name: # If general scheme keywords OR a specific scheme was identified
        entities = {}
        if extracted_scheme_name:
            entities["scheme_name"] = extracted_scheme_name
        # You could add more entity extraction here e.g. "झारखंड की योजनाएं" -> filter: "jharkhand"
        if "झारखंड" in query_lower and ("योजना" in query_lower or "स्कीम" in query_lower):
            entities["filter"] = "jharkhand"
        elif ("केंद्र" in query_lower or "भारत" in query_lower or "अखिल भारतीय" in query_lower) and ("योजना" in query_lower or "स्कीम" in query_lower):
            entities["filter"] = "all_india"
        return {"intent": "ask_scheme_info", "entities": entities}

    # Priority 5: Other Crop-Specific Intents
    identified_crop_agri = None
    for crop in KNOWN_CROPS:
        if crop.lower() in query_lower: identified_crop_agri = crop; break
        for ck in CROP_KEYWORDS:
            if f"{crop.lower()} {ck.lower()}" in query_lower: identified_crop_agri = crop; break
        if identified_crop_agri: break

    if identified_crop_agri:
        entities_agri = {"crop_name": identified_crop_agri}
        # Order of checks for crop specific details (more specific keywords first)
        for k in PEST_INFO_KEYWORDS:
            if k.lower() in query_lower: return {"intent": "ask_crop_pests", "entities": entities_agri}
        for k in FERTILIZER_KEYWORDS:
            if k.lower() in query_lower: return {"intent": "ask_crop_fertilizers", "entities": entities_agri}
        for k in SOIL_TYPE_KEYWORDS:
            if k.lower() in query_lower: return {"intent": "ask_crop_soil_type", "entities": entities_agri}
        for k in IRRIGATION_KEYWORDS:
            if k.lower() in query_lower: return {"intent": "ask_crop_irrigation", "entities": entities_agri}
        for k in SOWING_TIME_KEYWORDS: # Sowing time often uses general "कब करें"
            if k.lower() in query_lower: return {"intent": "ask_crop_sowing_time", "entities": entities_agri}
        for k in GENERAL_INFO_KEYWORDS: # General info last among crop specific
            if k.lower() in query_lower: return {"intent": "ask_crop_general_info", "entities": entities_agri}
            
    return {"intent": "unknown", "entities": {}}

if __name__ == '__main__':
    print("Testing NLU Processor (Rule-Based)...")
    if not CROP_DATA: print("WARNING: Crop data not loaded.")
    else: print(f"Loaded crops: {len(KNOWN_CROPS)} crops - e.g., {KNOWN_CROPS[:3] if KNOWN_CROPS else 'None'}")
    if not MANDI_PRICE_DATA: print("WARNING: Mandi price data not loaded.")
    else: print(f"Loaded Mandis: {len(KNOWN_MANDIS)} mandis - (Core e.g.: {KNOWN_MANDI_CORE_LOCATIONS[:3] if KNOWN_MANDI_CORE_LOCATIONS else 'None'})")
    if not SCHEMES_DATA: print("WARNING: Schemes data not loaded.")
    else: print(f"Loaded Schemes: {len(SCHEMES_DATA)} (Sample keywords from data: {KNOWN_SCHEME_KEYWORDS_FROM_DATA[:3] if KNOWN_SCHEME_KEYWORDS_FROM_DATA else 'None'})")
    print(f"Known Locations for Weather: {len(KNOWN_LOCATIONS_FOR_WEATHER)} locations - e.g., {KNOWN_LOCATIONS_FOR_WEATHER[:3] if KNOWN_LOCATIONS_FOR_WEATHER else 'None'}")
    print("-" * 30)

    queries = [
        "मदद करो", "आप क्या कर सकते हैं?",
        "आज कानपुर में मौसम कैसा है", "मौसम कैसा है",
        "गेहूं की खेती कब करें", "गेहूं के बारे में बताओ", "गेहूं में कौन से कीट लगते हैं",
        "गेहूं में कौन सी खाद डालें?", "गेहूं के लिए मिट्टी कैसी चाहिए?", "गेहूं में सिंचाई कब करें?",
        "कानपुर मंडी में गेहूं का भाव क्या है?", "गेहूं का दाम",
        "किसानों के लिए सरकारी योजनाएं कौन सी हैं?",
        "पीएम किसान योजना के बारे में बताओ", # Example of specific scheme query
        "नाबार्ड की योजना", # Example of query that might match a keyword in schemes data
        "झारखंड की योजनाएं", # Example of category filter
        "धन्यवाद", "कुछ भी ऊल जलूल",
    ]
    for q in queries:
        result = process_query_rule_based(q)
        print(f"Query: '{q}' => Intent: {result['intent']}, Entities: {result['entities']}")