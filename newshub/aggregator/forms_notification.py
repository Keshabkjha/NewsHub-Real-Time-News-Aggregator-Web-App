from django import forms
from django.core.exceptions import ValidationError
from .models import NotificationPreference

class NotificationPreferenceForm(forms.ModelForm):
    """
    Form for managing notification preferences.
    """
    # Email Digest Frequency
    email_digest_frequency = forms.ChoiceField(
        label='Email Digest Frequency',
        choices=NotificationPreference.EMAIL_DIGEST_CHOICES,
        help_text='How often would you like to receive email digests?',
        widget=forms.Select(attrs={'class': 'mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md'}),
    )
    
    # Notification Channels
    keyword_alerts = forms.ChoiceField(
        label='Keyword Alerts',
        choices=NotificationPreference.NOTIFICATION_CHANNEL_CHOICES,
        help_text='How would you like to receive keyword alerts?',
        widget=forms.Select(attrs={'class': 'mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md'}),
    )
    
    recommended_articles = forms.ChoiceField(
        label='Recommended Articles',
        choices=NotificationPreference.NOTIFICATION_CHANNEL_CHOICES,
        help_text='How would you like to receive article recommendations?',
        widget=forms.Select(attrs={'class': 'mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md'}),
    )
    
    trending_articles = forms.ChoiceField(
        label='Trending Articles',
        choices=NotificationPreference.NOTIFICATION_CHANNEL_CHOICES,
        help_text='How would you like to be notified about trending articles?',
        widget=forms.Select(attrs={'class': 'mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md'}),
    )
    
    system_messages = forms.ChoiceField(
        label='System Messages',
        choices=NotificationPreference.NOTIFICATION_CHANNEL_CHOICES,
        help_text='How would you like to receive system messages?',
        widget=forms.Select(attrs={'class': 'mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md'}),
    )
    
    # Marketing preferences
    marketing_emails = forms.BooleanField(
        label='Marketing Emails',
        required=False,
        help_text='Receive marketing emails about new features and offers.',
        widget=forms.CheckboxInput(attrs={'class': 'focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded'}),
    )
    
    class Meta:
        model = NotificationPreference
        fields = [
            'email_digest_frequency',
            'keyword_alerts',
            'recommended_articles',
            'trending_articles',
            'system_messages',
            'marketing_emails',
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial values from the instance if it exists
        if self.instance and self.instance.pk:
            # Set initial values for notification channels
            for field in ['keyword_alerts', 'recommended_articles', 'trending_articles', 'system_messages']:
                self.fields[field].initial = self.instance.get_notification_channel(field)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Save notification channel preferences
        for field in ['keyword_alerts', 'recommended_articles', 'trending_articles', 'system_messages']:
            setattr(instance, f"{field}_channel", self.cleaned_data[field])
        
        if commit:
            instance.save()
        
        return instance


class PushNotificationForm(forms.Form):
    """
    Form for handling push notification subscriptions.
    """
    endpoint = forms.URLField()
    auth = forms.CharField()
    p256dh = forms.CharField()
    
    def clean(self):
        cleaned_data = super().clean()
        # Add any additional validation if needed
        return cleaned_data


class UnsubscribeForm(forms.Form):
    """
    Form for handling email unsubscription.
    """
    email = forms.EmailField()
    token = forms.CharField()
    
    def clean(self):
        cleaned_data = super().clean()
        # Add token validation logic here
        return cleaned_data
