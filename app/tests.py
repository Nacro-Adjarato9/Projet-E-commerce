import unittest
from decimal import Decimal

import pytest
from django.contrib.messages import get_messages
from django.contrib.auth.models import User
from django.template import engines
from django.test import Client, TestCase
from django.urls import reverse

from .models import Profile, Category, Product, CartItem, Order, OrderItem
from .forms import RegistrationForm, LoginForm, ProductForm


class BaseConfigurationMixin:
    def setUp(self):
        self.client = Client()
        try:
            dj = engines["django"].engine
            if "django.templatetags.static" not in dj.builtins:
                dj.builtins.append("django.templatetags.static")
        except Exception:
            pass
        self.utilisateur_client = User.objects.create_user(
            username="client1", email="c1@example.com", password="pass1234"
        )
        self.utilisateur_vendeur = User.objects.create_user(
            username="seller1", email="s1@example.com", password="pass1234"
        )
        self.utilisateur_vendeur.profile.role = "vendeur"
        self.utilisateur_vendeur.profile.save()
        self.utilisateur_staff = User.objects.create_user(
            username="staff", email="staff@example.com", password="pass1234", is_staff=True
        )
        self.categorie = Category.objects.create(name="Cat A", slug="cat-a", is_active=True)
        self.produit_actif = Product.objects.create(
            seller=self.utilisateur_vendeur,
            category=self.categorie,
            name="Produit Actif",
            price=Decimal("1000.00"),
            stock=10,
            is_active=True,
            is_featured=True,
        )
        self.produit_inactif = Product.objects.create(
            seller=self.utilisateur_vendeur,
            category=self.categorie,
            name="Produit Inactif",
            price=Decimal("500.00"),
            stock=0,
            is_active=False,
        )


@pytest.mark.integration
class TestsVuesDeBase(BaseConfigurationMixin, TestCase):
    def test_deconnexion_redirige(self):
        self.client.login(username=self.utilisateur_client.username, password="pass1234")
        r = self.client.get(reverse("logout"))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.url.endswith(reverse("index")))

    def test_login_get_connecte_redirige_selon_role(self):
        self.client.login(username=self.utilisateur_client.username, password="pass1234")
        r = self.client.get(reverse("login"))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.url.endswith(reverse("index")))
        self.client.logout()
        self.client.login(username=self.utilisateur_vendeur.username, password="pass1234")
        r = self.client.get(reverse("login"))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.url.endswith(reverse("vendeur_dashboard")))

    def test_login_post_invalide_message_erreur(self):
        r = self.client.post(reverse("login"), {"username": "x", "password": "y"}, follow=True)
        self.assertEqual(r.status_code, 200)
        msgs = [m.message for m in get_messages(r.wsgi_request)]
        self.assertTrue(any("Erreur de connexion" in m for m in msgs))


@pytest.mark.integration
class TestsVuesBoutiquePanier(BaseConfigurationMixin, TestCase):
    def test_boutique_filtres_tri_pagination(self):
        for i in range(15):
            Product.objects.create(
                seller=self.utilisateur_vendeur,
                category=self.categorie,
                name=f"P{i}",
                price=Decimal("10.00") + i,
                stock=3,
                is_active=True
            )
        r = self.client.get(reverse("shop"), {"sort": "price_asc", "page": 1})
        self.assertEqual(r.status_code, 200)
        r = self.client.get(reverse("shop"), {"sort": "price_desc"})
        self.assertEqual(r.status_code, 200)
        r = self.client.get(reverse("shop"), {"sort": "name"})
        self.assertEqual(r.status_code, 200)
        r = self.client.get(reverse("shop"), {"sort": "rating"})
        self.assertEqual(r.status_code, 200)
        r = self.client.get(reverse("shop"), {"category": self.categorie.id})
        self.assertEqual(r.status_code, 200)

    def test_panier_anonyme_session_et_produit_manquant(self):
        session = self.client.session
        session["cart"] = {str(self.produit_actif.id): 2, "999999": 1}
        session.save()
        r = self.client.get(reverse("cart"))
        self.assertEqual(r.status_code, 200)
        elements = r.context["items"]
        self.assertTrue(any(getattr(it, "product", None) == self.produit_actif for it in elements))
        self.assertEqual(r.context["subtotal"], self.produit_actif.price * 2)

    def test_panier_auth_lecture_depuis_bd(self):
        self.client.login(username=self.utilisateur_client.username, password="pass1234")
        CartItem.objects.create(user=self.utilisateur_client, product=self.produit_actif, quantity=3)
        r = self.client.get(reverse("cart"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["subtotal"], self.produit_actif.price * 3)

    def test_ajout_au_panier_anonyme_puis_auth(self):
        r = self.client.get(reverse("add_to_cart", args=[self.produit_actif.id]), follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn(str(self.produit_actif.id), self.client.session.get("cart", {}))
        self.client.login(username=self.utilisateur_client.username, password="pass1234")
        r = self.client.get(reverse("add_to_cart", args=[self.produit_actif.id]), follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(CartItem.objects.filter(user=self.utilisateur_client, product=self.produit_actif).exists())

    def test_suppression_du_panier_anonyme_et_auth(self):
        session = self.client.session
        session["cart"] = {str(self.produit_actif.id): 1}
        session.save()
        r = self.client.get(reverse("remove_from_cart", args=[self.produit_actif.id]), follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertNotIn(str(self.produit_actif.id), self.client.session.get("cart", {}))
        self.client.login(username=self.utilisateur_client.username, password="pass1234")
        item = CartItem.objects.create(user=self.utilisateur_client, product=self.produit_actif, quantity=1)
        r = self.client.get(reverse("remove_from_cart", args=[item.id]), follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(CartItem.objects.filter(pk=item.id).exists())

    def test_mise_a_jour_element_panier_auth_tous_chemins(self):
        self.client.login(username=self.utilisateur_client.username, password="pass1234")
        item = CartItem.objects.create(user=self.utilisateur_client, product=self.produit_actif, quantity=1)
        r = self.client.post(reverse("update_cart_item", args=[item.id]), {"action": "inc"}, follow=True)
        self.assertEqual(r.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 2)
        r = self.client.post(reverse("update_cart_item", args=[item.id]), {"action": "dec"}, follow=True)
        self.assertEqual(r.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)
        r = self.client.post(reverse("update_cart_item", args=[item.id]), {"quantity": "5"}, follow=True)
        self.assertEqual(r.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 5)
        r = self.client.post(reverse("update_cart_item", args=[item.id]), {"quantity": "0"}, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(CartItem.objects.filter(pk=item.id).exists())
        item2 = CartItem.objects.create(user=self.utilisateur_client, product=self.produit_actif, quantity=1)
        r = self.client.post(reverse("update_cart_item", args=[item2.id]), {"quantity": "abc"}, follow=True)
        self.assertEqual(r.status_code, 200)
        msgs = [m.message for m in get_messages(r.wsgi_request)]
        self.assertTrue(any("Quantité invalide" in m for m in msgs))

    def test_mise_a_jour_element_panier_anonyme_tous_chemins(self):
        session = self.client.session
        session["cart"] = {str(self.produit_actif.id): 1}
        session.save()
        pid = str(self.produit_actif.id)
        r = self.client.post(reverse("update_cart_item", args=[self.produit_actif.id]), {"action": "inc"}, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.session["cart"][pid], 2)
        r = self.client.post(reverse("update_cart_item", args=[self.produit_actif.id]), {"action": "dec"}, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.session["cart"][pid], 1)
        r = self.client.post(reverse("update_cart_item", args=[self.produit_actif.id]), {"quantity": "4"}, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.session["cart"][pid], 4)
        r = self.client.post(reverse("update_cart_item", args=[self.produit_actif.id]), {"quantity": "0"}, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertNotIn(pid, self.client.session.get("cart", {}))
        session = self.client.session
        session["cart"] = {str(self.produit_actif.id): 1}
        session.save()
        r = self.client.post(reverse("update_cart_item", args=[self.produit_actif.id]), {"quantity": "xyz"}, follow=True)
        self.assertEqual(r.status_code, 200)
        msgs = [m.message for m in get_messages(r.wsgi_request)]
        self.assertTrue(any("Quantité invalide" in m for m in msgs))


@pytest.mark.integration
class TestsInscriptionEtCommande(BaseConfigurationMixin, TestCase):
    def test_inscription_get_puis_post_invalide(self):
        r = self.client.get(reverse("inscription"))
        self.assertEqual(r.status_code, 200)
        data = {
            "user_type": "client", "username": "xx", "email": "xx@ex.com",
            "password1": "a", "password2": "b", "first_name": "x", "last_name": "y",
            "telephone": "0", "date_naissance": "2000-01-01", "adresse": "rue",
            "ville": "Abj", "code_postal": "", "pays": "CI", "newsletter": False,
            "conditions": True,
        }
        r = self.client.post(reverse("inscription"), data=data, follow=True)
        self.assertEqual(r.status_code, 200)
        msgs = [m.message for m in get_messages(r.wsgi_request)]
        self.assertTrue(any("Veuillez corriger les erreurs" in m for m in msgs))

    def test_checkout_panier_vide_puis_avec_articles(self):
        self.client.login(username=self.utilisateur_client.username, password="pass1234")
        r = self.client.get(reverse("checkout"), follow=True)
        self.assertEqual(r.status_code, 200)
        msgs = [m.message for m in get_messages(r.wsgi_request)]
        self.assertTrue(any("panier est vide" in m.lower() for m in msgs))
        CartItem.objects.create(user=self.utilisateur_client, product=self.produit_actif, quantity=2)
        r = self.client.get(reverse("checkout"), follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Order.objects.filter(user=self.utilisateur_client).count(), 1)
        commande = Order.objects.get(user=self.utilisateur_client)
        self.assertEqual(commande.items.count(), 1)
        self.assertEqual(commande.total_price, self.produit_actif.price * 2)
        self.assertEqual(CartItem.objects.filter(user=self.utilisateur_client).count(), 0)


@pytest.mark.integration
class TestsCatalogueBoutique(BaseConfigurationMixin, TestCase):
    def test_boutique_affiche_uniquement_produits_actifs(self):
        url = reverse("shop")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        produits = list(resp.context["products"])
        noms = {p.name for p in produits}
        self.assertIn(self.produit_actif.name, noms)
        self.assertNotIn(self.produit_inactif.name, noms)

    def test_boutique_paginate_et_accepte_tris(self):
        for i in range(20):
            Product.objects.create(
                seller=self.utilisateur_vendeur,
                category=self.categorie,
                name=f"P{i}",
                price=Decimal("100.00") + i,
                stock=5,
                is_active=True,
            )
        resp = self.client.get(reverse("shop"), {"page": 1, "sort": "price_desc"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("products", resp.context)
        self.assertIn("paginator", resp.context)


@pytest.mark.integration
class TestsConnexion(BaseConfigurationMixin, TestCase):
    def test_login_transfere_panier_session_et_redirige(self):
        session = self.client.session
        session["cart"] = {str(self.produit_actif.id): 2}
        session.save()
        resp = self.client.post(
            reverse("login"),
            {"username": self.utilisateur_client.username, "password": "pass1234"},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.client.session.get("cart", {}), {})
        items = CartItem.objects.filter(user=self.utilisateur_client, product=self.produit_actif)
        self.assertEqual(items.count(), 1)
        self.assertEqual(items.first().quantity, 2)
        msgs = [m.message for m in get_messages(resp.wsgi_request)]
        self.assertTrue(any("transféré" in m.lower() for m in msgs))


@pytest.mark.integration
class TestsInscription(BaseConfigurationMixin, TestCase):
    def test_vue_inscription_cree_utilisateur_et_profil(self):
        donnees = {
            "user_type": "client",
            "username": "newuser",
            "email": "new@ex.com",
            "password1": "pass1234",
            "password2": "pass1234",
            "first_name": "New",
            "last_name": "User",
            "telephone": "0600000000",
            "date_naissance": "2000-01-01",
            "adresse": "1 rue",
            "ville": "Paris",
            "code_postal": "",
            "pays": "FR",
            "newsletter": True,
            "conditions": True,
        }
        resp = self.client.post(reverse("inscription"), data=donnees, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        u = User.objects.get(username="newuser")
        self.assertTrue(hasattr(u, "profile"))
        self.assertEqual(u.profile.role, "client")
        self.assertEqual(resp.redirect_chain[-1][0].endswith(reverse("login")), True)


@pytest.mark.integration
class TestsDroitsAcces(BaseConfigurationMixin, TestCase):
    def test_ajout_produit_requiert_role_vendeur(self):
        self.client.login(username=self.utilisateur_client.username, password="pass1234")
        resp = self.client.get(reverse("add_product"), follow=True)
        self.assertEqual(resp.status_code, 200)
        msgs = [m.message for m in get_messages(resp.wsgi_request)]
        self.assertTrue(any("vendeur" in m.lower() for m in msgs))

        self.client.logout()
        self.client.login(username=self.utilisateur_vendeur.username, password="pass1234")
        resp_ok = self.client.get(reverse("add_product"))
        self.assertEqual(resp_ok.status_code, 200)

        post_data = {
            "name": "Nouveau Produit",
            "category": self.categorie.id,
            "description": "desc",
            "price": "123.45",
            "old_price": "",
            "discount_percentage": "0",
            "badge": "",
            "stock": "3",
            "is_featured": True,
        }
        resp_post = self.client.post(reverse("add_product"), data=post_data, follow=True)
        self.assertEqual(resp_post.status_code, 200)
        self.assertTrue(
            Product.objects.filter(name="Nouveau Produit", seller=self.utilisateur_vendeur).exists()
        )

    def test_tableau_de_bord_admin_requiert_staff(self):
        self.client.login(username=self.utilisateur_client.username, password="pass1234")
        resp = self.client.get(reverse("admin_dashboard"), follow=True)
        self.assertEqual(resp.status_code, 200)
        msgs = [m.message for m in get_messages(resp.wsgi_request)]
        self.assertTrue(any("non autorisé" in m.lower() for m in msgs))
        self.client.logout()
        self.client.login(username=self.utilisateur_staff.username, password="pass1234")
        resp_ok = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(resp_ok.status_code, 200)


@pytest.mark.integration
class TestsTableauBordVendeur(BaseConfigurationMixin, TestCase):
    def test_acces_vendeur_200_et_bloque_client(self):
        self.client.login(username=self.utilisateur_vendeur.username, password="pass1234")
        resp = self.client.get(reverse("vendeur_dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.client.logout()
        self.client.login(username=self.utilisateur_client.username, password="pass1234")
        resp2 = self.client.get(reverse("vendeur_dashboard"), follow=True)
        self.assertEqual(resp2.status_code, 200)
        msgs = [m.message for m in get_messages(resp2.wsgi_request)]
        self.assertTrue(any("pas un vendeur" in m.lower() for m in msgs))


@pytest.mark.unit
class TestsFormulaires(BaseConfigurationMixin, TestCase):
    def test_loginform_identifiants_invalides_validationerror(self):
        form = LoginForm(data={"username": "ghost", "password": "wrong"})
        self.assertFalse(form.is_valid())
        self.assertIn("Nom d'utilisateur ou mot de passe incorrect.", form.errors["__all__"])

    def test_loginform_identifiants_valides_contient_user(self):
        form = LoginForm(data={"username": self.utilisateur_client.username, "password": "pass1234"})
        self.assertTrue(form.is_valid())
        self.assertIn("user", form.cleaned_data)
        self.assertEqual(form.cleaned_data["user"], self.utilisateur_client)

    def test_inscription_pseudo_deja_pris(self):
        data = {
            "user_type": "client",
            "username": self.utilisateur_client.username,
            "email": "new_unique@example.com",
            "password1": "pass1234",
            "password2": "pass1234",
            "first_name": "A",
            "last_name": "B",
            "telephone": "0600",
            "date_naissance": "2000-01-01",
            "adresse": "addr",
            "ville": "Paris",
            "code_postal": "",
            "pays": "FR",
            "newsletter": False,
            "conditions": True,
        }
        form = RegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("Ce nom d'utilisateur est déjà pris.", form.errors["username"])

    def test_inscription_email_deja_utilise(self):
        data = {
            "user_type": "client",
            "username": "uniqueuser",
            "email": self.utilisateur_client.email,
            "password1": "pass1234",
            "password2": "pass1234",
            "first_name": "A",
            "last_name": "B",
            "telephone": "0600",
            "date_naissance": "2000-01-01",
            "adresse": "addr",
            "ville": "Paris",
            "code_postal": "",
            "pays": "FR",
            "newsletter": False,
            "conditions": True,
        }
        form = RegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("Cet email est déjà utilisé.", form.errors["email"])

    def test_inscription_mots_de_passe_differents(self):
        data = {
            "user_type": "client",
            "username": "uniqueuser",
            "email": "unique@example.com",
            "password1": "pass1234",
            "password2": "different",
            "first_name": "A",
            "last_name": "B",
            "telephone": "0600",
            "date_naissance": "2000-01-01",
            "adresse": "addr",
            "ville": "Paris",
            "code_postal": "",
            "pays": "FR",
            "newsletter": False,
            "conditions": True,
        }
        form = RegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("Les mots de passe ne correspondent pas.", form.errors["__all__"])

    def test_inscription_vendeur_champs_requis_manquants(self):
        data = {
            "user_type": "vendeur",
            "username": "vend1",
            "email": "vend1@example.com",
            "password1": "pass1234",
            "password2": "pass1234",
            "first_name": "V",
            "last_name": "Endeur",
            "telephone": "0600",
            "date_naissance": "2000-01-01",
            "adresse": "addr",
            "ville": "Paris",
            "code_postal": "",
            "pays": "FR",
            "newsletter": False,
            "conditions": True,
        }
        form = RegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("Requis pour un vendeur.", form.errors["nom_entreprise"])
        self.assertIn("Requis pour un vendeur.", form.errors["siege"])

    def _donnees_inscription_de_base(self):
        return {
            "user_type": "client",
            "username": "newclient",
            "email": "newclient@example.com",
            "password1": "pass1234",
            "password2": "pass1234",
            "first_name": "New",
            "last_name": "Client",
            "telephone": "0600",
            "date_naissance": "2000-01-01",
            "adresse": "1 rue",
            "ville": "Paris",
            "code_postal": "",
            "pays": "FR",
            "newsletter": True,
            "conditions": True,
        }

    def test_inscription_save_cree_client_et_met_a_jour_profil(self):
        form = RegistrationForm(data=self._donnees_inscription_de_base())
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.username, "newclient")
        self.assertEqual(user.profile.role, "client")
        self.assertEqual(user.profile.city, "Paris")
        self.assertTrue(user.profile.newsletter)

    def test_inscription_save_vendeur_renseigne_champs_entreprise(self):
        data = self._donnees_inscription_de_base()
        data.update({
            "user_type": "vendeur",
            "username": "newvendor",
            "email": "newvendor@example.com",
            "nom_entreprise": "MaBoite",
            "siege": "Abidjan",
            "categories": "Mode;Chaussures",
            "description_entreprise": "Super boutique",
        })
        form = RegistrationForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        p = user.profile
        self.assertEqual(p.role, "vendeur")
        self.assertEqual(p.company_name, "MaBoite")
        self.assertEqual(p.head_office, "Abidjan")
        self.assertIn("Mode", p.main_categories)

    def test_product_form_attributs_attendus(self):
        form = ProductForm()
        attendus = {
            "name", "category", "description", "price", "old_price",
            "discount_percentage", "image", "image2", "image3",
            "badge", "stock", "is_featured"
        }
        self.assertTrue(attendus.issubset(set(form.fields.keys())))


@pytest.mark.integration
class TestsFonctionnalitesNonImpl(BaseConfigurationMixin, TestCase):
    @unittest.skip("02 Page de produit détaillée : non implémentée (aucune URL/view fournie).")
    def test_page_detail_produit(self):
        pass

    @unittest.expectedFailure
    def test_recherche_non_impl(self):
        resp = self.client.get(reverse("shop"), {"q": "Prod"})
        self.assertContains(resp, "0 résultat")

    @unittest.expectedFailure
    def test_flux_ajout_panier_non_impl(self):
        self.client.login(username=self.utilisateur_client.username, password="pass1234")
        resp = self.client.get(reverse("add_to_cart", args=[self.produit_actif.id]), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(CartItem.objects.filter(user=self.utilisateur_client).count(), 0)

    @unittest.skip("05 Validation du panier : non finalisée côté UI/processus.")
    def test_validation_panier(self):
        pass

    @unittest.skip("06 Système de favoris : non implémenté.")
    def test_favoris(self):
        pass

    @unittest.skip("07 Page de commande : non implémentée.")
    def test_page_commande(self):
        pass

    @unittest.skip("08 Suivi de commande : non implémenté.")
    def test_suivi_commande(self):
        pass

    @unittest.skip("09 Paiement d’une commande : non implémenté (pas de passerelle de paiement).")
    def test_paiement(self):
        pass

    @unittest.skip("12 Récupération du mot de passe : non configurée.")
    def test_recuperation_mot_de_passe(self):
        pass

    @unittest.skip("13 Historique des commandes : non implémenté (pas de vue dédiée).")
    def test_historique_commandes(self):
        pass

    @unittest.skip("14 Gestion des produits : partiel seulement (ajout ok, pas d’édition/suppression/liste dédiée).")
    def test_gestion_complete_produits(self):
        pass

    @unittest.skip("15 Gestion des catégories : non implémentée (pas de vues/back-office public).")
    def test_gestion_categories(self):
        pass

    @unittest.skip("16 Gestion des coupons : non implémentée.")
    def test_coupons(self):
        pass

    @unittest.skip("18 Confirmation email après paiement : non implémentée.")
    def test_confirmation_email_apres_paiement(self):
        pass

    @unittest.skip("19 Consultation des revenus : non implémentée.")
    def test_consultation_revenus(self):
        pass

    @unittest.skip("21 Validation des produits par l’admin : non implémentée (workflow d’approbation absent).")
    def test_validation_produits_admin(self):
        pass
