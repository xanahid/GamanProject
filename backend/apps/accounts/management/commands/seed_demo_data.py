from datetime import time

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import ClientProfile
from apps.content.models import Article, HomepageSection, TherapyMethod
from apps.scheduling.models import WeeklyAvailability
from apps.therapists.models import Department, Specialty, TherapistProfile

User = __import__("django.contrib.auth", fromlist=["get_user_model"]).get_user_model()


class Command(BaseCommand):
    help = "Seeds the database with demo data: Dr. Akbarzadeh, therapists, clients, availability, articles."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding Gaman demo data...")

        # --- Departments & Specialties ---------------------------------
        dept_couples, _ = Department.objects.get_or_create(slug="couples-family", defaults={"name": "زوج و خانواده", "order": 1})
        dept_teens, _ = Department.objects.get_or_create(slug="teens", defaults={"name": "نوجوانان", "order": 2})

        spec_schema, _ = Specialty.objects.get_or_create(slug="schema-therapy", defaults={"name": "اسکیما تراپی", "order": 1})
        spec_cbt, _ = Specialty.objects.get_or_create(slug="cbt", defaults={"name": "CBT", "order": 2})

        # --- Dr. Akbarzadeh (head of institute) -------------------------
        head_user, created = User.objects.get_or_create(
            username="sarah.akbarzadeh",
            defaults=dict(
                email="sarah@gaman.example", first_name="سارا", last_name="اکبرزاده",
                role=User.Role.THERAPIST, is_staff=True,
            ),
        )
        if created:
            head_user.set_password("ChangeMe123!")
            head_user.save()

        head_profile, _ = TherapistProfile.objects.get_or_create(
            user=head_user,
            defaults=dict(
                short_bio="روانپزشک متخصص با بیش از ۱۵ سال تجربه — مدیر مرکز گمان.",
                full_bio="دکتر اکبرزاده با بیش از ۱۵ سال تجربه بالینی، مدیریت مرکز روان‌درمانی گمان را بر عهده دارند.",
                age=42, years_active=15, is_head_of_institute=True, monthly_base_salary=600_000_000,
            ),
        )
        head_profile.departments.add(dept_couples)
        head_profile.specialties.add(spec_cbt)

        # Dr. Akbarzadeh available every day, 9-17, for intake sessions
        for weekday in range(6):
            WeeklyAvailability.objects.get_or_create(
                therapist=head_profile, weekday=weekday, start_time=time(9, 0), end_time=time(17, 0),
            )

        # --- Regular therapists ------------------------------------------
        therapist_defs = [
            dict(username="ali.mohammadi", first="علی", last="محمدی", bio_short="متخصص اسکیما تراپی.",
                 bio_full="دکتر محمدی متخصص اسکیما تراپی با آموزش مستقیم از موسسه یانگ در آمستردام است.",
                 age=38, years=10, specialties=[spec_schema], departments=[]),
            dict(username="mina.rezaei", first="مینا", last="رضایی", bio_short="CBT و زوج‌درمانی.",
                 bio_full="خانم رضایی روانشناس بالینی با تخصص در درمان شناختی-رفتاری و مشاوره زوج‌هاست.",
                 age=35, years=8, specialties=[spec_cbt], departments=[dept_couples]),
            dict(username="reza.karimi", first="رضا", last="کریمی", bio_short="روانشناسی نوجوان.",
                 bio_full="آقای کریمی متخصص روانشناسی نوجوانان با تمرکز بر اضطراب تحصیلی است.",
                 age=32, years=6, specialties=[], departments=[dept_teens]),
        ]

        created_therapists = []
        for t in therapist_defs:
            user, created = User.objects.get_or_create(
                username=t["username"],
                defaults=dict(
                    email=f"{t['username']}@gaman.example", first_name=t["first"], last_name=t["last"],
                    role=User.Role.THERAPIST,
                ),
            )
            if created:
                user.set_password("ChangeMe123!")
                user.save()

            profile, _ = TherapistProfile.objects.get_or_create(
                user=user,
                defaults=dict(
                    short_bio=t["bio_short"], full_bio=t["bio_full"], age=t["age"],
                    years_active=t["years"], monthly_base_salary=350_000_000,
                ),
            )
            profile.specialties.set(t["specialties"])
            profile.departments.set(t["departments"])

            for weekday in [0, 2, 4]:  # Sat, Mon, Wed
                WeeklyAvailability.objects.get_or_create(
                    therapist=profile, weekday=weekday, start_time=time(10, 0), end_time=time(16, 0),
                )
            created_therapists.append(profile)

        # --- Demo client ---------------------------------------------------
        client_user, created = User.objects.get_or_create(
            username="client.demo",
            defaults=dict(
                email="client@example.com", first_name="نوید", last_name="رستمی",
                role=User.Role.CLIENT, phone_number="+989120000000",
            ),
        )
        if created:
            client_user.set_password("ChangeMe123!")
            client_user.save()
        ClientProfile.objects.get_or_create(user=client_user, defaults=dict(age=29, occupation="طراح گرافیک"))

        # --- Therapy methods -------------------------------------------
        TherapyMethod.objects.get_or_create(
            slug="schema-therapy",
            defaults=dict(
                name="اسکیما تراپی", icon_emoji="🧠",
                teaser="اسکیما تراپی یک رویکرد درمانی یکپارچه است که توسط جفری یانگ توسعه یافته است...",
                full_description="توضیح کامل اسکیما تراپی...", order=1,
            ),
        )
        TherapyMethod.objects.get_or_create(
            slug="cbt",
            defaults=dict(
                name="درمان شناختی-رفتاری (CBT)", icon_emoji="💭",
                teaser="CBT یکی از اثربخش‌ترین روش‌های روان‌درمانی است که بر ارتباط افکار و رفتار تمرکز دارد...",
                full_description="توضیح کامل CBT...", order=2,
            ),
        )
        TherapyMethod.objects.get_or_create(
            slug="couples-therapy",
            defaults=dict(
                name="زوج‌درمانی", icon_emoji="👫",
                teaser="زوج‌درمانی فضایی امن برای بررسی چالش‌های رابطه و تقویت پیوند عاطفی است...",
                full_description="توضیح کامل زوج‌درمانی...", order=3,
            ),
        )

        # --- Articles ------------------------------------------------------
        Article.objects.get_or_create(
            slug="chronic-anxiety",
            defaults=dict(
                title="آیا اضطراب مزمن قابل درمان است؟",
                excerpt="اضطراب مزمن یکی از شایع‌ترین اختلالات روانی است. با رویکرد CBT آشنا شوید.",
                body="متن کامل مقاله درباره اضطراب مزمن...", author=head_user,
            ),
        )
        Article.objects.get_or_create(
            slug="schema-therapy-patterns",
            defaults=dict(
                title="اسکیما تراپی چگونه الگوهای قدیمی را تغییر می‌دهد؟",
                excerpt="اسکیماهای ناسازگار اولیه ریشه در دوران کودکی دارند. این الگوها قابل تغییرند.",
                body="متن کامل مقاله درباره اسکیما تراپی...", author=head_user,
            ),
        )

        # --- Example admin-configurable homepage section -----------------
        HomepageSection.objects.get_or_create(
            heading="چرا گمان؟",
            defaults=dict(
                body="تیمی متخصص، محیطی امن، و رویکردی مبتنی بر شواهد علمی.",
                background_color="#F5EDD5", text_color="#085041", order=10,
            ),
        )

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created head therapist + {len(created_therapists)} therapists + 1 demo client.\n"
            f"Login (any of them): password is 'ChangeMe123!'\n"
            f"  Head of institute: sarah.akbarzadeh\n"
            f"  Therapists: ali.mohammadi, mina.rezaei, reza.karimi\n"
            f"  Client: client.demo"
        ))
