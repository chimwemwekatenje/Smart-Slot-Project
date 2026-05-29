"""Management command to add images to resources."""
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from apps.resources.models import Resource
import os


class Command(BaseCommand):
    help = 'Add images to resources from the photos folder'

    def handle(self, *args, **options):
        # Define image mappings: resource_id -> image_path
        image_mappings = {
            1: 'r50_creator_s_kit_ecommerce_6073.webp',  # Main Boardroom A - projector
            2: 'r50_creator_s_kit_ecommerce_6073.webp',  # Executive Boardroom - video conferencing
            11: '612L0LuhL-L._AC_UF1000,1000_QL80_.jpg',  # chairs - office seating
        }
        
        photos_folder = r'c:\Users\HP\Desktop\Smart Slots\Smart-Slot-Project\photos'
        
        for resource_id, image_filename in image_mappings.items():
            try:
                resource = Resource.objects.get(id=resource_id)
                image_path = os.path.join(photos_folder, image_filename)
                
                if not os.path.exists(image_path):
                    self.stdout.write(self.style.WARNING(f'Image not found: {image_path}'))
                    continue
                
                with open(image_path, 'rb') as f:
                    resource.photo.save(
                        image_filename,
                        ContentFile(f.read()),
                        save=True
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully added image to resource {resource_id} ({resource.name})'
                    )
                )
            except Resource.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Resource {resource_id} not found'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error for resource {resource_id}: {e}'))
