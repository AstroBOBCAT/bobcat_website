from django import forms


class SearchForm(forms.Form):
    name = forms.CharField(
        required=False, label="Source Name", max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control",
                                      'placeholder': 'Type source name here...'}))
    ra_hms = forms.CharField(
        required=False, label="J2000 RA (hms)", max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control",
                                      'placeholder': 'Ex: 13h15m33.0149s'}))
    dec_dms = forms.CharField(
        required=False, label="J2000 Dec (dms)", max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control",
                                      'placeholder': 'Ex: -10d36m19.426s'}))
    ra_deg = forms.CharField(
        required=False, label="J2000 RA (deg)", max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control",
                                      'placeholder': 'Ex: 186.38756'}))
    dec_deg = forms.CharField(
        required=False, label="J2000 Dec (deg)", max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control",
                                      'placeholder': 'Ex: -21.55540'}))
