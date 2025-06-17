import csv
from collections import deque

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, authenticate, login
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.views import PasswordResetView
from django.core.exceptions import FieldDoesNotExist
from django.core.mail import EmailMultiAlternatives, send_mail
from django.db.models import Q
from django.shortcuts import redirect, render, get_object_or_404
from django.template import loader
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.html import strip_tags
from django.views.generic import CreateView, UpdateView, DeleteView, View, ListView

from accounts.models import User
from accounts.forms import UserForm, UserSearchForm, AdminUserForm, SignUpForm


class UserUpdateSelf(UpdateView):
    """
    Un utilisateur modifie ses informations
    """
    model = User
    form_class = UserForm
    success_url = reverse_lazy('annonces:admin-annonce-list')
    success_message = "Informations mises à jour"

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super(UserUpdateSelf, self).get_context_data()
        #stripe.api_key = settings.STRIPE_SECRET_KEY
        #subscription = stripe.Subscription.retrieve(self.request.user.stripeSubscriptionId)
        #product = stripe.Product.retrieve(subscription.plan.product)
        #print(subscription)

        #context["product"] = product
        #context["subscription"] = subscription
        return context


class UserUpdatePasswordSelf(UpdateView):
    """
    Un utilisateur peut modifier son mot de passe ici
    """
    model = User
    form_class = AdminPasswordChangeForm
    template_name = "accounts/user_password_update.html"
    success_url = "/"
    slug_field = "uuid"
    slug_url_kwarg = "user_uuid"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = User.objects.get(uuid=self.kwargs['user_uuid'])
        kwargs.pop('instance', None)
        return kwargs

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        user = form.save()
        user.save()
        User.objects.filter(email=user.email).exclude(id=user.id).update(password=user.password)
        update_session_auth_hash(self.request, user)
        messages.success(self.request, "Mot de passe mis à jour")
        return redirect("annonces:annonce-list")


class GeneratePassword(View):
    """
    Admin can send new password to user by email
    """
    permission_required = 'accounts.add_user'

    def post(self, request, *args, **kwargs):
        user = get_object_or_404(User, uuid=kwargs.get('user_uuid'))
        user.send_login_email()
        messages.success(request, "Nouveau mot de passe envoyé")
        return redirect('accounts:user-update', user_uuid=user.uuid)


class UserList(ListView):
    """
    Pour les superadmins et les admins d'équipe
    """
    model = User
    is_admin = True
    paginate_by = 30

    def get_form(self):
        form = UserSearchForm(self.request.GET)
        form.is_valid()
        return form

    def get_queryset(self):
        self.form = self.get_form()
        self.search = self.form.cleaned_data
        order = self.request.GET.get("order", "email")
        self.request.session['user_list_url'] = self.request.get_full_path()

        if self.search.get("group"):
            queryset = self.search["group"].user_set.all()
        else:
            queryset = User.objects.all()
        if self.search.get("statut") == "inactive":
            queryset = queryset.filter(is_active=False)
        else:
            queryset = queryset.filter(is_active=True)
        if self.search.get("query"):
            terms = [term for term in self.search["query"].split(" ") if term]
            query = Q()
            for term in terms:
                query = query & (Q(first_name__icontains=term) | Q(last_name__icontains=term) | Q(email__icontains=term))
            queryset = queryset.filter(query)

        if order:
            try:
                queryset = queryset.order_by(order)
            except FieldDoesNotExist:
                messages.error(self.request, "Ordre incorrect")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["search_form"] = self.form
        return context


class UserCreate(CreateView):
    model = User
    is_admin = True
    success_message = "Utilisateur ajouté"
    success_url = reverse_lazy("accounts:user-list")

    def get_form_class(self):
        if self.request.user.is_staff:
            return AdminUserForm
        else:
            return UserForm

    def form_valid(self, form):
        user = form.save()
        user.send_login_email()
        messages.success(self.request, self.success_message)
        return redirect(self.success_url)


class UserUpdate(UpdateView):
    model = User
    is_admin = True
    slug_field = "uuid"
    slug_url_kwarg = "user_uuid"
    success_message = "Utilisateur mis à jour"
    success_url = reverse_lazy("accounts:user-list")

    def get_form_class(self):
        if self.request.user.is_staff:
            return AdminUserForm
        else:
            return UserForm

    def form_valid(self, form):
        form.instance.is_active = True
        return super().form_valid(form)


class UserDelete(DeleteView):
    model = User
    slug_field = "uuid"
    slug_url_kwarg = "user_uuid"
    is_admin = True
    success_url = reverse_lazy("accounts:user-list")

    def post(self, request, *args, **kwargs):
        if request.POST.get("action") == "delete":
            messages.success(self.request, "Utilisateur supprimé")
            return super().post(request, *args, **kwargs)
        elif request.POST.get("action") == "disable":
            user = self.get_object()
            user.is_active = False
            user.save()
            messages.success(self.request, "Utilisateur archivé")
        return redirect(self.success_url)


class SignUp(CreateView):
    """
    Les utilisateurs peuvent s'inscrire eux-mêmes ici.
    Ils sont ajoutés par défaut dans le groupe des utilisateurs standards.
    """
    model = User
    success_message = "Votre compte a bien été créé, vous êtes connecté(e) !"
    success_url = reverse_lazy("home:tunnel-3")
    form_class = SignUpForm
    template_name = "accounts/signup.html"

    def form_valid(self, form):
        user = form.save()
        user.username = user.email
        user.save()
        # user.groups.add(Group.objects.get(name=settings.GROUP_STANDARD_USER))
        messages.success(self.request, self.success_message)
        next = self.request.GET.get("next", self.success_url)
        user = authenticate(username=user.email, password=form.cleaned_data["password1"])
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect(next)


class CustomPasswordResetView(PasswordResetView):

    def get_context_data(self, **kwargs):
        messages.get_messages(self.request)
        return super().get_context_data()
    def form_valid(self, form):
        user_exists = User.objects.filter(email=form.cleaned_data["email"])

        if user_exists:
            user = user_exists.first()
            html_message = render_to_string("registration/password_reset_email.html", {"user": user})
            text_message = strip_tags(html_message)
            send_mail(subject='SafeFlat - Nouveau mot de passe',
                      message=text_message,
                      from_email=settings.EMAIL_HOST_USER,
                      recipient_list=[[form.cleaned_data["email"]]],
                      html_message=html_message)

            return redirect(reverse_lazy('password_reset_done'))
        messages.error(self.request, "Aucun compte n'est associé à cette adresse email.")
        return render(self.request, self.template_name, {'form': form})

class InterfaceUserUpdate(UpdateView):
    model = User
    slug_field = "uuid"
    slug_url_kwarg = "user_uuid"
    template_name = "accounts/interface_user_form.html"
    fields = ['first_name',
              'last_name',
              'email',
              'telephone',
              ]
    success_url = reverse_lazy("annonces:annonce-list")

    def form_valid(self, form):
        form.instance.is_active = True
        return super().form_valid(form)