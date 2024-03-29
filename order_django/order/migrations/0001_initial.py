# Generated by Django 4.0.6 on 2022-07-20 05:20

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(blank=True, max_length=32)),
                ('seller_id', models.UUIDField(null=True)),
                ('buyer_id', models.UUIDField()),
                ('product_id', models.PositiveIntegerField()),
                ('total_incl_tax', models.DecimalField(decimal_places=2, max_digits=12, null=True)),
                ('date_shipped', models.DateTimeField(db_index=True, null=True)),
            ],
            options={
                'ordering': ['-created_at', '-updated_at'],
                'abstract': False,
            },
        ),
    ]
