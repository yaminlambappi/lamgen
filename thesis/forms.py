import magic
from django import forms


class UploadForm(forms.Form):
    title = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your thesis title...',
        })
    )
    pdf_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf',
            'id': 'pdfFileInput',
        })
    )

    def clean_pdf_file(self):
        pdf_file = self.cleaned_data.get('pdf_file')
        if not pdf_file:
            return pdf_file

        # Validate file extension
        name = pdf_file.name.lower()
        if not name.endswith('.pdf'):
            raise forms.ValidationError('Only PDF files are allowed. Please upload a .pdf file.')

        # Validate MIME type using python-magic
        try:
            header = pdf_file.read(2048)
            pdf_file.seek(0)
            mime_type = magic.from_buffer(header, mime=True)
            if mime_type != 'application/pdf':
                raise forms.ValidationError(
                    f'Invalid file type: {mime_type}. Only PDF files are accepted.'
                )
        except forms.ValidationError:
            raise
        except Exception:
            # If magic fails, fall back to extension check only
            pass

        return pdf_file
