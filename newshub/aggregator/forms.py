from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import UserPreference, NotificationPreference

class PreferenceForm(forms.ModelForm):
    class Meta:
        model = UserPreference
        fields = ['email_frequency', 'preferred_hour']
        widgets = {
            'preferred_hour': forms.NumberInput(attrs={'min': 0, 'max': 23, 'class': 'form-control'}),
        }


class NotificationPreferenceForm(forms.ModelForm):
    """Form for notification preferences."""
    class Meta:
        model = NotificationPreference
        fields = [
            'email_notifications_enabled', 
            'push_notifications_enabled',
            'marketing_emails',
            'notification_preferences'
        ]
        widgets = {
            'email_notifications_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'push_notifications_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'marketing_emails': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        email_enabled = cleaned_data.get('email_notifications_enabled', False)
        push_enabled = cleaned_data.get('push_notifications_enabled', False)
        
        if not email_enabled and not push_enabled:
            # If both are disabled, keep the previous preferences but mark as disabled
            self.cleaned_data['notification_preferences'] = self.instance.notification_preferences
            
        return cleaned_data


class PushSubscriptionForm(forms.Form):
    """Form for push notification subscription."""
    endpoint = forms.URLField(required=True)
    keys = forms.JSONField(required=True)
    
    def clean_keys(self):
        keys = self.cleaned_data.get('keys', {})
        if not isinstance(keys, dict):
            raise ValidationError(_('Keys must be a JSON object'))
        
        required_keys = {'p256dh', 'auth'}
        if not required_keys.issubset(keys.keys()):
            raise ValidationError(
                _('Missing required keys: %(keys)s'),
                code='missing_keys',
                params={'keys': ', '.join(required_keys - keys.keys())}
            )
        return keys


class EmailUnsubscribeForm(forms.Form):
    """Form for unsubscribing from email notifications."""
    email = forms.EmailField(required=True)
    token = forms.CharField(required=True)
    
    def clean(self):
        cleaned_data = super().clean()
        # Token validation would be implemented here
        return cleaned_data


class NotificationFilterForm(forms.Form):
    """Form for filtering notifications."""
    NOTIFICATION_TYPES = [
        ('all', _('All Types')),
        ('keyword_alert', _('Keyword Alerts')),
        ('daily_digest', _('Daily Digest')),
        ('weekly_digest', _('Weekly Digest')),
        ('system', _('System Notifications')),
    ]
    
    READ_STATUS = [
        ('all', _('All')),
        ('read', _('Read')),
        ('unread', _('Unread')),
    ]
    
    notification_type = forms.ChoiceField(
        choices=NOTIFICATION_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    read_status = forms.ChoiceField(
        choices=READ_STATUS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def filter_queryset(self, queryset):
        """Apply filters to the notification queryset."""
        if not self.is_valid():
            return queryset
            
        data = self.cleaned_data
        
        # Filter by notification type
        notification_type = data.get('notification_type')
        if notification_type and notification_type != 'all':
            queryset = queryset.filter(notification_type=notification_type)
        
        # Filter by read status
        read_status = data.get('read_status')
        if read_status == 'read':
            queryset = queryset.filter(read=True)
        elif read_status == 'unread':
            queryset = queryset.filter(read=False)
            
        return queryset
