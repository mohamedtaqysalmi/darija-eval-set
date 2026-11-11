import re

import darija_eval_set


def test_version_is_semver_like() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", darija_eval_set.__version__)
