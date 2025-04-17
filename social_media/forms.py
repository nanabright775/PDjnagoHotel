# forms.py

from django import forms
from .models import ChatBot

class ChatBotForm(forms.ModelForm):
    class Meta:
        model = ChatBot
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Type your message here...'}),
        }


from django import forms
from .models import SocialMediaPost

class SocialMediaPostForm(forms.ModelForm):
    class Meta:
        model = SocialMediaPost
        fields = ['platforms', 'message', 'image']
        widgets = {
            'platforms': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

    def __init__(self, *args, **kwargs):
        super(SocialMediaPostForm, self).__init__(*args, **kwargs)
        self.fields['platforms'].required = True
        self.fields['message'].required = True
        self.fields['image'].required = True
