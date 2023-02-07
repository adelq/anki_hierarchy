"""
Convert Subdecks to Tag Hierarchy (Anki Add-on)

Provides a new menu entry to convert the currently active deck's subdecks into
a tag hierarchy.

Copyright (c) 2017 Adel Qalieh <https://adelqalieh.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or any later
version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import re
if __name__ != "__main__":
    from aqt import mw
    from aqt.operations import CollectionOp
    from aqt.qt import QAction
    from aqt.utils import tooltip
    from anki.collection import OpChangesWithCount
    from anki.utils import int_time, ids2str
    from .config import get_user_option


def reformat_title(deck_name, separator="-"):
    """Convert deck name with spaces to compatible and clean Anki tag name"""
    # Replace spaces with separator (dashes) to avoid making multiple tags
    tag = deck_name.replace(" ", separator)
    tag = re.sub("%s+" % separator, separator, tag)
    # Remove apostrophes
    tag = tag.replace("'", "")
    # Remove trailing spaces
    tag = re.sub(r"-+::", "::", tag)
    tag = re.sub(r"::-+", "::", tag)
    # Remove spaces after commas
    tag = tag.replace(",-", ",")
    # Remove spaces around + signs
    tag = tag.replace("-+", "+")
    tag = tag.replace("+-", "+")
    return tag


def background_add_tags(col):
    """Main function to convert currently selected deck."""
    parent_deck_id = mw.col.decks.selected()
    children_decks = mw.col.decks.children(parent_deck_id)
    separator = get_user_option("Separator", "-")
    count = 0
    for child_deck_name, child_deck_id in children_decks:
        # Reformat deck title into an appropriate tag
        tag = reformat_title(child_deck_name, separator)
        child_cids = mw.col.decks.cids(child_deck_id)
        child_cards = (mw.col.get_card(cid) for cid in child_cids)
        child_nids = set(c.nid for c in child_cards)
        mw.col.tags.bulk_add(list(child_nids), tag)
        count += len(child_nids)

    return OpChangesWithCount(count=count)


def background_move_cards(col):
    count = 0
    parent_deck_id = mw.col.decks.selected()
    children_decks = mw.col.decks.children(parent_deck_id)
    for _, child_deck_id in children_decks:
        child_cids = mw.col.decks.cids(child_deck_id)
        mw.col.set_deck(card_ids=child_cids, deck_id=parent_deck_id)
        count += len(child_cids)
    mw.col.decks.remove([deck_id for _, deck_id in children_decks])
    return OpChangesWithCount(count=count)


def on_success(changes):
    tooltip(f"{changes.count} notes tagged with deck name")

    # Move cards to new deck if config option set
    if get_user_option("Merge decks", False):
        CollectionOp(
            parent=mw,
            op=background_move_cards
        ).success(lambda c: tooltip(f"Moved {c.count} cards to main deck")).run_in_background()


def convert_subdecks_to_tags():
    CollectionOp(parent=mw, op=background_add_tags).success(on_success).run_in_background()


# Add menu item
if __name__ != "__main__":
    action = QAction("Convert subdecks to tags", mw)
    action.triggered.connect(convert_subdecks_to_tags)
    mw.form.menuTools.addAction(action)

# Testing for tag cleanup
if __name__ == "__main__":
    import unittest

    class TestReformatTitle(unittest.TestCase):
        def test_reformat_title_basic(self):
            assert reformat_title("zanki step decks") == "zanki-step-decks"
            assert reformat_title("zanki::cardio path") == "zanki::cardio-path"

        def test_reformat_title_punctuation(self):
            assert reformat_title("molecular, cellular") == "molecular,cellular"
            assert reformat_title("physiology + embryo") == "physiology+embryo"

        def test_runs_separator(self):
            assert reformat_title("OBGYN- uWISE") == "OBGYN-uWISE"
            assert reformat_title("Medicine - Case") == "Medicine-Case"

    unittest.main()
