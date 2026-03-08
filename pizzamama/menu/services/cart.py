from decimal import Decimal, InvalidOperation


PANIER_SESSION_KEY = "panier"
TWOPLACES = Decimal("0.01")


def _coerce_price(value):
    try:
        return Decimal(str(value)).quantize(TWOPLACES)
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0.00")


def _coerce_quantity(value):
    try:
        quantity = int(value)
    except (TypeError, ValueError):
        return 0
    return max(quantity, 0)


def save_cart(session, cart):
    session[PANIER_SESSION_KEY] = cart
    session.modified = True


def get_cart(session, *, persist=False):
    raw_cart = session.get(PANIER_SESSION_KEY, {})
    cart = {}

    for key, item in raw_cart.items():
        if not isinstance(item, dict):
            continue

        quantity = _coerce_quantity(item.get("quantite"))
        if quantity <= 0:
            continue

        cart[str(key)] = {
            "nom": (str(item.get("nom") or "Pizza")).strip() or "Pizza",
            "prix": str(_coerce_price(item.get("prix"))),
            "quantite": quantity,
        }

    if persist and cart != raw_cart:
        save_cart(session, cart)

    return cart


def get_cart_lines(cart):
    lines = []
    for pizza_id, item in cart.items():
        price = _coerce_price(item.get("prix"))
        quantity = _coerce_quantity(item.get("quantite"))
        if quantity <= 0:
            continue

        line_total = (price * quantity).quantize(TWOPLACES)
        lines.append(
            {
                "id": str(pizza_id),
                "nom": item.get("nom", "Pizza"),
                "prix": price,
                "quantite": quantity,
                "line_total": line_total,
            }
        )

    return lines


def build_cart_context(session):
    cart = get_cart(session, persist=True)
    lines = get_cart_lines(cart)
    total = sum((line["line_total"] for line in lines), Decimal("0.00")).quantize(TWOPLACES)
    count = sum(line["quantite"] for line in lines)

    return {
        "panier": cart,
        "panier_lignes": lines,
        "total": total,
        "panier_count": count,
    }


def add_pizza_to_cart(session, pizza):
    cart = get_cart(session, persist=True)
    key = str(pizza.id)

    if key in cart:
        cart[key]["quantite"] += 1
    else:
        cart[key] = {
            "nom": pizza.nom,
            "prix": str(_coerce_price(pizza.prix)),
            "quantite": 1,
        }

    save_cart(session, cart)
    return cart


def decrease_pizza_quantity(session, pizza_id):
    cart = get_cart(session, persist=True)
    key = str(pizza_id)

    if key in cart:
        cart[key]["quantite"] -= 1
        if cart[key]["quantite"] <= 0:
            del cart[key]
        save_cart(session, cart)

    return cart


def remove_pizza_from_cart(session, pizza_id):
    cart = get_cart(session, persist=True)
    key = str(pizza_id)

    if key in cart:
        del cart[key]
        save_cart(session, cart)

    return cart


def clear_cart(session):
    save_cart(session, {})
