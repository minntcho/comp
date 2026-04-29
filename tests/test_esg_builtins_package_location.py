from esg_builtins import register_default_builtins as legacy_register_default_builtins
from esg_builtins import site_alias as legacy_site_alias

from comp.builtins.esg import register_default_builtins as package_register_default_builtins
from comp.builtins.esg import site_alias as package_site_alias


def test_esg_builtins_wrapper_matches_package_module():
    assert legacy_register_default_builtins is package_register_default_builtins
    assert legacy_site_alias is package_site_alias
