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
    Centralized image validator that distinguishes between:
      - wrong file type / extension (raises "not a valid file type")
      - corrupted / unreadable image (raises "corrupted image")
    """
    if not image_file:
        return image_file

    # Defaults
    max_file_size = max_file_size or getattr(settings, "IMAGE_MAX_FILE_SIZE", 5 * 1024 * 1024)
    max_dimension = max_dimension or getattr(settings, "IMAGE_MAX_DIMENSION", 3000)
    allowed_mimes = tuple(allowed_mimes or getattr(settings, "IMAGE_ALLOWED_MIMES", ("image/png", "image/jpeg", "image/webp")))
    allowed_exts = tuple(allowed_exts or getattr(settings, "IMAGE_ALLOWED_EXTS", (".png", ".jpg", ".jpeg", ".webp")))
    allowed_formats = tuple(f.upper() for f in (allowed_formats or getattr(settings, "IMAGE_ALLOWED_FORMATS", ("PNG", "JPEG", "WEBP"))))

    # Quick size hint check
    size = getattr(image_file, "size", None)
    if size is not None and size > max_file_size:
        raise ValidationError(f"{purpose.capitalize()} file too large (maximum {int(max_file_size / (1024 * 1024))} MB).")

    # Early hint checks (extension / content-type) -> clear "not allowed type" message
    name = getattr(image_file, "name", "") or ""
    content_type = getattr(image_file, "content_type", "")
    if name:
        lower_name = name.lower()
        if not lower_name.endswith(allowed_exts):
            raise ValidationError(f"Please upload a PNG, JPEG or WEBP {purpose}. SVG or other formats are not allowed.")
    if content_type and content_type not in allowed_mimes:
        raise ValidationError(f"Please upload a PNG, JPEG or WEBP {purpose}. SVG or other formats are not allowed.")

    # Work with underlying file-like object
    fileobj = getattr(image_file, "file", None) or getattr(image_file, "stream", None) or image_file

    try:
        try:
            fileobj.seek(0)
        except Exception:
            pass

        # verify to detect truncated / corrupted images
        try:
            verifier = Image.open(fileobj)
            verifier.verify()
        except UnidentifiedImageError:
            # Definitive "corrupted / unreadable image" message
            raise ValidationError(f"The uploaded {purpose} appears corrupted or unreadable.")
        except Exception:
            # Generic PIL failure -> treat as corrupted/unreadable
            raise ValidationError(f"The uploaded {purpose} appears corrupted or unreadable.")
        finally:
            try:
                fileobj.seek(0)
            except Exception:
                pass

        # Reopen and inspect dimensions/format
        with Image.open(fileobj) as img:
            img.load()
            fmt = (img.format or "").upper()
            if fmt not in allowed_formats:
                raise ValidationError(f"Please upload a PNG, JPEG or WEBP {purpose}. SVG or other formats are not allowed.")
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
    return validate_image_file(image_file, require_square=True, purpose=purpose)


def validate_logo(image_file, *, purpose="logo"):
    return validate_image_file(image_file, require_square=True, purpose=purpose)