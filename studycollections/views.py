from django.shortcuts import render, redirect, get_object_or_404
from .models import Collection
from django.contrib.auth.decorators import login_required
from .forms import CollectionForm
from django.http import HttpResponseForbidden

@login_required
def collection_list(request):
    collections = Collection.objects.filter(created_by=request.user)  # Filter collections by logged-in user
    return render(request, 'studycollections/collection_list.html', {'collections': collections})

@login_required  # Ensure the user is logged in
def create_collection(request):
    if request.method == 'POST':
        form = CollectionForm(request.POST)
        if form.is_valid():
            collection = form.save(commit=False)
            collection.created_by = request.user  # Set the creator of the collection
            collection.save()
            return redirect('collection_list')  # Redirect to the collection list after creating
    else:
        form = CollectionForm()

    return render(request, 'studycollections/create_collection.html', {'form': form})



def view_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    # Check permission
    user = request.user
    if collection.privacy == 'public':
        can_view = True
    else:
        can_view = (
            collection.created_by == user or
            user in collection.shared_with.all() or
            user in collection.collaborators.all()
        )

    if not can_view:
        return HttpResponseForbidden("You do not have permission to view this collection.")

    can_edit = collection.created_by == user or user in collection.collaborators.all()

    return render(request, 'studycollections/view_collection.html', {
        'collection': collection,
        'can_edit': can_edit,
    })
