from siapp.views.views_common import set_language


def buyer_map_infotext(lang: str = "de"):
    set_language(lang)

    infotext_dictionary = {
        "map": _("buyer_map_map"),
        "customer": _("buyer_map_customer"),
        "growth": _("buyer_map_growth"),
        "num_of_plants": _("buyer_map_num_of_plants"),
    }
    return infotext_dictionary
