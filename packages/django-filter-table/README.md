# PACKAGE_NAME

> A reusable Django package providing interactive data tables with user-selectable columns, filtering, HTMX/hyperscript interactions, and autocomplete widgets.

[![PyPI version](https://img.shields.io/pypi/v/PACKAGE_NAME.svg)](https://pypi.org/project/PACKAGE_NAME/)
[![Python versions](https://img.shields.io/pypi/pyversions/PACKAGE_NAME.svg)](https://pypi.org/project/PACKAGE_NAME/)
[![Django versions](https://img.shields.io/badge/Django-SUPPORTED_VERSIONS-blue.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-LICENSE-green.svg)](#license)

<!-- Replace PACKAGE_NAME, URLs, versions, and examples throughout this file. -->

## Overview

**PACKAGE_NAME** is a reusable Django application for building interactive,
server-rendered data tables.

It provides:

- Interactive Django tables
- User-selectable columns
- Column visibility and ordering
- Filtering
- Sorting and pagination
- HTMX-powered table updates
- `_hyperscript` interactions
- Autocomplete widgets for Django forms


The package is designed to keep application logic on the Django side while
using HTMX and `_hyperscript` for lightweight browser interactions.

---

## Features

### Interactive tables

- [ ] Define tables from Django querysets
- [ ] Select which columns are displayed
- [ ] Configure default column visibility
- [ ] Sort columns
- [ ] Paginate results
- [ ] Filter results
- [ ] Custom column rendering


### Filtering

Supported filters include:

- [ ] Text
- [ ] Choices
- [ ] Boolean
- [ ] Dates
- [ ] Numeric ranges
- [ ] Foreign keys

### Autocomplete

The package provides an autocomplete widget for Django forms.

Features include:

- [ ] Search-as-you-type
- [ ] Django queryset integration
- [ ] Configurable search fields
- [ ] Result limits
- [ ] Custom result rendering
- [ ] Permission-aware querysets
- [ ] Scoping results

---

## Requirements

| Dependency | Supported versions |
|---|---|
| Python | `>= 3.13` |
| Django | `4.2` |
| django-htmx | `>=1.23.0`
| django-bootstrap5 | `>=25.1`
| django-tables2 | `>=2.7.5`
| tablib | `>=3.8.0 `
| django-filter | `>=25.1`
| HTMX | `>= 2.0` |
| hyperscript | `>= 0.9.0` |
| bootstrap | >= 5.3

### Browser support

The package targets modern evergreen browsers.

Tested browsers:

- Chrome
- Firefox

---

## Installation

Install from PyPI:

```bash
pip install django-filter-table 
```

For a development installation:

```bash
pip install -e .
```

### Django configuration

Add the package to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "django-filter-table",
]
```

If the package requires additional configuration, add it here:

```python
# settings.py

DJANGO_TABLE= { 
    'user_profile_model': "UserProfiles", # user profile table
    'base_template': 'base.html'  # base template to use
}


```


---

## JavaScript dependencies

PACKAGE_NAME uses [HTMX](https://htmx.org/) for AJAX and CSS
transitions and [_hyperscript](https://hyperscript.org/)
for browser-side interactions.

Explain here how users should include these dependencies.

### HTMX

```html
<script src="YOUR_HTMX_SOURCE"></script>
```

### hyperscript

```html
<script src="YOUR_HYPERSCRIPT_SOURCE"></script>

### Bootstrap
<script src="YOUR_BOOTSTRAP_SOURCE"></script>

### Bootstrap icons
<script src="YOUR_BOOTSTRAP_ICON_SOURCE"></script>
```

> If PACKAGE_NAME provides these files itself, replace this section with
> instructions for loading them from Django static files.

---

# Quick start

This example shows the minimum setup required to create an interactive table.

## 1. Model

```python
from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    company = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class UserProfiles(models.Model):
    # user model field
    user_id = models.OneToOneField(
        'User', models.CASCADE, db_column='user_id')
    # This field type is a guess.
    table_settings = models.JSONField(blank=True)
    profile_id = models.AutoField(primary_key=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'user_profiles'

    def __str__(self):
        return f"{self.user_id.user_name}  preferences"

    def set_preference(self, table_name, key, value):
        settings = self.table_settings.get(table_name, {})
        settings[key] = value
        self.table_settings[table_name] = settings
        self.save(update_fields=['table_settings', 'updated_at'])

    def get_preference(self, table_name, key, default=None):
        return self.table_settings.get(table_name, {}).get(key, default)

python```

## 3. View

```python
# views.py

from .models import Customer


UNIVERSAL_SEARCH_FIELDS = [
    "name__icontains",
]


class CustomerListView(
    FilteredTableView
):
    title = 'Assets'
    model = Customer
    universal_search_fields = UNIVERSAL_SEARCH_FIELDS

python```

## 4. URL

```python
# urls.py

from django.urls import path
from .views import CustomerListView 

urlpatterns = [
    path("customers/", CustomerListView.as_view(), name="customer-list"),
    path('filter_table/', include('django_filter_table.urls')),
]
```

## 5. Template (base.html)

```html
{% load PACKAGE_TEMPLATE_TAGS %}

<!DOCTYPE html>
<html>
<head>

    <!-- HTMX -->
    <script src="YOUR_HTMX_SOURCE"></script>

    <!-- _hyperscript -->
    <script src="YOUR_HYPERSCRIPT_SOURCE"></script>

    <!-- bootstrap -->
    <script src="YOUR_BOOTSTRAP_SOURCE"></script>

    <!-- bootstrap icons -->
    <script src="YOUR_BOOTSTRAP_ICONS_SOURCE"></script>

</head>

<body>

    {% block content %}
    {% endblock content %}

    <!-- htmx selector funtions -->
    {% include "htmx_select/htmx_selector._hs" %}
</body>
</html>
```

---

# User-selectable columns

Explain how users open the column chooser and select columns.

Example:

```python
# Add real configuration here.
```

## Default visibility

By default all fields defined on models will be visible on table.
The default list of columns can be set with a list of 'default_columns' class attribute 
on the child class of Filtered table view. e.g:

  '''python
  class CustomerListView(FilteredTableView):
      title = 'Assets'
      model = Customer
      universal_search_fields = UNIVERSAL_SEARCH_FIELDS
      default_columns = ['name', company', 'email']  <-------------
  '''

## Restricted columns
No column restriction implemented

## Persisting column preferences

Table column preference is stored in database on the profile table.

---

# Filtering

Filtering uses the django-filter url mechanism.

Filters are dynamically generated through model introspection
of field types. The allowable filter type for each field type
is set the the generic filter module.

---

# Sorting

Table sorting uses the django-tables2 sorting mechanism.

---

# Pagination
Table pagination uses the django-tables2 pagination mechanism.


---

# Autocomplete widget

django-table-filter provides an autocomplete widget for Django form fields.

## Basic usage

Show a complete working example:

```python
from django import forms
from  django_filter_table.forms  import HTMXMultiPickerWidget


class CustomerForm(forms.Form):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        widget=HTMXMultiPickerWidget(
          model=model,
          field_name='field_name'
        ),
    )
```
The form can then be used in any request or CBV.


---

## Custom autocomplete behaviour

The autocomplete behaviour is set by using
the HTMXPicker class (from .utils) on any django model
that need to use the HTMXMultiPickerWidget widget.

If the class is missing then the widget will not work for that
model
e.g

```python
class Tblbrands(models.Model):
    brandid = models.BigAutoField(
        db_column="BrandID", primary_key=True, verbose_name="ID"
    )
    brandname = models.CharField(
        db_column="BrandName", unique=True, verbose_name="Brand"
    )

    htmx_picker = HtmxPicker(
        enabled=True,
        search_terms=('brandname__icontains',)
    )
```

---

# HTMX integration

Explain the HTMX architecture used by PACKAGE_NAME.

Typical request flow:

```text
Browser
   |
   | HTMX request
   v
Django view
   |
   | queryset / filtering / sorting
   v
Django template
   |
   | HTML fragment
   v
HTMX
   |
   v
Updated table and form filter 
```

Document:

- htmx request can be initiated by:
  - the filter form submission
  - pagination buttons
  - htmx action buttons
  - column actions (sorting, quick-filter)

- all urls are received the url of the main view.
 
- returned templates:
  html request: "django_filter_table/filter_table.html"  
  htmx request: "django_filter_table/filter_table.html#table-partial"

- htmx request content:
   - main - table context
   - out-of-bound replacement - filter form content, results summary and export button
  
- Browser history - works but could have outdated data.

## Example HTMX request

```http
GET /customers/?status__iexact=active
HX-Request: true
```

This request would return the table data filtered through django
filter on 'status' field with 'iexact' lookup. The filter form
will be returned with a 'status__iexact' field.

Sorting and pagination and export URL query params follows django 
table scheme. 

---

# `_hyperscript` integration

hyperscript is responsible for client interactions.
e.g
  - HTMXPickerWidget select and unselect span and input creation
    and destruction.
  - Showing and hiding of table bulk actions div
  - syncing row select boxes between table and card views 
  - column chooser selection and ordering.



```html
<!-- Add real example here -->
```
```



---

# Templates and customization

Below are the templates that can be overriden.
Please use these as templates for creating your
own.

```text
django_filter_table/
└── templates/
    └── django_filter_view/
        ├── base.html
```

---

# CSS customization

Bootstrap is the main styling framework used
with very limited inline styling on individual
components.
---

# Configuration

List every global setting.

```python
DJANGO_TABLE= { 
    'user_profile_model': "UserProfiles", # setting profile table
    'base_template': 'base.html' # setting base template
}
```


## CSRF

Data displayed by table are view only requests. No 
updates are carried out through form submissions.

Column chooser requests are POST requests using
django CSRF protection.

# Performance

Interactive tables can query large datasets, so document recommended usage.

## Querysets
Add Login and Permission mixin to FilteredTableView child
to control and restrict data access on a per user
basis.
The FilteredTableView is paginated by default, no other
optimisation is required.

Htmx select widget and quick column filters are paginated
and set to work with selected data types which have been 
optimised. Unoptimised data types will be blocked at 
a view level.


## Autocomplete

Performance of auto complete remains to be Tested
on large datasets

---

# Troubleshooting

## The table loads but filtering does nothing

Check:

1. HTMX is loaded.
2. The correct URL is being generated.
3. The request contains the expected parameters.
4. The Django view handles HTMX requests.
5. The expected template fragment is returned.
6. The HTMX target and swap behaviour are correct.

## The column chooser does not open

Check:

1. `_hyperscript` is loaded.
3. The package's JavaScript/static files are available.
4. There are no browser console errors.
5. User profile table and column exists

## Autocomplete returns no results

Check:

1. The queryset contains matching objects.
2. Search fields are configured correctly.
3. The minimum search length is satisfied.
4. The user has permission to see the results.
5. The main model and foreign key model have
    the HtmxPicker class configuration


# Compatibility
This is a small project and there will be no support for
older versions of python and django.

Main objected is to maintain compatibility with LTS 
releases of django and python

---

# Testing

Clone the repository:

```bash
git clone XXXXXXXXXXXXXXXXX
cd 
```

Create an environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

---

# License

PACKAGE_NAME is released under the MIT license.

---
