queryset_methods_to_patch = [
    'get', 'create', 'get_or_create', 'update_or_create', 'bulk_create',
    'bulk_update', 'count', 'in_bulk', 'iterator', 'latest', 'earliest',
    'first', 'last', 'aggregate', 'exists', 'contains', 'update', 'delete',
    'as_manager', 'explain', 'all',
]

model_methods_to_patch = ['save', 'delete', 'full_clean']
