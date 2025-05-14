from core import voice_input
from core import voice_output
from core import nlu_processor # To access KNOWN_CROPS, KNOWN_MANDI_CORE_LOCATIONS etc.
from core import intent_handler
from config import settings
import time

def clean_text_for_speech(text):
    """Removes common Markdown for better TTS."""
    if not text:
        return ""
    return text.replace("**", "").replace("*", "")

def run_krishi_mitra():
    # Initial greeting is now the comprehensive help message
    initial_greeting_text = intent_handler.handle_intent({"intent": "get_help", "entities": {}})
    print(f"BOT: {initial_greeting_text}")
    voice_output.speak_hindi(clean_text_for_speech(initial_greeting_text))

    awaiting_weather_location_cli = False
    
    # Context flags and storage for Mandi Price
    awaiting_mandi_info_cli = False
    pending_mandi_entities_cli = {}

    while True:
        print("-" * 20)
        user_query_text = voice_input.listen_hindi()
        bot_response_text = ""
        nlu_result_for_handler = {} # To store the NLU result that goes to the intent handler

        if user_query_text:
            print(f"आपने कहा: {user_query_text}")

            # 1. Check for Exit Commands
            exit_commands = ["धन्यवाद", "बाय", "बाय बाय", "स्टॉप", "बंद करो"]
            if any(command in user_query_text.lower() for command in exit_commands):
                bot_response_text = "आपकी सहायता करके खुशी हुई। फिर मिलेंगे!"
                # Reset all context flags on exit
                awaiting_weather_location_cli = False
                awaiting_mandi_info_cli = False
                pending_mandi_entities_cli = {}
            
            # 2. Handle Weather Location Context
            elif awaiting_weather_location_cli:
                if settings.DEBUG_MODE: print(f"CLI - Handling as weather location follow-up: {user_query_text}")
                nlu_result_for_handler = {"intent": "get_weather", "entities": {"location": user_query_text}}
                bot_response_text = intent_handler.handle_intent(nlu_result_for_handler)
                awaiting_weather_location_cli = False # Reset flag
            
            # 3. Handle Mandi Price Context
            elif awaiting_mandi_info_cli:
                if settings.DEBUG_MODE: print(f"CLI - Handling as Mandi info follow-up: {user_query_text}")
                
                potential_entity_text = user_query_text.strip()
                current_pending_entities = pending_mandi_entities_cli.copy()

                if not current_pending_entities.get("crop_name") and not current_pending_entities.get("mandi_location"):
                    is_known_crop = any(crop.lower() == potential_entity_text.lower() for crop in nlu_processor.KNOWN_CROPS)
                    is_known_mandi_core = False
                    temp_mandi_full_name = None
                    for i, core_loc_name in enumerate(nlu_processor.KNOWN_MANDI_CORE_LOCATIONS):
                        if core_loc_name.lower() == potential_entity_text.lower(): 
                            is_known_mandi_core = True
                            temp_mandi_full_name = nlu_processor.KNOWN_MANDIS[i]; break
                    if is_known_mandi_core: current_pending_entities["mandi_location"] = temp_mandi_full_name
                    elif is_known_crop: current_pending_entities["crop_name"] = potential_entity_text
                    else: current_pending_entities["crop_name"] = potential_entity_text
                elif not current_pending_entities.get("crop_name"): current_pending_entities["crop_name"] = potential_entity_text
                elif not current_pending_entities.get("mandi_location"):
                    found_mandi = False
                    for i, core_loc_name in enumerate(nlu_processor.KNOWN_MANDI_CORE_LOCATIONS):
                        if core_loc_name.lower() in potential_entity_text.lower(): current_pending_entities["mandi_location"] = nlu_processor.KNOWN_MANDIS[i]; found_mandi = True; break
                    if not found_mandi: current_pending_entities["mandi_location"] = potential_entity_text
                
                nlu_result_for_handler = {"intent": "get_mandi_price", "entities": current_pending_entities}
                bot_response_text = intent_handler.handle_intent(nlu_result_for_handler)
                
                still_awaiting_mandi = False
                if ("किस फसल का" in bot_response_text and "किस मंडी में" in bot_response_text) or \
                   (current_pending_entities.get("mandi_location") and not current_pending_entities.get("crop_name") and "किस फसल का" in bot_response_text) or \
                   (current_pending_entities.get("crop_name") and not current_pending_entities.get("mandi_location") and ("किस मंडी के बारे में" in bot_response_text or "किस मंडी में" in bot_response_text)):
                    still_awaiting_mandi = True
                    pending_mandi_entities_cli = current_pending_entities
                
                if still_awaiting_mandi: awaiting_mandi_info_cli = True
                else: awaiting_mandi_info_cli = False; pending_mandi_entities_cli = {}
            
            else:
                # 4. Normal NLU processing
                nlu_result = nlu_processor.process_query_rule_based(user_query_text)
                if settings.DEBUG_MODE: print(f"NLU Result: {nlu_result}")
                nlu_result_for_handler = nlu_result
                bot_response_text = intent_handler.handle_intent(nlu_result_for_handler)

                # --- Set context flags based on bot's response from NORMAL NLU path ---
                awaiting_weather_location_cli = False # Default reset
                if bot_response_text == "आप किस जगह के मौसम के बारे में जानना चाहते हैं?":
                    awaiting_weather_location_cli = True
                
                awaiting_mandi_info_cli = False # Default reset
                pending_mandi_entities_cli = {} 
                if nlu_result_for_handler.get("intent") == "get_mandi_price":
                    is_asking_for_both_cli = "आप किस फसल का और किस मंडी में भाव जानना चाहते हैं?" == bot_response_text
                    mandi_in_entities = nlu_result_for_handler.get("entities",{}).get('mandi_location')
                    is_asking_for_crop_cli = mandi_in_entities and f"आप {mandi_in_entities} में किस फसल का भाव जानना चाहते हैं?" == bot_response_text
                    crop_in_entities = nlu_result_for_handler.get("entities",{}).get('crop_name')
                    ask_for_mandi_template_part = "आप किस मंडी के बारे में पूछ रहे हैं?"
                    is_asking_for_mandi_cli = crop_in_entities and ask_for_mandi_template_part in bot_response_text
                    if is_asking_for_both_cli or is_asking_for_crop_cli or is_asking_for_mandi_cli:
                        awaiting_mandi_info_cli = True
                        pending_mandi_entities_cli = nlu_result_for_handler.get("entities", {}).copy()
            
            print(f"BOT: {bot_response_text}")
            cleaned_bot_response_for_speech = clean_text_for_speech(bot_response_text)
            voice_output.speak_hindi(cleaned_bot_response_for_speech)

            if "आपकी सहायता करके खुशी हुई।" in bot_response_text: # Exit condition
                break
        else:
            no_input_message = "मुझे क्षमा करें, मैं आपकी बात सुन नहीं पाया। क्या आप दोहरा सकते हैं?"
            if settings.DEBUG_MODE:
                print(f"BOT (debug - no input/error): {no_input_message}")

if __name__ == '__main__':
    try:
        run_krishi_mitra()
    except KeyboardInterrupt:
        print("\nBOT: अलविदा! कार्यक्रम समाप्त किया जा रहा है।")
        voice_output.speak_hindi("अलविदा!")
    except Exception as e:
        print(f"BOT: एक अप्रत्याशक्षित त्रुटि हुई: {e}")
        if settings.DEBUG_MODE:
            voice_output.speak_hindi("सिस्टम में एक अप्रत्याशक्षित त्रुटि हुई है।")