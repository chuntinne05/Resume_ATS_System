import os
from s3_service import s3_service

# ---------------------------------------------------------------------
# # Đọc file từ máy
# with open('CV-4.pdf', 'rb') as f:
#     file_content = f.read()

# # Upload file lên S3
# result = s3_service.upload_file(file_content, 'test.pdf')
# if result['success']:
#     print(f"Upload thành công!")
#     print(f"S3 Key: {result['s3_key']}")
#     print(f"S3 URL: {result['s3_url']}")
#     print(f"CDN URL: {result['cdn_url']}")
# else:
#     print(f"Upload thất bại: {result['error']}")

# ---------------------------------------------------------------------
# s3_key = 'resumes/5419f33e-cbc8-4001-8853-e62b4ff6f58e.pdf'  # Thay bằng s3_key từ bước upload
# file_content = s3_service.download_file(s3_key)
# if file_content:
#     with open('downloaded_test.pdf', 'wb') as f:
#         f.write(file_content)
#     print("Download thành công!")
# else:
#     print("Download thất bại!")

# ---------------------------------------------------------------------

# s3_key = 'resumes/5419f33e-cbc8-4001-8853-e62b4ff6f58e.pdf'  
# if s3_service.delete_file(s3_key):
#     print("Delete thành công!")
# else:
#     print("Delete thất bại!")

# ---------------------------------------------------------------------
# s3_key = 'resumes/5419f33e-cbc8-4001-8853-e62b4ff6f58e.pdf'  # Thay bằng s3_key từ bước upload
# url = s3_service.generate_presigned_url(s3_key)
# if url:
#     print(f"Presigned URL: {url}")
# else:
#     print("Không thể tạo presigned URL!")