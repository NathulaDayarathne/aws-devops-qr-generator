import hashlib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import qrcode
import boto3
import os
from io import BytesIO

# Loading Environment variable (AWS Access Key and Secret Key)
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# Allowing CORS for local testing
origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS S3 Configuration
s3 = boto3.client(
    's3',
    aws_access_key_id= os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key= os.getenv("AWS_SECRET_KEY"))

bucket_name = 'myawsqrbucket' # Add your bucket name here

@app.post("/generate-qr/")
async def generate_qr(url: str):
    try:
        # Debug: Print URL to verify input
        print(f"Generating QR for: {url}")

        # Generate QR Code
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Save QR Code to BytesIO
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        # Generate hashed filename
        hashed_url = hashlib.md5(url.encode()).hexdigest()
        file_name = f"qr_codes/{hashed_url}.png"

        # Debug: Print file name and bucket
        print(f"Uploading to S3: {bucket_name}/{file_name}")

        # Upload to S3
        s3.put_object(Bucket=bucket_name, Key=file_name, Body=img_byte_arr, ContentType='image/png')

        # Generate a pre-signed URL valid for 1 hour
        s3_url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': file_name}, ExpiresIn=3600)

        return {"qr_code_url": s3_url}
    
    except Exception as e:
        print(f"Error: {e}")  # Print full error for debugging
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
