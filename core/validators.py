from django.core.exceptions import ValidationError
from django.conf import settings
from PIL import Image, UnidentifiedImageError

def validate_image_file(
    image_file,
    *,
    max_file_size=None,
    max_dimension=None,
    require_square=False,
    allowed_mimes=None,
    allowed_exts=None,
    allowed_formats=None,
    purpose="image",
):
    """
    Centralized image validator.

    - image_file: UploadedFile / file-like object
    - max_file_size: bytes (defaults to settings.IMAGE_MAX_FILE_SIZE or 5MB)
    - max_dimension: max pixel width/height (defaults to settings.IMAGE_MAX_DIMENSION or 3000)
    - require_square: if True, enforce width == height
    - allowed_mimes / allowed_exts / allowed_formats: iterable of allowed hints/formats
      (defaults include PNG, JPEG, WEBP)
    - purpose: text used in error messages (e.g. 'logo', 'profile photo')

    Raises django.core.exceptions.ValidationError on invalid files.
    """
    if not image_file:
        return image_file

    # Defaults (configurable via Django settings)
    max_file_size = max_file_size or getattr(settings, "IMAGE_MAX_FILE_SIZE", 5 * 1024 * 1024)
    max_dimension = max_dimension or getattr(settings, "IMAGE_MAX_DIMENSION", 3000)
    allowed_mimes = tuple(allowed_mimes or getattr(settings, "IMAGE_ALLOWED_MIMES", ("image/png", "image/jpeg", "image/webp")))
    allowed_exts = tuple(allowed_exts or getattr(settings, "IMAGE_ALLOWED_EXTS", (".png", ".jpg", ".jpeg", ".webp")))
    allowed_formats = tuple(f.upper() for f in (allowed_formats or getattr(settings, "IMAGE_ALLOWED_FORMATS", ("PNG", "JPEG", "WEBP"))))

    # Quick size hint check
    size = getattr(image_file, "size", None)
    if size is not None and size > max_file_size:
        raise ValidationError(f"{purpose.capitalize()} file too large (maximum {int(max_file_size / (1024 * 1024))} MB).")

    # MIME / extension hints (not authoritative but useful early filter)
    content_type = getattr(image_file, "content_type", "")
    if content_type and content_type not in allowed_mimes:
        raise ValidationError(f"Please upload a {', '.join(x.replace('image/','').upper() for x in allowed_mimes)} {purpose}.")

    name = getattr(image_file, "name", "") or ""
    if name and not name.lower().endswith(allowed_exts):
        raise ValidationError(f"Please upload a {', '.join(e.lstrip('.') for e in allowed_exts)} {purpose}.")

    # Work with underlying file-like object
    fileobj = getattr(image_file, "file", None) or getattr(image_file, "stream", None) or image_file

    try:
        try:
            fileobj.seek(0)
        except Exception:
            # some wrappers don't support seek; continue anyway
            pass

        # First verify to detect truncated/corrupt images
        try:
            verifier = Image.open(fileobj)
            verifier.verify()
        except UnidentifiedImageError:
            raise ValidationError(f"The uploaded {purpose} is not a valid image.")
        except Exception as exc:
            # Catch other PIL errors (e.g. decompression bomb)
            raise ValidationError(f"The uploaded {purpose} could not be processed ({exc}).")
        finally:
            try:
                fileobj.seek(0)
            except Exception:
                pass

        # Reopen to inspect format and dimensions
        with Image.open(fileobj) as img:
            img.load()  # force full decode to detect issues
            fmt = (img.format or "").upper()
            if fmt not in allowed_formats:
                raise ValidationError(f"Please upload a valid {', '.join(allowed_formats)} {purpose}.")
            width, height = img.size
            if require_square and width != height:
                raise ValidationError(f"The {purpose} must be square (width and height must match).")
            if width > max_dimension or height > max_dimension:
                raise ValidationError(f"{purpose.capitalize()} dimensions too large (max {max_dimension}x{max_dimension} pixels).")
    finally:
        try:
            fileobj.seek(0)
        except Exception:
            pass

    return image_file


def validate_profile_photo(image_file, *, purpose="profile photo"):
    """
    Profile photo validator — uses the same file-size / dimension defaults as IMAGE_MAX_*
    and enforces square images.
    """
    return validate_image_file(image_file, require_square=True, purpose=purpose)


def validate_logo(image_file, *, purpose="logo"):
    """
    Logo validator — identical limits to profile photos and also enforces square images.
    """
    return validate_image_file(image_file, require_square=True, purpose=purpose)