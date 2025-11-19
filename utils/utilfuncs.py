import os
from dotenv import load_dotenv
from google import genai


load_dotenv()
def allowed_file(filename, allowed_ext):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_ext


os.environ["GEMINI_API_KEY"] = os.getenv('GEMINI_API_KEY')


def generate_story(product_name):
    client = genai.Client()

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=f"Share some historical background about {product_name} such that the reader feels like they should buy one. in about 120 words",
    )

    return response.text

