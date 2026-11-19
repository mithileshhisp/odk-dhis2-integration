##pip install requests python-dotenv
import os
import re
import csv
import hashlib
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

#ODK_BASE_URL = os.getenv["ODK_BASE_URL"].rstrip("/")
ODK_BASE_URL = os.getenv("ODK_BASE_URL")
ODK_PROJECT_ID = os.getenv("ODK_PROJECT_ID", "15")
ODK_FORM_ID = os.getenv(
    "ODK_FORM_ID", "hbnc_hbyc_visit"
)
ODK_USERNAME = os.getenv("ODK_USERNAME")
ODK_PASSWORD = os.getenv("ODK_PASSWORD")


DHIS2_BASE_URL = os.getenv("DHIS2_BASE_URL").rstrip("/")
DHIS2_USERNAME = os.getenv("DHIS2_USERNAME")
DHIS2_PASSWORD = os.getenv("DHIS2_PASSWORD")

PROGRAM_UID = os.environ["DHIS2_PROGRAM_UID"]
PROGRAM_STAGE_UID = os.environ["DHIS2_PROGRAM_STAGE_UID"]
CATEGORY_COMBO_UID = os.environ[
    "DHIS2_DEFAULT_CATEGORY_COMBO_UID"
]

MAPPING_CSV = Path("odk_dhis2_field_mapping.csv")

# First run: generate the mapping template.
# After reviewing the CSV, set this to True.
CREATE_METADATA = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

odk = requests.Session()
odk.auth = (ODK_USERNAME, ODK_PASSWORD)
odk.headers.update({"Accept": "application/xml"})


dhis2 = requests.Session()
dhis2.auth = (DHIS2_USERNAME, DHIS2_PASSWORD)
dhis2.headers.update({"Accept": "application/json"})

# Fields that should always be ignored
IGNORED_FIELDS = {
    "__system",
}

# Fields that identify the child
ATTRIBUTE_KEYWORDS = {
    "child_uid",
    "child_id",
    "child_name",
    "date_of_birth",
    "gender",
}

# Visit-specific observations
DATA_ELEMENT_KEYWORDS = {
    "visit_date",
    "weight",
    "height",
    "temperature",
    "referral_required",
}


def classify_field(field):
    name = field["field_name"].lower()
    path = field["field_path"].lower()

    if name.startswith("__") or name in IGNORED_FIELDS:
        return "IGNORE"

    if name in ATTRIBUTE_KEYWORDS:
        return "ATTRIBUTE"

    if name in DATA_ELEMENT_KEYWORDS:
        return "DATA_ELEMENT"

    # Do not create unknown fields automatically.
    return "IGNORE"

# ------------------------------------------------------------
# HTTP helpers
# ------------------------------------------------------------

def odk_get_metadata():
    url = (
        f"{ODK_BASE_URL}/v1/projects/{ODK_PROJECT_ID}"
        f"/forms/{ODK_FORM_ID}.svc/$metadata"
    )
    response = odk.get(url, timeout=60)
    response.raise_for_status()
    return response.text


def dhis_get(path, params=None):
    response = dhis2.get(
        f"{DHIS2_BASE_URL}/api/{path.lstrip('/')}",
        params=params,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def dhis_post(path, payload):
    response = dhis2.post(
        f"{DHIS2_BASE_URL}/api/{path.lstrip('/')}",
        json=payload,
        timeout=60,
    )

    if not response.ok:
        raise RuntimeError(
            f"POST {path} failed: "
            f"{response.status_code} {response.text}"
        )

    return response


def dhis_patch(path, operations):
    response = dhis2.patch(
        f"{DHIS2_BASE_URL}/api/{path.lstrip('/')}",
        json=operations,
        headers={"Content-Type": "application/json-patch+json"},
        timeout=60,
    )

    if not response.ok:
        raise RuntimeError(
            f"PATCH {path} failed: "
            f"{response.status_code} {response.text}"
        )

    return response


# ------------------------------------------------------------
# ODK metadata parsing
# ------------------------------------------------------------

def local_name(tag):
    """Remove an XML namespace from a tag name."""
    return tag.rsplit("}", 1)[-1]


def parse_odk_fields(xml_text):
    """
    Return fields from the root Submissions entity and nested
    ComplexType groups.

    Repeat EntityTypes are not automatically mapped to a stage.
    """
    root = ET.fromstring(xml_text)

    complex_types = {}
    entity_types = {}

    for element in root.iter():
        kind = local_name(element.tag)

        if kind == "ComplexType":
            complex_types[element.attrib["Name"]] = element

        elif kind == "EntityType":
            entity_types[element.attrib["Name"]] = element

    if "Submissions" not in entity_types:
        raise ValueError(
            "Could not find EntityType named 'Submissions' "
            "in ODK metadata."
        )

    fields = []

    def visit_properties(container, prefix="", stack=None):
        stack = stack or set()

        for prop in container:
            if local_name(prop.tag) != "Property":
                continue

            name = prop.attrib.get("Name")
            type_name = prop.attrib.get("Type", "")

            if not name:
                continue

            if name == "__system" or name.startswith("__"):
                continue

            path = f"{prefix}.{name}" if prefix else name
            simple_type = type_name.rsplit(".", 1)[-1]

            if simple_type in complex_types:
                if simple_type in stack:
                    log.warning(
                        "Skipping recursive complex type: %s",
                        path,
                    )
                    continue

                visit_properties(
                    complex_types[simple_type],
                    prefix=path,
                    stack=stack | {simple_type},
                )
                continue

            fields.append({
                "field_path": path,
                "field_name": name,
                "odata_type": simple_type,
                "target": "",
                "value_type": infer_value_type(simple_type),
                "unique": "false",
            })

    visit_properties(entity_types["Submissions"])

    # Log repeat tables for separate design and mapping.
    repeats = sorted(
        name for name in entity_types
        if name != "Submissions"
    )
    if repeats:
        log.warning(
            "ODK repeat/other entity types found; "
            "map these separately: %s",
            ", ".join(repeats),
        )

    return fields


def infer_value_type(odata_type):
    """
    Initial suggestion only. Review value types in the CSV
    before creating metadata.
    """
    mapping = {
        "String": "TEXT",
        "Int16": "INTEGER",
        "Int32": "INTEGER",
        "Int64": "INTEGER",
        "Decimal": "NUMBER",
        "Double": "NUMBER",
        "Single": "NUMBER",
        "Boolean": "BOOLEAN",
        "Date": "DATE",
        "DateTimeOffset": "DATETIME",
        "DateTime": "DATETIME",
    }
    return mapping.get(odata_type, "TEXT")


# ------------------------------------------------------------
# Mapping template
# ------------------------------------------------------------

def write_mapping_template(fields):
    with MAPPING_CSV.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "field_path",
                "field_name",
                "odata_type",
                "target",
                "value_type",
                "unique",
            ],
        )
        writer.writeheader()
        writer.writerows(fields)

    log.info("Mapping template created: %s", MAPPING_CSV)


def load_mapping():
    with MAPPING_CSV.open(
        "r", newline="", encoding="utf-8-sig"
    ) as file:
        rows = list(csv.DictReader(file))

    for row in rows:
        row["target"] = (
            row.get("target") or ""
        ).strip().upper()

        row["value_type"] = (
            row.get("value_type") or "TEXT"
        ).strip().upper()

        row["unique"] = (
            row.get("unique") or "false"
        ).strip().lower()

    return rows


# ------------------------------------------------------------
# Stable codes and names
# ------------------------------------------------------------

def metadata_code(field_path, prefix):
    digest = hashlib.sha256(
        field_path.encode("utf-8")
    ).hexdigest()[:20].upper()

    return f"{prefix}_{digest}"


def make_name(field_path):
    name = re.sub(r"[._/]+", " ", field_path)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:230] or "ODK Field"


def make_short_name(name):
    return name[:50].strip() or "ODK Field"


# ------------------------------------------------------------
# Find existing metadata by stable code
# ------------------------------------------------------------

def find_by_code(endpoint, code, collection):
    result = dhis_get(
        endpoint,
        params={
            "filter": f"code:eq:{code}",
            "fields": "id,name,code,valueType",
            "paging": "false",
        },
    )
    objects = result.get(collection, [])

    if len(objects) > 1:
        raise RuntimeError(
            f"Multiple {collection} objects found for code {code}"
        )

    return objects[0] if objects else None


def ensure_tracked_entity_attribute(row):
    code = metadata_code(row["field_path"], "ODK_HBNCC_TEA")

    existing = find_by_code(
        "trackedEntityAttributes",
        code,
        "trackedEntityAttributes",
    )
    if existing:
        log.info(
            "Attribute exists: %s (%s)",
            existing["name"], existing["id"],
        )
        return existing["id"]

    payload = {
        "name": make_name(row["field_path"]),
        "shortName": make_short_name(
            make_name(row["field_path"])
        ),
        "code": code,
        "valueType": row["value_type"],
        "unique": row["unique"] == "true",
        "inherit": False,
    }

    dhis_post("trackedEntityAttributes", payload)

    created = find_by_code(
        "trackedEntityAttributes",
        code,
        "trackedEntityAttributes",
    )
    if not created:
        raise RuntimeError(
            f"Attribute creation succeeded but code "
            f"{code} could not be found afterward."
        )

    log.info(
        "Created tracked entity attribute: %s (%s)",
        created["name"], created["id"],
    )
    return created["id"]


def ensure_data_element(row):
    code = metadata_code(row["field_path"], "ODK_HBNCC_DE")

    existing = find_by_code(
        "dataElements",
        code,
        "dataElements",
    )
    if existing:
        log.info(
            "Data element exists: %s (%s)",
            existing["name"], existing["id"],
        )
        return existing["id"]

    payload = {
        "name": make_name(row["field_path"]),
        "shortName": make_short_name(
            make_name(row["field_path"])
        ),
        "code": code,
        "valueType": row["value_type"],
        "domainType": "TRACKER",
        "aggregationType": "NONE",
        "categoryCombo": {"id": CATEGORY_COMBO_UID},
    }

    dhis_post("dataElements", payload)

    created = find_by_code(
        "dataElements",
        code,
        "dataElements",
    )
    if not created:
        raise RuntimeError(
            f"Data element creation succeeded but code "
            f"{code} could not be found afterward."
        )

    log.info(
        "Created data element: %s (%s)",
        created["name"], created["id"],
    )
    return created["id"]


# ------------------------------------------------------------
# Link created metadata to the existing Tracker program/stage
# ------------------------------------------------------------

def link_attribute_to_program(attribute_uid):
    program = dhis_get(
        f"programs/{PROGRAM_UID}",
        params={
            "fields": "id,name,trackedEntityAttributes[id]"
        },
    )

    linked_ids = {
        item["id"]
        for item in program.get("trackedEntityAttributes", [])
    }

    if attribute_uid in linked_ids:
        log.info("Attribute already linked to program.")
        return

    dhis_patch(
        f"programs/{PROGRAM_UID}",
        [{
            "op": "add",
            "path": "/trackedEntityAttributes/-",
            "value": {"id": attribute_uid},
        }],
    )
    log.info("Linked attribute to program.")


def link_data_element_to_stage(data_element_uid):
    stage = dhis_get(
        f"programStages/{PROGRAM_STAGE_UID}",
        params={
            "fields": "id,name,programStageDataElements[dataElement[id]]"
        },
    )

    linked_ids = {
        item["dataElement"]["id"]
        for item in stage.get("programStageDataElements", [])
        if item.get("dataElement", {}).get("id")
    }

    if data_element_uid in linked_ids:
        log.info("Data element already linked to stage.")
        return

    dhis_patch(
        f"programStages/{PROGRAM_STAGE_UID}",
        [{
            "op": "add",
            "path": "/programStageDataElements/-",
            "value": {
                "dataElement": {"id": data_element_uid},
                "compulsory": False,
            },
        }],
    )
    log.info("Linked data element to program stage.")


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():
    if not CREATE_METADATA:
        xml_text = odk_get_metadata()
        fields = parse_odk_fields(xml_text)
        write_mapping_template(fields)

        print()
        print("STEP 1 COMPLETE")
        print(f"Review and edit: {MAPPING_CSV}")
        print("Set target to ATTRIBUTE, DATA_ELEMENT, or IGNORE.")
        print("Review value_type and unique before proceeding.")
        print("Then set CREATE_METADATA = True and run again.")
        return

    if not MAPPING_CSV.exists():
        raise FileNotFoundError(
            f"{MAPPING_CSV} does not exist. "
            "Run once with CREATE_METADATA = False first."
        )

    rows = load_mapping()

    for row in rows:
        target = row["target"]
        field_path = row["field_path"]

        if target in ("", "IGNORE"):
            continue

        if target not in ("ATTRIBUTE", "DATA_ELEMENT"):
            raise ValueError(
                f"Invalid target {target!r} for {field_path}. "
                "Use ATTRIBUTE, DATA_ELEMENT, or IGNORE."
            )

        if not row["value_type"]:
            raise ValueError(
                f"Missing value_type for {field_path}"
            )

        log.info(
            "Processing %s as %s (%s)",
            field_path, target, row["value_type"],
        )

        if target == "ATTRIBUTE":
            uid = ensure_tracked_entity_attribute(row)
            link_attribute_to_program(uid)

        elif target == "DATA_ELEMENT":
            uid = ensure_data_element(row)
            link_data_element_to_stage(uid)

    log.info("Metadata workflow completed.")


def classify_field(field):
    """
    Classify a parsed ODK field using explicit rules.
    """
    name = field["field_name"].lower()
    path = field["field_path"].lower()

    if name in ATTRIBUTE_KEYWORDS:
        return "ATTRIBUTE"

    if name in DATA_ELEMENT_KEYWORDS:
        return "DATA_ELEMENT"

    # Optional rule for stable child identifiers.
    if name == "class_child_uid":
        return "ATTRIBUTE"

    # Do not guess when a field is not recognized.
    return "IGNORE"


def sync_odk_metadata_to_dhis2():
    # 1. Read the current ODK form schema.
    xml_text = odk_get_metadata()

    # 2. Parse fields in memory; no CSV required.
    fields = parse_odk_fields(xml_text)

    print(f"ODK fields discovered: {len(fields)}")

    created_or_existing = {
        "attributes": [],
        "data_elements": [],
        "ignored": [],
    }

    # 3. Create or reuse DHIS2 metadata.
    for field in fields:
        target = classify_field(field)
        field["target"] = target

        if target == "IGNORE":
            created_or_existing["ignored"].append(
                field["field_path"]
            )
            continue

        print(
            f"Processing {field['field_path']} "
            f"as {target}"
        )

        if target == "ATTRIBUTE":
            uid = ensure_tracked_entity_attribute(field)
            link_attribute_to_program(uid)

            created_or_existing["attributes"].append({
                "field": field["field_path"],
                "uid": uid,
            })

        elif target == "DATA_ELEMENT":
            uid = ensure_data_element(field)
            link_data_element_to_stage(uid)

            created_or_existing["data_elements"].append({
                "field": field["field_path"],
                "uid": uid,
            })

    # 4. Display a summary.
    print("\nMetadata synchronization completed.")
    print(
        "Attributes created/reused:",
        len(created_or_existing["attributes"]),
    )
    print(
        "Data elements created/reused:",
        len(created_or_existing["data_elements"]),
    )
    print(
        "Ignored fields:",
        len(created_or_existing["ignored"]),
    )

    return created_or_existing


if __name__ == "__main__":
    result = sync_odk_metadata_to_dhis2()


if __name__ == "__main__":
    main()
