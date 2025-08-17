# Development:
# python manage.py migrate_media_to_cloudinary
# Production (CLI on local machine):
# heroku login
# heroku git:remote -a mm-business-portal
# heroku run python manage.py migrate_media_to_cloudinary --app your-app-name
import os
import glob

from django.core.management.base import BaseCommand
from django.core.files import File

from cloudinary_storage.storage import MediaCloudinaryStorage
import cloudinary.uploader as cloudinary_uploader
from django.conf import settings
from businesses.models import Business, WheelerVerificationPhoto
from accounts.models import UserProfile

class Command(BaseCommand):
    help = 'Upload existing MEDIA_ROOT files to Cloudinary and relink model fields'

    def handle(self, *args, **options):
        storage = MediaCloudinaryStorage()
        # Preprocess: revert DB names to local basenames so match works
        self.stdout.write('Resetting DB image names to local basenames...')
        for biz in Business.objects.exclude(logo=''):
            basename = os.path.basename(biz.logo.name)
            biz.logo.name = basename
            biz.save(update_fields=['logo'])
        for prof in UserProfile.objects.exclude(photo=''):
            basename = os.path.basename(prof.photo.name)
            prof.photo.name = basename
            prof.save(update_fields=['photo'])
        for wp in WheelerVerificationPhoto.objects.exclude(image=''):
            basename = os.path.basename(wp.image.name)
            wp.image.name = basename
            wp.save(update_fields=['image'])
        # 1) Business logos: upload per-instance
        for biz in Business.objects.exclude(logo=''):
            # Determine local filename by removing Cloudinary suffix
            public_id = os.path.basename(biz.logo.name)
            root = public_id.rsplit('_', 1)[0]
            # find any matching file in business_logos with this root
            pattern = os.path.join(settings.MEDIA_ROOT, 'business_logos', f"{root}.*")
            matches = glob.glob(pattern)
            if not matches:
                self.stdout.write(f'SKIP Business #{biz.pk}: no local file matching {root} in business_logos/')
                continue
            local_path = matches[0]
            basename = os.path.basename(local_path)
            self.stdout.write(f'Uploading Business #{biz.pk} logo: {local_path}')
            try:
                resp = cloudinary_uploader.upload(
                    local_path,
                    folder=f"{settings.CLOUDINARY_STORAGE['FOLDER']}/media/business_logos",
                    public_id=root,
                    overwrite=True
                )
                cloud_name = resp.get('public_id')
            except Exception as e:
                self.stderr.write(f'ERROR uploading Business #{biz.pk}: {e}')
                continue
            biz.logo.name = cloud_name
            biz.save(update_fields=['logo'])
            self.stdout.write(f'Business #{biz.pk} logo → {cloud_name}')

        # 2) UserProfile photos: upload per-instance
        for prof in UserProfile.objects.exclude(photo=''):
            public_id = os.path.basename(prof.photo.name)
            root = public_id.rsplit('_', 1)[0]
            pattern = os.path.join(settings.MEDIA_ROOT, 'profile_photos', f"{root}.*")
            matches = glob.glob(pattern)
            if not matches:
                self.stdout.write(f'SKIP UserProfile #{prof.pk}: no local file matching {root} in profile_photos/')
                continue
            local_path = matches[0]
            basename = os.path.basename(local_path)
            self.stdout.write(f'Uploading UserProfile #{prof.pk} photo: {local_path}')
            try:
                resp = cloudinary_uploader.upload(
                    local_path,
                    folder=f"{settings.CLOUDINARY_STORAGE['FOLDER']}/media/profile_photos",
                    public_id=root,
                    overwrite=True
                )
                cloud_name = resp.get('public_id')
            except Exception as e:
                self.stderr.write(f'ERROR uploading UserProfile #{prof.pk}: {e}')
                continue
            prof.photo.name = cloud_name
            prof.save(update_fields=['photo'])
            self.stdout.write(f'UserProfile #{prof.pk} photo → {cloud_name}')

        # 3) WheelerVerificationPhoto entries: upload per-instance
        for wp in WheelerVerificationPhoto.objects.exclude(image=''):
            public_id = os.path.basename(wp.image.name)
            root = public_id.rsplit('_', 1)[0]
            pattern = os.path.join(settings.MEDIA_ROOT, 'verification_photos', f"{root}.*")
            matches = glob.glob(pattern)
            if not matches:
                self.stdout.write(f'SKIP VerificationPhoto #{wp.pk}: no local file matching {root} in verification_photos/')
                continue
            local_path = matches[0]
            basename = os.path.basename(local_path)
            self.stdout.write(f'Uploading VerificationPhoto #{wp.pk}: {local_path}')
            try:
                resp = cloudinary_uploader.upload(
                    local_path,
                    folder=f"{settings.CLOUDINARY_STORAGE['FOLDER']}/media/verification_photos",
                    public_id=root,
                    overwrite=True
                )
                cloud_name = resp.get('public_id')
            except Exception as e:
                self.stderr.write(f'ERROR uploading VerificationPhoto #{wp.pk}: {e}')
                continue
            wp.image.name = cloud_name
            wp.save(update_fields=['image'])
            self.stdout.write(f'VerificationPhoto #{wp.pk} → {cloud_name}')

        self.stdout.write(self.style.SUCCESS('Media migration complete.'))