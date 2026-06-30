from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render

from producers.models import Producer

from .models import Category, Product


REELS = [
    {"name": "Μπαρμπαγιάννης Κτήμα", "loc": "Καλαμάτα, Μεσσηνία", "views": "4.2χ",
     "url": "https://assets.mixkit.co/videos/22195/22195-720.mp4"},
    {"name": "Αμπελώνας Παπαδόπουλου", "loc": "Νεμέα, Κορινθία", "views": "7.8χ",
     "url": "https://assets.mixkit.co/videos/24745/24745-720.mp4"},
    {"name": "Μελισσοκομία Χαλκιά", "loc": "Βανιτσά, Αιτωλοακαρνανία", "views": "3.1χ",
     "url": "https://assets.mixkit.co/videos/46375/46375-720.mp4"},
    {"name": "Κτηνοτροφία Σφακιανάκη", "loc": "Ανώγεια, Κρήτη", "views": "5.6χ",
     "url": "https://assets.mixkit.co/videos/46563/46563-720.mp4"},
    {"name": "Αγρόκτημα Νικολάου", "loc": "Τυρός, Αρκαδία", "views": "2.9χ",
     "url": "https://assets.mixkit.co/videos/20560/20560-720.mp4"},
    {"name": "Μύλοι Θεσσαλίας", "loc": "Λάρισα, Θεσσαλία", "views": "8.1χ",
     "url": "https://assets.mixkit.co/videos/38410/38410-720.mp4"},
]


EVENTS = [
    {"day": "18", "month": "Οκτ", "type": "Συγκομιδή Ελιάς", "badge_class": "badge-green",
     "title": "Ελαιοσυλλογή στο Κτήμα Μπαρμπαγιάννη",
     "location": "Καλαμάτα, Μεσσηνία", "time": "08:00 – 16:00",
     "capacity": 30, "attending": 22,
     "desc": "Ζήσε την εμπειρία της παραδοσιακής ελαιοσυλλογής! Μάθε πώς μαζεύουμε τις ελιές, δες πώς γίνεται το λάδι και πάρε σπίτι 1 λίτρο εξτρά παρθένο.",
     "image": "https://loremflickr.com/800/500/olive,harvest?lock=201"},
    {"day": "05", "month": "Σεπ", "type": "Τρύγος", "badge_class": "badge-earth",
     "title": "Βιολογικός Τρύγος Αγιωργίτικου — Νεμέα",
     "location": "Νεμέα, Κορινθία", "time": "07:30 – 14:00",
     "capacity": 50, "attending": 38,
     "desc": "Εμπειρία τρύγου σε βιολογικό αμπελώνα. Δεκατιανό & μεσημεριανό με τοπικές λιχουδιές, γευσιγνωσία νέας σοδειάς και δώρο μπουκάλι κρασί.",
     "image": "https://loremflickr.com/800/500/grape,harvest,vineyard?lock=202"},
    {"day": "12", "month": "Αυγ", "type": "Μελισσοκομία", "badge_class": "badge-amber",
     "title": "Μάθε τα μυστικά της Μελισσοκομίας",
     "location": "Βανιτσά, Αιτ/νία", "time": "09:00 – 13:00",
     "capacity": 15, "attending": 10,
     "desc": "Γνώρισε τον κόσμο της μέλισσας. Δες πώς μαζεύουμε μέλι, μάθε για τη ζωή της κυψέλης και φύγε με 500γρ αφιλτράριστο θυμαρίσιο μέλι.",
     "image": "https://loremflickr.com/800/500/beekeeper,honeybee?lock=203"},
    {"day": "28", "month": "Ιουλ", "type": "Λαχανόκηπος", "badge_class": "badge-green",
     "title": "Καλοκαιρινή Συγκομιδή Λαχανικών",
     "location": "Τυρός, Αρκαδία", "time": "07:00 – 12:00",
     "capacity": 25, "attending": 14,
     "desc": "Πρωινή βόλτα στον βιολογικό λαχανόκηπο. Μαζεύουμε μαζί ντομάτες, αγγούρια & πιπεριές. Φεύγεις με καλάθι γεμάτο φρέσκα λαχανικά!",
     "image": "https://loremflickr.com/800/500/vegetable,garden,farm?lock=204"},
]


def home(request):
    category_slug = request.GET.get("category")
    query = request.GET.get("q", "").strip()

    producers = Producer.objects.annotate(product_count=Count("products")).prefetch_related("products")

    if category_slug:
        producers = producers.filter(products__category__slug=category_slug).distinct()
    if query:
        producers = producers.filter(
            Q(farm_name__icontains=query)
            | Q(village__icontains=query)
            | Q(region__icontains=query)
            | Q(products__name__icontains=query)
        ).distinct()

    context = {
        "producers": producers,
        "active_category": category_slug,
        "search_query": query,
        "stats": {
            "producers": Producer.objects.count(),
            "products": Product.objects.filter(is_active=True).count(),
            "regions": Producer.objects.values("region").exclude(region="").distinct().count(),
            "customers": "12k",
        },
        "reels": REELS,
        "events": EVENTS,
    }
    return render(request, "catalog/home.html", context)


def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related("producer", "category"), pk=pk, is_active=True)
    related = (
        Product.objects.filter(producer=product.producer, is_active=True)
        .exclude(pk=product.pk)[:4]
    )
    return render(request, "catalog/product_detail.html", {
        "product": product,
        "related": related,
    })


DEMO_REVIEWS = [
    {"name": "Μαρία Κ.", "initial": "Μ", "date": "Φεβ 2026", "stars": 5, "empty_stars": 0,
     "text": "Εξαιρετική ποιότητα! Η γεύση είναι αυθεντική και ξεχωρίζει από τα προϊόντα του σούπερ μάρκετ. Παραγγέλνω κάθε μήνα.",
     "verified": True},
    {"name": "Γιώργος Π.", "initial": "Γ", "date": "Ιαν 2026", "stars": 5, "empty_stars": 0,
     "text": "Ο παραγωγός είναι πάντα πρόθυμος και αξιόπιστος. Παράδοση γρήγορη, συσκευασία προσεγμένη. Σφαιρική εμπειρία αγοράς.",
     "verified": True},
    {"name": "Ελένη Σ.", "initial": "Ε", "date": "Δεκ 2025", "stars": 4, "empty_stars": 1,
     "text": "Πολύ καλή ποιότητα προϊόντων. Λίγο αργή η αποστολή αλλά αξίζει η αναμονή. Θα ξαναπαραγγείλω σίγουρα.",
     "verified": False},
]


def producer_detail(request, slug):
    producer = get_object_or_404(Producer, slug=slug)
    products = producer.products.filter(is_active=True).select_related("category")
    return render(request, "catalog/producer_detail.html", {
        "producer": producer,
        "products": products,
        "reviews": DEMO_REVIEWS,
    })
