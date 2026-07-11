from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generates a VAPID public/private key pair for Web Push notifications and prints .env-ready lines."

    def handle(self, *args, **options):
        try:
            from py_vapid import Vapid
        except ImportError:
            self.stderr.write(
                self.style.ERROR(
                    "py-vapid is not installed. Run: pip install py-vapid --break-system-packages"
                )
            )
            return

        import base64
        import tempfile

        vapid = Vapid()
        vapid.generate_keys()

        private_raw = vapid.private_pem()
        public_raw = vapid.public_key.public_bytes(
            encoding=__import__("cryptography.hazmat.primitives.serialization", fromlist=["Encoding"]).Encoding.X962,
            format=__import__("cryptography.hazmat.primitives.serialization", fromlist=["PublicFormat"]).PublicFormat.UncompressedPoint,
        )

        public_b64 = base64.urlsafe_b64encode(public_raw).rstrip(b"=").decode()

        self.stdout.write(self.style.SUCCESS("Add these to your .env file:\n"))
        self.stdout.write(f"VAPID_PUBLIC_KEY={public_b64}")
        self.stdout.write("VAPID_PRIVATE_KEY=<see private_key.pem written below, paste full PEM contents inline or load via file>")
        self.stdout.write(
            self.style.WARNING(
                "\nNote: pywebpush expects the PEM private key contents. "
                "Simplify by storing the .pem path instead and loading it in settings if preferred."
            )
        )
