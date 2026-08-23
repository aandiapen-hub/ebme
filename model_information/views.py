from django.db import transaction
from django.forms import ValidationError
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from documents.mixins import TempUploadMixin

from django.db.models.deletion import ProtectedError

# import models
from assets.models import Tblbrands, Tblmodel, Tblcategories, Tblcheckslists
from .models import (
    ModelView,
    Software,
    SoftwareModel,
    EquipmentConfiguration,
    EquipmentConfigurationModel,
    EquipmentConfigurationScope,
)
from .services.configuration import create_new_config_version
from .services.software import add_new_software_version

from django.views.generic import (
    UpdateView,
    CreateView,
    DeleteView,
    ListView,
    DetailView,
    FormView,
)

# import django-tables2
from django_tables2 import tables, SingleTableMixin, columns

from documents.services.documents import delete_object_document_links
from utils.generic_views import BulkUpdateView

# import forms
from .forms import (
    ConfigurationScopeCreateForm,
    ModelCreateForm,
    ModelUpdateForm,
    BrandBulkUpdateForm,
    ModelBulkUpdateForm,
    AddNewConfigVersionForm,
    AddNewSoftwareVersionForm,
    ModelCopyForm,
)

# import permissions mixins
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


from utils.generic_views import FilteredTableView, TableAction

# brand views


class FilteredBrandTableView(
    LoginRequiredMixin, PermissionRequiredMixin, FilteredTableView
):
    paginate_by = 25
    title = 'Brands'
    permission_required = "assets.view_tblbrands"
    table_class = None
    open_column = 'brandname'
    model = Tblbrands
    universal_search_fields = ["brandname__icontains"]
    default_columns = ["brandname"]

    actions = [
        TableAction(
            name='Add',
            type='link',
            on_selectable_items = False, 
            url=reverse_lazy('model_information:create_brand'),
            permission='assets.add_tblbrands',
            icon='bi-plus',
            color='outline-secondary'
        ),
    ]

class BrandUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Tblbrands
    fields = "__all__"
    template_name = "model_information/brand_update.html"
    permission_required = "assets.change_tblbrands"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context.get("cancel_url", None) is None:
            context["cancel_url"] = reverse(
                "model_information:brand_detail", kwargs={"pk": self.object.pk}
            )
        return context

    def get_success_url(self):
        return reverse("model_information:brand_detail", kwargs={"pk": self.object.pk})


class BrandBulkUpdateView(BulkUpdateView):
    context_object_name = "brand"
    model = Tblbrands
    permission_required = "assets.change_tblbrands"
    form_class = BrandBulkUpdateForm
    summary_field_names = None
    success_url = reverse_lazy("model_information:brandlist")


class BrandCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, TempUploadMixin, CreateView
):
    model = Tblbrands
    fields = "__all__"
    template_name = "model_information/brand_create.html"
    permission_required = "assets.add_tblbrands"
    success_url_app_view = "model_information:brand_detail"

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()

            temp_group = super().get_temp_group
            if temp_group:
                extracted_json = temp_group.extracted_json
                merged_gs1_ai = extracted_json.setdefault('merged_gs1_ai', {})
                merged_gs1_ai['brandid'] = self.object.pk
                temp_group.save(update_fields=['extracted_json'])

            self.after_save(form)

        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if context.get("cancel_url", None) is None:
            context["cancel_url"] = reverse("model_information:brandlist")
        return context


class BrandDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Tblbrands
    context_object_name = "brand"
    template_name = "model_information/brand_detail.html"
    permission_required = "assets.view_tblbrands"


class BrandDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Tblbrands
    template_name = "model_information/brand_delete.html"
    permission_required = "assets.delete_tblbrands"
    success_url = reverse_lazy("model_information:brandlist")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse_lazy("model_information:brandlist")
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                delete_object_document_links(self.object)
                self.object.delete()
            return HttpResponseRedirect(self.success_url)

        except Exception as e:
            # Return an error message as plain text (not JSON)
            form.add_error(
                None,
                f"An error occurred while deleting the brand. Error Details: {str(e)}",
            )
            return self.form_invalid(form)


# model views
class FilteredModelTableView(
    LoginRequiredMixin, PermissionRequiredMixin, FilteredTableView
):
    model = Tblmodel 
    title = 'Models'
    paginate_by = 25
    open_column = 'modelid'
    permission_required = "assets.view_tblmodel"
    universal_search_fields = [
        "modelname__icontains",
        "brandid__brandname__icontains" 
    ]

    actions = [
        TableAction(
            name='Add',
            type='link',
            on_selectable_items = False, 
            url=reverse_lazy('model_information:create_model'),
            permission='assets.add_tblmodel',
            icon='bi-plus',
            color='outline-secondary'
        ),
    ]

class ModelUpdateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    TempUploadMixin,
    UpdateView,
):
    model = Tblmodel
    form_class = ModelUpdateForm
    template_name = "model_information/model_update.html"
    permission_required = "assets.change_tblmodel"
    success_url_app_view = "model_information:model_view"
    initial_mapper = "update_model"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if context.get("cancel_url", None) is None:
            context["cancel_url"] = reverse(
                "model_information:model_view", kwargs={"pk": self.object.pk}
            )
        return context


class ModelBulkUpdateView(BulkUpdateView):
    context_object_name = "model"
    model = Tblmodel
    permission_required = "assets.change_tblmodel"
    form_class = ModelBulkUpdateForm
    summary_field_names = None
    success_url = reverse_lazy("model_information:modellist")


class ModelCreateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    TempUploadMixin,
    CreateView,
):
    model = Tblmodel
    form_class = ModelCreateForm
    template_name = "model_information/partials/model_create.html"
    permission_required = "assets.add_tblmodel"
    initial_mapper = "create_model"
    success_url_app_view = "model_information:model_view"

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            self.after_save(form)

        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if context.get("cancel_url", None) is None:
            context["cancel_url"] = reverse("model_information:modellist")

        return context

class ModelCopyView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    TempUploadMixin,
    FormView,
):
    model = Tblmodel
    form_class = ModelCopyForm
    template_name = "model_information/model_copy.html"
    permission_required = "assets.add_tblmodel"
    success_url_app_view = "model_information:model_view"
    initial_mapper = "create_model"

    def form_valid(self, form):
        model_id = self.request.POST.get('model_id', None)
        gtin = self.request.POST.get('gtin', None)
        model = Tblmodel.objects.filter(pk=model_id).first()
        if not gtin or not model:
            form.add(None, 'Copying not possbile, model or gtin missing')
            return self.form_invalid(form)

        model.pk = None
        model.gtin = gtin

        with transaction.atomic():
            model.save()
            self.object = model
            self.after_save(form)

        return HttpResponseRedirect(self.get_success_url())

    def get_initial(self):
        initial = super().get_initial()
        initial['model_id'] = self.kwargs.get('pk')
        return initial

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        model_id = self.kwargs.get('pk')
        context['model'] = Tblmodel.objects.filter(pk=model_id).first()

        if context.get("cancel_url", None) is None:
            context["cancel_url"] = reverse("model_information:modellist")

        return context

class ExistingModelListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Tblmodel
    permission_required = "assets.view_tblmodel"
    template_name = "model_information/partials/existing_model_list.html"
    context_object_name = "models"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["temp_group_id"] = self.request.GET.get("temp_group_id")
        context['search_term'] = self.request.GET.get("modelname")
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        search_term = self.request.GET.get("modelname")
        if search_term:
            queryset = queryset.filter(modelname__icontains=search_term).exclude()
            return queryset[:10]
        return None



class ModelDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Tblmodel
    template_name = "model_information/model_delete.html"
    permission_required = "assets.delete_tblmodel"
    success_url = reverse_lazy("model_information:modellist")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context.get("cancel_url", None) is None:
            context["cancel_url"] = reverse(
                "model_information:model_view", kwargs={"pk": self.object.pk}
            )
        return context

    def form_valid(self, form):
        self.object = self.get_object()

        try:
            with transaction.atomic():
                delete_object_document_links(self.object)
                self.object.delete()
            return HttpResponseRedirect(self.success_url)

        except ProtectedError:
            # Return an error message as plain text (not JSON)
            form.add_error(
                None,
                "Cannot delete model as it is still being used.",
            )
            return self.form_invalid(form)


class ModelDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Tblmodel
    template_name = "model_information/model_view.html"
    fields = "__all__"
    permission_required = "assets.view_tblmodel"


# category views
class FilteredCategoryTableView(
    LoginRequiredMixin, PermissionRequiredMixin, FilteredTableView
):
    model = Tblcategories
    title = 'Categories'
    paginate_by = 25
    permission_required = "assets.view_tblcategories"
    universal_search_fields = ["categoryname__icontains"]
    open_column = 'categoryname'
    default_columns = ["categoryid", "categoryname"]

    actions = [
        TableAction(
            name='Add',
            type='link',
            on_selectable_items = False, 
            url=reverse_lazy('model_information:create_category'),
            permission='assets.add_tblcategories',
            icon='bi-plus',
            color='outline-secondary'
        ),
    ]

class CategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Tblcategories
    fields = "__all__"
    template_name = "model_information/category_update.html"
    permission_required = "assets.change_tblcategories"

    def form_valid(self, form):
        self.object = form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "model_information:category_detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse(
            "model_information:category_detail", kwargs={"pk": self.object.pk}
        )
        return context


class CategoryCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, TempUploadMixin, CreateView
):
    model = Tblcategories
    fields = "__all__"
    template_name = "model_information/category_create.html"
    permission_required = "assets.add_tblcategories"
    success_url_app_view = "model_information:category_detail"


    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()

            temp_group = super().get_temp_group
            if temp_group:
                extracted_json = temp_group.extracted_json
                merged_gs1_ai = extracted_json.setdefault('merged_gs1_ai', {})
                merged_gs1_ai['categoryid'] = self.object.pk
                temp_group.save(update_fields=['extracted_json'])

            self.after_save(form)

        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context.get("cancel_url", None) is None:
            context["cancel_url"] = reverse("model_information:categorylist")
        return context


class CategoryDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Tblcategories
    template_name = "model_information/category_detail.html"
    context_object_name = "category"
    permission_required = "assets.view_tblcategories"
    context_object_name = "category"


class CategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Tblcategories
    template_name = "model_information/category_delete.html"
    permission_required = "assets.delete_tblcategories"
    success_url = reverse_lazy("model_information:categorylist")
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context.get("cancel_url", None) is None:
            context["cancel_url"] = reverse("model_information:categorylist")
        return context

    def form_valid(self, form):
        self.object = self.get_object()
        success_url = self.get_success_url()
        try:
            with transaction.atomic():
                delete_object_document_links(self.object)
                self.object.delete()
            return HttpResponseRedirect(success_url)

        except Exception as e:
            # Return an error message as plain text (not JSON)
            form.add_error(None, str("Category could not be deleted."))
            return self.form_invalid(form)


class ChecklistsTable(tables.Table):
    Actions = columns.TemplateColumn(
        template_name="model_information/tables/checklist_buttons.html",  # Path to your button template
        verbose_name="Actions",
        orderable=False,
    )  # Prevent sorting on this column

    class Meta:
        model = Tblcheckslists
        attrs = {
            "class": "table table-hover table-bordered table-striped  ",
            "thead": {
                "class": "table-bordered align-middle",
            },
        }
        template_name = "tables/tables2_with_filter.html"
        fields = ("testid", "modelid", "testname", "test_description")


class ChecklistsTableView(
    LoginRequiredMixin, PermissionRequiredMixin, SingleTableMixin, ListView
):
    model = Tblcheckslists
    table_class = ChecklistsTable
    template_name = "model_information/partials/checklist.html"
    paginate_by = 20
    permission_required = "assets.view_tblcheckslists"

    def get_queryset(self):
        queryset = super().get_queryset()
        modelid = self.request.GET.get("modelid")
        if modelid:
            queryset = queryset.filter(modelid=int(modelid))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        modelid = self.request.GET.get("modelid")
        if modelid:
            context["model"] = Tblmodel.objects.get(
                modelid=self.request.GET.get("modelid")
            )
        return context


class CheckUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Tblcheckslists
    fields = "__all__"
    template_name = "model_information/partials/modal.html"
    success_url = reverse_lazy("model_information:checklist")
    permission_required = "assets.change_tblcheckslists"

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            # Return empty 204 response so HTMX knows it's successful
            return HttpResponse(status=204)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Check"
        context["view_type"] = "update"
        return context


class CheckDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Tblcheckslists
    template_name = "model_information/partials/modal.html"
    permission_required = "assets.delete_tblcheckslists"
    success_url = reverse_lazy("model_information:checklist")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Test"
        context["check"] = Tblcheckslists.objects.get(pk=self.kwargs.get("pk"))

        context["view_type"] = "delete"
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            with transaction.atomic():
                delete_object_document_links(self.object)
                self.object.delete()

            if self.request.htmx:
                return HttpResponse(status=204)
            return HttpResponseRedirect(self.get_success_url())

        except Exception as e:
            # Return an error message as plain text (not JSON)
            context = self.get_context_data()
            context["error_message"] = (
                f"An error occurred while deleting the test. Error Details: {str(e)}"
            )
            return self.render_to_response(context)


class CheckCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Tblcheckslists
    fields = "__all__"
    template_name = "model_information/partials/modal.html"
    permission_required = "assets.add_tblcheckslists"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["modelid"] = self.request.GET.get("modelid")
        context["title"] = "Create New Test"
        context["view_type"] = "create"
        return context

    def get_initial(self):
        """Set a default value for the 'assetid' field using a query parameter"""
        initial = super().get_initial()
        initial["modelid"] = self.request.GET.get("modelid")  # Set default
        return initial

    def get_success_url(self):
        return reverse("model_information:checklist")

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            # Return empty 204 response so HTMX knows it's successful
            return HttpResponse(status=204)
        return super().form_valid(form)


# -------------
# configuration
# -------------

SOFTWARE_SEARCH_FIELDS = [
    "brand",
    "name",
    "part_number",
]


class SoftwareFilterView(
    LoginRequiredMixin, PermissionRequiredMixin, FilteredTableView
):
    paginate_by = 25
    title = 'Software'
    permission_required = "model_information.view_software"
    model = Software
    table_class = None
    open_column = 'id'
    universal_search_fields = SOFTWARE_SEARCH_FIELDS
    default_columns = [
        "brand",
        "name",
        "version",
        "release_date",
        "software_type_id",
    ]
    actions = [
        TableAction(
            name='Add',
            type='link',
            on_selectable_items = False, 
            url=reverse_lazy('model_information:software_create'),
            permission='model_information.add_software',
            icon='bi-plus',
            color='outline-secondary'
        ),
    ]


class SoftwareDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = "model_information.view_software"
    model = Software
    template_name = "model_information/software_detail.html"
    context_object_name = "software"


class SoftwareCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "model_information.add_software"
    model = Software
    fields = "__all__"
    template_name = "model_information/software_create.html"
    context_object_name = "software"

    def get_success_url(self):
        return reverse(
            "model_information:software_detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse("model_information:softwares")
        return context


class AddNewSoftwareVersion(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    permission_required = "model_information.add_software"
    template_name = "model_information/software_add_version.html"
    form_class = AddNewSoftwareVersionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        software_id = self.kwargs.get("pk")
        context["software"] = Software.objects.get(pk=software_id)
        return context

    def form_valid(self, form):
        software_id = self.kwargs.get("pk")
        new_version = form.cleaned_data["new_version"]
        software = Software.objects.get(pk=software_id)
        try:
            self.object = add_new_software_version(software, new_version)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            "model_information:software_detail", kwargs={"pk": self.object.pk}
        )


class SoftwareUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "model_information.change_software"
    model = Software
    fields = "__all__"
    template_name = "model_information/software_update.html"
    context_object_name = "software"

    def get_success_url(self):
        return reverse(
            "model_information:software_detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse(
            "model_information:software_detail", kwargs={"pk": self.object.pk}
        )
        return context


class SoftwareDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "model_information.delete_software"
    model = Software
    template_name = "model_information/software_delete.html"
    context_object_name = "software"
    success_url = reverse_lazy("model_information:softwares")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse(
            "model_information:software_detail", kwargs={"pk": self.object.pk}
        )
        return context


class SoftwareModelCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "model_information.add_softwaremodel"
    model = SoftwareModel
    fields = "__all__"
    template_name = "model_information/software_model_create.html"

    def get_initial(self):
        initial = super().get_initial()
        initial.update(**self.request.GET)
        return initial

    def get_success_url(self):
        return reverse(
            "model_information:software_detail", kwargs={"pk": self.object.software.pk}
        )


class SoftwareModelDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "model_information.delete_softwaremodel"
    model = SoftwareModel
    fields = "__all__"
    template_name = "model_information/software_model_delete.html"
    context_object_name = "software_model"

    def get_success_url(self):
        return reverse(
            "model_information:software_detail", kwargs={"pk": self.object.software.pk}
        )


SOFTWARE_SEARCH_FIELDS = [
    "brand",
    "name",
]


class ConfigurationFilterView(
    LoginRequiredMixin, PermissionRequiredMixin, FilteredTableView
):
    paginate_by = 25
    title = 'Configuration'
    permission_required = "model_information.view_equipmentconfiguration"
    model = EquipmentConfiguration
    table_class = None
    open_column = 'id'
    universal_search_fields = SOFTWARE_SEARCH_FIELDS
    default_columns = [
        "brand",
        "configuration_status",
        "version",
    ]
    actions = [
        TableAction(
            name='Add',
            type='link',
            on_selectable_items = False, 
            url=reverse_lazy('model_information:configuration_create'),
            permission='model_information.add_equipmentconfiguration',
            icon='bi-plus',
            color='outline-secondary'
        ),
    ]


class ConfigurationDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = "model_information.view_equipmentconfiguration"
    model = EquipmentConfiguration
    template_name = "model_information/configuration_detail.html"
    context_object_name = "config"


class ConfigurationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "model_information.add_equipmentconfiguration"
    model = EquipmentConfiguration
    fields = "__all__"
    template_name = "model_information/configuration_create.html"
    context_object_name = "config"

    def get_success_url(self):
        return reverse(
            "model_information:configuration_detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse("model_information:configuration_create")
        return context


class AddNewConfigVersion(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    permission_required = "model_information.add_equipmentconfiguration"
    template_name = "model_information/configuration_add_version.html"
    form_class = AddNewConfigVersionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config_id = self.kwargs.get("pk")
        context["config"] = EquipmentConfiguration.objects.get(pk=config_id)
        return context

    def form_valid(self, form):
        config_id = self.kwargs.get("pk")
        self.object = EquipmentConfiguration.objects.get(pk=config_id)
        try:
            self.object = create_new_config_version(self.object)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            "model_information:configuration_detail", kwargs={"pk": self.object.pk}
        )


class ConfigurationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "model_information.change_equipmentconfiguration"
    model = EquipmentConfiguration
    fields = "__all__"
    template_name = "model_information/configuration_update.html"
    context_object_name = "config"

    def get_success_url(self):
        return reverse(
            "model_information:configuration_detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse(
            "model_information:configuration_detail", kwargs={"pk": self.object.pk}
        )
        return context


class ConfigurationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "model_information.delete_equipmentconfiguration"
    model = EquipmentConfiguration
    fields = "__all__"
    template_name = "model_information/configuration_delete.html"
    context_object_name = "config"
    success_url = reverse_lazy("model_information:configurations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse(
            "model_information:configuration_detail", kwargs={"pk": self.object.pk}
        )
        return context


class ConfigurationModelCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    permission_required = "model_information.add_equipmentconfigurationmodel"
    model = EquipmentConfigurationModel
    fields = "__all__"
    template_name = "model_information/configuration_model_create.html"

    def get_initial(self):
        initial = super().get_initial()
        initial.update(**self.request.GET)
        return initial

    def get_success_url(self):
        return reverse(
            "model_information:configuration_detail",
            kwargs={"pk": self.object.configuration.pk},
        )


class ConfigurationModelDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    permission_required = "model_information.delete_equipmentconfigurationmodel"
    model = EquipmentConfigurationModel
    fields = "__all__"
    template_name = "model_information/configuration_model_delete.html"
    context_object_name = "config_model"

    def get_success_url(self):
        return reverse(
            "model_information:configuration_detail",
            kwargs={"pk": self.object.configuration.pk},
        )


class ConfigurationScopeCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    permission_required = "model_information.add_equipmentconfigurationscope"
    model = EquipmentConfigurationScope
    form_class = ConfigurationScopeCreateForm
    template_name = "model_information/configuration_scope_create.html"
    context_object_name = "scope"

    def get_initial(self):
        initial = super().get_initial()
        initial.update(**self.request.GET)
        return initial

    def get_success_url(self):
        return reverse(
            "model_information:configuration_detail",
            kwargs={"pk": self.object.configuration.pk},
        )


class ConfigurationScopeDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    permission_required = "model_information.delete_equipmentconfigurationscope"
    model = EquipmentConfigurationScope
    fields = "__all__"
    template_name = "model_information/configuration_scope_delete.html"
    context_object_name = "scope"

    def get_success_url(self):
        return reverse(
            "model_information:configuration_detail",
            kwargs={"pk": self.object.configuration.pk},
        )
