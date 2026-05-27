import os
import django
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.resources.models import Resource
from apps.core.models import Organisation
from apps.accounts.models import User

def main():
    print("Starting upload test...")

    # Ensure an organization exists
    org, _ = Organisation.objects.get_or_create(name="Test Org")
    
    # Ensure a user exists (BaseModel requires created_by)
    user, _ = User.objects.get_or_create(email="test@example.com", defaults={"username": "testuser"})

    # Create a small dummy image in memory
    print("Generating a test image...")
    img = Image.new('RGB', (100, 100), color='blue')
    img_io = BytesIO()
    img.save(img_io, format='JPEG')
    img_io.seek(0)
    
    img_file = SimpleUploadedFile("test_blue_image.jpg", img_io.getvalue(), content_type="image/jpeg")

    # Create a resource and attach the image
    print("Creating a Resource object and saving to trigger upload...")
    res = Resource(
        name="Test Upload Resource", 
        category="Test", 
        price=9.99, 
        organisation=org
    )
    res.photo = img_file
    res.save()

    print("--- Results ---")
    print(f"Resource ID: {res.id}")
    print(f"Photo local field: {res.photo}")
    print(f"Supabase Image URL: {res.image_url}")

    if res.image_url:
        print("\nSUCCESS: Image uploaded to Supabase and URL is populated!")
    else:
        print("\nFAILED: image_url is missing. Check if SUPABASE_URL and SUPABASE_KEY are set in .env and the media bucket is accessible.")

if __name__ == "__main__":
    main()
