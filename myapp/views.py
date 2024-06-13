from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
import requests
import google.generativeai as genai
from gradientai import Gradient

os.environ['GRADIENT_ACCESS_TOKEN'] = "qYBtXzJmTK2MzTIpqBqcuPsQSCIfbZHO"
os.environ['GRADIENT_WORKSPACE_ID'] = "e8ee528f-553e-45ca-98b1-480af025193c_workspace"
os.environ['GOOGLE_GEMINI_API_KEY'] = "AIzaSyCopiBoMqbChpDXPkfR1SKZfLDOO3CbF1w"

genai.configure(api_key=os.environ["GOOGLE_GEMINI_API_KEY"])
gemini_model = genai.GenerativeModel('gemini-pro')

def extract_job_and_location(query):
    with Gradient() as gradient:
        base_model = gradient.get_base_model(base_model_slug="nous-hermes2")
        prompt = f"Extract the job and location from the following query: '{query}'. 'job, location:"
        completion = base_model.complete(query=prompt, max_generated_token_count=200).generated_output
        return completion.strip()

def search_jobs(job, location):
    url = "https://jsearch.p.rapidapi.com/search"
    query_string = f"{job} in {location}"
    querystring = {"query": query_string, "page": "1", "num_pages": "1"}
    headers = {
        "X-RapidAPI-Key": "674b369e0dmsh1f421d3fdf28ae2p17e46cjsnce591ae3e24f",
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    return response.json()

@csrf_exempt
def chat(request):
    if request.method == 'POST':
        user_query = request.POST.get('query')
        extracted_info = extract_job_and_location(user_query)
        parts = extracted_info.split(',')
        if len(parts) == 2:
            job = parts[0].replace("job:", "").strip()
            location = parts[1].replace("location:", "").strip()
            job_results = search_jobs(job, location)
            prompt = f"User query: '{user_query}'. Based on the following job data, provide a detailed response: {job_results}"
            try:
                response = gemini_model.generate_content(prompt)
                if response and response.parts:
                    response_text = str(response.parts[0].text)  # Convert to string
                else:
                    response_text = "Failed to generate response from Gemini model."
            except Exception as e:
                response_text = f"An error occurred: {str(e)}"
        else:
            response_text = "Could not extract job and location. Please try again."
        return JsonResponse({'response': response_text})  # Return the extracted text

def home(request):
    return HttpResponse("Welcome to the home page!")