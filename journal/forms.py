from django import forms

from .models import Emotion, JournalEntry


class JournalEntryForm(forms.ModelForm):
    mood = forms.TypedChoiceField(
        choices=[(n, str(n)) for n in range(1, 11)],
        coerce=int,
        widget=forms.RadioSelect,
        label="Cum a fost ziua, de la 1 la 10?",
    )
    emotions = forms.MultipleChoiceField(
        choices=Emotion.choices,
        widget=forms.CheckboxSelectMultiple,
        label="Ce ai simțit azi? Alege între 1 și 3.",
    )

    class Meta:
        model = JournalEntry
        fields = ["text", "mood", "emotions"]
        labels = {"text": "Ce s-a întâmplat azi?"}
        help_texts = {
            "text": "Scrie liber, fără să numești ce ai simțit. Emoțiile le alegi mai jos."
        }
        widgets = {"text": forms.Textarea(attrs={"rows": 7})}

    def clean_emotions(self):
        emotions = self.cleaned_data["emotions"]
        if len(emotions) > 3:
            raise forms.ValidationError("Alege cel mult 3 emoții.")
        return emotions