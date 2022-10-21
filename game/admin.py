from django.contrib import admin
from django.urls import reverse

from game import models


class PageInline(admin.StackedInline):
    model = models.Page
    show_change_link = True

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
    show_change_link = True

class PageAdmin(admin.ModelAdmin):
    inlines = (
        QuestionInline,
    )
    list_display = ('title', 'game')
    list_filter = ('game__name',)


class ResponseInline(admin.StackedInline):
    model = models.Response

class QuestionAdmin(admin.ModelAdmin):
    @admin.display(description='Page')
    def page_title(self, question):
        return question.page.title

    inlines = (
        ResponseInline,
    )
    list_display = (
        'order',
        'question',
        'page_title',
    )
    list_display_links = (
        'question',
    )
    list_filter = ('page__game__name',)


class ResponseAdmin(admin.ModelAdmin):
    @admin.display(description='Question')
    def question_only(self, response):
        return response.question.question

    list_display = (
        'value',
        'team',
        'question_only',
    )
    list_filter = (
        'question__page__game__name',
        'question__page__title',
    )


class TeamAdmin(admin.ModelAdmin):
    @admin.display(description='Game')
    def game_name(self, team):
        return team.game.name

    list_display = (
        'name',
        'members',
        'game_name',
    )
    list_filter = (
        'game__name',
    )

admin.site.register(models.Game, GameAdmin)
admin.site.register(models.Team, TeamAdmin)
admin.site.register(models.Page, PageAdmin)
admin.site.register(models.Question, QuestionAdmin)
admin.site.register(models.Response, ResponseAdmin)
