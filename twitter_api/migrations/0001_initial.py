# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import m2m_history.fields
import annoying.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.BigIntegerField(serialize=False, primary_key=True)),
                ('created_at', models.DateTimeField()),
                ('lang', models.CharField(max_length=10)),
                ('entities', annoying.fields.JSONField()),
                ('fetched', models.DateTimeField(null=True, verbose_name='Fetched', blank=True)),
                ('text', models.TextField()),
                ('favorited', models.BooleanField(default=False)),
                ('retweeted', models.BooleanField(default=False)),
                ('truncated', models.BooleanField(default=False)),
                ('source', models.CharField(max_length=100)),
                ('source_url', models.URLField(null=True)),
                ('favorites_count', models.PositiveIntegerField()),
                ('retweets_count', models.PositiveIntegerField()),
                ('replies_count', models.PositiveIntegerField(null=True)),
                ('place', annoying.fields.JSONField(null=True)),
                ('contributors', annoying.fields.JSONField(null=True)),
                ('coordinates', annoying.fields.JSONField(null=True)),
                ('geo', annoying.fields.JSONField(null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigIntegerField(serialize=False, primary_key=True)),
                ('created_at', models.DateTimeField()),
                ('lang', models.CharField(max_length=10)),
                ('entities', annoying.fields.JSONField()),
                ('fetched', models.DateTimeField(null=True, verbose_name='Fetched', blank=True)),
                ('screen_name', models.CharField(unique=True, max_length=50, verbose_name='Screen name')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('description', models.TextField(verbose_name='Description')),
                ('location', models.CharField(max_length=100, verbose_name='Location')),
                ('time_zone', models.CharField(max_length=100, null=True, verbose_name='Time zone')),
                ('contributors_enabled', models.BooleanField(default=False, verbose_name='Contributors enabled')),
                ('default_profile', models.BooleanField(default=False, verbose_name='Default profile')),
                ('default_profile_image', models.BooleanField(default=False, verbose_name='Default profile image')),
                ('follow_request_sent', models.BooleanField(default=False, verbose_name='Follow request sent')),
                ('following', models.BooleanField(default=False, verbose_name='Following')),
                ('geo_enabled', models.BooleanField(default=False, verbose_name='Geo enabled')),
                ('is_translator', models.BooleanField(default=False, verbose_name='Is translator')),
                ('notifications', models.BooleanField(default=False, verbose_name='Notifications')),
                ('profile_use_background_image', models.BooleanField(default=False, verbose_name='Profile use background image')),
                ('protected', models.BooleanField(default=False, verbose_name='Protected')),
                ('verified', models.BooleanField(default=False, verbose_name='Verified')),
                ('profile_background_image_url', models.URLField(max_length=300, null=True)),
                ('profile_background_image_url_https', models.URLField(max_length=300, null=True)),
                ('profile_background_tile', models.BooleanField(default=False)),
                ('profile_background_color', models.CharField(max_length=6)),
                ('profile_banner_url', models.URLField(max_length=300, null=True)),
                ('profile_image_url', models.URLField(max_length=300, null=True)),
                ('profile_image_url_https', models.URLField(max_length=300)),
                ('url', models.URLField(max_length=300, null=True)),
                ('profile_link_color', models.CharField(max_length=6)),
                ('profile_sidebar_border_color', models.CharField(max_length=6)),
                ('profile_sidebar_fill_color', models.CharField(max_length=6)),
                ('profile_text_color', models.CharField(max_length=6)),
                ('favorites_count', models.PositiveIntegerField()),
                ('followers_count', models.PositiveIntegerField()),
                ('friends_count', models.PositiveIntegerField()),
                ('listed_count', models.PositiveIntegerField()),
                ('statuses_count', models.PositiveIntegerField()),
                ('utc_offset', models.IntegerField(null=True)),
                ('followers', m2m_history.fields.ManyToManyHistoryField(to='twitter_api.User')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='status',
            name='author',
            field=models.ForeignKey(related_name='statuses', to='twitter_api.User'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='status',
            name='favorites_users',
            field=m2m_history.fields.ManyToManyHistoryField(related_name='favorites', to='twitter_api.User'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='status',
            name='in_reply_to_status',
            field=models.ForeignKey(related_name='replies', to='twitter_api.Status', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='status',
            name='in_reply_to_user',
            field=models.ForeignKey(related_name='replies', to='twitter_api.User', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='status',
            name='retweeted_status',
            field=models.ForeignKey(related_name='retweets', to='twitter_api.Status', null=True),
            preserve_default=True,
        ),
    ]
