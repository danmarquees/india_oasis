# store/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import CustomerProfile

class CustomUserCreationForm(UserCreationForm):
    # Campos dos modelos User e CustomerProfile que queremos no formulário.
    # O UserCreationForm já nos dá os campos de senha por padrão.
    nome = forms.CharField(max_length=150, required=True, label="Nome Completo")
    email = forms.EmailField(required=True, label="E-mail")
    cpf = forms.CharField(max_length=14, required=True)
    telefone = forms.CharField(max_length=20, required=True)
    data_nascimento = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    genero = forms.CharField(max_length=20, required=False)
    password = forms.CharField(label="Senha", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmação de Senha", widget=forms.PasswordInput)
    cep = forms.CharField(max_length=9, required=True)
    endereco = forms.CharField(max_length=255, required=True)
    numero = forms.CharField(max_length=20, required=True)
    complemento = forms.CharField(max_length=100, required=False)
    bairro = forms.CharField(max_length=100, required=True)
    cidade = forms.CharField(max_length=100, required=True)
    estado = forms.CharField(max_length=2, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        # AQUI DEFINIMOS OS NOMES DOS CAMPOS QUE O FORMULÁRIO IRÁ USAR.
        # NOTE QUE NÃO USAMOS 'password1', USAMOS 'password'.
        fields = ('nome', 'email', 'password', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este endereço de e-mail já está em uso.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        nome_completo = self.cleaned_data['nome']
        parts = nome_completo.split(' ', 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ''

        if commit:
            user.save()
            # Cria o CustomerProfile com os dados restantes do formulário
            CustomerProfile.objects.create(
                user=user,
                cpf=self.cleaned_data.get('cpf'),
                telefone=self.cleaned_data.get('telefone'),
                data_nascimento=self.cleaned_data.get('data_nascimento'),
                genero=self.cleaned_data.get('genero'),
                cep=self.cleaned_data.get('cep'),
                endereco=self.cleaned_data.get('endereco'),
                numero=self.cleaned_data.get('numero'),
                complemento=self.cleaned_data.get('complemento'),
                bairro=self.cleaned_data.get('bairro'),
                cidade=self.cleaned_data.get('cidade'),
                estado=self.cleaned_data.get('estado'),
            )
        return user
