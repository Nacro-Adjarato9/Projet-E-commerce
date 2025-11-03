from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from .models import Profile, Product, Category


class LoginForm(forms.Form):
    """Formulaire de connexion"""
    username = forms.CharField(max_length=150, label="Nom d'utilisateur")
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")

    def clean(self):
        cleaned = super().clean()
        username = cleaned.get("username")
        password = cleaned.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise ValidationError("Nom d'utilisateur ou mot de passe incorrect.")
            cleaned["user"] = user
        return cleaned


class RegistrationForm(forms.Form):
	# Type d'utilisateur
	user_type = forms.ChoiceField(choices=(('client', 'Client'), ('vendeur', 'Vendeur')), initial='client')

	# Connexion
	username = forms.CharField(max_length=150)
	email = forms.EmailField()
	password1 = forms.CharField(widget=forms.PasswordInput)
	password2 = forms.CharField(widget=forms.PasswordInput)

	# Infos personnelles
	first_name = forms.CharField(max_length=150)
	last_name = forms.CharField(max_length=150)
	telephone = forms.CharField(max_length=30)
	date_naissance = forms.DateField(required=True, input_formats=["%Y-%m-%d"])  # <input type=date>

	adresse = forms.CharField(widget=forms.Textarea)
	ville = forms.CharField(max_length=120)
	code_postal = forms.CharField(max_length=20, required=False)
	pays = forms.CharField(max_length=120)

	# Vendeur
	nom_entreprise = forms.CharField(max_length=255, required=False)
	siege = forms.CharField(max_length=255, required=False)
	categories = forms.CharField(max_length=255, required=False)
	description_entreprise = forms.CharField(widget=forms.Textarea, required=False)

	# Consentements
	newsletter = forms.BooleanField(required=False)
	conditions = forms.BooleanField(required=True)

	def clean_username(self):
		username = self.cleaned_data["username"].strip()
		if User.objects.filter(username__iexact=username).exists():
			raise ValidationError("Ce nom d'utilisateur est déjà pris.")
		return username

	def clean_email(self):
		email = self.cleaned_data["email"].strip()
		if User.objects.filter(email__iexact=email).exists():
			raise ValidationError("Cet email est déjà utilisé.")
		return email

	def clean(self):
		cleaned = super().clean()
		p1 = cleaned.get("password1")
		p2 = cleaned.get("password2")
		if p1 and p2 and p1 != p2:
			raise ValidationError("Les mots de passe ne correspondent pas.")

		if cleaned.get("user_type") == "vendeur":
			# Champs requis pour vendeur côté serveur
			if not cleaned.get("nom_entreprise"):
				self.add_error("nom_entreprise", "Requis pour un vendeur.")
			if not cleaned.get("siege"):
				self.add_error("siege", "Requis pour un vendeur.")
		return cleaned

	def save(self):
		data = self.cleaned_data
		user = User.objects.create_user(
			username=data["username"],
			email=data["email"],
			password=data["password1"],
			first_name=data["first_name"],
			last_name=data["last_name"],
		)

		# Un profil vide est créé par le signal; on le met à jour
		profile: Profile = user.profile  # type: ignore[attr-defined]
		profile.role = data["user_type"]
		profile.phone = data["telephone"]
		profile.birth_date = data["date_naissance"]
		profile.address = data["adresse"]
		profile.city = data["ville"]
		profile.postal_code = data.get("code_postal") or ""
		profile.country = data["pays"]
		profile.newsletter = data.get("newsletter", False)

		if data["user_type"] == "vendeur":
			profile.company_name = data.get("nom_entreprise", "")
			profile.head_office = data.get("siege", "")
			profile.main_categories = data.get("categories", "")
			profile.company_description = data.get("description_entreprise", "")

		profile.save()
		return user


class ProductForm(forms.ModelForm):
	"""Formulaire pour ajouter/modifier un produit"""
	
	class Meta:
		model = Product
		fields = ['name', 'category', 'description', 'price', 'old_price', 
				  'discount_percentage', 'image', 'image2', 'image3', 
				  'badge', 'stock', 'is_featured']
		widgets = {
			'name': forms.TextInput(attrs={
				'class': 'form-input',
				'placeholder': 'Nom du produit'
			}),
			'category': forms.Select(attrs={'class': 'form-input'}),
			'description': forms.Textarea(attrs={
				'class': 'form-input',
				'placeholder': 'Description détaillée du produit',
				'rows': 4
			}),
			'price': forms.NumberInput(attrs={
				'class': 'form-input',
				'placeholder': 'Prix en FCFA'
			}),
			'old_price': forms.NumberInput(attrs={
				'class': 'form-input',
				'placeholder': 'Ancien prix (optionnel)'
			}),
			'discount_percentage': forms.NumberInput(attrs={
				'class': 'form-input',
				'placeholder': '0-100'
			}),
			'badge': forms.Select(attrs={'class': 'form-input'}),
			'stock': forms.NumberInput(attrs={
				'class': 'form-input',
				'placeholder': 'Quantité en stock'
			}),
			'is_featured': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
		}
		labels = {
			'name': 'Nom du produit',
			'category': 'Catégorie',
			'description': 'Description',
			'price': 'Prix (FCFA)',
			'old_price': 'Ancien prix (FCFA)',
			'discount_percentage': 'Réduction (%)',
			'image': 'Image principale',
			'image2': 'Image 2 (optionnelle)',
			'image3': 'Image 3 (optionnelle)',
			'badge': 'Badge',
			'stock': 'Stock disponible',
			'is_featured': 'Produit mis en avant',
		}

