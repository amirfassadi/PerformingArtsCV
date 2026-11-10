from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('portfolio', '0005_alter_payment_status')]

    operations = [
        migrations.CreateModel(
            name='RequestThrottle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=180, unique=True)),
                ('window_started', models.DateTimeField()),
                ('attempts', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='SupportRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('support', 'پشتیبانی'), ('content', 'گزارش محتوا'), ('account', 'درخواست حذف حساب')], max_length=20)),
                ('subject', models.CharField(max_length=160)),
                ('message', models.TextField(max_length=5000)),
                ('status', models.CharField(choices=[('open', 'باز'), ('reviewing', 'در حال بررسی'), ('closed', 'بسته')], default='open', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='support_requests', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
