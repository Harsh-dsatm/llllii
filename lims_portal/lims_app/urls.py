from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import *

urlpatterns = [
    path("", home_redirect, name="home_redirect"),
    path('home', home, name='home'),
    path('readers', readers_tab, name='readers'),
    path('readers/add', save_reader, name='add_reader'),
    path('books', books_tab, name='books'),
    path('books/add', add_book, name='add_book'),
    path('books/rent/<int:book_id>/', rent_book, name='rent_book'),
    path('my-bag', my_bag, name='my_bag'),
    path('return-book/<int:rental_id>/', return_book, name='return_book'),
    path('api/readers/', get_readers_ajax, name='get_readers_ajax'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
path('my-bag', my_bag, name='my_bag'),
path('return-book/<int:rental_id>/', return_book, name='return_book'),