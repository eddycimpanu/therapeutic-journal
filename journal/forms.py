from django import forms

from .models import Emotion, JournalEntry


class JournalEntryForm(forms.ModelForm):
    mood = forms.IntegerField(
        min_value=1, max_value=10, label="Nota zilei (1–10)"
    )
    emotions = forms.MultipleChoiceField(
        choices=Emotion.choices,
        widget=forms.CheckboxSelectMultiple,
        label="Ce emoții ai simțit azi? (1–3)",
    )

    class Meta:
        model = JournalEntry
        fields = ["text", "mood", "emotions"]
        labels = {"text": "Cum ți-a fost ziua?"}
        help_texts = {
            "text": "Descrie ce s-a întâmplat azi, fără să numești ce ai simțit."
        }
        widgets = {"text": forms.Textarea(attrs={"rows": 6})}

    def clean_emotions(self):
        emotions = self.cleaned_data["emotions"]
        if len(emotions) > 3:
            raise forms.ValidationError("Alege cel mult 3 emoții.")
        return emotions