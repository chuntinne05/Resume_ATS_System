import boto3
import os
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any
import uuid
import time
from pathlib import Path
import mimetypes
from dotenv import load_dotenv

load_dotenv()

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'ap-southeast-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'resume-ats-files')
        self.cloudfront_domain = os.getenv('CLOUDFRONT_DOMAIN', '')

    def upload_file(self, file_content: bytes, filename: str, content_type: str = None) -> Dict[str, Any]:
        """Upload file to S3"""
        try:
            file_extension = Path(filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            s3_key = f"resumes/{unique_filename}"
            
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'original_filename': filename,
                    'upload_timestamp': str(int(time.time()))
                }
            )
            
            # Generate URLs
            s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            cdn_url = f"https://{self.cloudfront_domain}/{s3_key}" if self.cloudfront_domain else s3_url
            
            return {
                'success': True,
                's3_key': s3_key,
                's3_url': s3_url,
                'cdn_url': cdn_url,
                'file_size': len(file_content),
                'content_type': content_type
            }
            
        except ClientError as e:
            return {
                'success': False,
                'error': str(e)
            }
        
    def download_file(self, s3_key: str) -> Optional[bytes]:
        """Download file from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response['Body'].read()
        except ClientError:
            return None
    
    def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False
    
    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """Generate presigned URL for file access"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError:
            return None
        
s3_service = S3Service()