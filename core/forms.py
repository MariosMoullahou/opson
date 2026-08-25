from django.forms import CheckboxInput, Select, SelectMultiple, Textarea

_WIDGET_CLASSES = {
    Textarea: 'form-textarea',
    Select: 'form-select',
    SelectMultiple: 'form-select',
    CheckboxInput: 'form-checkbox',
}
_DEFAULT_WIDGET_CLASS = 'form-input'


class StyledFieldsMixin:
    """Applies the stylesheet's form classes to every widget, so templates can render {{ field }} plainly."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            css_class = _WIDGET_CLASSES.get(type(widget), _DEFAULT_WIDGET_CLASS)
            existing = widget.attrs.get('class', '')
            widget.attrs['class'] = f'{existing} {css_class}'.strip()
