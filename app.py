import streamlit as st
from audio_recorder_singleton import audio_recorder
import openai
import sqlite3
from datetime import datetime

# --- DATABASE SETUP ---
conn = sqlite3.connect('schedule_db.sqlite', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS deadlines (task TEXT, due_date TEXT, status TEXT)')
conn.commit()

# --- APP UI ---
st.set_page_config(page_title="Iron Coach AI", page_icon="🎙️")
st.title("🎙️ Iron Coach: Strict Academic Lead")

# --- 1. BURNOUT SENSOR (The Gatekeeper) ---
st.sidebar.header("🧠 Vitals Check")
mental_score = st.sidebar.slider("Brain Fatigue (1=Fresh, 10=Fried)", 1, 10, 5)

# --- 2. VOICE INTERACTION ---
st.subheader("Speak to your Coach")
audio_bytes = audio_recorder(text="Tap to update your day", icon_size="2x", icon_name="microphone")

if audio_bytes:
    # Save audio for OpenAI Whisper
    with open("temp_audio.wav", "wb") as f:
        f.write(audio_bytes)
    
    # Transcribe Speech
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    audio_file = open("temp_audio.wav", "rb")
    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    user_text = transcript.text
    st.info(f"You: {user_text}")

    # --- 3. AI LOGIC WITH BURNOUT OVERRIDE ---
    prompt = f"""
    User Fatigue Level: {mental_score}/10. 
    Current Time: {datetime.now().strftime("%H:%M")}.
    User Input: "{user_text}"
    
    Instructions:
    - If Fatigue > 7: Refuse hard work. Schedule 'Mind Rest' or low-intensity admin.
    - Breakdown any mentioned projects into 'Atomic Tasks' (max 45 mins).
    - Use the 30% Buffer Rule: Keep slots open for emergencies.
    - Be strict, concise, and prioritize the schedule.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a brutal, honest academic coach. You hate procrastination but you fear student burnout more. Your goal is maximum efficiency."},
            {"role": "user", "content": prompt}
        ]
    )
    
    ai_advice = response.choices[0].message.content
    st.success(ai_advice)

    # --- 4. VOICE RESPONSE (TTS) ---
    speech = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=ai_advice
    )
    st.audio(speech.content, format="audio/mp3", autoplay=True)

# --- 5. TIMETABLE & DATA ---
with st.expander("📅 View Timetable & Deadlines"):
    st.write("Current Timetable: [Hardcoded for Demo - Upload logic can be added]")
    # Persistent Database view
    data = c.execute('SELECT * FROM deadlines').fetchall()
    st.table(data)
