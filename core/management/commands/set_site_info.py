# python manage.py set_site_info --name="Mobility Mapper" --domain="mobilitymapper.co.uk"
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site

class Command(BaseCommand):
    help = 'Sets the site name and domain for the current SITE_ID.'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, required=True, help='Site name')
        parser.add_argument('--domain', type=str, required=True, help='Site domain')

    def handle(self, *args, **options):
        site_id = 1  # Default SITE_ID
        name = options['name']
        domain = options['domain']
        site, created = Site.objects.get_or_create(id=site_id)
        site.name = name
        site.domain = domain
        site.save()
        self.stdout.write(self.style.SUCCESS(f'Site info updated: {name} ({domain})'))
