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

# views.py

# views.py


def browse_public_collections(request):
    public_collections = Collection.objects.filter(privacy='public').order_by('-created_at')
    return render(request, 'studycollections/public_collections.html', {'collections': public_collections})

def collection_detail(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    # Optional: prevent accessing private collections by others
    if collection.privacy == 'private' and collection.created_by != request.user and request.user not in collection.shared_with.all() and request.user not in collection.collaborators.all():
        return render(request, '403.html', status=403)

    return render(request, 'studycollections/collection_detail.html', {'collection': collection})