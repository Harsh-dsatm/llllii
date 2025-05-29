from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import admin, messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import *


def home(request):
    return render(request, 'home.html', context={"current_tab": "home"})


def readers_tab(request):
    readers = reader.objects.all()
    return render(request, 'readers.html',
                  context={"current_tab": "readers", "readers": readers})


def save_reader(request):
    if request.method == 'POST':
        reader_item = reader(
            reference_id=request.POST['reader_ref_id'],
            reader_name=request.POST['reader_name'],
            reader_contact=request.POST['reader_contact'],
            reader_address=request.POST['address'],
            active=True
        )
        reader_item.save()
        messages.success(request, 'Reader added successfully!')
        return redirect('/readers')
    else:
        return redirect('/readers')


def books_tab(request):
    books = Book.objects.all()

    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query) |
            Q(category__icontains=search_query)
        )

    return render(request, 'books.html', {
        "current_tab": "books",
        "books": books,
        "search_query": search_query
    })


def add_book(request):
    if request.method == 'POST':
        try:
            book = Book(
                title=request.POST['book_title'],
                author=request.POST['book_author'],
                isbn=request.POST['book_isbn'],
                category=request.POST['book_category'],
                publisher=request.POST.get('book_publisher', ''),
                status='available'
            )

            # Handle file upload if present
            if 'book_file' in request.FILES:
                book.book_file = request.FILES['book_file']

            book.save()
            messages.success(request, 'Book added successfully!')
        except Exception as e:
            if 'unique constraint' in str(e).lower():
                messages.error(request, 'A book with this ISBN already exists!')
            else:
                messages.error(request, f'Error adding book: {str(e)}')

        return redirect('/books')
    else:
        return redirect('/books')


def rent_book(request, book_id):
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        reader_id = request.POST.get('reader_id')

        if not reader_id:
            messages.error(request, 'Please select a reader!')
            return redirect('/books')

        if book.status != 'available':
            messages.error(request, 'This book is not available for rental!')
            return redirect('/books')

        try:
            reader_obj = get_object_or_404(reader, id=reader_id)

            # Create rental record
            rental = BookRental(
                book=book,
                reader=reader_obj,
                due_date=timezone.now() + timedelta(days=14),  # 2 weeks rental period
                status='active'
            )
            rental.save()

            # Update book status
            book.status = 'rented'
            book.save()

            messages.success(request, f'Book "{book.title}" rented to {reader_obj.reader_name}!')
        except Exception as e:
            messages.error(request, f'Error renting book: {str(e)}')

        return redirect('/books')
    else:
        return redirect('/books')


def my_bag(request):
    # Get reader based on session or user (you'll need to implement user authentication)
    # For now, let's assume we're getting all rentals or filtering by a specific reader

    reader_id = request.GET.get('reader_id')  # You can implement proper user session management

    if reader_id:
        try:
            reader_obj = get_object_or_404(reader, id=reader_id)
            rentals = BookRental.objects.filter(reader=reader_obj, status='active').select_related('book')
        except:
            rentals = BookRental.objects.none()
    else:
        # Show all active rentals for demo purposes
        rentals = BookRental.objects.filter(status='active').select_related('book', 'reader')

    # Update overdue status
    for rental in rentals:
        if rental.is_overdue():
            rental.status = 'overdue'
            rental.save()

    return render(request, 'my_bag.html', {
        "current_tab": "my_bag",
        "rentals": rentals,
        "readers": reader.objects.filter(active=True)  # For reader selection
    })


def return_book(request, rental_id):
    if request.method == 'POST':
        rental = get_object_or_404(BookRental, id=rental_id)

        # Update rental status
        rental.status = 'returned'
        rental.return_date = timezone.now()
        rental.save()

        # Update book status
        rental.book.status = 'available'
        rental.book.save()

        messages.success(request, f'Book "{rental.book.title}" returned successfully!')
        return redirect('/my-bag')
    else:
        return redirect('/my-bag')


def get_readers_ajax(request):
    """AJAX endpoint to get readers for book rental"""
    readers = reader.objects.filter(active=True).values('id', 'reader_name')
    return JsonResponse(list(readers), safe=False)
def my_bag(request):
    """
    View to display all currently rented books with reader information
    """
    # Get search query if provided
    search_query = request.GET.get('search', '').strip()

    # Get reader filter if provided
    reader_id = request.GET.get('reader_id')

    # Get all active rentals (books that haven't been returned)
    rentals = BookRental.objects.select_related('book', 'reader').filter(
        status__in=['active', 'overdue']  # Show active and overdue rentals
    ).order_by('-rental_date')

    # Filter by specific reader if provided
    if reader_id:
        try:
            reader_obj = get_object_or_404(reader, id=reader_id)
            rentals = rentals.filter(reader=reader_obj)
        except:
            rentals = BookRental.objects.none()

    # Filter by search query if provided
    if search_query:
        rentals = rentals.filter(
            Q(book__title__icontains=search_query) |
            Q(book__author__icontains=search_query) |
            Q(book__isbn__icontains=search_query) |
            Q(reader__reader_name__icontains=search_query) |
            Q(reader__reader_contact__icontains=search_query) |
            Q(reader__reference_id__icontains=search_query)
        )

    # Update overdue status for all rentals
    for rental in rentals:
        if rental.is_overdue() and rental.status == 'active':
            rental.status = 'overdue'
            rental.save()

    # Calculate summary statistics
    overdue_count = rentals.filter(status='overdue').count()
    active_count = rentals.filter(status='active').count()
    unique_readers = rentals.values('reader').distinct().count()

    context = {
        'rentals': rentals,
        'search_query': search_query,
        'overdue_count': overdue_count,
        'active_count': active_count,
        'unique_readers': unique_readers,
        'readers': reader.objects.filter(active=True),  # For reader filter dropdown
        'current_tab': 'my_bag'
    }

    return render(request, 'my-bag.html', context)