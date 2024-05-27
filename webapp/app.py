from flask import Flask, render_template, request, jsonify
from flask_restful import reqparse, abort, Api, Resource
from tensorflow.keras.models import load_model # type: ignore
import cv2
import base64
import numpy as np
from PIL import Image
import io
import re
import tensorflow as tf

tf.TF_ENABLE_ONEDNN_OPTS = 1

img_size = 100
app = Flask(__name__)
app.config['TEMPLATES'] = "./src/templates" # Set templates directory
app.config['STATIC'] = "./src/static"  # Set static files directory

try:
    model = load_model('model/pneumonia_x_rays_v1_0.h5')
    print("Model loaded successfully!")

except FileNotFoundError as e:
    print(f"Error: {e}")

label_dict = {0: "Pneumonia Negative", 1: "Pneumonia Positive"}

def preprocess(img):
    '''Takes in an image and augments it.

    Args:
        img - an image of any shape.
    Return:
        reshaped image that has been grayed, resized and then reshaped.
    '''
    img = np.array(img)

    if img.ndim == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    else:
        gray = img
    
    gray = gray / 255
    resized = cv2.resize(gray, (img_size, img_size))
    reshaped = resized.reshape(1, img_size, img_size)

    return reshaped

@app.route("/")
def index():
    '''Renders the HTML Template for UI.

    No Args.

    Return:
        Html index body for the application
    '''
    return render_template("index.html")

@app.route("/predict", methods = ['POST'])
def predict():
    '''Defines a route that handles POST requests to "/predict"

    Args:
        No Args.
    Reurn:
        The response as a JSON object
    '''
    print()
    message = request.get_json(force = True)
    encoded = message['image']
    decoded = base64.b64decode(encoded)
    dataBytesIO = io.BytesIO(decoded)
    dataBytesIO.seek()

    image = Image.open(dataBytesIO)

    test_image = preprocess(image)

    prediction = model.predict(test_image)
    result = np.argmax(prediction, axis = 1)[0]
    accuracy = float(np.max(prediction, axis = 1)[0])

    label = label_dict[result]

    print(prediction, result, accuracy)

    response = {'prediction': {'result': label, 'accuracy': accuracy}}

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug = True)