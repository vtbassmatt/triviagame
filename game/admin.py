from django.contrib import admin
from django.urls import reverse

from game import models


class PageInline(admin.StackedInline):
    model = models.Page

class GameAdmin(admin.ModelAdmin):
    inlines = (
        PageInline,
    )
    def view_on_site(self, obj):
        # HACK: layer violation, as this URL is defined in `host`
        url = reverse('host_join', args=(obj.id,))
        return url


class QuestionInline(admin.StackedInline):
    model = models.Question

class PageAdmin(admin.ModelAdmin):
    inlines = (
        QuestionInline,
    )

admin.site.register(models.Game, GameAdmin)
admin.site.register(models.Team)
admin.site.register(models.Page, PageAdmin)
admin.site.register(models.Question)
admin.site.register(models.Response)
