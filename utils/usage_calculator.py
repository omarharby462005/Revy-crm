import logging

logger = logging.getLogger(__name__)


# Token pricing (USD)
FLASH_INPUT_COST_PER_TOKEN = 0.25 / 1_000_000
FLASH_OUTPUT_COST_PER_TOKEN = 1.5 / 1_000_000


def calc_total_usage(result: dict) -> dict:
    """
    Calculate total token usage and estimated cost
    across all LLM nodes: booking, direct, and sales.
    """

    nodes = [
        ("booking_usage", result.get("booking_usage")),
        ("direct_usage", result.get("direct_usage")),
        ("sales_usage", result.get("sales_usage")),
    ]

    total_input_tokens = 0
    total_output_tokens = 0
    total_tokens = 0
    total_cost_usd = 0.0

    breakdown = {}

    for node_key, node_usage in nodes:

        if not node_usage:
            continue

        try:
            input_tokens = int(
                node_usage.get("input_tokens", 0) or 0
            )

            output_tokens = int(
                node_usage.get("output_tokens", 0) or 0
            )

            node_total_tokens = int(
                node_usage.get("total_tokens", 0)
                or (input_tokens + output_tokens)
            )

        except (TypeError, ValueError):
            logger.exception(
                "Invalid token usage in node: %s",
                node_key
            )
            continue

        if not (input_tokens or output_tokens or node_total_tokens):
            continue

        # Calculate node cost
        node_cost = (
            input_tokens * FLASH_INPUT_COST_PER_TOKEN
            + output_tokens * FLASH_OUTPUT_COST_PER_TOKEN
        )

        # Store individual node usage
        breakdown[node_key] = {
            "input": input_tokens,
            "output": output_tokens,
            "total": node_total_tokens,
            "cost_usd": node_cost,
        }

        # Calculate total usage
        total_input_tokens += input_tokens
        total_output_tokens += output_tokens
        total_tokens += node_total_tokens
        total_cost_usd += node_cost

    total_cost_cents = total_cost_usd * 100

    req_per_dollar = (
        int(1.0 / total_cost_usd)
        if total_cost_usd > 0
        else 0
    )

    return {
        "breakdown": breakdown,
        "total_input": total_input_tokens,
        "total_output": total_output_tokens,
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost_usd,
        "total_cost_cents": total_cost_cents,
        "req_per_dollar": req_per_dollar,
    }


def check_and_alert_high_token_usage(
    usage: dict,
    context: dict = None,
    threshold: int = 40000
) -> bool:
    """
    Send a production alert when total token consumption
    reaches or exceeds the specified threshold.
    """

    if not usage or not isinstance(usage, dict):
        return False

    total_tokens = usage.get("total_tokens", 0)

    if total_tokens < threshold:
        return False

    try:
        from notification_center import send_production_alert

        alert_context = {
            "total_tokens": f"{total_tokens:,}",
            "total_input": f"{usage.get('total_input', 0):,}",
            "total_output": f"{usage.get('total_output', 0):,}",
            "estimated_cost_usd": (
                f"${usage.get('total_cost_usd', 0.0):.4f}"
            ),
            "token_threshold": f"{threshold:,}",
        }

        if context and isinstance(context, dict):
            alert_context.update(context)

        send_production_alert(
            subject=(
                f"High LLM Token Consumption Alert "
                f"({total_tokens:,} Tokens)"
            ),
            body_or_error=(
                f"A request execution consumed "
                f"{total_tokens:,} LLM tokens, "
                f"reaching or exceeding the alert threshold "
                f"of {threshold:,} tokens."
            ),
            context=alert_context,
            level="WARNING",
        )

        logger.warning(
            "[HighTokenAlert] Threshold reached "
            "(%d >= %d) | Alert sent",
            total_tokens,
            threshold
        )

        return True

    except Exception as err:
        logger.exception(
            "[HighTokenAlert] Failed to send alert: %s",
            err
        )

        return False