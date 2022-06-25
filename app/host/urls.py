from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.host_home, name='host_home'),
    path('join/', views.host_join, name='host_join'),
    path('join/<int:id>/', views.host_join, name='host_join'),
    path('open/', views.toggle_game, name='toggle_game'),
    path('pages/', views.pages, name='pages'),
    path('pages/<int:page_id>', views.score_page, name='score_page'),
    path('pages/open/', views.toggle_page, { 'open': True }, name='open_page'),
    path('pages/close/', views.toggle_page, { 'open': False }, name='close_page'),
    path('leaderboard/', views.host_leaderboard, name='host_leaderboard'),
    path('team/<int:team_id>', views.team_page, name='team_page'),
    path('editor/new/', views.new_game, name='new_game'),
    path('editor/<int:game_id>/', views.edit_game, name='edit_game'),
    path('editor/page/<int:page_id>/', views.edit_page, name='edit_page'),
    path('editor/page/new/<int:game_id>/', views.new_page, name='new_page'),
    path('editor/question/<int:question_id>/', views.edit_question, name='edit_question'),
    path('accounts/', include('django.contrib.auth.urls')),
]
