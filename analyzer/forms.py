from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class DocumentForm(forms.Form):
    docfile = forms.FileField(label='Выберите файл для загрузки')

class ImportExcelForm(forms.Form): file = forms.FileField(label= "Выберите Excel-файл для загрузки")

#Создание новых форм для входа
class NewUserForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(NewUserForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user