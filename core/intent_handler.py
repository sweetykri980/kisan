from utils.data_loaders import get_crop_data, get_mandi_price_data, get_schemes_data
from utils import api_clients # Assuming you have this for get_live_weather_data
from config import settings
import random

# Load all necessary data at the module level
CROP_DATA = get_crop_data()
MANDI_PRICE_DATA = get_mandi_price_data()
SCHEMES_DATA = get_schemes_data()

def _format_list_to_hindi_string(items_list):
    """Helper function to format a list into a Hindi string e.g., 'A, B और C'."""
    if not items_list:
        return ""
    if len(items_list) == 1:
        return items_list[0]
    if len(items_list) == 2:
        return " और ".join(items_list)
    # For 3 or more items: "A, B, C और D" -> "A, B, C और D"
    return ", ".join(items_list[:-1]) + " और " + items_list[-1]

def handle_intent(nlu_result):
    intent = nlu_result.get("intent")
    entities = nlu_result.get("entities", {})

    # Check if necessary data is loaded for specific intents
    crop_specific_intents = [
        "ask_crop_sowing_time", "ask_crop_general_info", "ask_crop_pests",
        "ask_crop_fertilizers", "ask_crop_soil_type", "ask_crop_irrigation"
    ]
    if intent in crop_specific_intents and not CROP_DATA:
        if settings.DEBUG_MODE: print("Intent Handler Error: Crop data not loaded for a crop-specific intent.")
        return "क्षमा करें, मैं इस समय फसल सलाहकार डेटा तक नहीं पहुंच पा रहा हूँ।"
    
    if intent == "get_mandi_price" and not MANDI_PRICE_DATA:
        if settings.DEBUG_MODE: print("Intent Handler Error: Mandi price data not loaded.")
        return "क्षमा करें, मैं इस समय मंडी भाव डेटा तक नहीं पहुंच पा रहा हूँ।"
    
    if intent == "ask_scheme_info" and not SCHEMES_DATA:
        if settings.DEBUG_MODE: print("Intent Handler Error: Schemes data not loaded.")
        return "क्षमा करें, मेरे पास अभी योजनाओं की जानकारी उपलब्ध नहीं है।"

    # --- Intent Handling Logic ---
    if intent == "get_help":
        help_message = (
            "मैं आपकी मदद कर सकता हूँ: फसल की बुवाई का समय, सामान्य जानकारी, कीट-रोग, खाद (उर्वरक), मिट्टी, और सिंचाई की जानकारी; साथ ही मौसम की जानकारी, मंडी भाव, और सरकारी योजनाओं के बारे में भी बता सकता हूँ। "
            "उदाहरण: 'गेहूं की खेती कब करें', 'धान में कीट', 'मक्का के लिए खाद', 'आलू के लिए मिट्टी', 'टमाटर में सिंचाई', 'दिल्ली में मौसम', 'कानपुर मंडी में गेहूं का भाव', 'सरकारी योजनाएं दिखाओ'। "
            "बातचीत समाप्त करने के लिए 'धन्यवाद' या 'बाय' कहें।"
        )
        return help_message

    elif intent == "get_weather":
        location = entities.get("location")
        if not location:
            return "आप किस जगह के मौसम के बारे में जानना चाहते हैं?"
        
        if settings.DEBUG_MODE: print(f"Intent Handler: Fetching weather for {location}")
        weather_data = api_clients.get_live_weather_data(location) # Assumes api_clients is imported

        if weather_data:
            try:
                city_name = weather_data.get("name", location) 
                main_weather = weather_data.get("weather", [{}])[0]
                description_hindi = main_weather.get("description", "उपलब्ध नहीं")
                main_details = weather_data.get("main", {})
                temp_celsius = main_details.get("temp")
                humidity = main_details.get("humidity")
                
                response_parts = [f"{city_name} में मौसम {description_hindi} है।"]
                if temp_celsius is not None:
                    response_parts.append(f"तापमान लगभग {temp_celsius:.1f}° सेल्सियस है")
                if humidity is not None:
                    response_parts.append(f"और हवा में नमी {humidity}% है।")
                
                return " ".join(response_parts)
            except Exception as e:
                if settings.DEBUG_MODE:
                    print(f"Intent Handler: Error parsing weather data for {location}: {e}")
                return f"क्षमा करें, {location} के लिए मौसम की जानकारी को समझने में कुछ दिक्कत हुई।"
        else:
            return f"क्षमा करें, मैं {location} के लिए मौसम की जानकारी प्राप्त नहीं कर सका। कृपया शहर का नाम जांचें या बाद में प्रयास करें।"

    elif intent == "get_mandi_price":
        crop_name = entities.get("crop_name")
        mandi_location = entities.get("mandi_location")

        if not crop_name and not mandi_location:
            return "आप किस फसल का और किस मंडी में भाव जानना चाहते हैं?"
        elif not mandi_location: # Crop specified, but not mandi
            responses = []
            if MANDI_PRICE_DATA: # Ensure data is loaded
                for mandi, crops_in_mandi in MANDI_PRICE_DATA.items():
                    if crop_name in crops_in_mandi:
                        price_info = crops_in_mandi[crop_name]
                        responses.append(f"{crop_name} का भाव {mandi} में {price_info['price']} है (आखरी अपडेट: {price_info['last_updated']})।")
            if responses:
                return " ".join(responses) if len(responses) < 3 else " विभिन्न मंडियों में भाव इस प्रकार हैं: " + " ".join(responses)
            else:
                return f"क्षमा करें, मुझे {crop_name} के लिए किसी भी मंडी में भाव की जानकारी नहीं है। आप किस मंडी के बारे में पूछ रहे हैं?"
        elif not crop_name: # Mandi specified, but not crop
            return f"आप {mandi_location} में किस फसल का भाव जानना चाहते हैं?"
        
        # Both crop_name and mandi_location are specified
        if MANDI_PRICE_DATA and mandi_location in MANDI_PRICE_DATA:
            mandi_info = MANDI_PRICE_DATA[mandi_location]
            if crop_name in mandi_info:
                price_info = mandi_info[crop_name]
                return (f"{crop_name} का भाव {mandi_location} में {price_info['price']} है। "
                        f"यह जानकारी {price_info['last_updated']} को अपडेट की गई थी।")
            else:
                return f"क्षमा करें, {mandi_location} में {crop_name} के भाव की जानकारी उपलब्ध नहीं है।"
        else: # Mandi location not found in our data
            return f"क्षमा करें, मुझे {mandi_location} की जानकारी नहीं है। मैं कुछ चुनिंदा मंडियों का ही भाव बता सकता हूँ।"

    elif intent == "ask_scheme_info":
        entities_from_nlu = entities # Use the full entities dict passed from NLU
        specific_scheme_name_query = entities_from_nlu.get("scheme_name")

        response_parts = []
        schemes_found_for_details = []

        if not isinstance(SCHEMES_DATA, list) or not SCHEMES_DATA:
            return "क्षमा करें, मेरे पास अभी योजनाओं की विस्तृत जानकारी उपलब्ध नहीं है।"

        if specific_scheme_name_query:
            for scheme in SCHEMES_DATA:
                s_name = scheme.get("name", "").lower()
                s_keywords = [k.lower() for k in scheme.get("keywords", [])]
                query_part = specific_scheme_name_query.lower()
                if query_part in s_name or query_part in s_keywords or s_name in query_part: # More flexible matching
                    schemes_found_for_details.append(scheme)
                    break 
            
        if schemes_found_for_details:
            scheme = schemes_found_for_details[0]
            response_parts.append(f"**{scheme.get('name', 'योजना')}**")
            if scheme.get('category'): response_parts.append(f"*श्रेणी:* {scheme.get('category')}")
            if scheme.get('focus'): response_parts.append(f"*मुख्य उद्देश्य:* {scheme.get('focus')}")
            if scheme.get('details'): response_parts.append(f"*विवरण:* {scheme.get('details')}")
            if scheme.get('eligibility'): response_parts.append(f"*पात्रता:* {scheme.get('eligibility')}")
            if scheme.get('advice'): response_parts.append(f"*सलाह:* {scheme.get('advice')}")
        else: 
            response_parts.append("किसानों और ग्रामीण विकास के लिए कई योजनाएं और सलाहकार सेवाएं उपलब्ध हैं।")
            filter_category = entities_from_nlu.get("filter") # NLU needs to provide this for filtering
            
            schemes_to_list_display = []
            temp_list_for_filtering = []

            if filter_category == "jharkhand":
                temp_list_for_filtering = [s for s in SCHEMES_DATA if "Jharkhand" in s.get("category", "")]
                if temp_list_for_filtering: response_parts.append("\n**झारखंड विशिष्ट योजनाएं/पहल:**")
            elif filter_category == "all_india":
                temp_list_for_filtering = [s for s in SCHEMES_DATA if "All India" in s.get("category", "")]
                if temp_list_for_filtering: response_parts.append("\n**अखिल भारतीय योजनाएं:**")
            else: # No filter or filter didn't match specific category, list a mix
                jharkhand_schemes = [s for s in SCHEMES_DATA if "Jharkhand" in s.get("category", "")]
                all_india_schemes = [s for s in SCHEMES_DATA if "All India" in s.get("category", "")]
                if jharkhand_schemes:
                    response_parts.append("\n**कुछ झारखंड विशिष्ट योजनाएं/पहल:**")
                    for i, scheme in enumerate(jharkhand_schemes[:min(3, len(jharkhand_schemes))]): response_parts.append(f"- {scheme.get('name')}")
                    if len(jharkhand_schemes) > 3: response_parts.append("  और भी...")
                if all_india_schemes:
                    response_parts.append("\n**कुछ अखिल भारतीय योजनाएं:**")
                    for i, scheme in enumerate(all_india_schemes[:min(3, len(all_india_schemes))]): response_parts.append(f"- {scheme.get('name')}")
                    if len(all_india_schemes) > 3: response_parts.append("  और भी...")
                if not jharkhand_schemes and not all_india_schemes and SCHEMES_DATA:
                    response_parts.append("\n**कुछ मुख्य योजनाएं हैं:**")
                    for i, scheme in enumerate(SCHEMES_DATA[:min(3, len(SCHEMES_DATA))]): response_parts.append(f"- {scheme.get('name')}")
            
            if temp_list_for_filtering: # if a filter was applied
                for i, scheme in enumerate(temp_list_for_filtering[:min(5, len(temp_list_for_filtering))]):
                    response_parts.append(f"- {scheme.get('name')}")
                if len(temp_list_for_filtering) > 5: response_parts.append("  और भी...")

            response_parts.append("\nआप किसी विशिष्ट योजना का नाम लेकर पूछ सकते हैं, या श्रेणी के अनुसार (जैसे 'झारखंड की योजनाएं')।")
        
        return "\n".join(response_parts)

    elif intent == "ask_crop_sowing_time":
        crop_name = entities.get("crop_name")
        if crop_name:
            crop_info = CROP_DATA.get(crop_name)
            if crop_info and "sowing_time" in crop_info:
                return f"{crop_name} की बुवाई का सही समय {crop_info['sowing_time']} है।"
            else: return f"क्षमा करें, मुझे {crop_name} की बुवाई के समय की जानकारी नहीं है।"
        else: return "आप किस फसल की बुवाई के समय के बारे में पूछ रहे हैं?"

    elif intent == "ask_crop_general_info":
        crop_name = entities.get("crop_name")
        if crop_name:
            crop_info = CROP_DATA.get(crop_name)
            if crop_info and "general_info" in crop_info and crop_info["general_info"]:
                return f"{crop_name} के बारे में यह जानकारी है: {crop_info['general_info']}"
            else: return f"क्षमा करें, मेरे पास {crop_name} के बारे में सामान्य जानकारी उपलब्ध नहीं है।"
        else: return "आप किस फसल के बारे में सामान्य जानकारी चाहते हैं?"

    elif intent == "ask_crop_pests":
        crop_name = entities.get("crop_name")
        if crop_name:
            crop_info = CROP_DATA.get(crop_name)
            if crop_info and "pests" in crop_info and crop_info["pests"]:
                return f"{crop_name} में लगने वाले प्रमुख कीट या रोग हैं: {_format_list_to_hindi_string(crop_info['pests'])}।"
            else: return f"क्षमा करें, मेरे पास {crop_name} के कीट या रोगों की विशिष्ट जानकारी उपलब्ध नहीं है।"
        else: return "आप किस फसल के कीट या रोगों के बारे में पूछ रहे हैं?"

    elif intent == "ask_crop_fertilizers":
        crop_name = entities.get("crop_name")
        if crop_name:
            crop_info = CROP_DATA.get(crop_name)
            if crop_info and "fertilizers" in crop_info and crop_info["fertilizers"]:
                fertilizer_info = crop_info["fertilizers"]
                if isinstance(fertilizer_info, dict):
                    response_parts = [f"{crop_name} के लिए खाद की सलाह:"]
                    for key, value in fertilizer_info.items():
                        response_parts.append(f"{key.capitalize()}: {value}")
                    return " ".join(response_parts)
                else:
                    return f"{crop_name} के लिए खाद की सलाह है: {fertilizer_info}"
            else: return f"क्षमा करें, मेरे पास {crop_name} के लिए खाद की विशिष्ट जानकारी उपलब्ध नहीं है।"
        else: return "आप किस फसल के लिए खाद की जानकारी चाहते हैं?"

    elif intent == "ask_crop_soil_type":
        crop_name = entities.get("crop_name")
        if crop_name:
            crop_info = CROP_DATA.get(crop_name)
            if crop_info and "soil_type" in crop_info and crop_info["soil_type"]:
                return f"{crop_name} के लिए उपयुक्त मिट्टी है: {crop_info['soil_type']}"
            else: return f"क्षमा करें, मेरे पास {crop_name} के लिए मिट्टी की विशिष्ट जानकारी उपलब्ध नहीं है।"
        else: return "आप किस फसल के लिए मिट्टी की जानकारी चाहते हैं?"

    elif intent == "ask_crop_irrigation":
        crop_name = entities.get("crop_name")
        if crop_name:
            crop_info = CROP_DATA.get(crop_name)
            if crop_info and "irrigation" in crop_info and crop_info["irrigation"]:
                return f"{crop_name} की सिंचाई के बारे में जानकारी: {crop_info['irrigation']}"
            else: return f"क्षमा करें, मेरे पास {crop_name} के लिए सिंचाई की विशिष्ट जानकारी उपलब्ध नहीं है।"
        else: return "आप किस फसल के लिए सिंचाई की जानकारी चाहते हैं?"

    else: # Default for "unknown" intent
        base_unknown_response = "क्षमा करें, मैं आपका सवाल समझ नहीं पाया।"
        if hasattr(settings, 'EXAMPLE_QUERIES') and settings.EXAMPLE_QUERIES:
            try:
                num_examples = min(2, len(settings.EXAMPLE_QUERIES))
                example_queries = random.sample(settings.EXAMPLE_QUERIES, num_examples)
                examples_text = " आप ऐसा कुछ पूछ सकते हैं: " + " या ".join([f"'{q}'" for q in example_queries])
                return base_unknown_response + examples_text
            except ValueError: # Handle case where EXAMPLE_QUERIES might be too short for num_examples
                return base_unknown_response + " आप 'मदद' या 'सहायता' कहकर जान सकते हैं कि मैं क्या कर सकता हूँ।"
            except Exception as e:
                if settings.DEBUG_MODE: print(f"Error generating example queries for unknown intent: {e}")
                return base_unknown_response + " आप 'मदद' या 'सहायता' कहकर जान सकते हैं कि मैं क्या कर सकता हूँ।"
        else:
            return base_unknown_response + " आप 'मदद' या 'सहायता' कहकर जान सकते हैं कि मैं क्या कर सकता हूँ।"

if __name__ == '__main__':
    print("Testing Intent Handler...")
    print("-" * 30)
    # Help
    nlu_res_help = {"intent": "get_help", "entities": {}}
    print(f"NLU (Help): {nlu_res_help} \n=> Response: {handle_intent(nlu_res_help)}")
    print("-" * 30)

    # Schemes Test
    print("--- Scheme Info Intent Handler Tests ---")
    if not SCHEMES_DATA:
        print("WARNING: Schemes data not loaded for testing.")
    else:
        nlu_scheme_general = {"intent": "ask_scheme_info", "entities": {}}
        print(f"NLU (General Scheme Query): {nlu_scheme_general} \n=> Response: {handle_intent(nlu_scheme_general)}")
        print("-" * 10)
        
        # Simulate NLU extracting a specific scheme name by its keyword
        # Ensure your schemes_advisory.json has a scheme with "पीएम किसान" in its name or keywords
        nlu_scheme_specific_keyword = {"intent": "ask_scheme_info", "entities": {"scheme_name": "पीएम किसान"}}
        print(f"NLU (Specific Scheme by Keyword 'पीएम किसान'): {nlu_scheme_specific_keyword} \n=> Response: {handle_intent(nlu_scheme_specific_keyword)}")
        print("-" * 10)

        # Simulate NLU extracting a scheme by its full name
        # Ensure 'Mukhyamantri Mainiya Samman Yojana (झारखंड)' is a name in your schemes_advisory.json
        nlu_scheme_specific_name = {"intent": "ask_scheme_info", "entities": {"scheme_name": "Mukhyamantri Mainiya Samman Yojana (झारखंड)"}}
        print(f"NLU (Specific Scheme by Name): {nlu_scheme_specific_name} \n=> Response: {handle_intent(nlu_scheme_specific_name)}")
        print("-" * 10)
        
        # Simulate asking for a category (NLU needs to be enhanced to set this filter)
        # nlu_scheme_jharkhand = {"intent": "ask_scheme_info", "entities": {"filter": "jharkhand"}}
        # print(f"NLU (Jharkhand Schemes Filter): {nlu_scheme_jharkhand} \n=> Response: {handle_intent(nlu_scheme_jharkhand)}")
    print("-" * 30)

    # Weather Test
    print("--- Weather Intent Handler Tests ---")
    if settings.OPENWEATHERMAP_API_KEY and settings.OPENWEATHERMAP_API_KEY != "YOUR_ACTUAL_OPENWEATHERMAP_API_KEY_HERE":
        nlu_weather1 = {"intent": "get_weather", "entities": {"location": "Delhi"}}
        print(f"NLU (Weather Delhi): {nlu_weather1} \n=> Response: {handle_intent(nlu_weather1)}")
    else:
        print("Skipping live weather test: API key not configured.")
    nlu_weather2 = {"intent": "get_weather", "entities": {"location": None}}
    print(f"NLU (Weather No Location): {nlu_weather2} \n=> Response: {handle_intent(nlu_weather2)}")
    print("-" * 30)
    
    # Add more tests for other intents if you like, for example:
    print("--- Crop Fertilizers Test ---")
    nlu_fert1 = {"intent": "ask_crop_fertilizers", "entities": {"crop_name": "गेहूं"}}
    print(f"NLU: {nlu_fert1} => Response: {handle_intent(nlu_fert1)}")
    print("-" * 30)

    # Unknown Intent Test
    print("--- Unknown Intent Test ---")
    nlu_res_unknown = {"intent": "unknown", "entities": {}}
    print(f"NLU (Unknown): {nlu_res_unknown} \n=> Response: {handle_intent(nlu_res_unknown)}")
    print("-" * 30)