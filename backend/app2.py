from flask import Flask, request, jsonify
from pymongo import MongoClient
from cryptography.fernet import Fernet
import os
import numpy as np
from pydub import AudioSegment
from PIL import Image
import io
import wave
import cloudinary
import cloudinary.uploader


# Flask App Configuration
app = Flask(__name__)


# MongoDB Configuration
client = MongoClient("mongodb+srv://kartikaggarwal2004:mkSb1EJX16svaJrT@cluster0.6jxu4.mongodb.net/?retryWrites=true&w=majority")
db = client.medical_steganography
patient_collection = db.patients


# Cloudinary Configuration
cloudinary.config(
    cloud_name="dkbsrsblc",
    api_key="691958665838133",
    api_secret="-ZA3LEoVu9lrXQalz-T-ds0SAhE"
)


# Encryption Configuration
encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)


# Helper Functions
def hide_text_in_image(image_path, text, output_path="stego_image.png"):
    image = Image.open(image_path)
    pixels = np.array(image)
    binary_text = ''.join(format(ord(char), '08b') for char in text) + '1111111111111110'

    if len(binary_text) > pixels.size:
        raise ValueError("Text too long to hide in this image.")

    data_index = 0
    for i in range(pixels.shape[0]):
        for j in range(pixels.shape[1]):
            pixel = pixels[i][j]
            for k in range(3):
                if data_index < len(binary_text):
                    pixel[k] = int(bin(pixel[k])[2:9] + binary_text[data_index], 2)
                    data_index += 1
            pixels[i][j] = pixel

    stego_image = Image.fromarray(pixels)
    stego_image.save(output_path)
    return output_path


def retrieve_text_from_image(stego_image_path):
    image = Image.open(stego_image_path)
    pixels = np.array(image)
    binary_text = ""
    for i in range(pixels.shape[0]):
        for j in range(pixels.shape[1]):
            pixel = pixels[i][j]
            for k in range(3):
                binary_text += bin(pixel[k])[2:][-1]

    message = ""
    for i in range(0, len(binary_text), 8):
        byte = binary_text[i:i+8]
        if byte == "11111110":
            break
        message += chr(int(byte, 2))
    return message


def hide_text_in_audio(audio_path, message, output_audio_path="stego_audio.wav"):
    audio = AudioSegment.from_file(audio_path, format="wav")
    audio_data = np.array(audio.get_array_of_samples(), dtype=np.int16)
    binary_message = ''.join(format(ord(char), '08b') for char in message) + '1111111111111110'

    if len(binary_message) > len(audio_data):
        raise ValueError("Message is too long to hide in the audio.")

    for i in range(len(binary_message)):
        audio_data[i] = (audio_data[i] & 0xFFFE) | int(binary_message[i])

    stego_audio = AudioSegment(
        audio_data.tobytes(),
        frame_rate=audio.frame_rate,
        sample_width=audio.sample_width,
        channels=audio.channels
    )
    stego_audio.export(output_audio_path, format="wav")
    return output_audio_path


def retrieve_text_from_audio(stego_audio_path):
    with wave.open(stego_audio_path, "rb") as audio_file:
        frames = audio_file.readframes(audio_file.getnframes())
    audio_data = np.frombuffer(frames, dtype=np.int16)
    binary_message = ""
    for sample in audio_data:
        binary_message += str(sample & 1)

    message = ""
    for i in range(0, len(binary_message), 8):
        byte = binary_message[i:i+8]
        if byte == "11111110":
            break
        message += chr(int(byte, 2))
    return message

@app.route('/hide', methods=['POST'])
def hide_data():
    file = request.files['file']
    patient_id = request.form['patient_id']
    patient_data = request.form['data']

    encrypted_data = cipher_suite.encrypt(patient_data.encode())
    file_path = os.path.join("temp", file.filename)
    file.save(file_path)

    if file.mimetype.startswith('image/'):
        stego_path = hide_text_in_image(file_path, encrypted_data.decode())
    elif file.mimetype.startswith('audio/'):
        stego_path = hide_text_in_audio(file_path, encrypted_data.decode())
    else:
        return jsonify({"error": "Unsupported file type"}), 400

    upload_result = cloudinary.uploader.upload(stego_path, resource_type="auto")
    os.remove(file_path)
    os.remove(stego_path)

    patient_collection.insert_one({
        "patient_id": patient_id,
        "encrypted_data": encrypted_data.decode(),
        "file_url": upload_result["secure_url"],
        "file_type": file.mimetype.split('/')[0]
    })

    return jsonify({"message": "Data hidden successfully", "file_url": upload_result["secure_url"]})

@app.route('/retrieve', methods=['POST'])
def retrieve_data():
    file_url = request.json['file_url']
    file_path = cloudinary.utils.download_private(file_url)

    if "image" in file_url:
        encrypted_data = retrieve_text_from_image(file_path)
    elif "audio" in file_url:
        encrypted_data = retrieve_text_from_audio(file_path)
    else:
        return jsonify({"error": "Unsupported file type"}), 400

    decrypted_data = cipher_suite.decrypt(encrypted_data.encode()).decode()
    os.remove(file_path)

    return jsonify({"message": "Data retrieved successfully", "data": decrypted_data})

if __name__ == '__main__':
    os.makedirs("temp", exist_ok=True)
    app.run(debug=True)
