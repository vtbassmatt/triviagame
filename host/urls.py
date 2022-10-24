from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.host_home, name='host_home'),
    path('<int:game_id>/join/', views.host_join, name='host_join'),
    path('<int:game_id>/toggle/', views.toggle_game, name='toggle_game'),
    path('<int:game_id>/pages/', views.pages, name='pages'),
    path('pages/<int:page_id>', views.score_page, name='score_page'),
    path('score/', views.assign_score, name='assign_score'),
    path('pages/state/', views.set_page_state, name='set_page_state'),
    path('leaderboard/', views.host_leaderboard, name='host_leaderboard'),
    path('team/<int:team_id>', views.team_page, name='team_page'),
    path('editor/new/', views.new_game, name='new_game'),
    path('editor/<int:game_id>/', views.edit_game, name='edit_game'),
    path('editor/page/<int:page_id>/', views.edit_page, name='edit_page'),
    path('editor/page/<int:page_id>/up/', views.page_move, { 'delta': -1 }, name='page_up'),
    path('editor/page/<int:page_id>/down/', views.page_move, { 'delta': 1 }, name='page_down'),
    path('editor/page/new/<int:game_id>/', views.new_page, name='new_page'),
    path('editor/page/<int:page_id>/delete/', views.delete_page, name='delete_page'),
    path('editor/question/<int:question_id>/', views.edit_question, name='edit_question'),
    path('editor/question/<int:question_id>/up/', views.question_move, { 'delta': -1 }, name='question_up'),
    path('editor/question/<int:question_id>/down/', views.question_move, { 'delta': 1 }, name='question_down'),
    path('editor/question/new/<int:page_id>/', views.new_question, name='new_question'),
    path('editor/question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('accounts/', include('django.contrib.auth.urls')),
]
