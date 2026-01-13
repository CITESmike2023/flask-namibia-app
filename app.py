from flask import Flask, render_template, request
import google.generativeai as genai
import PIL.Image
import json
import textwrap
import pandas as pd
import io
import base64   

app = Flask(__name__)

# Set API Key
API_KEY = "AIzaSyB9YAQGtQkvbZ3dWdd7tF63eLts4ubXwro"  # Replace with your actual API key

def describe_image(image, api_key):
    """
    Uses Gemini 2.5 Flash to analyze an image and extract species details.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name='gemini-2.5-flash', 
        generation_config={"response_mime_type": "application/json"})

        prompt = """ This image contains possible animals in Namibia Desert at a waterhole. 
        The weather information is in the top left corner and timestamp on the right of the image.
        Determine the total number of individuals in the image. 
        Identify all the species in the image and the counts for each species.

        Generate a JSON object with the following keys: "Features" and ""Description".  Do not include any other text.

        In the "Features" section of the JSON include 
        species name, count of each species, temperature, date, and time as separate fields.
        The Features should be in JSON format with the structure:
                  {
                    "Species": "Oryx",
                    "Count": 12,
                    "Temperature": 13.0,
                    "Date": "2024-10-23",
                    "Time": "00:54:34"
                   }
        If the total number of individuals is 0, then report Species as "None" and Count as 0. 
        If the temperature, date, and time is missing report at "N/A". 

        In the "Description" section of the JSON include a short note (three sentences) on the description
        of the picture, including behavour of the aniamsls, temperature, date, and time. 
        """

        response = model.generate_content([prompt, image])
        return response.text

    except Exception as e:
        return f"An error occurred: {e}"

@app.route("/", methods=["GET", "POST"])
def index():
    print("🚀 Flask is running and rendering index.html")  # Debugging print
    extracted_info = None
    image_data = None
    description = None

    if request.method == "POST":
        uploaded_file = request.files["file"]

        if uploaded_file:
            print("📂 File uploaded:", uploaded_file.filename)  # Debugging print
            try:
                # Read and process image
                image = PIL.Image.open(uploaded_file)

                # Convert image to base64 for HTML display
                buffered = io.BytesIO()

                # Ensure the image is in a format that can be saved as JPEG
                if image.mode not in ("RGB", "L"):
                    image = image.convert("RGB")  # Convert RGBA or P mode to RGB

                # Save the image as JPEG
                image.save(buffered, format="JPEG")

                # Encode the image in base64 for display in HTML
                image_data = base64.b64encode(buffered.getvalue()).decode("utf-8")

                # Analyze image using Gemini
                print("🧠 Sending image to Gemini for analysis...")
                response_json_string = describe_image(image, API_KEY)
                print("✅ Response received from Gemini!")
                print("response=", response_json_string)

                # Parse JSON response
                data = json.loads(response_json_string)
                features = data.get("Features", [])

                if isinstance(features, list) and features:
                    df = pd.DataFrame(features)
                    df["Filename"] = uploaded_file.filename
                    extracted_info = df.to_html(classes="table table-bordered table-striped table-sm text-end", index=False)
                    print("✅ Extracted features:", df)

                # Parse JSON dedescription
                description = data.get("Description", "")

                # If description is a list (e.g., multiple sentences returned by Gemini), 
                # join into a single string
                if isinstance(description, list):  
                    description = " ".join(description)  

                # If description is not a string (e.g., None, number, unexpected type),
                #  convert it to a string
                if not isinstance(description, str):  
                    description = str(description)  

                # Format the text to wrap lines at 80 characters for better readability
                description = textwrap.fill(description, width=80)

            except json.JSONDecodeError:
                extracted_info = "<p style='color: red;'>Error: Invalid JSON response.</p>"
                print("❌ JSON parsing error! Response:", response_json_string)

    return render_template("index.html", extracted_info=extracted_info, image_data=image_data, description=description)

if __name__ == "__main__":
    print("🚀 Starting Flask app... Visit http://127.0.0.1:5000/")
    app.run(debug=True)

