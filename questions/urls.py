from django.urls import path
from . import views
app_name = 'questions'
urlpatterns = [path('api/question/<int:question_id>/vote/', views.question_vote, name='question_vote'), path('api/answer/<int:answer_id>/vote/', views.answer_vote, name='answer_vote'), path('api/correct/', views.correct_answer, name='correct_answer'), path('', views.index, name='index'), path('hot/', views.hot, name='hot'), path('tag/<str:tag>/', views.tag, name='tag'), path('question/<int:question_id>/', views.question, name='question'), path('ask/', views.ask, name='ask')]
