from . import models
# pylint: disable=W0612

def post_load():
    # use post_load to avoid overriding
    # _get_search_domain when this module is not installed
    from . import controllers
