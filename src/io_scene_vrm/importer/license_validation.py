# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import contextlib
from typing import Optional
from urllib.parse import ParseResult, parse_qsl, urlparse

from bpy.app.translations import pgettext

from ..common.convert import Json


class LicenseConfirmationRequiredProp:
    def __init__(
        self,
        url: Optional[str],
        json_key: Optional[str],
        message: str,
    ) -> None:
        self.url = url
        self.json_key = json_key
        self.message = message

    def description(self) -> str:
        return f"""class=LicenseConfirmationRequired
url={self.url}
json_key={self.json_key}
message={self.message}
"""


class LicenseConfirmationRequiredError(Exception):
    def __init__(self, props: list[LicenseConfirmationRequiredProp]) -> None:
        self.props = props
        super().__init__(self.description())

    def description(self) -> str:
        return "\n".join([prop.description() for prop in self.props])

    def license_confirmations(self) -> list[dict[str, str]]:
        return [
            {
                "name": "LicenseConfirmation" + str(index),
                "url": prop.url or "",
                "json_key": prop.json_key or "",
                "message": prop.message or "",
            }
            for index, prop in enumerate(self.props)
        ]


def validate_license_url(
    url_str: str, json_key: str, props: list[LicenseConfirmationRequiredProp]
) -> None:
    if not url_str:
        return
    url = None
    with contextlib.suppress(ValueError):
        url = urlparse(url_str)
    if url:
        query_dict = dict(parse_qsl(url.query))
        if validate_vroid_hub_license_url(
            url, query_dict, json_key, props
        ) or validate_uni_virtual_license_url(url, query_dict, json_key, props):
            return
    props.append(
        LicenseConfirmationRequiredProp(
            url_str,
            json_key,
            pgettext("Is this VRM allowed to Edit? CHECK IT LICENSE"),
        )
    )


def validate_vroid_hub_license_url(
    url: ParseResult,
    query_dict: dict[str, str],
    json_key: str,
    props: list[LicenseConfirmationRequiredProp],
) -> bool:
    # https://hub.vroid.com/en/license?allowed_to_use_user=everyone&characterization_allowed_user=everyone&corporate_commercial_use=allow&credit=unnecessary&modification=allow&personal_commercial_use=profit&redistribution=allow&sexual_expression=allow&version=1&violent_expression=allow
    if url.hostname != "hub.vroid.com" or not url.path.endswith("/license"):
        return False
    if query_dict.get("modification") == "disallow":
        props.append(
            LicenseConfirmationRequiredProp(
                url.geturl(),
                json_key,
                pgettext(
                    'This VRM is licensed by VRoid Hub License "Alterations: No".'
                ),
            )
        )
    return True


def validate_uni_virtual_license_url(
    url: ParseResult,
    query_dict: dict[str, str],
    json_key: str,
    props: list[LicenseConfirmationRequiredProp],
) -> bool:
    # https://uv-license.com/en/license?utf8=%E2%9C%93&pcu=true
    if url.hostname != "uv-license.com" or not url.path.endswith("/license"):
        return False
    if query_dict.get("remarks") == "true":
        props.append(
            LicenseConfirmationRequiredProp(
                url.geturl(),
                json_key,
                pgettext('This VRM is licensed by UV License with "Remarks".'),
            )
        )
    return True


def validate_vrm1_license(
    json_dict: dict[str, Json], _confirmations: list[LicenseConfirmationRequiredProp]
) -> None:
    extensions_dict = json_dict.get("extensions")
    if not isinstance(extensions_dict, dict):
        return

    vrmc_vrm_dict = extensions_dict.get("VRMC_vrm")
    if not isinstance(vrmc_vrm_dict, dict):
        return

    return


def validate_vrm0_license(
    json_dict: dict[str, Json], confirmations: list[LicenseConfirmationRequiredProp]
) -> None:
    extensions_dict = json_dict.get("extensions")
    if not isinstance(extensions_dict, dict):
        return

    vrm_dict = extensions_dict.get("VRM")
    if not isinstance(vrm_dict, dict):
        return

    meta_dict = vrm_dict.get("meta")
    if not isinstance(meta_dict, dict):
        return

    license_name = meta_dict.get("licenseName")
    if license_name in [
        # https://github.com/vrm-c/vrm-specification/blob/master/specification/0.0/schema/vrm.meta.schema.json#L56
        "CC_BY_ND",
        "CC_BY_NC_ND",
    ]:
        confirmations.append(
            LicenseConfirmationRequiredProp(
                None,
                None,
                pgettext("This VRM is not allowed to Edit. CHECK ITS LICENSE"),
            )
        )

    if license_name == "Other":
        other_license_url = meta_dict.get("otherLicenseUrl")
        if other_license_url is None:
            confirmations.append(
                LicenseConfirmationRequiredProp(
                    None,
                    None,
                    pgettext(
                        'The VRM selects "Other" license but no license url is found.'
                    ),
                )
            )
        else:
            validate_license_url(
                str(other_license_url), "otherLicenseUrl", confirmations
            )

    other_permission_url = meta_dict.get("otherPermissionUrl")
    if other_permission_url is not None:
        validate_license_url(
            str(other_permission_url),
            "otherPermissionUrl",
            confirmations,
        )


def validate_license(
    json_dict: dict[str, Json], spec_version_number: tuple[int, int]
) -> None:
    """Validate that the license is not a non-modifiable license, such as CC_ND."""
    confirmations: list[LicenseConfirmationRequiredProp] = []

    if tuple(spec_version_number) >= (1, 0):
        validate_vrm1_license(json_dict, confirmations)
    else:
        validate_vrm0_license(json_dict, confirmations)

    if confirmations:
        raise LicenseConfirmationRequiredError(confirmations)
