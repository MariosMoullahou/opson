# Reels — Πώς δουλεύουν στα μεγάλα apps & πώς θα τα φτιάξουμε στο Opson

## Πώς δουλεύουν στο Instagram / TikTok

### 1. Data model
Κάθε Reel ανήκει σε **έναν χρήστη/account** και έχει:
- `owner` (FK σε User)
- `video_file` (URL σε CDN)
- `thumbnail` (auto-generated από το πρώτο frame)
- `caption`, `hashtags`, `mentions`
- `audio_track` (FK σε Sound — επαναχρησιμοποιήσιμο, π.χ. trending ήχοι)
- `duration`, `width`, `height`
- `created_at`
- counters: `views`, `likes`, `comments`, `shares`, `saves`

### 2. Storage / delivery
Δεν τα σερβίρει η Django/web app. Τα videos:
- Ανεβαίνουν σε **object storage** (S3, GCS).
- Περνάνε από **transcoding pipeline** → πολλά resolutions
  (240p / 480p / 720p / 1080p) + HLS/DASH manifests.
- Σερβίρονται από **CDN** (Cloudflare, Akamai) με **adaptive bitrate**
  ανάλογα με τη σύνδεση του χρήστη.
- Δεν στέλνεται ποτέ το ολόκληρο αρχείο — το player ζητάει chunks.

### 3. Feed / ranking
Το «Reels feed» **δεν** είναι reverse-chronological. Είναι ranked queue που
γεμίζει με βάση:
- Engagement στον χρήστη (likes / follows / saves σε παρόμοιο content).
- Πόσο watch time παίρνει το video συνολικά.
- Recency boost για νέα videos.
- Diversity (να μη βλέπεις 5 reels ίδιου creator).

Τρέχει σε **recommendation pipeline** (offline candidate generation + online
ranking με ML). Επιστρέφει top-N IDs, η app τα φορτώνει.

### 4. Επιπλέον features
- **Sounds:** ένα audio track ζει σαν δικό του entity. Το «Use this sound»
  κρατάει FK ώστε να βρίσκεις όλα τα videos με τον ίδιο ήχο.
- **Stitching / Duets / Remix:** ένα reel μπορεί να δείχνει σε `parent_reel`.
- **Insights:** counters ενημερώνονται async με queues (Kafka / Redis
  Streams), όχι σε κάθε view (αλλιώς πέφτει η DB).

### 5. UX
- Κάθετο swipe feed που **prefetch-άρει** το επόμενο video.
- Auto-pause όταν βγαίνει από το viewport.
- Tap to mute, double-tap to like.

---

## Πώς θα γίνει «mini-Instagram» στο Opson (ρεαλιστικό, χωρίς Kafka)

### Ελάχιστο model

```python
# producers/models.py
class Reel(models.Model):
    producer = models.ForeignKey(
        Producer, on_delete=models.CASCADE, related_name="reels"
    )
    title = models.CharField(max_length=140)
    video = models.FileField(upload_to="reels/")          # ή video_url για external
    thumbnail = models.ImageField(upload_to="reels/thumbs/", blank=True)
    caption = models.TextField(blank=True)
    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Τι μπαίνει στον MVP
- Producer ανεβάζει video από το dashboard (`FileField`, max ~30s).
- Στο home: τα τελευταία 6
  `Reel.objects.select_related("producer").order_by("-created_at")[:6]`.
- Click στο reel → το υπάρχον modal με auto-play.
- Like / View counters με POST σε ένα μικρό endpoint.

### Τι **δεν** μπαίνει στον MVP
- Recommendation engine — απλή ταξινόμηση by views / recency.
- Transcoding — απλά serve το `.mp4` που ανέβηκε.
- Audio tracks / stitching / duets.
- CDN — Django `MEDIA_URL` φτάνει για demo.

### Status σήμερα
- `catalog/views.py:9-22` έχει `REELS = [...]` (στατική Python λίστα).
- Καμία σχέση με `Producer` ή `User` — μόνο string match στα ονόματα.
- Videos από `assets.mixkit.co` (γενικό stock).

### Επόμενα βήματα όταν αποφασίσουμε να το χτίσουμε
1. Δημιουργία `Reel` model + migration.
2. Producer dashboard form για upload.
3. Αντικατάσταση της `REELS` λίστας στο `catalog/views.py` με queryset.
4. (Προαιρετικό) Endpoint `POST /reels/{id}/like` για counter.
