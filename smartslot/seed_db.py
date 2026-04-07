import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.core.models import Organisation
from apps.resources.models import Resource

def run():
    # 1. Create Superuser (so you can log into Admin)
    # Using simple credentials: admin / admin
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@smartslot.com', 'admin')
        print("Created Superuser: 'admin' with password: 'admin'")
    else:
        print("Superuser 'admin' already exists.")

    # 2. Create the organisation based on your use case
    equip_group, created = Organisation.objects.get_or_create(name='Equip Group')

    if created:
        print(f"Created Organisation: {equip_group}")
    else:
        print(f"Organisation {equip_group} already exists.")

    # 3. List of resources based on boardrooms, vehicles, and equipment
    resources = [
        {
            "name": "Main Boardroom A",
            "description": "Large boardroom located in Area 3 office featuring a smart projector and seating for 20.",
            "price": 0.00,
            "category": "Boardroom",
            "custom_fields": {"capacity": 20, "has_projector": True}
        },
        {
            "name": "Executive Boardroom",
            "description": "Premium boardroom for executive meetings and VIP client sessions.",
            "price": 10000.00, # Arbitrary price, assumingly MWK
            "category": "Boardroom",
            "custom_fields": {"capacity": 10, "has_video_conferencing": True}
        },
        {
            "name": "Toyota Hilux GD-6 (Field Vehicle)",
            "description": "Double cabin vehicle suited for out-of-town client operations and field work.",
            "price": 50000.00,
            "category": "Vehicle",
            "custom_fields": {"plate_number": "BU 4587", "passengers": 5}
        },
        {
            "name": "Sony Portable Projector",
            "description": "High visibility portable projector for client presentations.",
            "price": 5000.00,
            "category": "Equipment",
            "custom_fields": {"resolution": "1080p", "type": "portable"}
        }
    ]

    for res in resources:
        obj, r_created = Resource.objects.get_or_create(
            name=res['name'],
            organisation=equip_group,
            defaults={
                "description": res['description'],
                "price": res['price'],
                "category": res['category'],
                "custom_fields": res['custom_fields']
            }
        )
        if r_created:
            print(f"Created Resource: {obj}")
        else:
            print(f"Resource {obj} already exists.")

if __name__ == '__main__':
    run()

