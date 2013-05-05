# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'User.profile_image_url_https'
        db.alter_column('twitter_api_user', 'profile_image_url_https', self.gf('django.db.models.fields.URLField')(max_length=300))

        # Changing field 'User.profile_image_url'
        db.alter_column('twitter_api_user', 'profile_image_url', self.gf('django.db.models.fields.URLField')(max_length=300))

        # Changing field 'User.profile_background_image_url_https'
        db.alter_column('twitter_api_user', 'profile_background_image_url_https', self.gf('django.db.models.fields.URLField')(max_length=300))

        # Changing field 'User.profile_banner_url'
        db.alter_column('twitter_api_user', 'profile_banner_url', self.gf('django.db.models.fields.URLField')(max_length=300))

        # Changing field 'User.profile_background_image_url'
        db.alter_column('twitter_api_user', 'profile_background_image_url', self.gf('django.db.models.fields.URLField')(max_length=300))

        # Changing field 'User.url'
        db.alter_column('twitter_api_user', 'url', self.gf('django.db.models.fields.URLField')(max_length=300, null=True))
    def backwards(self, orm):

        # Changing field 'User.profile_image_url_https'
        db.alter_column('twitter_api_user', 'profile_image_url_https', self.gf('django.db.models.fields.URLField')(max_length=200))

        # Changing field 'User.profile_image_url'
        db.alter_column('twitter_api_user', 'profile_image_url', self.gf('django.db.models.fields.URLField')(max_length=200))

        # Changing field 'User.profile_background_image_url_https'
        db.alter_column('twitter_api_user', 'profile_background_image_url_https', self.gf('django.db.models.fields.URLField')(max_length=200))

        # Changing field 'User.profile_banner_url'
        db.alter_column('twitter_api_user', 'profile_banner_url', self.gf('django.db.models.fields.URLField')(max_length=200))

        # Changing field 'User.profile_background_image_url'
        db.alter_column('twitter_api_user', 'profile_background_image_url', self.gf('django.db.models.fields.URLField')(max_length=200))

        # Changing field 'User.url'
        db.alter_column('twitter_api_user', 'url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True))
    models = {
        'twitter_api.status': {
            'Meta': {'object_name': 'Status'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'statuses'", 'to': "orm['twitter_api.User']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {}),
            'entities': ('annoying.fields.JSONField', [], {}),
            'favorited': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'favorites_count': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'fetched': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'in_reply_to_status': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'replies'", 'null': 'True', 'to': "orm['twitter_api.Status']"}),
            'in_reply_to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'replies'", 'null': 'True', 'to': "orm['twitter_api.User']"}),
            'lang': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'retweeted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'retweets_count': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'source_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'truncated': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'twitter_api.user': {
            'Meta': {'object_name': 'User'},
            'contributors_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {}),
            'default_profile': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'default_profile_image': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'entities': ('annoying.fields.JSONField', [], {}),
            'favorites_count': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'fetched': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'follow_request_sent': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'followers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'followings'", 'symmetrical': 'False', 'to': "orm['twitter_api.User']"}),
            'followers_count': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'following': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'friends_count': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'geo_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'is_translator': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'lang': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'listed_count': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'notifications': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'profile_background_color': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'profile_background_image_url': ('django.db.models.fields.URLField', [], {'max_length': '300'}),
            'profile_background_image_url_https': ('django.db.models.fields.URLField', [], {'max_length': '300'}),
            'profile_background_tile': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'profile_banner_url': ('django.db.models.fields.URLField', [], {'max_length': '300'}),
            'profile_image_url': ('django.db.models.fields.URLField', [], {'max_length': '300'}),
            'profile_image_url_https': ('django.db.models.fields.URLField', [], {'max_length': '300'}),
            'profile_link_color': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'profile_sidebar_border_color': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'profile_sidebar_fill_color': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'profile_text_color': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'profile_use_background_image': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'protected': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'screen_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'statuses_count': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'time_zone': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '300', 'null': 'True'}),
            'utc_offset': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['twitter_api']