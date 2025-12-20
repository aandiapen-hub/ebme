from django.db.models import ForeignKey
from collections import Counter


def data_summary2(model, qs, field_names=None):
    counts_by_column = {}
    # Only consider concrete local fields
    fields = [
        f
        for f in model._meta.get_fields()
        if f.concrete and not f.many_to_many and not f.auto_created
    ]
    for field in fields:
        name = field.attname  # e.g., "customer_id" or "status"
        values_qs = qs.values_list(name, flat=True)
        counts = Counter(values_qs)
        if isinstance(field, ForeignKey):
            related_model = model._meta.get_field(field.attname).remote_field.model
            related_objs = related_model.objects.filter(pk__in=counts.keys())
            id_to_name = {a.pk: str(a) for a in related_objs}
            summary = [
                {"pk": pk, "name": id_to_name.get(pk), "count": count}
                for pk, count in counts.items()
            ]
            counts_by_column[field.verbose_name] = summary

    return counts_by_column
