from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.core.validators import URLValidator
from django.forms import ValidationError
from target_object_database.models import TargetObject


class SourceForm(forms.ModelForm):
    target_content = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super(SourceForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(SourceForm, self).clean()
        target_type = self.cleaned_data.get("target_type")
        target_content = self.cleaned_data.get("target_content")

        if target_type in ("tx", "vd"):
            if not target_content:
                self.add_error("target_content", "This field is required.")
        elif target_type == "ig":
            if target_content:
                self.validate_manifest_url(target_content)
                self.validate_manifest_unique(target_content)
            else:
                self.add_error("target_content", "This field is required.")

    def validate_manifest_url(self, target_content):
        try:
            validate_https_url = URLValidator(schemes=["https"])
            validate_https_url(target_content)
        except ValidationError as e:
            self.add_error(
                "target_content",
                'Not a valid manifest URL. Make sure it\'s only one URL and that it begins with "https".',
            )

    def validate_manifest_unique(self, target_content):
        found = None
        try:
            found = TargetObject.objects.filter(
                target_content__icontains=target_content
            )[0]
        except:
            pass
        if found and found.pk != self.instance.pk:
            msg = (
                "The image manifest must be unique. It is already provided by source '%s' (ID:%s)."
                % (found.target_title, found.pk)
            )
            self.add_error("target_content", msg)

    class Meta:
        model = TargetObject
        fields = (
            "target_title",
            "target_author",
            "target_content",
            "target_citation",
            "target_creator",
            "target_courses",
            "target_type",
        )

