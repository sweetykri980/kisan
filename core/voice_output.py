from gtts import gTTS
import os
from playsound import playsound
from config import settings # To get the TTS language and response filename

def speak_hindi(text_to_speak):
    if not text_to_speak:
        if settings.DEBUG_MODE:
            print("TTS: No text provided to speak.")
        return

    # Define the audio file path using PROJECT_ROOT from settings
    audio_file_path = os.path.join(settings.PROJECT_ROOT, settings.AUDIO_RESPONSE_FILENAME)

    try:
        if settings.DEBUG_MODE:
            print(f"TTS: Attempting to speak: '{text_to_speak}'")

        # Create gTTS object
        tts = gTTS(text=text_to_speak, lang=settings.TTS_LANGUAGE, slow=False)
        
        # Save the audio file
        tts.save(audio_file_path)

        # Play the audio file
        playsound(audio_file_path)

        if settings.DEBUG_MODE:
            print(f"TTS: Successfully played: '{text_to_speak}'")

    except ImportError:
        if settings.DEBUG_MODE:
            print("TTS Error: gTTS or playsound library not found. Please install them using 'pip install gTTS playsound==1.2.2'.")
        print(f"BOT (audio fallback): {text_to_speak}") # Fallback
    except Exception as e:
        if settings.DEBUG_MODE:
            print(f"TTS Error: An error occurred during text-to-speech: {e}")
        print(f"BOT (audio fallback): {text_to_speak}") # Fallback
    finally:
        # After attempting to play (whether successful or not), try to remove the temporary audio file.
        if os.path.exists(audio_file_path):
            try:
                os.remove(audio_file_path)
                if settings.DEBUG_MODE: # Optional: uncomment to confirm deletion
                    print(f"TTS: Temporary audio file '{audio_file_path}' removed.")
            except Exception as e_remove:
                # If removal fails (e.g., still locked for some reason), print a debug message.
                # This might still happen if playsound is extremely slow to release, but it's less likely.
                if settings.DEBUG_MODE:
                    print(f"TTS: Error removing temporary audio file '{audio_file_path}': {e_remove}")

if __name__ == '__main__':
    print("यह वॉयस आउटपुट मॉड्यूल का सीधा परीक्षण है।")
    
    speak_hindi("नमस्ते, यह एक परीक्षण है।")
    speak_hindi("कृषि मित्र AI आपकी सहायता के लिए तैयार है।")
    speak_hindi("") # Test with empty string
    speak_hindi("गेहूं की खेती के लिए अक्टूबर और नवंबर का महीना उत्तम होता है।")