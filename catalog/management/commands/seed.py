from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from catalog.models import Category, Product
from producers.models import Producer

User = get_user_model()


CATEGORIES = [
    ("Όλα",        "ola",            "🌿", 1),
    ("Λαχανικά",   "laxanika",       "🥬", 10),
    ("Φρούτα",     "frouta",         "🍎", 20),
    ("Ελαιόλαδο",  "elaiolado",      "🫒", 30),
    ("Μέλι",       "meli",           "🍯", 40),
    ("Γαλακτοκομικά","galaktokomika","🧀", 50),
    ("Δημητριακά", "dimitriaka",     "🌾", 60),
    ("Κρασί",      "krasi",          "🍷", 70),
    ("Βότανα",     "votana",         "🌺", 80),
    ("Αυγά",       "avga",           "🥚", 90),
    ("Κονσέρβες",  "konserves",      "🫙", 100),
    ("Ξηροί Καρποί","ksiroi-karpoi", "🌰", 110),
]


PRODUCERS = [
    {
        "username": "barbayiannis",
        "farm_name": "Μπαρμπαγιάννης Κτήμα",
        "village": "Καλαμάτα",
        "region": "Μεσσηνία",
        "badge": "bio",
        "rating": "4.9",
        "rating_count": 128,
        "bio": "Παραδοσιακή ελαιοκαλλιέργεια 3ης γενιάς στους πρόποδες του Ταϋγέτου. Τα ελαιόδεντρά μας είναι πάνω από 200 χρονών. Χρησιμοποιούμε αποκλειστικά βιολογικές μεθόδους από το 1995.",
        "cover_url": "https://loremflickr.com/600/400/olive,grove?lock=101",
        "products": [
            ("Ελαιόλαδο", "Ελαιόλαδο Εξαιρετικό Παρθένο", "liter", "750ml", "12.50", 30, "🫒",
             "Ψυχρή έκθλιψη εντός 24 ωρών από τη συγκομιδή. Πικάντικο, χορτόσπερμο, χαμηλή οξύτητα.",
             "https://loremflickr.com/600/400/olive,oil?lock=1"),
            ("Ελαιόλαδο", "Ελιές Καλαμών", "kg", "500γρ", "5.90", 25, "🫒",
             "Ολόκληρες ελιές Καλαμών σε άρμη — εκλεκτή ποικιλία.",
             "https://loremflickr.com/600/400/olives?lock=2"),
            ("Ελαιόλαδο", "Πατέ Ελιάς", "jar", "200γρ", "4.20", 20, "🍶",
             "Παχύρρευστο πατέ από ώριμες ελιές με βότανα.",
             "https://loremflickr.com/600/400/tapenade,olive?lock=3"),
            ("Ελαιόλαδο", "Ελαιόλαδο Βιολογικό 5L", "liter", "5L", "48.00", 12, "🫒",
             "Συσκευασία 5 λίτρων, ιδανική για το σπίτι.",
             "https://loremflickr.com/600/400/olive,oil,tin?lock=4"),
        ],
    },
    {
        "username": "xalkias",
        "farm_name": "Μελισσοκομία Χαλκιά",
        "village": "Βανιτσά",
        "region": "Αιτωλοακαρνανία",
        "badge": "traditional",
        "rating": "4.8",
        "rating_count": 94,
        "bio": "Οικογενειακή μελισσοκομία από τη δεκαετία του '80 στα βουνά της Αιτωλοακαρνανίας. Τα μελίσσια μας κινούνται ελεύθερα σε αδιάβατα φυσικά τοπία χωρίς ρύπανση.",
        "cover_url": "https://loremflickr.com/600/400/beehive,beekeeper?lock=102",
        "products": [
            ("Μέλι", "Μέλι Ελάτης", "jar", "500γρ", "9.80", 40, "🍯",
             "Σκούρο, πυκνό μέλι από έλατα — αρωματικό και πλούσιο.",
             "/static/img/honey.jpg"),
            ("Μέλι", "Θυμαρίσιο Μέλι", "jar", "500γρ", "8.50", 35, "🍯",
             "Κλασσικό θυμαρίσιο, χρυσαφί χρώμα, έντονο άρωμα θυμαριού.",
             "/static/img/THIMARI.jpg"),
            ("Μέλι", "Ανθόμελο", "jar", "1kg", "15.00", 18, "🍯",
             "Μείγμα από νεκταρόμελα διαφόρων αγριολούλουδων.",
             "https://loremflickr.com/600/400/honey,flower?lock=7"),
            ("Μέλι", "Κηρήθρα", "piece", "200γρ", "11.00", 15, "🍯",
             "Ολόκληρο κομμάτι κηρήθρας με μέλι μέσα της.",
             "/static/img/kipseli.jpg"),
        ],
    },
    {
        "username": "sfakianakis",
        "farm_name": "Κτηνοτροφία Σφακιανάκη",
        "village": "Ανώγεια",
        "region": "Κρήτη",
        "badge": "bio",
        "rating": "4.7",
        "rating_count": 76,
        "bio": "Κρητική κτηνοτροφία με πρόβατα και κατσίκες σε ελεύθερη βόσκηση στα Ψηλορείτη. Παραδοσιακές κρητικές συνταγές τυριού που περνούν από γενιά σε γενιά.",
        "cover_url": "https://loremflickr.com/600/400/sheep,goat,farm?lock=103",
        "products": [
            ("Γαλακτοκομικά", "Γραβιέρα Κρήτης ΠΟΠ", "kg", "500γρ", "13.00", 22, "🧀",
             "Σκληρό κρητικό τυρί ΠΟΠ, παλαιωμένο 6 μήνες.",
             "https://loremflickr.com/600/400/cheese,aged?lock=9"),
            ("Γαλακτοκομικά", "Ανθότυρος Φρέσκος", "kg", "400γρ", "6.50", 28, "🧀",
             "Φρέσκο, απαλό κρητικό τυρί από κατσίκι και πρόβατο.",
             "https://loremflickr.com/600/400/white,cheese?lock=10"),
            ("Γαλακτοκομικά", "Μυζήθρα", "kg", "500γρ", "7.20", 24, "🧀",
             "Φρέσκο τυρί, ιδανικό για γλυκά και αλμυρά πιάτα.",
             "https://loremflickr.com/600/400/ricotta,cheese?lock=11"),
            ("Γαλακτοκομικά", "Ξινομυζήθρα", "kg", "300γρ", "5.80", 20, "🧀",
             "Ώριμη μυζήθρα με ξινή γεύση, τοπική σπεσιαλιτέ.",
             "https://loremflickr.com/600/400/feta,cheese?lock=12"),
        ],
    },
    {
        "username": "papadopoulos",
        "farm_name": "Αμπελώνας Παπαδόπουλου",
        "village": "Νεμέα",
        "region": "Κορινθία",
        "badge": "pdo",
        "rating": "5.0",
        "rating_count": 211,
        "bio": "Βιολογικός αμπελώνας 45 στρεμμάτων στη Νεμέα από το 1978. Εξειδίκευση στο Αγιωργίτικο ΠΟΠ Νεμέα. Τα κρασιά μας έχουν βραβευτεί σε διεθνείς διαγωνισμούς.",
        "cover_url": "https://loremflickr.com/600/400/vineyard,grapes?lock=104",
        "products": [
            ("Κρασί", "Αγιωργίτικο ΠΟΠ Ερυθρός", "liter", "750ml", "16.00", 50, "🍷",
             "Πλούσιο, βελούδινο ερυθρό κρασί από Αγιωργίτικο.",
             "https://loremflickr.com/600/400/red,wine?lock=13"),
            ("Κρασί", "Ροζέ Νεμέα", "liter", "750ml", "13.50", 45, "🥂",
             "Φρέσκο ροζέ — ιδανικό για καλοκαιρινά γεύματα.",
             "https://loremflickr.com/600/400/rose,wine?lock=14"),
            ("Φρούτα", "Επιτραπέζιο Σταφύλι", "kg", "1kg", "4.80", 30, "🍇",
             "Φρέσκα σταφύλια από τον αμπελώνα.",
             "https://loremflickr.com/600/400/grapes,vineyard?lock=15"),
            ("Κρασί", "Κρασί Παλαιωμένο 2020", "liter", "750ml", "24.00", 18, "🍷",
             "Παλαιωμένο 4 έτη σε δρύινα βαρέλια.",
             "https://loremflickr.com/600/400/wine,bottle?lock=16"),
        ],
    },
    {
        "username": "nikolaou",
        "farm_name": "Αγρόκτημα Νικολάου",
        "village": "Τυρός",
        "region": "Αρκαδία",
        "badge": "bio",
        "rating": "4.6",
        "rating_count": 53,
        "bio": "Βιολογικός λαχανόκηπος σε ορεινή Αρκαδία. Εποχιακά λαχανικά χωρίς φυτοφάρμακα, συλλεγμένα κάθε πρωί. Παράδοση εντός 24ωρών.",
        "cover_url": "https://loremflickr.com/600/400/vegetable,garden?lock=105",
        "products": [
            ("Λαχανικά", "Ντομάτες Βιολογικές", "kg", "1kg", "3.20", 60, "🍅",
             "Φρέσκες, αρωματικές ντομάτες μαζεμένες κάθε πρωί.",
             "https://loremflickr.com/600/400/tomatoes?lock=17"),
            ("Λαχανικά", "Αγγούρια", "kg", "1kg", "2.50", 50, "🥒",
             "Τραγανά αγγούρια χωρίς κερί ούτε πλαστικό.",
             "https://loremflickr.com/600/400/cucumber?lock=18"),
            ("Λαχανικά", "Πιπεριές Φλωρίνης", "kg", "500γρ", "3.80", 35, "🫑",
             "Γλυκές κόκκινες πιπεριές Φλωρίνης.",
             "https://loremflickr.com/600/400/peppers,red?lock=19"),
            ("Λαχανικά", "Μαρούλια", "piece", "τμχ", "1.20", 40, "🥗",
             "Φρέσκα μαρούλια, παράδοση σε 24 ώρες.",
             "https://loremflickr.com/600/400/lettuce,salad?lock=20"),
        ],
    },
    {
        "username": "myloi",
        "farm_name": "Μύλοι Θεσσαλίας",
        "village": "Λάρισα",
        "region": "Θεσσαλία",
        "badge": "traditional",
        "rating": "4.5",
        "rating_count": 88,
        "bio": "Παραδοσιακός νερόμυλος που λειτουργεί από το 1920. Αλέθουμε ελληνικό σκληρό σιτάρι με παραδοσιακές πέτρες. Καμία χημική επεξεργασία, καμία προσθήκη.",
        "cover_url": "https://loremflickr.com/600/400/wheat,field,flour?lock=107",
        "products": [
            ("Δημητριακά", "Αλεύρι Ολικής Άλεσης", "kg", "1kg", "3.50", 40, "🌾",
             "Σκούρο αλεύρι με όλο τον φλοιό — υψηλής ποιότητας.",
             "https://loremflickr.com/600/400/flour,wheat?lock=21"),
            ("Δημητριακά", "Χυλοπίτες Χειροποίητες", "kg", "500γρ", "5.20", 28, "🍝",
             "Παραδοσιακές χειροποίητες χυλοπίτες.",
             "https://loremflickr.com/600/400/pasta,homemade?lock=22"),
            ("Δημητριακά", "Σιμιγδάλι Χονδρό", "kg", "1kg", "2.80", 35, "🌾",
             "Χονδρό σιμιγδάλι από σκληρό σιτάρι.",
             "https://loremflickr.com/600/400/grain,semolina?lock=23"),
            ("Δημητριακά", "Τραχανάς Ξινός", "kg", "500γρ", "4.90", 22, "🥖",
             "Παραδοσιακός χωριάτικος ξινός τραχανάς.",
             "https://loremflickr.com/600/400/dried,pasta?lock=24"),
        ],
    },
]


class Command(BaseCommand):
    help = "Seed the database with Opson demo data (Greek producers + products)."

    def handle(self, *args, **opts):
        # Wipe existing seedable data so re-seeding is idempotent
        Product.objects.all().delete()
        Producer.objects.all().delete()
        Category.objects.all().delete()
        # Producer-role users get cleared (admin/customer survive)
        User.objects.filter(role=User.Role.PRODUCER).delete()

        # Categories
        cat_by_name = {}
        for name, slug, emoji, sort_order in CATEGORIES:
            if slug == "ola":
                continue  # "Όλα" is a UI-only filter, no row needed
            cat = Category.objects.create(name=name, slug=slug, emoji=emoji, sort_order=sort_order)
            cat_by_name[name] = cat
        self.stdout.write(self.style.SUCCESS(f"Categories: {Category.objects.count()}"))

        # Producers + products
        for p in PRODUCERS:
            user = User.objects.create_user(
                username=p["username"],
                email=f"{p['username']}@gaiaroots.local",
                password="demo1234",
                role=User.Role.PRODUCER,
            )
            producer = Producer.objects.create(
                user=user,
                farm_name=p["farm_name"],
                village=p["village"],
                region=p["region"],
                badge=p["badge"],
                rating=Decimal(p["rating"]),
                rating_count=p["rating_count"],
                bio=p["bio"],
                cover_url=p["cover_url"],
            )
            for cat_name, name, unit, unit_label, price, stock, emoji, desc, image_url in p["products"]:
                Product.objects.create(
                    producer=producer,
                    category=cat_by_name.get(cat_name),
                    name=name,
                    unit=unit,
                    unit_label=unit_label,
                    price=Decimal(price),
                    stock=stock,
                    emoji=emoji,
                    description=desc,
                    image_url=image_url,
                )
        self.stdout.write(self.style.SUCCESS(f"Producers: {Producer.objects.count()} (password: demo1234)"))
        self.stdout.write(self.style.SUCCESS(f"Products: {Product.objects.count()}"))

        # Customer
        if not User.objects.filter(username="customer").exists():
            customer = User.objects.create_user(
                username="customer",
                email="customer@gaiaroots.local",
                password="demo1234",
                role=User.Role.CUSTOMER,
            )
            self.stdout.write(self.style.SUCCESS("Customer: customer / demo1234"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Producer logins (all demo1234):"))
        for p in PRODUCERS:
            try:
                self.stdout.write(f"  {p['username']:18} - {p['farm_name']}")
            except UnicodeEncodeError:
                self.stdout.write(f"  {p['username']}")
