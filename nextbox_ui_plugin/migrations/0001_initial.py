from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0010_update_jsonfield'),
    ]

    operations = [
        migrations.CreateModel(
            name='SavedTopology',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=100)),
                ('topology', models.JSONField()),
                ('layout_context', models.JSONField(blank=True, null=True)),
                ('timestamp', models.DateTimeField()),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.adminuser')),
            ],
        ),
    ]
