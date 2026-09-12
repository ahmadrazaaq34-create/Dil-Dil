import io
import re
import time
import threading
from google import genai
from google.genai import types
from core.network import setup_fast_network

# Activate fast IPv4 routing to eliminate the 15-35s timeout
setup_fast_network()

# Regex to strip emojis completely (carefully scoped ranges — must NOT touch
# CJK / Arabic / Devanagari / Cyrillic text, only actual emoji blocks)
EMOJI_REGEX = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U00002702-\U000027B0"  # dingbats
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000026FF"  # misc symbols (sun, cloud...)
    "\U00002B00-\U00002BFF"  # arrows & stars
    "]+", flags=re.UNICODE
)

# Zero-width joiner & variation selector leftovers from stripped emojis
EMOJI_RESIDUE_REGEX = re.compile("[\u200d\ufe0f\u20e3]")

class GeminiEngine:
    TARGET_LANGUAGES = {
        "english": "English (Fluent & Natural)",
        "urdu": "Urdu (اردو رسم الخط)",
        "roman_urdu": "Roman Urdu (Latin Alphabet)",
        "arabic": "Arabic (العربية)",
        "hindi": "Hindi (हिंदी)",
        "spanish": "Spanish (Español)",
        "french": "French (Français)",
        "german": "German (Deutsch)",
        "portuguese": "Portuguese (Português)",
        "russian": "Russian (Русский)",
        "chinese": "Chinese (Mandarin 简体中文)",
        "japanese": "Japanese (日本語)",
        "turkish": "Turkish (Türkçe)",
        "italian": "Italian (Italiano)",
        "persian": "Persian (فارسی)",
        "punjabi": "Punjabi (پنجابی)",
        "bengali": "Bengali (বাংলা)",
        "dutch": "Dutch (Nederlands)",
        "indonesian": "Indonesian (Bahasa Indonesia)"
    }

    FALLBACK_MODELS = ["gemini-flash-lite-latest", "gemini-flash-latest", "gemini-3.8-flash", "gemini-3.7-flash"]

    def __init__(self, api_key: str = "", model_name: str = "gemini-flash-lite-latest", on_model_changed=None):
        self.api_key = api_key
        self.model_name = model_name
        self.on_model_changed = on_model_changed
        self._client = None
        if self.api_key:
            self._init_client()

    def set_api_key(self, api_key: str):
        self.api_key = api_key.strip()
        self._init_client()

    def _init_client(self):
        try:
            self._client = genai.Client(api_key=self.api_key)
            # Automatically start background check for the latest Gemini model
            self.discover_latest_model_async(self.on_model_changed)
        except Exception as e:
            self._client = None
            raise RuntimeError(f"Failed to initialize Gemini Client: {e}")

    def is_configured(self) -> bool:
        return bool(self.api_key and self._client)

    def discover_latest_model_async(self, on_discovered=None):
        """
        Asynchronously queries Google Gemini API to discover the newest available Flash model.
        Runs in the background without blocking the UI or audio streaming.
        Validates model availability and seamlessly sets the newest active model.
        """
        if not self.is_configured():
            return

        def _worker():
            try:
                models_list = list(self._client.models.list())
                
                def rank_model(name: str):
                    n = name.lower()
                    if any(x in n for x in ['tts', 'image', 'imagen', 'embed', 'computer-use']):
                        return (-1, 0, 0)
                    # Prefer official Google production alias for lowest latency
                    if 'flash-lite-latest' in n:
                        return (1000, 2, 0)
                    if 'flash-latest' in n:
                        return (900, 1, 0)
                    # Next prefer version-numbered models (e.g. 3.8, 3.7)
                    m = re.search(r'gemini-(\d+)(?:\.(\d+))?-flash(?:-lite)?', n)
                    if m:
                        major = int(m.group(1))
                        minor = int(m.group(2) or 0)
                        is_lite = 1 if 'lite' in n else 0
                        return (major * 10 + minor, is_lite, 0)
                    return (0, 0, 0)

                candidates = []
                for m in models_list:
                    name = m.name.replace("models/", "")
                    if "flash" in name.lower():
                        score = rank_model(name)
                        if score[0] > 0:
                            candidates.append((name, score))

                candidates.sort(key=lambda x: x[1], reverse=True)

                chosen_model = None
                for cand_name, _ in candidates[:5]:
                    try:
                        self._client.models.get(model=cand_name)
                        chosen_model = cand_name
                        break
                    except Exception:
                        continue

                if chosen_model:
                    if chosen_model != self.model_name:
                        print(f"[GeminiEngine] Auto-upgraded to latest Gemini model: {chosen_model} (previous: {self.model_name})")
                        self.model_name = chosen_model
                    else:
                        print(f"[GeminiEngine] Active model verified up-to-date: {chosen_model}")
                    if on_discovered:
                        on_discovered(chosen_model)
            except Exception as e:
                print(f"[GeminiEngine] Background model discovery: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def _get_system_instruction(self, target_lang: str) -> str:
        lang_key = target_lang.lower().strip()

        base_negative_rules = (
            "\nCRITICAL SPEAKER & SILENCE RULES (STRICT):\n"
            "- MANDATORY SILENCE FILTER: If the user did not speak any clear, intelligible words, or if there is only silence, breathing, background noise, clicks, or hum, you MUST return ABSOLUTELY NOTHING. Return an empty string \"\".\n"
            "- NEVER GUESS OR HALLUCINATE: Never invent, guess, fabricate, or autocomplete conversational sentences (such as scheduling meetings, phone calls, greetings, or project tasks) if they were not explicitly spoken in this audio.\n"
            "- SPEAKER ISOLATION: Transcribe ONLY the primary foreground speaker talking directly into the microphone. Drop and ignore any background chatter, TV, music, or other people speaking in the room.\n"
            "- NO EMOJIS: Never use emojis, symbols, or emoticons. Output clean plain text only.\n"
            "- NO COMMENTARY: Output ONLY the transcribed or translated words. No quotation marks, notes, or explanations."
        )

        if lang_key == "urdu":
            return (
                "You are an expert Urdu voice dictation transcriber.\n"
                "The user is speaking in Urdu.\n"
                "Task:\n"
                "1. Accurately transcribe the user's speech into proper Urdu script (اردو).\n"
                "2. Transcribe any spoken English loanwords naturally into Urdu script.\n"
                "3. Remove vocal fillers like 'uh', 'um'.\n"
                "4. STRICT FIDELITY: Transcribe only what was actually spoken. If silent, output nothing.\n"
                "5. OUTPUT RULE: Output ONLY the transcribed Urdu text."
                + base_negative_rules
            )
        elif lang_key == "roman_urdu":
            return (
                "You are an expert voice transcriber for Roman Urdu (Urdu written in English Latin alphabet).\n"
                "The user is speaking in Pakistani Urdu.\n"
                "Task:\n"
                "1. Transcribe the speech phonetically into standard, clean Roman Urdu.\n"
                "2. Remove filler sounds.\n"
                "3. STRICT FIDELITY: Transcribe only what was actually spoken. If silent, output nothing.\n"
                "4. OUTPUT RULE: Output ONLY the Roman Urdu text."
                + base_negative_rules
            )
        elif lang_key == "english":
            return (
                "You are an elite real-time voice dictation translator specializing in conversational Pakistani Urdu, Hindi, and Hinglish.\n"
                "Task:\n"
                "1. Listen carefully to the user's speech.\n"
                "2. Translate accurately into fluent, natural, grammatically sound English.\n"
                "3. Clean up vocal fillers.\n"
                "4. STRICT FIDELITY: Never hallucinate words not spoken by the user.\n"
                "5. If speech is silent, inaudible, or only noise, output NOTHING (empty string).\n"
                "6. LANGUAGE LOCK (CRITICAL): The output MUST be 100% pure English. Translate every spoken word into English.\n"
                "7. OUTPUT RULE: Output ONLY the final plain English text. No quotes or commentary."
                + base_negative_rules
            )
        else:
            lang_name = self.TARGET_LANGUAGES.get(lang_key, lang_key.capitalize())
            return (
                f"You are an expert real-time voice translator.\n"
                f"The user is speaking. Translate the speech accurately into natural, grammatically correct {lang_name}.\n"
                f"STRICT FIDELITY: Do NOT add, infer, or fabricate unmentioned context. If silent, output nothing.\n"
                f"LANGUAGE LOCK (CRITICAL): The output MUST be 100% in {lang_name}.\n"
                f"OUTPUT RULE: Output ONLY the translated {lang_name} text."
                + base_negative_rules
            )

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        cleaned = text.strip()
        if (cleaned.startswith('"') and cleaned.endswith('"')) or \
           (cleaned.startswith("'") and cleaned.endswith("'")):
            cleaned = cleaned[1:-1].strip()

        # Strip any emojis injected by the model
        cleaned = EMOJI_REGEX.sub('', cleaned)
        cleaned = EMOJI_RESIDUE_REGEX.sub('', cleaned)

        # Strip simulation / repeating zeros artifact
        cleaned = re.sub(r'(?i)^(simulation|simulated|sim|0000+)\b[\s:0-9\-]*', '', cleaned).strip()

        # Silence hallucination patterns to suppress
        hallucination_patterns = [
            r'(?i)^let\'?s schedule a meeting.*',
            r'(?i)^call me as soon as you reach.*',
            r'(?i)^thank you for watching.*',
            r'(?i)^subtitles by.*',
            r'(?i)^please subscribe.*',
            r'(?i)^you\'?re welcome.*',
            r'(?i)^silence\.?$',
            r'(?i)^no speech.*',
        ]
        for pat in hallucination_patterns:
            if re.fullmatch(pat, cleaned):
                return ""

        # Collapse multiple spaces
        cleaned = re.sub(r' +', ' ', cleaned)
        return cleaned.strip()

    def process_audio(self, wav_bytes: bytes, target_lang: str = "english", retry_count: int = 2) -> str:
        """
        Sends audio WAV bytes to Gemini Flash and translates/transcribes into target_lang.
        Filters out any emojis, simulation codes, or unwanted artifacts.
        """
        collected = []
        def _collect(s):
            collected.append(s)
        self.process_audio_stream(wav_bytes, target_lang=target_lang, on_sentence=_collect)
        return " ".join(collected).strip()

    def process_audio_stream(self, wav_bytes: bytes, target_lang: str = "english", on_sentence=None, voice_profile_bytes: bytes = None) -> str:
        """
        Streams audio transcription/translation from Gemini.
        Focuses strictly on the foreground microphone speaker and eliminates background chatter.
        Sends ONLY the live speech audio part to prevent model confusion and save API quota.
        """
        if not self.is_configured():
            raise ValueError("Gemini API key is not configured. Please check Settings.")

        if not wav_bytes or len(wav_bytes) < 2000:
            return ""

        system_instruction = self._get_system_instruction(target_lang)
        audio_part = types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav")

        prompt = (
            "Transcribe or translate the speech from the primary speaker talking into the microphone.\n"
            "If the audio contains only silence, static, or background noise without speech, output an empty string.\n"
            "Output ONLY the final plain text directly. No commentary, no tags, no quotes."
        )
        contents_payload = [audio_part, prompt]

        last_error = None
        models_to_try = [self.model_name] + [m for m in self.FALLBACK_MODELS if m != self.model_name]

        for model in models_to_try:
            t0 = time.time()
            try:
                print(f"[GeminiEngine] Streaming audio with {model} (Speaker Isolation: {bool(voice_profile_bytes)})...")
                response_stream = self._client.models.generate_content_stream(
                    model=model,
                    contents=contents_payload,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.0,
                    )
                )

                full_text_chunks = []
                buffer = ""
                # Match full stops, exclamation marks, question marks, or newlines
                delim_pattern = re.compile(r'([.!?\n]+)\s*')

                for chunk in response_stream:
                    chunk_text = chunk.text or ""
                    if not chunk_text:
                        continue
                    full_text_chunks.append(chunk_text)
                    buffer += chunk_text

                    # Split completed sentences
                    while True:
                        match = delim_pattern.search(buffer)
                        if not match:
                            # If buffer is getting very long (>120 chars) and has a comma or clause break, split it
                            if len(buffer) > 120 and (',' in buffer or ';' in buffer):
                                comma_idx = max(buffer.rfind(','), buffer.rfind(';'))
                                if comma_idx > 30:
                                    part = buffer[:comma_idx + 1]
                                    buffer = buffer[comma_idx + 1:].lstrip()
                                    cleaned_part = self.clean_text(part)
                                    if cleaned_part and on_sentence:
                                        on_sentence(cleaned_part)
                                    continue
                            break

                        end_pos = match.end()
                        sentence = buffer[:end_pos]
                        buffer = buffer[end_pos:].lstrip()

                        cleaned_sentence = self.clean_text(sentence)
                        if cleaned_sentence and on_sentence:
                            on_sentence(cleaned_sentence)

                # Flush any remaining text in buffer
                if buffer.strip():
                    cleaned_remaining = self.clean_text(buffer)
                    if cleaned_remaining and on_sentence:
                        on_sentence(cleaned_remaining)

                full_text = self.clean_text("".join(full_text_chunks))
                dt = time.time() - t0
                print(f"[GeminiEngine] Streaming completed in {dt:.2f}s: \"{full_text}\"")
                return full_text
            except Exception as e:
                last_error = e
                dt = time.time() - t0
                print(f"[GeminiEngine] Model {model} stream failed in {dt:.2f}s: {e}")
                err_str = str(e).lower()
                if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
                    continue
                if "503" in err_str or "not found" in err_str or "unavailable" in err_str:
                    continue
                raise e

        if last_error:
            raise last_error
        return ""

