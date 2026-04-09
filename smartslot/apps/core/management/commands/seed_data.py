from django.core.management.base import BaseCommand
from apps.core.models import Organisation
from apps.resources.models import Resource


ORGANISATIONS = [
    'Equip Group',
    'Blantyre Consulting Limited',
    'Malawi Revenue Authority',
    'National Bank of Malawi',
    'Sunbird Tourism',
    'University of Malawi',
    'Airtel Malawi',
    'Press Corporation Limited',
]

RESOURCES = [
    {
        'org': 'Equip Group',
        'items': [
            {'name': 'Main Boardroom', 'category': 'Boardroom', 'price': '0.00',
             'description': 'Seats 20 people. Projector, whiteboard, and video conferencing available.'},
            {'name': 'Executive Suite', 'category': 'Boardroom', 'price': '5000.00',
             'description': 'Premium meeting room for executive meetings. Seats 10.'},
            {'name': 'Toyota Hilux (EG-001)', 'category': 'Vehicle', 'price': '15000.00',
             'description': 'Double cab pickup for field operations. Driver available on request.'},
        ],
    },
    {
        'org': 'Blantyre Consulting Limited',
        'items': [
            {'name': 'Conference Hall A', 'category': 'Conference Hall', 'price': '20000.00',
             'description': 'Large conference hall seating 100 people. Full AV setup included.'},
            {'name': 'Training Room 1', 'category': 'Training Room', 'price': '8000.00',
             'description': 'Seats 30 people. Ideal for workshops and training sessions.'},
            {'name': 'Projector (BLC-P01)', 'category': 'Equipment', 'price': '2000.00',
             'description': 'HD projector available for hire. Includes HDMI and VGA cables.'},
        ],
    },
    {
        'org': 'University of Malawi',
        'items': [
            {'name': 'Great Hall', 'category': 'Event Venue', 'price': '50000.00',
             'description': 'Iconic venue seating 500 guests. Available for graduations, conferences, and public events.'},
            {'name': 'Senate Room', 'category': 'Boardroom', 'price': '0.00',
             'description': 'Formal meeting room for official university business. Seats 25.'},
            {'name': 'Minibus (UNIMA-01)', 'category': 'Vehicle', 'price': '12000.00',
             'description': '30-seater minibus for official university trips.'},
        ],
    },
    {
        'org': 'Sunbird Tourism',
        'items': [
            {'name': 'Lakeview Banquet Hall', 'category': 'Event Venue', 'price': '80000.00',
             'description': 'Stunning lakeside venue for weddings, galas, and corporate events. Seats 300.'},
            {'name': 'Business Centre Room', 'category': 'Boardroom', 'price': '10000.00',
             'description': 'Fully equipped business centre meeting room. Seats 12.'},
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed dummy organisations and resources for demo'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding organisations...')
        org_map = {}
        for name in ORGANISATIONS:
            org, created = Organisation.objects.get_or_create(name=name)
            org_map[name] = org
            status = 'Created' if created else 'Already exists'
            self.stdout.write(f'  {status}: {name}')

        self.stdout.write('Seeding resources...')
        for entry in RESOURCES:
            org = org_map.get(entry['org'])
            if not org:
                continue
            for item in entry['items']:
                _, created = Resource.objects.get_or_create(
                    name=item['name'],
                    organisation=org,
                    defaults={
                        'category': item['category'],
                        'price': item['price'],
                        'description': item['description'],
                    },
                )
                status = 'Created' if created else 'Already exists'
                self.stdout.write(f'  {status}: {item["name"]} @ {entry["org"]}')

        self.stdout.write(self.style.SUCCESS('Done. Seed data loaded successfully.'))
