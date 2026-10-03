from django import forms
class DateInput(forms.DateInput):
    input_type = "date"
    template_name="widgets/date.html"


    def __init__(self, *args, **kwargs):
        kwargs.setdefault("format", "%Y-%m-%d")  # HTML5 format
        super().__init__(*args, **kwargs)
