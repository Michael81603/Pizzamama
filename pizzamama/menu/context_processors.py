from menu.services.cart import build_cart_context


def cart_summary(request):
    cart_context = build_cart_context(request.session)
    return {
        "nav_cart_count": cart_context["panier_count"],
        "nav_cart_total": cart_context["total"],
        "nav_cart_has_items": cart_context["panier_count"] > 0,
    }
