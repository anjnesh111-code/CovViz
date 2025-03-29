import humanize

def format_number(num):
    """
    Format numbers with commas and handle large values gracefully.
    """
    try:
        return humanize.intcomma(int(num))
    except (ValueError, TypeError):
        return "N/A"

