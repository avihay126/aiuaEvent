import boto3
import os
from dotenv import load_dotenv

load_dotenv()


def get_s3_client():
    s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION'),
)    
    return s3_client



def upload_image_to_s3(s3_key, image, s3_client):
    try:
        
        s3_client.upload_fileobj(
            image,
            os.getenv('AWS_BUCKET_NAME'),
            s3_key,
        )
        s3_url = f"https://{os.getenv('AWS_BUCKET_NAME')}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{s3_key}"
        print(f"Image uploaded successfully to: {s3_url}")
        return s3_url
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        raise Exception(f"Error uploading to S3: {e}")