from flask import Flask, request, jsonify
from core import nlu_processor
from core import intent_handler
from config import settings
import uuid # To generate session IDs if client doesn't send one for the first time

app = Flask(__name__)

# In-memory store for user session contexts
# In a production app, you'd use something more robust like Redis, a database, or Flask-Session
user_sessions = {}

def get_session_context(session_id):
    """Initializes or retrieves session context."""
    if session_id not in user_sessions:
        user_sessions[session_id] = {
            "awaiting_weather_location": False,
            "awaiting_mandi_info": False,
            "pending_mandi_entities": {}
            # Add any other context flags you might need in the future
        }
    return user_sessions[session_id]

def reset_mandi_context(context):
    context["awaiting_mandi_info"] = False
    context["pending_mandi_entities"] = {}

def reset_weather_context(context):
    context["awaiting_weather_location"] = False

@app.route('/')
def home():
    return "कृषि मित्र AI - API is running with context handling!"

@app.route('/ask', methods=['POST'])
def ask_krishi_mitra_contextual():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    user_query_text = data.get('query')
    session_id = data.get('session_id')

    if not user_query_text:
        return jsonify({"error": "No query provided"}), 400
    
    if not session_id:
        # If no session_id provided by client, generate one for this interaction
        # A real client should manage and resend its session_id
        session_id = str(uuid.uuid4()) 
        # return jsonify({"error": "No session_id provided"}), 400 # Or handle as new session

    # Get or initialize context for this session
    session_context = get_session_context(session_id)

    if settings.DEBUG_MODE:
        print(f"\nAPI Server - Session ID: {session_id}")
        print(f"API Server - Received query: {user_query_text}")
        print(f"API Server - Context BEFORE processing: {session_context}")

    bot_response_text = ""
    nlu_result_for_handler = {}

    # 1. Check for Exit Commands (clears context)
    exit_commands = ["धन्यवाद", "बाय", "बाय बाय", "स्टॉप", "बंद करो"]
    if any(command in user_query_text.lower() for command in exit_commands):
        bot_response_text = "आपकी सहायता करके खुशी हुई। फिर मिलेंगे!"
        reset_weather_context(session_context)
        reset_mandi_context(session_context)
        # Optionally, you could remove the session from user_sessions here if it's truly the end.
        # if session_id in user_sessions:
        #     del user_sessions[session_id]
    
    # 2. Handle Weather Location Context
    elif session_context["awaiting_weather_location"]:
        if settings.DEBUG_MODE: print(f"API Server - Handling as weather location follow-up: {user_query_text}")
        nlu_result_for_handler = {"intent": "get_weather", "entities": {"location": user_query_text}}
        bot_response_text = intent_handler.handle_intent(nlu_result_for_handler)
        reset_weather_context(session_context)
            
    # 3. Handle Mandi Price Context
    elif session_context["awaiting_mandi_info"]:
        if settings.DEBUG_MODE: print(f"API Server - Handling as Mandi info follow-up: {user_query_text}")
        potential_entity_text = user_query_text.strip()
        current_pending_entities = session_context["pending_mandi_entities"].copy()

        if not current_pending_entities.get("crop_name") and not current_pending_entities.get("mandi_location"):
            is_known_crop = any(c.lower() == potential_entity_text.lower() for c in nlu_processor.KNOWN_CROPS)
            is_known_mandi_core = any(m.lower() == potential_entity_text.lower() for m in nlu_processor.KNOWN_MANDI_CORE_LOCATIONS)
            if is_known_mandi_core:
                for i, core_loc_name in enumerate(nlu_processor.KNOWN_MANDI_CORE_LOCATIONS):
                    if core_loc_name.lower() == potential_entity_text.lower(): current_pending_entities["mandi_location"] = nlu_processor.KNOWN_MANDIS[i]; break
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
            session_context["pending_mandi_entities"] = current_pending_entities # Persist for next turn
        
        if still_awaiting_mandi: session_context["awaiting_mandi_info"] = True
        else: reset_mandi_context(session_context)
            
    else:
        # 4. Normal NLU processing
        nlu_result = nlu_processor.process_query_rule_based(user_query_text)
        if settings.DEBUG_MODE: print(f"API Server - NLU Result: {nlu_result}")
        nlu_result_for_handler = nlu_result
        bot_response_text = intent_handler.handle_intent(nlu_result)

        # --- Set context flags based on bot's response from NORMAL NLU path ---
        reset_weather_context(session_context) # Default reset
        if bot_response_text == "आप किस जगह के मौसम के बारे में जानना चाहते हैं?":
            session_context["awaiting_weather_location"] = True
        
        reset_mandi_context(session_context) # Default reset
        if nlu_result_for_handler.get("intent") == "get_mandi_price":
            is_asking_for_both = "आप किस फसल का और किस मंडी में भाव जानना चाहते हैं?" == bot_response_text
            is_asking_for_crop = nlu_result_for_handler.get("entities",{}).get('mandi_location') and "किस फसल का भाव जानना चाहते हैं" in bot_response_text
            is_asking_for_mandi = nlu_result_for_handler.get("entities",{}).get('crop_name') and ("किस मंडी के बारे में पूछ रहे हैं" in bot_response_text or "किस मंडी में भाव जानना चाहते हैं" in bot_response_text)
            if is_asking_for_both or is_asking_for_crop or is_asking_for_mandi:
                session_context["awaiting_mandi_info"] = True
                session_context["pending_mandi_entities"] = nlu_result_for_handler.get("entities", {}).copy()

    if settings.DEBUG_MODE:
        print(f"API Server - Bot Response: {bot_response_text}")
        print(f"API Server - Context AFTER processing: {session_context}")
    
    return jsonify({
        "session_id": session_id, # Return session_id so client can use it for next request
        "user_query": user_query_text,
        "nlu_intent": nlu_result_for_handler.get("intent"),
        "nlu_entities": nlu_result_for_handler.get("entities"),
        "bot_response": bot_response_text,
        "awaiting_weather_location": session_context["awaiting_weather_location"], # Optionally send context state back
        "awaiting_mandi_info": session_context["awaiting_mandi_info"]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=settings.DEBUG_MODE)