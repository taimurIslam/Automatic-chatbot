from django.urls import path, include
from .views import *
from django.conf.urls import url

urlpatterns = [
url('training/', chat_bot_training, name='chat_bot_training'),
url('chat/', chat_bot_chatting.as_view(), name='chat_bot_chatting'),
]
