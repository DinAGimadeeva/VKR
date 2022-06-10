from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render, redirect
from .forms import NewUserForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required

from .models import Document
from .forms import DocumentForm

import urllib
from urllib import parse

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import io

def plot_to_inline_img(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)  # rewind the data

    return('<img src = "data:image/png;base64,{}"/>'.format(str(base64.b64encode(buf.read()))[2:-1]))

# Create your views here.

@login_required
def index(request):
    template = loader.get_template('home.html')

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            newdoc = Document(docfile=request.FILES['docfile'])
            newdoc.user = request.user
            newdoc.save()

            # Redirect to the document list after POST
            return redirect('viewstats', csvfn= newdoc.docfile.name.replace("/", "-", 4))
        else:
            message = 'В форму введены неверные данные. Исправьте следующие недочёты:'
    else:
        form = DocumentForm()  # An empty, unbound form

    # Load documents for the list page
    documents = Document.objects.filter(user=request.user)

    def f(d):
        d.viewstatsurl = d.docfile.name.replace("/", "-", 4)
        return(d)

    context = {'form': form, 'documents': [f(d) for d in documents]}
    rendered_page = template.render(context, request)
    return HttpResponse(rendered_page)

@login_required
def viewstats(request, csvfn):
    template = loader.get_template('statistics.html')
    csvfn = csvfn.replace("-", "/", 4)

    df = pd.read_excel(csvfn)

#подсчет и вывод статистики (среднее и дисперсия и прочее)
    varstats = []
    for j in range(df.shape[1]):

        plt.figure()
        plt.hist(df.iloc[:,j], color="#FF7F50")
        fhist = plot_to_inline_img(plt.gcf())

        plt.figure()
        x = np.sort(df.iloc[:,j])
        y = np.arange(len(x)) / float(len(x))

        plt.step(x, y)
        fecdf = plot_to_inline_img(plt.gcf())

        varstats.append({
            'varname': df.columns.values[j],
            'n': df.shape[0],
            'mean': df.iloc[:,j].mean(),
            'var': df.iloc[:, j].var(),
            'std': df.iloc[:, j].std(),
            'median': df.iloc[:,j].median(),
            'q25': df.iloc[:,j].quantile(0.25),
            'q75': df.iloc[:,j].quantile(0.75),
            'iqr': df.iloc[:, j].quantile(0.75) - df.iloc[:,j].quantile(0.25),
            'fhist': fhist,
            'fecdf': fecdf,
        })

    sns.pairplot(df)
    fpp = plot_to_inline_img(plt.gcf())

    sns.pairplot(df, kind="kde")
    fpp2 = plot_to_inline_img(plt.gcf())

    context = {'csvfn': csvfn, 'stats': varstats, 'fpp': fpp, 'fpp2': fpp2}

    rendered_page = template.render(context, request)
    return HttpResponse(rendered_page)


def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        print(form)
        if form.is_valid():
            print("123")
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация завершена." )
            return redirect("index")
        print("345")
        messages.error(request, "Неправильно введены данные.")
    form = NewUserForm()
    return render (request=request, template_name="register.html", context={"register_form":form})


def login_request(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"Вы зашли как {username}.")
                return redirect("index")
            else:
                messages.error(request,"Неверный пароль или логин.")
        else:
            messages.error(request,"Неверный логин или пароль.")
    form = AuthenticationForm()
    return render(request=request, template_name="login.html", context={"login_form": form})


def logout_request(request):
    logout(request)
    messages.info(request, "Вы успешно вышли.")
    return redirect("login")