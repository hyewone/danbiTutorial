from django.urls import path
from .views import TasksView, TaskView, SubTaskView, TeamsView, SignUpView, LoginView

urlpatterns = [
    path('tasks', TasksView.as_view(), name='task-list'),
    path('tasks/<int:task_id>', TaskView.as_view(), name='task-detail'),
    path('subtasks/<int:subtask_id>', SubTaskView.as_view(), name='subtask-detail'),
    path('teams', TeamsView.as_view(), name='teams'),
    path('signup', SignUpView.as_view(), name='signup'),
    path('login', LoginView.as_view(), name='login'),
]