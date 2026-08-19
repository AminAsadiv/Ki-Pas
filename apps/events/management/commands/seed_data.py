from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.events.models import EventCategory, EventSubcategory

CATEGORIES = [
    ('Sports', 'dumbbell', ['Football','Basketball','Volleyball','Tennis','Running','Cycling','Hiking','Gym & Fitness','Martial Arts','Swimming','Table Tennis','Chess','Other Sports']),
    ('Entertainment', 'music', ['Concerts','Festivals','Movies','Gaming','Board Games','Karaoke','Parties','Comedy Shows']),
    ('Education', 'book-open', ['Study Groups','Workshops','Seminars','Language Exchange','Coding','Book Clubs','Tutoring']),
    ('Technology', 'cpu', ['Startup Meetups','AI','Programming','Robotics','Cybersecurity','Networking']),
    ('Business', 'briefcase', ['Networking','Entrepreneurship','Investing','Job Fair','Mentorship','Freelancing']),
    ('Arts', 'palette', ['Photography','Painting','Music','Dance','Theater','Writing','Film Making']),
    ('Food & Drinks', 'utensils', ['Restaurant Meetups','Coffee','Cooking Classes','Wine Tasting','Food Festival']),
    ('Travel & Outdoors', 'map', ['Road Trips','Camping','Backpacking','Sightseeing','Nature Walks','Beach','Fishing']),
    ('Community', 'heart', ['Volunteering','Charity','Environmental Cleanup','Blood Donation','Neighborhood Meetup']),
    ('Lifestyle', 'sparkles', ['Pets','Parenting','Fashion','Wellness','Meditation','Yoga']),
    ('Social', 'users', ['Meet New Friends','Singles Meetup','Family Gathering','Birthday','Picnic','Casual Hangout']),
    ('Health', 'activity', ['Mental Health','Support Groups','Wellness Talks','Fitness Challenges']),
    ('Activism', 'megaphone', ['Peaceful Protest','Awareness Campaign','Community Discussion','Petition Gathering']),
    ('Shopping', 'shopping-bag', ['Garage Sale','Flea Market','Swap Meet','Product Launch']),
    ('Religion & Culture', 'globe', ['Cultural Festival','Museum Visit','Religious Gathering','Traditional Celebration']),
    ('Online', 'monitor', ['Virtual Meetup','Livestream','Online Workshop','Watch Party']),
    ('Emergency', 'alert-triangle', ['SOS','Lost & Found','Disaster Relief','Community Alert']),
]

class Command(BaseCommand):
    help = 'Seed initial categories and subcategories'

    def handle(self, *args, **kwargs):
        for i, (name, icon, subs) in enumerate(CATEGORIES):
            cat, created = EventCategory.objects.get_or_create(
                slug=slugify(name),
                defaults={'name': name, 'icon': icon, 'order': i}
            )
            if created:
                self.stdout.write(f'  Created: {name}')
            for sub_name in subs:
                EventSubcategory.objects.get_or_create(
                    category=cat, slug=slugify(sub_name),
                    defaults={'name': sub_name}
                )
        self.stdout.write(self.style.SUCCESS(f'Done! {EventCategory.objects.count()} categories seeded.'))
