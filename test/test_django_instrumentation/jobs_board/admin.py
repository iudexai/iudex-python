from django.contrib import admin

from .models import Company, Profile, Project, Skill

admin.site.register(Skill)
admin.site.register(Company)
admin.site.register(Profile)
admin.site.register(Project)
