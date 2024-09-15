from datetime import datetime, timedelta
from io import BytesIO
from os import getenv
from pathlib import Path
from queue import Queue
from threading import Thread
from time import sleep

import requests
import speech_recognition as sr

from .asr import speech_to_text

APP_OUTPUT_ID = int(getenv('AUX_OUTPUT_ID'))
RECORD_TIMEOUT = int(getenv('RECORD_TIMEOUT'))
PHRASE_TIMEOUT = int(getenv('PHRASE_TIMEOUT'))
INPUT_LANGUAGE = getenv('TARGET_LANGUAGE_CODE')
LOGGING = getenv("LOGGING", 'False').lower() in ('true', '1', 't')
APP_AUDIO_WAV_PATH = Path(__file__).resolve().parent.parent / r'audio\app_audio.wav'


def request_thread(queue, phrase_time, now):
    try:
        translation = speech_to_text(APP_AUDIO_WAV_PATH, 'translate', INPUT_LANGUAGE)
    except requests.exceptions.JSONDecodeError:
        print('Too many requests to process at once')
        return

    if translation:
        queue.put(translation)
        if LOGGING:
            delay = (datetime.utcnow() - now).total_seconds()
            if phrase_time:
                print(
                    f'Previous time: {phrase_time.time().strftime("%H:%M:%S")}, Now: {now.time().strftime("%H:%M:%S")}, Delay: {delay}, Translation: {translation}')
            else:
                print(f'Now: {now.time()}, Delay: {delay}, Translation: {translation}')


def translate_audio(translation_queue):
    data_queue = Queue()

    recorder = sr.Recognizer()
    recorder.dynamic_energy_threshold = False

    audio_output = sr.Microphone(device_index=APP_OUTPUT_ID)

    def record_callback(_, audio):
        raw_data = audio.get_raw_data()
        data_queue.put(raw_data)

    recorder.listen_in_background(audio_output, record_callback, phrase_time_limit=RECORD_TIMEOUT)

    phrase_time = None
    last_sample = bytes()

    while True:
        now = datetime.utcnow()

        if not data_queue.empty():
            prev_phrase_time = phrase_time
            if phrase_time and now - phrase_time > timedelta(seconds=PHRASE_TIMEOUT):
                last_sample = bytes()
            phrase_time = now

            while not data_queue.empty():
                data = data_queue.get()
                last_sample += data

            audio_data = sr.AudioData(last_sample, audio_output.SAMPLE_RATE, audio_output.SAMPLE_WIDTH)
            wav_data = BytesIO(audio_data.get_wav_data())
            with open(APP_AUDIO_WAV_PATH, 'w+b') as f:
                f.write(wav_data.read())

            Thread(target=request_thread, args=[translation_queue, prev_phrase_time, now], daemon=True).start()

        else:
            sleep(0.5)
