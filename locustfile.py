from locust import HttpUser, task, between

class UtilisateurEcommerce(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def voir_boutique(self):
        self.client.get("/shop/")

    @task(1)
    def ajouter_au_panier(self):
        self.client.get("/add-to-cart/1/", allow_redirects=True)

    @task(1)
    def voir_panier(self):
        self.client.get("/cart/")
