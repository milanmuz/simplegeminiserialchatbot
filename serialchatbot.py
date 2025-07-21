from google import genai
import config
import serial
import time

SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 2400  # Must match the baud rate of your receiving device
MESSAGE_TO_SEND = "\r\n"*5 # \r\n are common line termination characters


client = genai.Client(api_key=config.API_KEY) # Provide your api key
chat = client.chats.create(model="gemini-2.5-flash")


def answer(user_input):
    response = chat.send_message(user_input)
    return response.text

def chunk_text_loop (text, chunk_size=80):
    chunks = []
    for i in range(0, len(text), chunk_size):
        # Slice the text from current index 'i' up to 'i + chunk_size'
        # Python's slicing handles the end gracefully if it's shorter than chunk_size
        chunk = text[i:i + chunk_size]
        chunks.append(chunk)
    return chunks


ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
time.sleep(2)  # Give some time for the connection to establish

# Encode the string to bytes before sending
# Serial ports always send/receive bytes, not strings directly.
greeting_message = MESSAGE_TO_SEND + "Ask me something." + "\r\n"
data_to_send_bytes = greeting_message.encode('utf-8')

# Write the data to the serial port
bytes_written = ser.write(data_to_send_bytes)



print_response = ""
cursor = "\r\n" + ">>> "
received_message = ""
question = ""
format_warning = " Your answer have to be maximum 75 characters long including spaces."

while True:
    data_to_send_bytes = cursor.encode('utf-8')
    bytes_written = ser.write(data_to_send_bytes)
    received_message = ""
    question = ""
    while question == "":
        if ser.in_waiting > 0:
            received_data_bytes = ser.read(ser.in_waiting)
            received_char = received_data_bytes.decode('utf-8')
            received_message += received_char
            bytes_written = ser.write(received_data_bytes)
            if '\r' in received_char:
                question = received_message
                print(question)

    if question != "quit":

        reply = answer(question+format_warning)
        data_to_send_bytes = MESSAGE_TO_SEND.encode('utf-8')
        bytes_written = ser.write(data_to_send_bytes)
        time.sleep(2)
        question = ""
        chunks1 = chunk_text_loop(reply)
        for t, part in enumerate(chunks1):
            print_response = "AI: " + part
            print(f"Chunk {t + 1} (length {len(part)}): '{part}'")
            data_to_send_bytes = print_response.encode('utf-8')
            bytes_written = ser.write(data_to_send_bytes)
            time.sleep(6)

    elif question == "quit":
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial port closed.")
        break