from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('uncurse/', views.uncurse, name='uncurse'),
    path('join/', views.join_game, name='join_game'),
    path('join/<int:id>/<str:code>/', views.join_game, name='join_game'),
    path('join/team/', views.create_team, name='create_team'),
    path('rejoin/', views.rejoin_team, name='rejoin_team'),
    path('rejoin/<int:id>/<str:code>/', views.rejoin_team, name='rejoin_team'),
    path('play/', views.play, name='play'),
    path('play/<int:page_order>/', views.answer_sheet, name='answer_sheet'),
    path('play/q/<int:question_id>/', views.question_hx, name='question_hx'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('healthcheck/', views.healthcheck, name='healthcheck'),
]
