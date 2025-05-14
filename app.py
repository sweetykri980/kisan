import streamlit as st
from core import voice_input
from core import voice_output
from core import nlu_processor 
from core import intent_handler
from config import settings
import os
import time

# --- Helper Function for TTS Cleaning ---
def clean_text_for_speech(text):
    """Removes common Markdown for better TTS."""
    if not text:
        return ""
    return text.replace("**", "").replace("*", "")

# --- Page Configuration ---
st.set_page_config(
    page_title="कृषि मित्र AI",
    page_icon="🌾",
    layout="centered"
)

# --- App Title ---
st.title("🌾 कृषि मित्र AI - आपका डिजिटल खेती सहायक")
st.caption("खेती से सम्बंधित जानकारी के लिए मुझसे पूछें! आप अपना सवाल नीचे टाइप कर सकते हैं या 'सवाल बोलें' बटन का उपयोग कर सकते हैं।")

# --- Initialize session state variables ---
if "messages" not in st.session_state:
    initial_greeting_text = intent_handler.handle_intent({"intent": "get_help", "entities": {}})
    st.session_state.messages = [{"role": "assistant", "content": initial_greeting_text, "show_feedback": False}]
    if "greeted" not in st.session_state: 
        voice_output.speak_hindi(clean_text_for_speech(initial_greeting_text))
        st.session_state.greeted = True

if "awaiting_weather_location" not in st.session_state:
    st.session_state.awaiting_weather_location = False
if "awaiting_mandi_info" not in st.session_state:
    st.session_state.awaiting_mandi_info = False
if "pending_mandi_entities" not in st.session_state:
    st.session_state.pending_mandi_entities = {}

# --- Display chat messages ---
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"]) # Display with Markdown
        if message["role"] == "assistant" and message.get("show_feedback", False) and i > 0 : 
            feedback_key_prefix = f"feedback_{i}_" 
            cols = st.columns([1, 1, 10]) 
            with cols[0]:
                if st.button("👍", key=f"{feedback_key_prefix}up"):
                    st.toast("धन्यवाद! आपकी प्रतिक्रिया दर्ज की गई।", icon="👍")
            with cols[1]:
                if st.button("👎", key=f"{feedback_key_prefix}down"):
                    st.toast("धन्यवाद! हम इसे बेहतर बनाने का प्रयास करेंगे।", icon="👎")

# --- Function to handle processing query and getting bot response ---
def process_and_respond(user_query_text):
    if not user_query_text:
        return

    with st.chat_message("user"):
        st.markdown(user_query_text)
    st.session_state.messages.append({"role": "user", "content": user_query_text, "show_feedback": False})

    bot_response_text = ""
    nlu_result_for_handler = {} 

    exit_commands = ["धन्यवाद", "बाय", "बाय बाय", "स्टॉप", "बंद करो"]
    if any(command in user_query_text.lower() for command in exit_commands):
        bot_response_text = "आपकी सहायता करके खुशी हुई। फिर मिलेंगे!"
        st.session_state.awaiting_weather_location = False
        st.session_state.awaiting_mandi_info = False
        st.session_state.pending_mandi_entities = {}
    elif st.session_state.awaiting_weather_location:
        if settings.DEBUG_MODE: print(f"Streamlit App - Handling as weather location follow-up: {user_query_text}")
        nlu_result_for_handler = {"intent": "get_weather", "entities": {"location": user_query_text}}
        bot_response_text = intent_handler.handle_intent(nlu_result_for_handler)
        st.session_state.awaiting_weather_location = False
    elif st.session_state.awaiting_mandi_info:
        if settings.DEBUG_MODE: print(f"Streamlit App - Handling as Mandi info follow-up: {user_query_text}")
        potential_entity_text = user_query_text.strip()
        current_pending_entities = st.session_state.pending_mandi_entities.copy()
        if not current_pending_entities.get("crop_name") and not current_pending_entities.get("mandi_location"):
            is_known_crop = any(crop.lower() == potential_entity_text.lower() for crop in nlu_processor.KNOWN_CROPS)
            is_known_mandi_core = False; temp_mandi_full_name = None
            for i, core_loc_name in enumerate(nlu_processor.KNOWN_MANDI_CORE_LOCATIONS):
                if core_loc_name.lower() == potential_entity_text.lower(): is_known_mandi_core = True; temp_mandi_full_name = nlu_processor.KNOWN_MANDIS[i]; break
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
            st.session_state.pending_mandi_entities = current_pending_entities
        if still_awaiting_mandi: st.session_state.awaiting_mandi_info = True
        else: st.session_state.awaiting_mandi_info = False; st.session_state.pending_mandi_entities = {}
    else:
        nlu_result = nlu_processor.process_query_rule_based(user_query_text)
        if settings.DEBUG_MODE: print(f"Streamlit App - NLU Result: {nlu_result}")
        nlu_result_for_handler = nlu_result
        bot_response_text = intent_handler.handle_intent(nlu_result)
        st.session_state.awaiting_weather_location = False # Default reset
        if bot_response_text == "आप किस जगह के मौसम के बारे में जानना चाहते हैं?": st.session_state.awaiting_weather_location = True
        
        st.session_state.awaiting_mandi_info = False # Default reset
        st.session_state.pending_mandi_entities = {}
        if nlu_result_for_handler.get("intent") == "get_mandi_price":
            is_asking_for_both = "आप किस फसल का और किस मंडी में भाव जानना चाहते हैं?" == bot_response_text
            mandi_in_entities = nlu_result_for_handler.get("entities",{}).get('mandi_location')
            is_asking_for_crop = mandi_in_entities and f"आप {mandi_in_entities} में किस फसल का भाव जानना चाहते हैं?" == bot_response_text
            crop_in_entities = nlu_result_for_handler.get("entities",{}).get('crop_name')
            ask_for_mandi_template_part = "आप किस मंडी के बारे में पूछ रहे हैं?"
            is_asking_for_mandi = crop_in_entities and ask_for_mandi_template_part in bot_response_text
            if is_asking_for_both or is_asking_for_crop or is_asking_for_mandi:
                st.session_state.awaiting_mandi_info = True
                st.session_state.pending_mandi_entities = nlu_result_for_handler.get("entities", {}).copy()

    with st.chat_message("assistant"):
        st.markdown(bot_response_text) # Display with Markdown
    
    cleaned_bot_response_for_speech = clean_text_for_speech(bot_response_text)
    voice_output.speak_hindi(cleaned_bot_response_for_speech)
    st.session_state.messages.append({"role": "assistant", "content": bot_response_text, "show_feedback": True})

    if "आपकी सहायता करके खुशी हुई।" in bot_response_text:
         st.info("बातचीत समाप्त हो गई है। आप टैब बंद कर सकते हैं।")

text_prompt = st.chat_input("अपना सवाल यहाँ लिखें...")

if st.button("🎙️ सवाल बोलें (Speak Question)"):
    with st.spinner("सुन रहा हूँ..."):
        recognized_text = voice_input.listen_hindi()
    if recognized_text:
        st.success(f"आपने कहा (लगभग): {recognized_text}")
        process_and_respond(recognized_text)
        st.rerun() 
    else:
        st.error("क्षमा करें, मैं आपकी बात सुन नहीं पाया। कृपया दोबारा प्रयास करें या टाइप करें।")

if text_prompt:
    process_and_respond(text_prompt)
    st.rerun() # Rerun after processing text input to update the chat display