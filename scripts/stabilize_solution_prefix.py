import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SOLUTION_NAME = "ppdemo_ReleaseRadar"
PUBLISHER_NAME = "ppdemo"
CUSTOMIZATION_PREFIX = "ppdemo"
OPTION_VALUE_PREFIX = "11411"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: stabilize_solution_prefix.py <path-to-Solution.xml>")

    solution_path = Path(sys.argv[1])
    tree = ET.parse(solution_path)
    manifest = tree.find("./SolutionManifest")
    publisher = manifest.find("./Publisher") if manifest is not None else None

    if manifest is None or manifest.findtext("./UniqueName") != SOLUTION_NAME:
        raise ValueError(f"Unexpected solution manifest in {solution_path}")
    if publisher is None or publisher.findtext("./UniqueName") != PUBLISHER_NAME:
        raise ValueError(f"Unexpected publisher in {solution_path}")
    if publisher.findtext("./CustomizationPrefix") != CUSTOMIZATION_PREFIX:
        raise ValueError(f"Unexpected customization prefix in {solution_path}")
    if publisher.find("CustomizationOptionValuePrefix") is None:
        raise ValueError(f"Missing option-value prefix in {solution_path}")

    content = solution_path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"(<CustomizationOptionValuePrefix>\s*)\d+(\s*</CustomizationOptionValuePrefix>)"
    )
    content, replacements = pattern.subn(
        rf"\g<1>{OPTION_VALUE_PREFIX}\g<2>", content
    )
    if replacements != 1:
        raise ValueError(
            f"Expected one option-value prefix in {solution_path}, found {replacements}"
        )

    solution_path.write_text(content, encoding="utf-8", newline="")
    verified = ET.parse(solution_path)
    verified_publisher = verified.find("./SolutionManifest/Publisher")
    if (
        verified_publisher is None
        or verified_publisher.findtext("./CustomizationOptionValuePrefix")
        != OPTION_VALUE_PREFIX
    ):
        raise ValueError(f"Failed to set stable option-value prefix in {solution_path}")

    print(
        f"Publisher {PUBLISHER_NAME} option-value prefix: {OPTION_VALUE_PREFIX}"
    )


if __name__ == "__main__":
    main()
