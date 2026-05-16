from importlib import import_module

ACTION_MODULES = (
    "general",
    "auto_battle",
    "boss_battle",
    "rare_beast",
    "focus_energy",
    "sunflower",
    "clicker",
    "interception",
)


def register_all():
    for module_name in ACTION_MODULES:
        import_module(f"custom.action.{module_name}")
