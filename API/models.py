from django.db import models


class Proxy(models.Model):
    name = models.CharField('NAME', max_length=30)
    host = models.CharField('HOST', max_length=30)
    port = models.CharField('PORT', max_length=30)
    login = models.CharField('LOGIN', max_length=30)
    password = models.CharField('PASSWORD', max_length=30)
