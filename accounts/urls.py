from django.contrib.auth.views import PasswordResetView

import accounts.views as aviews
from django.urls import path

app_name = 'accounts'
urlpatterns = [

    #Admin
    path('admin/liste/', aviews.UserList.as_view(), name='user-list'),
    path('admin/creation/', aviews.UserCreate.as_view(), name='user-create'),
    path('admin/modification/<uuid:user_uuid>', aviews.UserUpdate.as_view(), name='user-update'),
    path('admin/suppression/<uuid:user_uuid>', aviews.UserDelete.as_view(), name='user-delete'),
    path('admin/mon_profil/', aviews.UserUpdateSelf.as_view(), name='user-update-self'),
    path('admin/nouveau_mdp/<uuid:user_uuid>/', aviews.GeneratePassword.as_view(), name='user-newpassword'),
    path('modification/mdp/<uuid:user_uuid>/', aviews.UserUpdatePasswordSelf.as_view(), name='user-update-password-self'),

    #Accueil
    path('inscription/', aviews.SignUp.as_view(), name='user-signup'),
    path('password-reset/', aviews.CustomPasswordResetView.as_view(), name='password-reset'),

    #Interface
    path('modification/<uuid:user_uuid>', aviews.InterfaceUserUpdate.as_view(), name='interface-user-update'),
]
