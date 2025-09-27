from fastapi import FastAPI, File, UploadFile, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware   # <-- add this
import uvicorn
import os
import subprocess
import uuid
import base64
import requests

# Load API key (hardcoded here for demo; best practice = env var)
GOOGLE_API_KEY = 'AIzaSyDVksTONkieWNhplzhmpXTHCsYrjdDh1Mc'
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

app = FastAPI()

# ✅ Enable CORS so frontend (Next.js) can call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # for dev: allow all, in prod: ["https://your-frontend.vercel.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads folder exists
os.makedirs("uploads", exist_ok=True)

@app.get("/")
async def home():
    return {"message": "Welcome! Use POST /upload/ (file) or POST /upload-base64/ (base64) to upload and transcribe audio."}

# -------- FILE UPLOAD ENDPOINT ----------
@app.post("/upload/")
async def upload_audio(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    input_path = f"uploads/{file_id}_{file.filename}"
    output_path = f"uploads/{file_id}.wav"

    # Save uploaded file
    with open(input_path, "wb") as f:
        f.write(await file.read())

    # Convert to wav with ffmpeg
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-ar", "48000", "-ac", "1", output_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        return JSONResponse(content={"error": f"Conversion failed: {e}"}, status_code=500)

    # Encode wav to base64
    try:
        with open(output_path, "rb") as f:
            encoded_audio = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        return JSONResponse(content={"error": f"Reading wav failed: {str(e)}"}, status_code=500)

    # Send to Google API
    return await transcribe_with_google(encoded_audio)

# -------- BASE64 DIRECT ENDPOINT ----------
@app.post("/upload-base64/")
async def upload_audio_base64(audio: str = Body(..., embed=True)):
    """
    Expects JSON body: { "audio": "BASE64_STRING" }
    """
    return await transcribe_with_google(audio)

# -------- SHARED GOOGLE API CALL ----------
async def transcribe_with_google(encoded_audio: str):
    body = {
        "config": {
            "encoding": "LINEAR16",
            "sampleRateHertz": 48000,
            "languageCode": "en-US"
        },
        "audio": {"content": encoded_audio}
    }

    try:
        response = requests.post(
            f"https://speech.googleapis.com/v1/speech:recognize?key={GOOGLE_API_KEY}",
            headers={"Content-Type": "application/json"},
            json=body
        )
        data = response.json()

        if "results" in data:
            combined = " ".join([r["alternatives"][0]["transcript"] for r in data["results"]])
            return {"transcript": combined, "raw_response": data}
        else:
            return JSONResponse(content={"error": "No transcript found", "details": data}, status_code=400)

    except Exception as e:
        return JSONResponse(content={"error": f"Google API request failed: {str(e)}"}, status_code=500)

# -------- RUN LOCALLY --------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000, reload=True)































# # thhis is for make post request 
# # https://m4a-to-wav-by-python.onrender.com/upload/



# from fastapi import FastAPI, File, UploadFile
# from fastapi.responses import JSONResponse
# import uvicorn
# import os
# import subprocess
# import uuid
# import base64
# import requests

# # Load API key from environment
# GOOGLE_API_KEY = 'AIzaSyDVksTONkieWNhplzhmpXTHCsYrjdDh1Mc'
# # GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# app = FastAPI()

# # Ensure uploads folder exists
# os.makedirs("uploads", exist_ok=True)

# @app.post("/upload/")
# async def upload_audio(file: UploadFile = File(...)):
#     file_id = str(uuid.uuid4())
#     input_path = f"uploads/{file_id}_{file.filename}"
#     output_path = f"uploads/{file_id}.wav"

#     # Save uploaded file
#     with open(input_path, "wb") as f:
#         f.write(await file.read())

#     # Convert to wav with ffmpeg
#     try:
#         subprocess.run(
#             ["ffmpeg", "-y", "-i", input_path, "-ar", "48000", "-ac", "1", output_path],
#             check=True,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE
#         )
#     except subprocess.CalledProcessError as e:
#         return JSONResponse(content={"error": f"Conversion failed: {e}"}, status_code=500)

#     # Encode wav to base64
#     try:
#         with open(output_path, "rb") as f:
#             encoded_audio = base64.b64encode(f.read()).decode("utf-8")
#     except Exception as e:
#         return JSONResponse(content={"error": f"Reading wav failed: {str(e)}"}, status_code=500)

#     # Prepare Google API request
#     body = {
#         "config": {
#             "encoding": "LINEAR16",  # since we converted to wav
#             "sampleRateHertz": 48000,
#             "languageCode": "en-US"
#         },
#         "audio": {
#             "content": encoded_audio
#         }
#     }

#     try:
#         response = requests.post(
#             f"https://speech.googleapis.com/v1/speech:recognize?key={GOOGLE_API_KEY}",
#             headers={"Content-Type": "application/json"},
#             json=body
#         )
#         data = response.json()

#         if "results" in data:
#             combined = " ".join([r["alternatives"][0]["transcript"] for r in data["results"]])
#             return {"transcript": combined, "raw_response": data}
#         else:
#             return JSONResponse(content={"error": "No transcript found", "details": data}, status_code=400)

#     except Exception as e:
#         return JSONResponse(content={"error": f"Google API request failed: {str(e)}"}, status_code=500)


















# # from fastapi import FastAPI, File, UploadFile
# # from fastapi.responses import JSONResponse
# # import uvicorn
# # import os
# # import subprocess
# # import uuid
# # import base64

# # app = FastAPI()

# # @app.post("/upload/")
# # async def upload_audio(file: UploadFile = File(...)):
# #     file_id = str(uuid.uuid4())
# #     input_path = f"uploads/{file_id}.m4a"
# #     output_path = f"uploads/{file_id}.wav"

# #     with open(input_path, "wb") as f:
# #         f.write(await file.read())

# #     # Convert .m4a to .wav using ffmpeg
# #     try:
# #         subprocess.run(["ffmpeg", "-y", "-i", input_path, output_path], check=True)
# #     except subprocess.CalledProcessError:
# #         return JSONResponse(content={"error": "Conversion failed"}, status_code=500)

# #     # Read .wav file and encode to base64
# #     try:
# #         with open(output_path, "rb") as f:
# #             encoded_audio = base64.b64encode(f.read()).decode("utf-8")
# #         return {
# #             "filename": f"{file_id}.wav",
# #             "base64_audio": encoded_audio
# #         }
# #     except Exception as e:
# #         return JSONResponse(content={"error": f"Reading output failed: {str(e)}"}, status_code=500)
