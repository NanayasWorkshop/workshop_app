from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.utils import timezone

from ..models import Client, ContactPerson, ClientHistory, Communication, ClientDocument
from ..forms import ClientForm, ContactPersonForm, ClientDocumentForm


@login_required
def client_list(request):
    """
    Display a list of all clients in the system.
    """
    # Get filter parameters from request
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')
    search_query = request.GET.get('search', '')
    
    # Start with all clients
    clients = Client.objects.all().order_by('name')
    
    # Apply filters if provided
    if status_filter:
        clients = clients.filter(status=status_filter)
    
    if type_filter:
        clients = clients.filter(type=type_filter)
    
    if search_query:
        clients = clients.filter(
            Q(name__icontains=search_query) | 
            Q(client_id__icontains=search_query) |
            Q(primary_email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(industry__icontains=search_query)
        )
    
    context = {
        'clients': clients,
        'status_choices': Client.STATUS_CHOICES,
        'type_choices': Client.CLIENT_TYPES,
        'selected_status': status_filter,
        'selected_type': type_filter,
        'search_query': search_query,
    }
    
    return render(request, 'workshop_app/clients/list.html', context)


@login_required
def client_detail(request, client_id):
    """
    Display detailed information about a specific client.
    """
    # Get the client
    client = get_object_or_404(Client, client_id=client_id)
    
    # Get contact persons
    contacts = client.contacts.all()
    
    # Get client history/stats
    try:
        history = client.history
    except ClientHistory.DoesNotExist:
        # Create history if it doesn't exist
        history = ClientHistory.objects.create(client=client)
    
    # Get communications
    communications = Communication.objects.filter(client_history=history).order_by('-date')
    
    # Get documents
    documents = client.documents.all().order_by('-upload_date')
    
    # Handle document upload form
    if request.method == 'POST' and 'upload_document' in request.POST:
        document_form = ClientDocumentForm(request.POST, request.FILES, client=client)
        if document_form.is_valid():
            document_form.save()
            messages.success(request, "Document uploaded successfully.")
            return HttpResponseRedirect(request.path)
    else:
        document_form = ClientDocumentForm(client=client)
    
    context = {
        'client': client,
        'contacts': contacts,
        'history': history,
        'communications': communications,
        'documents': documents,
        'document_form': document_form,
    }
    
    return render(request, 'workshop_app/clients/detail.html', context)


@login_required
def client_create(request):
    """
    Create a new client.
    """
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            
            # Create client history
            ClientHistory.objects.create(client=client)
            
            messages.success(request, f"Client '{client.name}' created successfully.")
            return redirect('workshop_app:client_detail', client_id=client.client_id)
    else:
        form = ClientForm()
    
    context = {
        'form': form,
        'title': 'Add New Client',
        'is_new': True,
    }
    
    return render(request, 'workshop_app/clients/form.html', context)


@login_required
def client_update(request, client_id):
    """
    Update an existing client's information.
    """
    client = get_object_or_404(Client, client_id=client_id)
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f"Client '{client.name}' updated successfully.")
            return redirect('workshop_app:client_detail', client_id=client.client_id)
    else:
        form = ClientForm(instance=client)
    
    context = {
        'form': form,
        'client': client,
        'title': f"Edit Client: {client.name}",
        'is_new': False,
    }
    
    return render(request, 'workshop_app/clients/form.html', context)


@login_required
def client_delete(request, client_id):
    """
    Delete a client and all related data.
    """
    client = get_object_or_404(Client, client_id=client_id)
    
    if request.method == 'POST':
        client_name = client.name  # Store name before deletion
        client.delete()
        messages.success(request, f"Client '{client_name}' deleted successfully.")
        return redirect('workshop_app:client_list')
    
    context = {
        'client': client,
    }
    
    return render(request, 'workshop_app/clients/confirm_delete.html', context)


@login_required
def contact_create(request, client_id):
    """
    Add a new contact person to a client.
    """
    client = get_object_or_404(Client, client_id=client_id)
    
    if request.method == 'POST':
        form = ContactPersonForm(request.POST, client=client)
        if form.is_valid():
            contact = form.save()
            
            # If this is set as primary, unset others
            if contact.primary_contact:
                ContactPerson.objects.filter(
                    client=client, 
                    primary_contact=True
                ).exclude(id=contact.id).update(primary_contact=False)
            
            messages.success(request, f"Contact '{contact.name}' added successfully.")
            return redirect('workshop_app:client_detail', client_id=client.client_id)
    else:
        form = ContactPersonForm(client=client)
    
    context = {
        'form': form,
        'client': client,
        'title': f"Add Contact for {client.name}",
        'is_new': True,
    }
    
    return render(request, 'workshop_app/clients/contact_form.html', context)


@login_required
def contact_update(request, contact_id):
    """
    Update an existing contact person.
    """
    contact = get_object_or_404(ContactPerson, id=contact_id)
    client = contact.client
    
    if request.method == 'POST':
        form = ContactPersonForm(request.POST, instance=contact, client=client)
        if form.is_valid():
            updated_contact = form.save()
            
            # If this is set as primary, unset others
            if updated_contact.primary_contact:
                ContactPerson.objects.filter(
                    client=client, 
                    primary_contact=True
                ).exclude(id=updated_contact.id).update(primary_contact=False)
            
            messages.success(request, f"Contact '{updated_contact.name}' updated successfully.")
            return redirect('workshop_app:client_detail', client_id=client.client_id)
    else:
        form = ContactPersonForm(instance=contact, client=client)
    
    context = {
        'form': form,
        'contact': contact,
        'client': client,
        'title': f"Edit Contact: {contact.name}",
        'is_new': False,
    }
    
    return render(request, 'workshop_app/clients/contact_form.html', context)


@login_required
def contact_delete(request, contact_id):
    """
    Delete a contact person.
    """
    contact = get_object_or_404(ContactPerson, id=contact_id)
    client = contact.client
    
    if request.method == 'POST':
        contact_name = contact.name  # Store name before deletion
        contact.delete()
        messages.success(request, f"Contact '{contact_name}' deleted successfully.")
        return redirect('workshop_app:client_detail', client_id=client.client_id)
    
    context = {
        'contact': contact,
        'client': client,
    }
    
    return render(request, 'workshop_app/clients/contact_confirm_delete.html', context)


@login_required
def communication_add(request, client_id):
    """
    Add a communication log entry for a client.
    """
    client = get_object_or_404(Client, client_id=client_id)
    
    # Get or create client history
    history, _ = ClientHistory.objects.get_or_create(client=client)
    
    if request.method == 'POST':
        # Get form data
        comm_type = request.POST.get('comm_type')
        contact_id = request.POST.get('contact_person')
        summary = request.POST.get('summary')
        follow_up = request.POST.get('follow_up_required') == 'on'
        follow_up_date = request.POST.get('follow_up_date')
        attachment = request.FILES.get('attachment')
        
        # Validate required fields
        if not summary:
            messages.error(request, "Communication summary is required.")
            return redirect('workshop_app:client_detail', client_id=client.client_id)
        
        # Create communication record
        communication = Communication(
            client_history=history,
            comm_type=comm_type,
            summary=summary,
            staff_member=request.user,
            follow_up_required=follow_up,
            attachment=attachment
        )
        
        # Set optional fields
        if contact_id:
            try:
                contact = ContactPerson.objects.get(id=contact_id, client=client)
                communication.contact_person = contact
            except ContactPerson.DoesNotExist:
                pass
        
        if follow_up and follow_up_date:
            try:
                communication.follow_up_date = timezone.datetime.strptime(follow_up_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        communication.save()
        messages.success(request, "Communication log added successfully.")
        return redirect('workshop_app:client_detail', client_id=client.client_id)
    
    # Just redirect to detail page if not POST
    return redirect('workshop_app:client_detail', client_id=client.client_id)


@login_required
def document_delete(request, document_id):
    """
    Delete a client document.
    """
    document = get_object_or_404(ClientDocument, id=document_id)
    client = document.client
    
    if request.method == 'POST':
        document_title = document.title  # Store title before deletion
        document.delete()
        messages.success(request, f"Document '{document_title}' deleted successfully.")
        return redirect('workshop_app:client_detail', client_id=client.client_id)
    
    context = {
        'document': document,
        'client': client,
    }
    
    return render(request, 'workshop_app/clients/document_confirm_delete.html', context)
