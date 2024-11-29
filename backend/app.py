from flask import Flask, request, jsonify, send_file
from pymongo import MongoClient
from cryptography.fernet import Fernet
import os
import numpy as np
from pydub import AudioSegment
from PIL import Image
import io
import wave

# Encode text into an image
def hide_text_in_image(image_path, text, output_path="stego_image.png"):
    # Load image
    image = Image.open(image_path)
    pixels = np.array(image)

    # Convert the message into binary format and add an "EOF" delimiter
    binary_text = ''.join(format(ord(char), '08b') for char in text) + '1111111111111110'  # End of text marker

    # Check if image has enough capacity
    if len(binary_text) > pixels.size:
        print("Text too long to hide in this image.")
        return

    # Encode message into the pixels (using LSB on RGB channels)
    data_index = 0
    for i in range(pixels.shape[0]):
        for j in range(pixels.shape[1]):
            pixel = pixels[i][j]
            for k in range(3):  # Loop over RGB channels
                if data_index < len(binary_text):
                    pixel[k] = int(bin(pixel[k])[2:9] + binary_text[data_index], 2)
                    data_index += 1
            pixels[i][j] = pixel  # Update pixel

    # Save the stego image
    stego_image = Image.fromarray(pixels)
    stego_image.save(output_path)
    print(f"Message hidden in image and saved as '{output_path}'.")


# Decode text from an image
def retrieve_text_from_image(stego_image_path):
    image = Image.open(stego_image_path)
    pixels = np.array(image)

    # Retrieve the hidden binary message from LSB of each RGB channel
    binary_text = ""
    for i in range(pixels.shape[0]):
        for j in range(pixels.shape[1]):
            pixel = pixels[i][j]
            for k in range(3):  # Loop over RGB channels
                binary_text += bin(pixel[k])[2:][-1]

    # Convert binary data to text, stop at the EOF marker
    message = ""
    for i in range(0, len(binary_text), 8):
        byte = binary_text[i:i+8]
        if byte == "11111110":  # End of message (EOF)
            break
        message += chr(int(byte, 2))

    print("Retrieved message:", message)


# Encode text into an audio file
def hide_text_in_audio(audio_path, message, output_audio_path="stego_audio.wav"):
    # Load the audio file
    audio = AudioSegment.from_file(audio_path, format="wav")
    audio_data = np.array(audio.get_array_of_samples(), dtype=np.int16)

    # Convert message to binary and add EOF marker
    binary_message = ''.join(format(ord(char), '08b') for char in message) + '1111111111111110'  # EOF

    if len(binary_message) > len(audio_data):
        print("Message is too long to hide in the audio.")
        return

    # Encode the message into the LSB of each audio sample
    for i in range(len(binary_message)):
        audio_data[i] = (audio_data[i] & 0xFFFE) | int(binary_message[i])  # Modify LSB

    # Create a new AudioSegment from the modified data
    stego_audio = AudioSegment(
        audio_data.tobytes(),
        frame_rate=audio.frame_rate,
        sample_width=audio.sample_width,
        channels=audio.channels
    )

    # Export the modified audio
    stego_audio.export(output_audio_path, format="wav")
    print(f"Message hidden in audio and saved as '{output_audio_path}'.")


# Decode text from an audio file
def retrieve_text_from_audio(stego_audio_path):
    # Open the stego audio file
    with wave.open(stego_audio_path, "rb") as audio_file:
        frames = audio_file.readframes(audio_file.getnframes())
    audio_data = np.frombuffer(frames, dtype=np.int16)

    # Extract binary message from LSBs
    binary_message = ""
    for sample in audio_data:
        binary_message += str(sample & 1)  # Extract LSB

    # Convert binary to text until EOF marker
    message = ""
    for i in range(0, len(binary_message), 8):
        byte = binary_message[i:i+8]
        if byte == "11111110":  # EOF marker
            break
        message += chr(int(byte, 2))

    print("Retrieved message:", message)   

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads"
client = MongoClient("mongodb+srv://kartikaggarwal2004:mkSb1EJX16svaJrT@cluster0.6jxu4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client.medical_steganography
patient_collection = db.patients

# Generate a key for encryption
encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/hide', methods=['POST'])
def hide_data():
    file = request.files['file']
    patient_id = request.form['patient_id']
    patient_data = request.form['data']

    # Encrypt the data
    encrypted_data = cipher_suite.encrypt(patient_data.encode())

    # Save the uploaded file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    # Determine file type
    if file.mimetype.startswith('image/'):
        output_file = os.path.join(app.config['UPLOAD_FOLDER'], f"stego_{file.filename}")
        hide_text_in_image(file_path, encrypted_data.decode(), output_file)
    elif file.mimetype.startswith('audio/'):
        output_file = os.path.join(app.config['UPLOAD_FOLDER'], f"stego_{file.filename}")
        hide_text_in_audio(file_path, encrypted_data.decode(), output_file)
    else:
        return jsonify({"error": "Unsupported file type"}), 400

    # Save metadata to MongoDB
    patient_collection.insert_one({
        "patient_id": patient_id,
        "encrypted_data": encrypted_data.decode(),
        "file_name": f"stego_{file.filename}",
        "file_path": output_file
    })

    return jsonify({"message": "Data hidden successfully", "file": output_file})

@app.route('/retrieve', methods=['POST'])
def retrieve_data():
    file = request.files['file']

    # Save the uploaded file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    # Determine file type
    if file.mimetype.startswith('image/'):
        encrypted_data = retrieve_text_from_image(file_path)
    elif file.mimetype.startswith('audio/'):
        encrypted_data = retrieve_text_from_audio(file_path)
    else:
        return jsonify({"error": "Unsupported file type"}), 400

    # Decrypt the data
    decrypted_data = cipher_suite.decrypt(encrypted_data.encode()).decode()

    return jsonify({"message": "Data retrieved successfully", "data": decrypted_data})

if __name__ == '__main__':
    app.run(debug=True)
