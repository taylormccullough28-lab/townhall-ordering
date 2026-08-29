"""Vendor-specific behaviour, encoded from the order guide.

These are the pieces of institutional knowledge that currently live in one
person's head:

* **Arena Liquor** takes orders by email only. The system will not produce a
  phone or text script for Arena, and Gursev's number appears only under an
  explicit emergency label.
* **OYO Vodka** always routes to Arena. Zack's number stays hidden unless the
  manager marks Arena out of stock.
* **Sixth City and Cavalier** rotate. Output is a style-and-count
  recommendation, never a SKU.
* **Southern Glazer's** Wednesday follow-up is offered only when the Tuesday
  order will not cover, and is flagged "confirm with Bethany first".
* **Superior** has two windows; the second is recommended only when a four-day
  cover meaningfully shrinks the order.
* **Heidelberg's** delivery note rides on the receiving checklist.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING

from ..catalog.models import Contact, Vendor

if TYPE_CHECKING:  # pragma: no cover
    from .engine import OrderEngine, VendorOrder


def apply_vendor_rules(
    engine: "OrderEngine",
    order: "VendorOrder",
    *,
    at: datetime,
    calendar: dict[date, object] | None = None,
    on_hand: dict[str, float] | None = None,
    on_order: dict[str, float] | None = None,
    counted_at: datetime | None = None,
    overrides: dict[str, int] | None = None,
) -> None:
    """Rewrite a raw order in place according to the vendor's rules."""
    rules = order.vendor.rules
    if rules.style_only:
        _apply_style_only(order)
    if rules.email_only:
        order.notes.append(
            f"Email only. Send to {rules.order_email}. Do not call or text this vendor."
        )
    if rules.delivery_note:
        order.notes.append(f"Receiving: {rules.delivery_note}")
    if rules.keg_return_required:
        order.notes.append("Empty keg return count is required before this delivery can be received.")
    for note in rules.notes:
        order.notes.append(" ".join(note.split()))

    if order.vendor.key == "superior":
        _recommend_superior_window(engine, order, at=at, calendar=calendar, on_hand=on_hand,
                                   on_order=on_order, counted_at=counted_at, overrides=overrides)
    if order.vendor.key == "southern_glazers":
        _offer_southern_glazers_followup(order)


def _apply_style_only(order: "VendorOrder") -> None:
    """Collapse SKU lines into a style-and-count recommendation."""
    from .engine import StyleRecommendation

    rules = order.vendor.rules
    total_units = sum(line.final_packs for line in order.lines)
    styles = sorted({line.product.style for line in order.lines if line.product.style})
    contact = order.vendor.contact.name if order.vendor.contact else "the rep"
    order.style_recommendations.append(
        StyleRecommendation(
            vendor_key=order.vendor.key,
            count=int(total_units),
            unit=rules.style_unit or "keg",
            styles=styles,
            ask=f"ask {contact} what's available",
            reasoning=[line.reasoning for line in order.lines],
        )
    )
    order.notes.append(
        "Rotating line: no specific SKU is suggested. The count comes from forecast depletion; "
        "the styles are a preference, not an order."
    )
    order.lines = []


def _recommend_superior_window(
    engine: "OrderEngine",
    order: "VendorOrder",
    *,
    at: datetime,
    calendar,
    on_hand,
    on_order,
    counted_at,
    overrides,
) -> None:
    """Compare a 7-day cover against a 4-day cover and recommend accordingly."""
    if order.plan.optional_windows_used:
        return
    alternative = engine.suggest_vendor(
        order.vendor.key,
        at=at,
        on_hand=on_hand,
        on_order=on_order,
        calendar=calendar,
        include_optional_windows=True,
        counted_at=counted_at,
        overrides=overrides,
        _skip_vendor_rules=True,
    )
    single = sum(line.order_units for line in order.lines)
    both = sum(line.order_units for line in alternative.lines)
    reduction = (single - both) / single if single else 0.0
    threshold = engine.config.superior_second_window_threshold
    order.window_recommendation = {
        "sunday_only_units": round(single, 2),
        "sunday_only_days_of_cover": order.plan.days_of_cover,
        "sunday_plus_thursday_units": round(both, 2),
        "sunday_plus_thursday_days_of_cover": alternative.plan.days_of_cover,
        "reduction_fraction": round(reduction, 4),
        "threshold": threshold,
        "recommend_second_window": reduction >= threshold,
    }
    if reduction >= threshold:
        order.notes.append(
            f"Use the Thursday window as well: ordering to Friday instead of next Monday cuts "
            f"this order by {reduction:.0%}."
        )
    else:
        order.notes.append(
            f"Sunday order only. The Thursday window would cut this order by just "
            f"{reduction:.0%}, under the {threshold:.0%} threshold."
        )


def _offer_southern_glazers_followup(order: "VendorOrder") -> None:
    """Offer the Wednesday follow-up when Tuesday's order will not cover.

    "Will not cover" is concrete: a line whose need was capped (by a per-delivery
    maximum or a manager override) leaves the bar short before the next Tuesday
    delivery. Rounding up to pack size means an uncapped line always covers, so
    the offer fires exactly when there is a real shortfall.
    """
    shortfalls = []
    for line in order.lines:
        required = line.reasoning.need_units
        supplied = line.final_packs * line.product.pack_size
        if required - supplied > 1e-9:
            shortfalls.append(
                {
                    "product": line.product.key,
                    "name": line.product.name,
                    "short_units": round(required - supplied, 4),
                    "reason": "capped" if line.reasoning.caps else "manager override",
                }
            )
    if not shortfalls:
        order.follow_up_offer = {
            "offered": False,
            "reason": "The Tuesday order covers to the next Tuesday delivery.",
        }
        return

    window = next(
        (w for w in order.vendor.windows if w.optional and w.requires_confirmation), None
    )
    order.follow_up_offer = {
        "offered": True,
        "window": window.key if window else None,
        "confirm_with": (window.confirm_with if window else None) or "Bethany",
        "flag": "confirm with Bethany first - not guaranteed",
        "shortfalls": shortfalls,
    }
    order.notes.append(
        "Tuesday's order will not cover to next Tuesday. A Wednesday follow-up is available - "
        "confirm with Bethany first, it is not guaranteed."
    )


@dataclass
class VendorOutput:
    """The message a manager actually sends, in this vendor's channel."""

    vendor_key: str
    channel: str
    subject: str | None
    body: str
    recipient: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "vendor": self.vendor_key,
            "channel": self.channel,
            "recipient": self.recipient,
            "subject": self.subject,
            "body": self.body,
        }


def render_order(order: "VendorOrder", *, arena_out_of_stock: bool = False) -> VendorOutput:
    """Render a vendor order into its sending channel.

    Args:
        order: The suggested order.
        arena_out_of_stock: Unlocks the OYO direct contact. It stays hidden
            otherwise, because the supplier agreement routes OYO through Arena.

    Returns:
        A :class:`VendorOutput`: an email body for Arena, copy-paste text for the
        phone and text vendors, a style recommendation for the rotating lines.
    """
    vendor = order.vendor
    rules = vendor.rules
    lines: list[str] = []

    header_date = order.plan.delivery.strftime("%A %b %d")
    lines.append(f"TownHall Columbus - order for delivery {header_date}")
    lines.append("")

    if order.style_recommendations:
        for recommendation in order.style_recommendations:
            lines.append(recommendation.text())
    for line in order.lines:
        if line.final_packs <= 0:
            continue
        lines.append(
            f"{line.final_packs} x {line.product.pack_label} {line.product.name}"
            + (f" ({line.product.pack_size:g} {line.product.unit_label})" if line.product.pack_size > 1 else "")
        )
    if len(lines) == 2:
        lines.append("(nothing to order this cycle)")

    if order.notes:
        lines.append("")
        lines.append("Notes:")
        lines.extend(f"- {note}" for note in order.notes)

    contact_line = _contact_line(vendor, arena_out_of_stock=arena_out_of_stock)
    if contact_line:
        lines.append("")
        lines.append(contact_line)

    body = "\n".join(lines)
    if rules.email_only:
        return VendorOutput(
            vendor_key=vendor.key,
            channel="email",
            subject=f"TownHall Columbus order - delivery {header_date}",
            body=body,
            recipient=rules.order_email,
        )
    return VendorOutput(
        vendor_key=vendor.key,
        channel=vendor.channel,
        subject=None,
        body=body,
        recipient=vendor.contact.phone if vendor.contact else None,
    )


def _contact_line(vendor: Vendor, *, arena_out_of_stock: bool) -> str | None:
    rules = vendor.rules
    if rules.email_only:
        return f"Send to: {rules.order_email} (email only)"
    if rules.route_through:
        if rules.routed_contact_hidden_unless == "arena_out_of_stock" and not arena_out_of_stock:
            return (
                f"Order through {rules.route_through}. The direct contact stays hidden unless "
                "Arena is marked out of stock."
            )
        contact = vendor.contact
        if contact:
            return f"Arena out of stock - direct: {contact.name} {contact.phone}"
    contact = vendor.contact
    if contact and (contact.phone or contact.email):
        return f"Call: {contact.name or vendor.name} {contact.phone or contact.email}"
    return None


def emergency_contact(vendor: Vendor) -> Contact | None:
    """The emergency-only contact, never used for a routine order."""
    return vendor.rules.emergency_contact
