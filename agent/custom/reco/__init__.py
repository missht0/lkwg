from importlib import import_module

RECO_MODULES = ()


def register_all():
    for module_name in RECO_MODULES:
        import_module(f"custom.reco.{module_name}")
