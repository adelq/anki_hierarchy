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
    from anki.utils import intTime, ids2str
    from anki.lang import _
    from aqt.qt import QAction
    from .config import get_user_option

SEPARATOR = get_user_option("Separator", "-")


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


def convert_subdecks_to_tags():
    """Main function to convert currently selected deck."""
    parent_deck_id = mw.col.decks.selected()
    children_decks = mw.col.decks.children(parent_deck_id)
    mw.checkpoint(_("convert subdeck to tags"))
    for child_deck_name, child_deck_id in children_decks:
        # Reformat deck title into an appropriate tag
        tag = reformat_title(child_deck_name, SEPARATOR)

        # Get old card properties
        child_cids = mw.col.decks.cids(child_deck_id)
        mod = intTime()
        usn = mw.col.usn()
        str_cids = ids2str(child_cids)

        # Move cards to new deck if config option set
        if get_user_option("Merge decks", False):
            mw.col.db.execute(
                "update cards set usn=?, mod=?, did=? where id in " + str_cids,
                usn, mod, parent_deck_id
            )
            mw.col.decks.rem(child_deck_id)

        # New tag based on child deck name
        child_cards = (mw.col.getCard(cid) for cid in child_cids)
        child_nids = set(c.nid for c in child_cards)
        mw.col.tags.bulkAdd(list(child_nids), tag)
    mw.requireReset()


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
