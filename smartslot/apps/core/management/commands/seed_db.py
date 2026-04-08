from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.models import Organisation
from apps.resources.models import Resource

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with sample data for SmartSlot.'

    def handle(self, *args, **kwargs):
        self._create_superuser()
        orgs = self._create_organisations()
        self._create_org_users(orgs)
        self._create_resources(orgs)
        self.stdout.write(self.style.SUCCESS('\nSmartSlot database seeded successfully.'))

    # ------------------------------------------------------------------ #
    #  Users
    # ------------------------------------------------------------------ #

    def _create_superuser(self):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                'admin', 'admin@smartslot.mw', 'admin',
                role='PlatformAdmin'
            )
            self.stdout.write(self.style.SUCCESS("Created platform admin  →  admin / admin"))
        else:
            self.stdout.write(self.style.WARNING("Platform admin 'admin' already exists."))

    def _create_org_users(self, orgs):
        equip, blantyre = orgs['equip'], orgs['blantyre']

        users = [
            # Equip Group
            dict(username='equip_admin',    email='admin@equipgroup.mw',      password='pass1234',
                 first_name='Tadala',  last_name='Banda',   role='OrganisationAdmin', org=equip),
            dict(username='equip_recep',    email='recep@equipgroup.mw',       password='pass1234',
                 first_name='Chisomo', last_name='Phiri',   role='Receptionist',      org=equip),
            dict(username='lusekero',       email='lusekero@equipgroup.mw',    password='pass1234',
                 first_name='Lusekero', last_name='Mwanjoka', role='Employee',         org=equip),
            dict(username='chimwemwe',      email='chimwemwe@equipgroup.mw',   password='pass1234',
                 first_name='Chimwemwe', last_name='Katenje', role='Employee',         org=equip),
            # Blantyre Consulting
            dict(username='blantyre_admin', email='admin@blantyreconsult.mw',  password='pass1234',
                 first_name='Mphatso', last_name='Chirwa',  role='OrganisationAdmin', org=blantyre),
            dict(username='blantyre_recep', email='recep@blantyreconsult.mw',  password='pass1234',
                 first_name='Yankho',  last_name='Tembo',   role='Receptionist',      org=blantyre),
            dict(username='sifiso',         email='sifiso@blantyreconsult.mw', password='pass1234',
                 first_name='Sifiso',  last_name='Chitowe', role='Employee',           org=blantyre),
        ]

        for u in users:
            org = u.pop('org')  
            if not User.objects.filter(username=u['username']).exists():
                User.objects.create_user(**u)
                self.stdout.write(self.style.SUCCESS(
                    f"  Created user  →  {u['username']} ({u['role']})"
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"  User '{u['username']}' already exists."
                ))

    

    def _create_organisations(self):
        equip, created = Organisation.objects.get_or_create(name='Equip Group')
        if created:
            self.stdout.write(self.style.SUCCESS("Created organisation  →  Equip Group"))
        else:
            self.stdout.write(self.style.WARNING("Organisation 'Equip Group' already exists."))

        blantyre, created = Organisation.objects.get_or_create(name='Blantyre Consulting Ltd')
        if created:
            self.stdout.write(self.style.SUCCESS("Created organisation  →  Blantyre Consulting Ltd"))
        else:
            self.stdout.write(self.style.WARNING("Organisation 'Blantyre Consulting Ltd' already exists."))

        return {'equip': equip, 'blantyre': blantyre}



    def _create_resources(self, orgs):
        equip    = orgs['equip']
        blantyre = orgs['blantyre']

        resources = [
            # Equip Group
            {
                "organisation": equip,
                "name": "Main Boardroom A",
                "description": (
                    "Spacious boardroom at the Area 3 Lilongwe office. "
                    "Seats 20, equipped with a wall-mounted smart projector, "
                    "whiteboard, and high-speed Wi-Fi."
                ),
                "price": 0.00,
                "category": "Boardroom",
                "custom_fields": {"capacity": 20, "has_projector": True, "floor": "Ground"}
            },
            {
                "organisation": equip,
                "name": "Executive Boardroom",
                "description": (
                    "Premium boardroom reserved for executive meetings and VIP client sessions. "
                    "Features video-conferencing equipment and leather seating for 10."
                ),
                "price": 10000.00,
                "category": "Boardroom",
                "custom_fields": {"capacity": 10, "has_video_conferencing": True, "floor": "First"}
            },
            {
                "organisation": equip,
                "name": "Toyota Hilux GD-6",
                "description": (
                    "Double-cabin 4x4 field vehicle for out-of-town client operations. "
                    "Fuel card included. Driver available on request."
                ),
                "price": 50000.00,
                "category": "Vehicle",
                "custom_fields": {"plate_number": "BU 4587", "passengers": 5, "fuel_card": True}
            },
            {
                "organisation": equip,
                "name": "Toyota Corolla (Town Runs)",
                "description": (
                    "Sedan for in-city errands and client pickups within Lilongwe. "
                    "Self-drive permitted for authorised staff."
                ),
                "price": 15000.00,
                "category": "Vehicle",
                "custom_fields": {"plate_number": "LLW 9921", "passengers": 4, "self_drive": True}
            },
            {
                "organisation": equip,
                "name": "Sony Portable Projector",
                "description": (
                    "Full HD portable projector ideal for client presentations and off-site workshops. "
                    "Includes carry bag and HDMI/USB-C adapters."
                ),
                "price": 5000.00,
                "category": "Equipment",
                "custom_fields": {"resolution": "1080p", "lumens": 3200, "portable": True}
            },
            {
                "organisation": equip,
                "name": "Canon EOS R50 Camera Kit",
                "description": (
                    "Mirrorless camera kit for corporate events, site visits, and marketing shoots. "
                    "Includes 18-45mm lens, tripod, and two batteries."
                ),
                "price": 8000.00,
                "category": "Equipment",
                "custom_fields": {"megapixels": 24, "includes_tripod": True, "lens": "18-45mm"}
            },

            # Blantyre Consulting Ltd 
            {
                "organisation": blantyre,
                "name": "Conference Room 1",
                "description": (
                    "Main conference room at the Blantyre CBD office. "
                    "Seats 15 with a ceiling-mounted projector and air conditioning."
                ),
                "price": 0.00,
                "category": "Boardroom",
                "custom_fields": {"capacity": 15, "has_projector": True, "air_conditioned": True}
            },
            {
                "organisation": blantyre,
                "name": "Training Room",
                "description": (
                    "Dedicated training room with individual workstations for 12 participants. "
                    "Ideal for workshops, onboarding sessions, and seminars."
                ),
                "price": 7500.00,
                "category": "Boardroom",
                "custom_fields": {"capacity": 12, "workstations": 12, "has_whiteboard": True}
            },
            {
                "organisation": blantyre,
                "name": "Mitsubishi Pajero (Field)",
                "description": (
                    "SUV for field assignments and inter-city travel. "
                    "Requires advance booking of at least 24 hours."
                ),
                "price": 45000.00,
                "category": "Vehicle",
                "custom_fields": {"plate_number": "BT 1134", "passengers": 7, "advance_notice_hrs": 24}
            },
            {
                "organisation": blantyre,
                "name": "Epson EB-X51 Projector",
                "description": (
                    "Portable XGA projector for presentations and training sessions. "
                    "Brightness 3800 lumens, includes remote and carry case."
                ),
                "price": 3500.00,
                "category": "Equipment",
                "custom_fields": {"resolution": "XGA", "lumens": 3800, "portable": True}
            },
        ]

        for res in resources:
            org = res.pop('organisation')
            obj, created = Resource.objects.get_or_create(
                name=res['name'],
                organisation=org,
                defaults=res
            )
            status = "Created" if created else "Exists "
            style  = self.style.SUCCESS if created else self.style.WARNING
            self.stdout.write(style(
                f"  [{org.name}]  {status}  →  {obj.name}"
            ))
