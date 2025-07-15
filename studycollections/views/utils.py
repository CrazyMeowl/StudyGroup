def user_can_view(user, collection):
    """Return True if user may view this collection."""
    if collection.privacy == 'public':
        return True
    return (
        user == collection.created_by
        or user in collection.collaborators.all()
        or user in collection.viewers.all()
    )

def user_can_edit(user, collection):
    """Return True if user may edit (add questions to) this collection."""
    return user == collection.created_by or user in collection.collaborators.all()