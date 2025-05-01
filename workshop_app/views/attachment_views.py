from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404

from ..models import MaterialAttachment
from ..forms import MaterialAttachmentForm

@login_required
def material_attachment_view(request, attachment_id):
    """
    View a material attachment.
    """
    attachment = get_object_or_404(MaterialAttachment, id=attachment_id)
    
    # Only allow access to users who can view the material
    if not request.user.is_authenticated:
        raise Http404("Attachment not found")
    
    # Render different templates based on file type
    if attachment.is_image():
        context = {
            'attachment': attachment,
            'material': attachment.material,
        }
        return render(request, 'workshop_app/materials/attachment_image.html', context)
    elif attachment.is_pdf():
        # For PDFs, either render in browser or use a PDF viewer template
        context = {
            'attachment': attachment,
            'material': attachment.material,
        }
        return render(request, 'workshop_app/materials/attachment_pdf.html', context)
    else:
        # For other files, prompt download
        response = HttpResponse(attachment.file, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{attachment.file.name.split("/")[-1]}"'
        return response

@login_required
def material_attachment_download(request, attachment_id):
    """
    Download a material attachment.
    """
    attachment = get_object_or_404(MaterialAttachment, id=attachment_id)
    
    # Only allow access to users who can view the material
    if not request.user.is_authenticated:
        raise Http404("Attachment not found")
    
    # Serve the file for download
    response = HttpResponse(attachment.file, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{attachment.file.name.split("/")[-1]}"'
    return response

