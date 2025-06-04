# Bog'cha Oshxonasi Boshqaruv Tizimi

## Loyiha Haqida Umumiy Ma'lumot

Bog'cha oshxonasi boshqaruv tizimi bolalar bog'chalarining oshxona faoliyatini samarali boshqarish uchun ishlab chiqilgan zamonaviy dasturiy yechimdir. Tizim oshxona xodimlariga mahsulotlarni hisobga olish, ovqatlar tarkibini boshqarish va batafsil hisobotlarni ko'rish imkoniyatini taqdim etadi. Dastur real hayotdagi ehtiyojlarni hisobga olgan holda yaratilgan bo'lib, bog'cha oshxonalarining kundalik faoliyatini optimallashtirish va nazorat qilishga qaratilgan.

## Texnologik Arxitektura

### Backend Texnologiyalari
Tizimning server qismi FastAPI framework asosida qurilgan bo'lib, yuqori unumdorlik va zamonaviy API standartlarini ta'minlaydi. Ma'lumotlar bazasi sifatida PostgreSQL ishlatilgan, bu esa murakkab so'rovlar va katta hajmdagi ma'lumotlarni samarali boshqarish imkonini beradi. Rivojlantirish jarayonida soddalik uchun SQLite ham qo'llab-quvvatlanadi.

### Frontend Yechimi
Foydalanuvchi interfeysi HTML5, CSS3 va JavaScript texnologiyalari asosida yaratilgan. Vizualizatsiya uchun Chart.js kutubxonasi ishlatilgan bo'lib, bu esa interaktiv grafiklar va hisobotlar yaratish imkonini beradi. Responsive dizayn tamami qurilmalar uchun moslashtirilgan.

### Real-vaqt Texnologiyalari
WebSocket protokoli orqali real-vaqt yangilanishlar ta'minlanadi, bu esa ombor holatini jonli kuzatish va ovqat berish jarayonida zudlik bilan ogohlantirish berish imkonini yaratadi.

### Asinxron Vazifalar Tizimi
Celery va Redis yordamida fon vazifalari amalga oshiriladi, jumladan oylik hisobotlarni avtomatik yaratish va porsiya taxminlarini qayta hisoblash.

## Asosiy Funksional Imkoniyatlar

### Mahsulotlar Boshqaruv Moduli
Tizim orqali barcha oshxona mahsulotlarini to'liq boshqarish mumkin. Har bir mahsulot uchun nom, grammdagi umumiy miqdor va yetkazilgan sana kiritiladi. Mahsulot ma'lumotlari istalgan vaqtda yangilanishi yoki o'chirilishi mumkin. Tizim mahsulotlar qoldiqlarini avtomatik kuzatib boradi va minimal chegaradan kamaygan hollarda ogohlantirish beradi.

### Ovqatlar va Retseptlar Boshqaruvi
Har bir ovqat uchun batafsil retsept yaratish imkoniyati mavjud. Retseptda ovqat nomi va har bir ingredient uchun kerakli miqdor aniq belgilanadi. Ovqatlar va ularning retseptlari ehtiyojga qarab yangilanishi yoki o'chirilishi mumkin. Tizim avtomatik ravishda har bir ovqatdan nechta porsiya tayyorlash mumkinligini hisoblaydi.

### Ovqat Berish va Monitoring Tizimi
Ovqat berish jarayoni avtomatlashtirilgan bo'lib, "Ovqat berildi" tugmasi bosilgan paytda zarur ingredientlar ombordan kerakli miqdorda avtomatik ayriladi. Agar biror ingredient yetarli bo'lmasa, tizim darhol xatolik xabarini ko'rsatadi va ovqat berish jarayonini to'xtatadi. Har bir ovqat berish holati sana, vaqt va mas'ul xodim ma'lumotlari bilan to'liq qayd qilinadi.

### Dinamik Porsiya Hisoblash Algoritmi
Tizim mavjud mahsulotlar asosida har bir ovqatdan nechta porsiya tayyorlash mumkinligini doimiy ravishda hisoblaydi. Bu hisob-kitoblar ingredientlar miqdori o'zgarishi bilan avtomatik yangilanadi va oshxona xodimlariga dolzarb ma'lumot taqdim etadi.

### Hisobotlar va Vizualizatsiya Tizimi
Keng qamrovli hisobot tizimi ingredientlar iste'moli, kelib tushgan sanalar va ovqat tayyorlash statistikasi bo'yicha batafsil grafiklar taqdim etadi. Oylik hisobotlarda tayyorlangan porsiyalar soni, tayyorlanishi mumkin bo'lgan porsiyalar soni va ularning orasidagi farq foizi ko'rsatiladi. Agar farq 10-15 foizdan oshsa, tizim ehtimoliy suiste'mol haqida signal beradi.

### Foydalanuvchilarni Kuzatish va Loglash
Tizim har bir ovqat berish holatini batafsil qayd qiladi, jumladan kim tomonidan qaysi ovqat berilgani, aniq sana va vaqt ma'lumotlari. Barcha ovqat berish holatlari maxsus jadvalda tartibli ko'rsatiladi va kerakli filtrlash imkoniyatlari mavjud.

## Xavfsizlik va Kirish Nazorati

### Rolga Asoslangan Kirish Tizimi
Tizim uch xil foydalanuvchi roli bilan ishlaydi. Administrator rolida foydalanuvchilar barcha funksiyalarga kirish huquqiga ega bo'lib, sozlamalar va to'liq hisobotlarni boshqarishi mumkin. Oshpaz rolida foydalanuvchilar faqat ovqat berish funksiyasidan foydalanish huquqiga ega. Menejer rolida foydalanuvchilar omborni yangilash va tahlillarni ko'rish imkoniyatiga ega.

### Ma'lumotlar Xavfsizligi
Barcha foydalanuvchi ma'lumotlari shifrlangan holda saqlanadi va tizim zamonaviy xavfsizlik standartlariga muvofiq ishlaydi. Kirish nazorati JWT tokenlar orqali amalga oshiriladi va har bir so'rov autentifikatsiya va avtorizatsiya jarayonlaridan o'tadi.

## Ogohlantirishlar va Monitoring

### Avtomatik Ogohlantirishlar
Tizim ingredient miqdori belgilangan minimumdan kamaygan hollarda avtomatik ogohlantirish beradi. Oylik hisobotlarda farq 15 foizdan oshgan hollarda maxsus ogohlantirish chiqariladi. Real-vaqt rejimida ombor holati kuzatiladi va kritik vaziyatlarda zudlik bilan xabar beriladi.

### Fon Vazifalari
Celery yordamida amalga oshiriladigan fon vazifalari oylik hisobotlarni avtomatik yaratish, porsiya taxminlarini muntazam qayta hisoblash va tizim ma'lumotlarini yangilashni o'z ichiga oladi.

## Tizim Talablari va O'rnatish

### Minimal Tizim Talablari
Tizimni ishga tushirish uchun Python 3.8 yoki undan yuqori versiya, PostgreSQL 12 yoki SQLite3, Redis server va kamida 1GB RAM talab qilinadi. Rivojlantirish muhiti uchun bu talablar kamroq bo'lishi mumkin.

### O'rnatish Jarayoni
Loyihani o'rnatish uchun avval virtual muhit yaratish va faollashtirilishi kerak. Keyin requirements.txt faylidagi barcha bog'liqliklarni o'rnatish zarur. Ma'lumotlar bazasi migratsiyalarini bajarish va superuser yaratish o'rnatish jarayonining muhim qismlaridir.

### Muhit Sozlamalari
Loyiha .env fayl orqali sozlanadi va unda ma'lumotlar bazasi ulanish ma'lumotlari, maxfiy kalitlar va debug rejimi kabi muhim parametrlar belgilanadi. Production muhiti uchun maxsus xavfsizlik sozlamalari qo'llanilishi kerak.

## Ishlab Chiqish va Sinov

### Kod Sifati va Testlar
Loyiha zamonaviy dasturlash amaliyotlariga amal qiladi va to'liq test qamrovi ta'minlanadi. Unit testlar, integratsiya testlari va API testlari mavjud. Kod sifati statik tahlil vositalari orqali nazorat qilinadi.

### Rivojlantirish Jarayoni
Loyiha Git versiya nazorati tizimi orqali boshqariladi va feature branch workflow metodologiyasi qo'llaniladi. Har bir yangi funksiya alohida branch da ishlab chiqiladi va to'liq testdan o'tgandan so'ng asosiy kodga qo'shiladi.

## Deployment va Production

### Production Sozlamalari
Production muhitida tizim Gunicorn WSGI server bilan ishga tushiriladi va Nginx reverse proxy orqali xizmat ko'rsatiladi. Ma'lumotlar bazasi uchun PostgreSQL ishlatiladi va Redis Celery vazifalar navbati uchun konfiguratsiya qilinadi.

### Monitoring va Logging
Production muhitida to'liq logging tizimi faol bo'lib, barcha muhim hodisalar va xatolar qayd qilinadi. Tizim unumdorligi va resurs iste'moli doimiy monitoring qilinadi.

## Texnik Qo'llab-quvvatlash

### Hujjatlar
Barcha API endpointlari uchun batafsil hujjatlar Swagger/OpenAPI format da taqdim etiladi. Foydalanuvchi qo'llanmalari va texnik hujjatlar alohida taqdim qilinadi.

### Yordam va Qo'llab-quvvatlash
Texnik yordam uchun maxsus kanallar tashkil etilgan va muntazam yangilanishlar va yaxshilanishlar rejalashtirililgan. Bug reportlar va feature requestlar GitHub Issues orqali boshqariladi.

## Kelajak Rivojlanish Rejalari

Tizimning kelajakdagi versiyalarida mobil ilova qo'llab-quvvatlash, kengaytirilgan analitika, AI asosidagi bashoratli tahlil va boshqa bog'chalar bilan integratsiya imkoniyatlari rejalashtirilgan. Foydalanuvchilardan kelgan fikr-mulohazalar asosida yangi funksiyalar qo'shilishi davom ettiriladi.

### Run with docker
docker compose exec web python manage.py migrate
docker compose exec web python manage.py create_default_roles
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py collectstatic --noinput


sudo lsof -i :6379
sudo systemctl stop redis-server
sudo systemctl disable redis-server


docker compose down --volumes # Oldingi konteynerlarni o'chiradi
docker system prune -a --volumes # Barcha keraksiz docker resurslarini tozalaydi


docker compose build
docker compose up -d
