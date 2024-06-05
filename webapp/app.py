import sys
import os
from flask import Flask, render_template, request, jsonify
from tensorflow.keras.models import load_model
import cv2
import numpy as np
from PIL import Image
import io
import base64

# Set default encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Set the environment variable to enable OneDNN optimizations
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '1'

template_dir = os.path.abspath('webapp\\src\\templates')
static_dir = os.path.abspath('webapp\\src\\static')
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

model = None

def load_model_once():
    global model
    if model is None:
        model = load_model('C:\\Users\\njugu\\Coding\\pneumonia_X_rays_reading\\webapp\\model\\pneumonia_x_rays_v1_0.keras')
        print("Model loaded successfully!")

label_dict = {0: "Pneumonia Negative", 1: "Pneumonia Positive"}

def preprocess(image):
    '''Takes in an image and preprocesses it for the model.
    
    Args:
        image - an image of any shape.
    Returns:
        A reshaped image that has been converted to grayscale, resized, normalized, and reshaped.
    '''
    # Convert image to numpy array
    img_array = np.array(image)

    # Convert to grayscale if the image is not already grayscale
    if img_array.ndim == 3:
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    elif img_array.ndim == 4 and img_array.shape[2] == 4:
        # If the image has an alpha channel, remove it
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2GRAY)

    # Resize the image to the required size
    resized_img = cv2.resize(img_array, (224, 224))

    # Normalize the image
    normalized_img = resized_img / 255.0

    # Reshape the image to add the batch and channel dimensions
    reshaped_img = normalized_img.reshape(1, 224, 224, 1)

    return reshaped_img

@app.before_request
def before_first_request():
    load_model_once()

@app.route("/")
def index():
    '''Renders the HTML Template for UI. Html index body for the application'''
    return render_template("index.html")

@app.route("/predict", methods=['POST'])
def predict():
    '''Defines a route that handles POST requests to "/predict"

    Args:
        No Args.
    Return:
        The response as a JSON object
    '''
    try:
        message = request.get_json(force=True)
        encoded = message['image']
        decoded = base64.b64decode(encoded)
        dataBytesIO = io.BytesIO(decoded)
        image = Image.open(dataBytesIO)

        print(f"Image mode: {image.mode}, size: {image.size}")  # Debugging information

        test_image = preprocess(image)

        print(f"Input image shape: {test_image.shape}")  # Debugging information

        prediction = model.predict(test_image)
        print(f"Prediction shape: {prediction.shape}")  # Debugging information
        print(f"Prediction values: {prediction}")  # Debugging information

        positive_probability = prediction[0][1]
        negative_probability = prediction[0][0]

        response = {
            'prediction': {
                'result': label_dict[np.argmax(prediction, axis=1)[0]],
                'accuracy': positive_probability,
                'negative_probability': negative_probability,
                'positive_probability': positive_probability
            }
        }

        return jsonify(response)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Could not process image'}), 500

if __name__ == '__main__':
    app.run(debug=True)
