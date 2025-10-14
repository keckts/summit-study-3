from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, Div
from .models import Blog

class BlogForm(forms.ModelForm):
    title = forms.CharField(max_length=200, label='Blog Title')
    content = forms.CharField(widget=forms.Textarea, label='Content')
    cover_image = forms.ImageField(required=False, label='Cover Image')
    slug = forms.SlugField(max_length=200, label='Slug')

    class Meta:
        model = Blog
        fields = ['title', 'content', 'cover_image', 'slug']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('title', css_class='form-control mb-3', placeholder='Enter blog title'),
            Field('content', css_class='form-control mb-3', placeholder='Write your content here', rows=8),
            Field('cover_image', css_class='form-control mb-3'),
            Field('slug', css_class='form-control mb-3', placeholder='Enter slug (auto-generated if left blank)'),
            Submit('submit', 'Publish Blog', css_class='btn btn-primary w-100')
        )
