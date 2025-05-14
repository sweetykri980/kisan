import speech_recognition as sr
from config import settings # Import settings from your config package
# import wave # Not directly needed if using get_wav_data()

def listen_hindi():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        print("कृषि मित्र AI सुन रहा है... कृपया बोलिए।")
        recognizer.pause_threshold = 1
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        try:
            print("अब आप बोल सकते हैं...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

            '''# --- START DEBUG: Save captured audio ---
            if settings.DEBUG_MODE:
                try:
                    with open("captured_audio.wav", "wb") as f:
                        f.write(audio.get_wav_data())
                    print(">>> [DEBUG] Audio captured and saved to captured_audio.wav for review.")
                except Exception as e_audio_save:
                    print(f">>> [DEBUG] Error saving audio: {e_audio_save}")
            # --- END DEBUG ---'''

        except sr.WaitTimeoutError:
            # ... (rest of your code for this exception)
            if settings.DEBUG_MODE:
                print(" कोई आवाज़ नहीं मिली (Timeout).")
            return None
        # ... (other exception blocks)
        except Exception as e: # General exception for listen part
            if settings.DEBUG_MODE:
                print(f"ऑडियो सुनने में त्रुटि: {e}")
            return None


    try:
        print("पहचान रहा है...")
        query = recognizer.recognize_google(audio, language=settings.ASR_LANGUAGE)
        if settings.DEBUG_MODE:
            print(f"उपयोगकर्ता ने कहा: {query}")
        return query.lower()
        
    except sr.UnknownValueError:
        if settings.DEBUG_MODE:
            print("क्षमा करें, मैं आपकी बात समझ नहीं पाया।")
        return None
    except sr.RequestError as e:
        if settings.DEBUG_MODE:
            print(f"Google Speech Recognition सेवा से परिणाम प्राप्त करने में असमर्थ; {e}")
        return None
    except Exception as e: # General exception for recognition part
        if settings.DEBUG_MODE:
            print(f"भाषण पहचानने में एक अप्रत्याशित त्रुटि हुई: {e}")
        return None


if __name__ == '__main__':
    print("यह वॉयस इनपुट मॉड्यूल का सीधा परीक्षण है।")
    print("Ctrl+C दबाकर बाहर निकलें।")
    while True:
        recognized_text = listen_hindi()
        if recognized_text:
            print(f"पहचाना गया पाठ: {recognized_text}")
        else:
            print("कुछ भी पहचाना नहीं गया या कोई त्रुटि हुई। फिर से प्रयास कर रहा हूँ।")
        print("-" * 20)