from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from core.models import Photographer
import re
import uuid

def validate_name(name):
    pattern = r'^[A-Za-zא-ת ]+$'
    if re.match(pattern, name):
        return True
    return False


def validate_password(password):
    if 6 <= len(password) <= 10:
        if password[0].isupper():
            if any(char.isdigit() for char in password):
                return True
    return False


def validate_email(email):
    pattern = r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True
    return False


def validate_phone(phone):
    if len(phone) == 10 and phone.isdigit() and phone.startswith('05'):
        return True
    return False


def validate_input(name, email, password, phone):
    if validate_name(name):
        if validate_email(email):
            if validate_password(password):
                if validate_phone(phone):
                    return "Success"
                else:
                    return "Invalid phone"
            else:
                return "Invalid password"
        else:
            return "Invalid email"
    else:
        return "Invalid name"


@api_view(['POST'])
def register_photographer(request):
    name = request.data.get('name')
    password = request.data.get('password')
    email = request.data.get('email')
    phone = request.data.get('phone')

    valid = validate_input(name, email, password, phone)
    if valid != "Success":
        return Response({'error': valid}, status=status.HTTP_400_BAD_REQUEST)

    if Photographer.objects.filter(email=email).exists():
        return Response({'error': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)

    photographer = Photographer.objects.create(
        name=name,
        password=make_password(password),
        email=email,
        phone=phone,
        secret=''
    )

    return Response({'message': 'Registration successful'}, status=status.HTTP_201_CREATED)




@api_view(['POST'])
def login_photographer(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not validate_email(email) or not validate_password(password):
        return Response({'error': 'Invalid email or password'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        photographer = Photographer.objects.get(email=email)
    except Photographer.DoesNotExist:
        return Response({'error': 'Invalid email or password'}, status=status.HTTP_400_BAD_REQUEST)

    if check_password(password, photographer.password):

        token = str(uuid.uuid4())
        photographer.secret = token
        photographer.save()

        response = Response({'message': 'Login successful'}, status=status.HTTP_200_OK)
        response.set_cookie(key='auth_token', value=token, httponly=True, secure=True)
        return response

    return Response({'error': 'Invalid email or password'}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
def logout_photographer(request):
    response = Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
    response.delete_cookie('auth_token')
    return response