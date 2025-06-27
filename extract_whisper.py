from pydub import AudioSegment
import speech_recognition as sr

audio = AudioSegment.from_mp3("Track 019.mp3")
audio.export("Track_019.wav", format="wav")

r = sr.Recognizer()
with sr.AudioFile("Track_019.wav") as source:
    audio_data = r.record(source)

text = r.recognize_google(audio_data)
print(text)