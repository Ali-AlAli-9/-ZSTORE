import os
import urllib.request
from urllib.parse import quote
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from products.models import Product
from django.conf import settings

UNSPLASH_IDS = [
    "1511707171634-5f897ff02aa9",  # smartphone (iPhone)
    "1580910051074-3eb694886505",  # phone (Samsung)
    "1517336714731-489689fd1ca8",  # MacBook on desk
    "1496181133206-80ce9b88a853",  # laptop on desk
    "1505740420928-5e560c06d30e",  # headphones
    "1606220588913-b3aacb4d2f46",  # earbuds (AirPods)
    "1523275335684-37898b6baf30",  # watch
    "1579586337278-3befd40fd17a",  # watch
    "1544244015-0df4b3ffc6b0",     # tablet
    "1615663245857-ac93bb7c39e7",  # mouse
    "1593642632559-0c6d3fc62b89",  # gaming laptop
    "1578303512597-81e6cc155b3e",  # Nintendo Switch
    "1626379953822-baec19c3accd",  # e-reader (Kindle)
    "1580910051074-3eb694886505",  # phone (Pixel)
    "1516035069371-29a1b244cc32",  # camera
]

PLACEHOLD_COLORS = [
    ("4f46e5", "ffffff"),  # indigo
    ("7c3aed", "ffffff"),  # violet
    ("2563eb", "ffffff"),  # blue
    ("0891b2", "ffffff"),  # cyan
    ("7c3aed", "ffffff"),  # violet
    ("6366f1", "ffffff"),  # indigo
    ("0d9488", "ffffff"),  # teal
    ("0d9488", "ffffff"),  # teal
    ("2563eb", "ffffff"),  # blue
    ("6b7280", "ffffff"),  # gray
    ("dc2626", "ffffff"),  # red
    ("e11d48", "ffffff"),  # rose
    ("ca8a04", "ffffff"),  # yellow
    ("4f46e5", "ffffff"),  # indigo
    ("d97706", "ffffff"),  # amber
]

PRODUCTS = [
    {
        "name": "iPhone 16 Pro Max",
        "description": "Apple's flagship smartphone featuring the A18 Pro chip, 48MP camera system, titanium design, and all-day battery life. Supports Apple Intelligence and advanced AI features.",
        "price": 1199.99,
        "stock": 15,
    },
    {
        "name": "Samsung Galaxy S25 Ultra",
        "description": "Samsung's premium flagship with built-in S Pen, 200MP camera, Galaxy AI features, and a stunning Dynamic AMOLED 2X display. Snapdragon 8 Elite processor.",
        "price": 1099.99,
        "stock": 12,
    },
    {
        "name": "MacBook Pro 16-inch M4",
        "description": "Apple's most powerful laptop with the M4 chip, up to 22 hours of battery life, Liquid Retina XDR display, and Thunderbolt 5 connectivity. Ideal for professionals.",
        "price": 2499.99,
        "stock": 8,
    },
    {
        "name": "Dell XPS 15",
        "description": "Premium Windows laptop featuring Intel Core Ultra processor, 15.6-inch OLED InfinityEdge display, slim aluminum chassis, and NVIDIA GeForce RTX graphics.",
        "price": 1799.99,
        "stock": 10,
    },
    {
        "name": "Sony WH-1000XM5",
        "description": "Industry-leading noise canceling wireless headphones with exceptional sound quality, 30-hour battery life, multipoint connection, and ultra-comfortable design.",
        "price": 349.99,
        "stock": 25,
    },
    {
        "name": "AirPods Pro 2",
        "description": "Apple's premium earbuds with Active Noise Cancellation, Adaptive Audio, USB-C charging case with Find My support, and personalized spatial audio.",
        "price": 249.99,
        "stock": 30,
    },
    {
        "name": "Apple Watch Ultra 2",
        "description": "The most rugged Apple Watch yet with 49mm titanium case, precision dual-frequency GPS, siren, and up to 36 hours of battery life. Built for extreme sports.",
        "price": 799.99,
        "stock": 18,
    },
    {
        "name": "Samsung Galaxy Watch 7",
        "description": "Advanced smartwatch with BioActive sensor, sleep apnea detection, Samsung Health AI features, and Wear OS with One UI Watch 6.",
        "price": 449.99,
        "stock": 20,
    },
    {
        "name": "iPad Pro 13-inch M4",
        "description": "Apple's thinnest and most powerful iPad with the M4 chip, Ultra Retina XDR tandem OLED display, Apple Pencil Pro support, and 5G connectivity.",
        "price": 1299.99,
        "stock": 14,
    },
    {
        "name": "Logitech MX Master 3S",
        "description": "Premium wireless mouse with 8000 DPI optical sensor, quiet click buttons, electromagnetic scroll wheel, and USB-C fast charging. 70-day battery life.",
        "price": 99.99,
        "stock": 40,
    },
    {
        "name": "ASUS ROG Zephyrus G14",
        "description": "Ultraportable gaming laptop with AMD Ryzen 9 processor, NVIDIA RTX 4070 graphics, 14-inch QHD 165Hz display, and excellent battery life for gamers on the go.",
        "price": 1599.99,
        "stock": 7,
    },
    {
        "name": "Nintendo Switch OLED",
        "description": "Nintendo's latest console with a vibrant 7-inch OLED screen, enhanced audio, 64GB internal storage, and a wide adjustable stand for tabletop mode.",
        "price": 349.99,
        "stock": 22,
    },
    {
        "name": "Kindle Paperwhite",
        "description": "Amazon's best e-reader with a 6.8-inch glare-free display, adjustable warm light, waterproof design (IPX8), and weeks of battery life. 16GB storage.",
        "price": 149.99,
        "stock": 35,
    },
    {
        "name": "Google Pixel 9 Pro",
        "description": "Google's AI-first smartphone with Tensor G4 chip, 50MP main camera with Super Res Zoom, Gemini AI assistant, and 7 years of OS updates.",
        "price": 899.99,
        "stock": 16,
    },
    {
        "name": "Canon EOS R6 Mark II",
        "description": "Full-frame mirrorless camera with 24.2MP sensor, up to 40fps electronic shutter, 6K oversampled 4K video, and advanced Dual Pixel CMOS AF II.",
        "price": 2499.99,
        "stock": 5,
    },
]


def download_image(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    response = urllib.request.urlopen(req, timeout=timeout)
    return response.read()


class Command(BaseCommand):
    help = "Seed the database with real products and images"

    def handle(self, *args, **options):
        self.stdout.write("Seeding products...")

        media_dir = os.path.join(settings.MEDIA_ROOT, "products")
        os.makedirs(media_dir, exist_ok=True)

        Product.objects.all().delete()
        self.stdout.write("  Cleared existing products")

        created = 0

        for idx, prod_data in enumerate(PRODUCTS):
            name = prod_data["name"]
            self.stdout.write(f"  [{idx+1}/{len(PRODUCTS)}] {name}...", ending=" ")

            img_data = None
            unsplash_id = UNSPLASH_IDS[idx]
            if unsplash_id:
                try:
                    url = f"https://images.unsplash.com/photo-{unsplash_id}?w=800&q=80"
                    img_data = download_image(url)
                except Exception:
                    img_data = None

            if img_data is None:
                bg, fg = PLACEHOLD_COLORS[idx]
                url = f"https://placehold.co/800x600/{bg}/{fg}?text={quote(name)}"
                img_data = download_image(url)

            product = Product(
                name=name,
                description=prod_data["description"],
                price=prod_data["price"],
                stock=prod_data["stock"],
            )
            product.image.save(f"product_{idx+1}.jpg", ContentFile(img_data), save=True)
            self.stdout.write(self.style.SUCCESS("OK"))
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f"\nDone! {created} products created.")
        )
