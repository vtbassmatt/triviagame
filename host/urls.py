from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.host_home, name='host_home'),
    path('<int:game_id>/toggle/', views.toggle_game, name='toggle_game'),
    path('<int:game_id>/pages/', views.pages, name='pages'),
    path('<int:game_id>/pages/state/', views.set_page_state, name='set_page_state'),
    path('<int:game_id>/pages/<int:page_id>', views.score_page, name='score_page'),
    path('<int:game_id>/score/', views.assign_score, name='assign_score'),
    path('<int:game_id>/leaderboard/', views.host_leaderboard, name='host_leaderboard'),
    path('<int:game_id>/team/<int:team_id>', views.team_page, name='team_page'),
    path('<int:game_id>/team/<int:team_id>/edit', views.hx_edit_team, name='edit_team'),
    path('editor/new/', views.new_game, name='new_game'),
    path('editor/<int:game_id>/', views.edit_game, name='edit_game'),
    path('editor/<int:game_id>/hosts', views.edit_game_hosts, name='edit_game_hosts'),
    path('editor/<int:game_id>/hosts/<int:user_id>', views.hx_remove_game_host, name='remove_game_host'),
    path('editor/page/<int:page_id>/', views.edit_page, name='edit_page'),
    path('editor/page/<int:page_id>/metadata/', views.hx_edit_page_metadata, name='edit_page_metadata'),
    path('editor/page/<int:page_id>/up/', views.page_move, { 'delta': -1 }, name='page_up'),
    path('editor/page/<int:page_id>/down/', views.page_move, { 'delta': 1 }, name='page_down'),
    path('editor/page/new/<int:game_id>/', views.new_page, name='new_page'),
    path('editor/page/<int:page_id>/delete/', views.delete_page, name='delete_page'),
    path('editor/question/<int:question_id>/', views.edit_question, name='edit_question'),
    path('editor/question/<int:question_id>/up/', views.question_move, { 'delta': -1 }, name='question_up'),
    path('editor/question/<int:question_id>/down/', views.question_move, { 'delta': 1 }, name='question_down'),
    path('editor/question/new/<int:page_id>/', views.new_question, name='new_question'),
    path('editor/question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('auth/prelogout', views.host_confirm_logout, name='confirm_logout'),
    path('auth/', include('django.contrib.auth.urls')),
]
