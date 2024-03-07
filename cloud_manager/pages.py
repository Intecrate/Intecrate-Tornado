"""
Depricated
"""

from __future__ import annotations
from cloud_manager.webserver import BaseHandler
from cloud_manager.common.tools import log, get_homedir

import os


print("pages.py is depricated")
exit()


class MainHandler(BaseHandler):
    def get(self):
        home_url = f"{self.request.protocol}://{self.request.host}/home"
        log(f'Redirecting to home: "{home_url}"')
        self.redirect(home_url, permanent=False)


class Home(BaseHandler):
    def get(self):
        log("trying to render home")
        homepage = os.path.join(get_homedir(), "templates/index.html")
        self.render(homepage)
        self.set_status(200)


class Signup(BaseHandler):
    def get(self):
        log(f"Current user is {self.get_current_user()}")
        if self.get_current_user():
            log("User already logged in, redirecting")
            self.redirect("/home")
            return

        page = os.path.join(get_homedir(), "templates/signup.html")
        self.render(page)
        self.set_status(200)


class Login(BaseHandler):
    def get(self):
        message = self.get_query_argument("msg", None, True)

        if message is not None:
            log(f"Login with message: {message}")

        page = os.path.join(get_homedir(), "templates/login.html")
        self.render(page)
        self.set_status(200)


class Contact(BaseHandler):
    def get(self):
        page = os.path.join(get_homedir(), "templates/contact.html")
        self.render(page)
        self.set_status(200)


class Products(BaseHandler):
    def get(self):
        page = os.path.join(get_homedir(), "templates/products.html")
        self.render(page)
        self.set_status(200)


class Profile(BaseHandler):
    def get(self):
        if not self.get_current_user():
            log("User not logged in, redirecting")
            self.redirect("/login")
            return

        page = os.path.join(get_homedir(), "templates/profile.html")
        self.render(page)
        self.set_status(200)


MAP = {
    "/": MainHandler,
    "/home": Home,
    "/signup": Signup,
    r"/login": Login,
    "/contact": Contact,
    "/products": Products,
}


def get_map() -> list[tuple]:
    return list(MAP.items())
