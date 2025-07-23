from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import CustomerProfile, Review, ContactMessage

class CustomUserCreationForm(UserCreationForm):
    nome = forms.CharField(max_length=150, required=True, label="Nome Completo")
    email = forms.EmailField(required=True, label="E-mail") # Este será o username

    cpf = forms.CharField(max_length=14, required=True)
    telefone = forms.CharField(max_length=20, required=True)
    data_nascimento = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    genero = forms.CharField(max_length=20, required=False)
    cep = forms.CharField(max_length=9, required=True)
    endereco = forms.CharField(max_length=255, required=True)
    numero = forms.CharField(max_length=20, required=True)
    complemento = forms.CharField(max_length=100, required=False)
    bairro = forms.CharField(max_length=100, required=True)
    cidade = forms.CharField(max_length=100, required=True)
    estado = forms.CharField(max_length=2, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        # Deixar UserCreationForm lidar com 'username', 'password', 'password2'.
        # 'email' do formulário será mapeado para 'username'.
        # 'nome' do formulário será mapeado para 'first_name' e 'last_name'.
        # Não precisamos listar explicitamente os campos extras aqui,
        # eles são campos de formulário que serão lidos no save.
        fields = UserCreationForm.Meta.fields + ('email',) # Adiciona email para o UserCreationForm lidar.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove o campo 'username' gerado pelo UserCreationForm se já não for necessário
        # Se 'email' está sendo usado como username, o campo 'username' não é exibido.
        if 'username' in self.fields:
            self.fields['username'].required = False # Não é mais necessário preencher o username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este endereço de e-mail já está em uso.")
        return email

    def save(self, commit=True):
        # Chama o save do UserCreationForm para criar o objeto User
        user = super().save(commit=False)
        user.username = self.cleaned_data['email'] # Define o username como o email
        user.email = self.cleaned_data['email'] # Define o email do User

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

class ReviewForm(forms.ModelForm):
    # Rating field will be rendered as radio buttons for star selection
    rating = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)],
        widget=forms.RadioSelect,
        label="Sua Avaliação (Estrelas)"
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Deixe seu comentário sobre o produto...'}),
        required=False,
        label="Comentário"
    )

    class Meta:
        model = Review
        fields = ['rating', 'comment']
        # Excluímos product e user pois eles serão preenchidos na view
        # O campo 'rating' já é um PositiveIntegerField no modelo, o ChoiceField o converte corretamente.
        labels = {
            'rating': 'Avaliação',
            'comment': 'Comentário',
        }
        widgets = {
            'rating': forms.RadioSelect(attrs={'class': 'star-rating-input'}),
        }

# ---- NOVO FORMULÁRIO DE CONTATO ----
class ContactForm(forms.ModelForm):
    SUBJECT_CHOICES = [
        ('', 'Selecione um assunto'),
        ('duvida-produto', 'Dúvida sobre produto'),
        ('pedido', 'Informações sobre pedido'),
        ('sugestao', 'Sugestão'),
        ('reclamacao', 'Reclamação'),
        ('parceria', 'Parceria comercial'),
        ('outro', 'Outro'),
    ]
    subject = forms.ChoiceField(choices=SUBJECT_CHOICES, widget=forms.Select(attrs={
        'class': 'w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
    }))

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Seu nome completo',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'seuemail@exemplo.com',
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-vertical',
                'placeholder': 'Conte-nos como podemos ajudá-lo...'
            }),
        }

# ---- NOVO FORMULÁRIO DE LOGIN ----
class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={
            'autofocus': True,
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
            'placeholder': 'seuemail@exemplo.com'
        })
    )
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
            'placeholder': 'Sua senha'
        }),
    )

# ---- FORMULÁRIO DE PERFIL DO USUÁRIO ----
class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomerProfile
        # Exclui o campo 'user' pois ele não deve ser editado pelo usuário
        exclude = ['user']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input'}),
            'cpf': forms.TextInput(attrs={'class': 'form-input'}),
            'telefone': forms.TextInput(attrs={'class': 'form-input'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'genero': forms.TextInput(attrs={'class': 'form-input'}),
            'cep': forms.TextInput(attrs={'class': 'form-input'}),
            'endereco': forms.TextInput(attrs={'class': 'form-input'}),
            'numero': forms.TextInput(attrs={'class': 'form-input'}),
            'complemento': forms.TextInput(attrs={'class': 'form-input'}),
            'bairro': forms.TextInput(attrs={'class': 'form-input'}),
            'cidade': forms.TextInput(attrs={'class': 'form-input'}),
            'estado': forms.TextInput(attrs={'class': 'form-input'}),
        }
