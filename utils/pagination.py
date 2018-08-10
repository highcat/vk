# -*- coding: utf-8 -*-
#
# **Copied from django-el-pagination package.**
#
from django.conf import settings

# The default callable returns a sequence of pages producing Digg-style
# pagination, and depending on the settings below.
DEFAULT_CALLABLE_EXTREMES = getattr(
    settings, 'EL_PAGINATION_DEFAULT_CALLABLE_EXTREMES', 3)
DEFAULT_CALLABLE_AROUNDS = getattr(
    settings, 'EL_PAGINATION_DEFAULT_CALLABLE_AROUNDS', 2)
# Whether or not the first and last pages arrows are displayed.
DEFAULT_CALLABLE_ARROWS = getattr(
    settings, 'EL_PAGINATION_DEFAULT_CALLABLE_ARROWS', False)



def get_page_numbers(
        current_page, num_pages, extremes=DEFAULT_CALLABLE_EXTREMES,
        arounds=DEFAULT_CALLABLE_AROUNDS, arrows=DEFAULT_CALLABLE_ARROWS):
    """
    Default callable for page listing.
    Produce a Digg-style pagination.
    
    """
    page_range = range(1, num_pages + 1)
    pages = []
    if current_page != 1:
        if arrows:
            pages.append('first')
        pages.append('previous')

    # Get first and last pages (extremes).
    first = page_range[:extremes]
    pages.extend(first)
    last = page_range[-extremes:]

    # Get the current pages (arounds).
    current_start = current_page - 1 - arounds
    if current_start < 0:
        current_start = 0
    current_end = current_page + arounds
    if current_end > num_pages:
        current_end = num_pages
    current = page_range[current_start:current_end]

    # Mix first with current pages.
    to_add = current
    if extremes:
        diff = current[0] - first[-1]
        if diff > 1:
            pages.append(None)
        elif diff < 1:
            to_add = current[abs(diff) + 1:]
    pages.extend(to_add)

    # Mix current with last pages.
    if extremes:
        diff = last[0] - current[-1]
        to_add = last
        if diff > 1:
            pages.append(None)
        elif diff < 1:
            to_add = last[abs(diff) + 1:]
        pages.extend(to_add)

    if current_page != num_pages:
        pages.append('next')
        if arrows:
            pages.append('last')
    return pages
