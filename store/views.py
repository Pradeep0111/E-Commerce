from django.shortcuts import render,redirect
from django.http import JsonResponse
import json
from .models import *
import datetime
from .utils import cookieCart, cartData,guestOrder
from django.contrib.auth.forms import UserCreationForm
from .forms import CreateUserForm
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required

# Create your views here.

def store(request):

    data = cartData(request)
    cartItems = data['cartItems']

    products = Product.objects.all()
    context={'products':products,'cartItems':cartItems}
    return render(request,'store/store.html',context)

from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def checkout(request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context={'items':items,'order':order,'cartItems':cartItems}
    return render(request,'store/checkout.html',context)

@login_required(login_url='login')
def cart(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
   
    context={'items':items,'order':order,'cartItems':cartItems}
    return render(request,'store/cart.html',context)

def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    
    print('Action:',action)
    print('ProductId:',productId)


    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer,complete=False)

    orderItem, created = OrderItem.objects.get_or_create(order=order,product=product)

    if action =='add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action =='remove':
        orderItem.quantity = (orderItem.quantity - 1)
        
    orderItem.save()
    if orderItem.quantity<=0:
        orderItem.delete()
    return JsonResponse('Item was added',safe=False)

from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer,complete=False)

    else:
        customer,order = guestOrder(request,data)

    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == order.get_cart_total:
        order.complete = True
    order.save()

    if order.shipping == True:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            pincode=data['shipping']['pincode'],
        )
    return JsonResponse('Payment Complete!',safe=False)

def signup(request):
    form = CreateUserForm()
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            user = form.cleaned_data.get('username')
            messages.success(request,'Account was created for '+user)
            return redirect('store')

    context={'form':form}
    return render(request,'store/signup.html',context)
    
def Login(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request,username=username ,password=password)

        if user is not None:
            login(request,user)
            return redirect("store")
        else:
            messages.info(request,'Username or password is incorrect')
    context={}
    return render(request,'store/login.html',context) 

def logoutUser(request):
    logout(request)
    return redirect("store")