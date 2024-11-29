from flask import Flask, request, jsonify
from pymongo import MongoClient
import os
import numpy as np
from pydub import AudioSegment
from PIL import Image
import io
import wave
import cloudinary
import cloudinary.uploader
from flask_cors import CORS
import random
import string


# Flask App Configuration
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})


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


# Monoalphabetic Substitution Cipher Functions

def generate_substitution_alphabet():
    """
    Generates a random monoalphabetic substitution alphabet.
    """
    alphabet = string.ascii_lowercase
    shuffled = list(alphabet)
    random.shuffle(shuffled)
    return dict(zip(alphabet, shuffled))

# Initialize the substitution alphabet (this can be saved and reused for decryption)
substitution_alphabet = generate_substitution_alphabet()
reverse_substitution_alphabet = {v: k for k, v in substitution_alphabet.items()}


def monoalphabetic_encrypt(text):
    """
    Encrypts the given text using a monoalphabetic substitution cipher.
    """
    encrypted_text = []
    for char in text:
        if char.isalpha():
            char_lower = char.lower()
            encrypted_char = substitution_alphabet[char_lower]
            if char.isupper():
                encrypted_text.append(encrypted_char.upper())
            else:
                encrypted_text.append(encrypted_char)
        else:
            encrypted_text.append(char)
    return ''.join(encrypted_text)


def monoalphabetic_decrypt(encrypted_text):
    """
    Decrypts the given encrypted text using the reverse of the monoalphabetic substitution cipher.
    """
    decrypted_text = []
    for char in encrypted_text:
        if char.isalpha():
            char_lower = char.lower()
            decrypted_char = reverse_substitution_alphabet[char_lower]
            if char.isupper():
                decrypted_text.append(decrypted_char.upper())
            else:
                decrypted_text.append(decrypted_char)
        else:
            decrypted_text.append(char)
    return ''.join(decrypted_text)


# Steganography Helper Functions (No Change)
def hide_text_in_image(image_path, text, output_path="stego_image.png"):
    image = Image.open(image_path)
    pixels = np.array(image)
    binary_text = ''.join(format(ord(char), '08b') for char in text) + '11111110'

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
    binary_message = ''.join(format(ord(char), '08b') for char in message) + '11111110'

    if len(binary_message) > len(audio_data):
        raise ValueError("Message is too long to hide in the audio.")

    for i in range(len(binary_message)):
        audio_data[i] = (audio_data[i] & 0b111111111111110) | int(binary_message[i])

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
    print(message)
    return message


@app.route('/hide', methods=['POST'])
def hide_data():
    file = request.files['file']
    patient_id = request.form['patient_id']
    patient_data = request.form['data']
    print(file)
    print(patient_id)

    encrypted_data = monoalphabetic_encrypt(patient_data)  # Use Monoalphabetic Substitution Cipher for encryption
    file_path = os.path.join("temp", file.filename)
    file.save(file_path)

    if file.mimetype.startswith('image/'):
        stego_path = hide_text_in_image(file_path, encrypted_data)
    elif file.mimetype.startswith('audio/'):
        stego_path = hide_text_in_audio(file_path, encrypted_data)
    else:
        return jsonify({"error": "Unsupported file type"}), 400

    upload_result = cloudinary.uploader.upload(stego_path, resource_type="auto")
    os.remove(file_path)
    os.remove(stego_path)

    patient_collection.insert_one({
        "patient_id": patient_id,
        "encrypted_data": encrypted_data,
        "file_url": upload_result["secure_url"],
        "file_type": file.mimetype.split('/')[0]
    })

    return jsonify({"message": "Data hidden successfully", "file_url": upload_result["secure_url"]})


@app.route('/retrieve', methods=['POST'])
def retrieve_data():
    patient_id = request.form['patient_id']
    patient = patient_collection.find_one({"patient_id": patient_id})

    if patient:
        encrypted_data = patient['encrypted_data']
        file_url = patient['file_url']
        file_type = patient['file_type']

        # Decrypt the data using Monoalphabetic Substitution Cipher
        decrypted_data = monoalphabetic_decrypt(encrypted_data)

        return jsonify({
            "message": "Data retrieved successfully",
            "decrypted_data": decrypted_data,
            "file_url": file_url,
            "file_type": file_type
        })
    else:
        return jsonify({"error": "Patient not found"}), 404


if __name__ == "__main__":
    app.run(debug=True)
