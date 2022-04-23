import contextlib
import re
from typing import Any, Dict, List, Optional
from urllib.parse import ParseResult, parse_qsl, urlparse

from ..common import deep
from ..external.fake_bpy_module_support import pgettext


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


class LicenseConfirmationRequired(Exception):
    def __init__(self, props: List[LicenseConfirmationRequiredProp]) -> None:
        self.props = props
        super().__init__(self.description())

    def description(self) -> str:
        return "\n".join([prop.description() for prop in self.props])

    def license_confirmations(self) -> List[Dict[str, str]]:
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
    url_str: str, json_key: str, props: List[LicenseConfirmationRequiredProp]
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
            pgettext(
                'Is this VRM allowed to edited? Please check its "{json_key}" value.'
            ).format(json_key=json_key),
        )
    )


def validate_vroid_hub_license_url(
    url: ParseResult,
    query_dict: Dict[str, str],
    json_key: str,
    props: List[LicenseConfirmationRequiredProp],
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
    query_dict: Dict[str, str],
    json_key: str,
    props: List[LicenseConfirmationRequiredProp],
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


def validate_license(json_dict: Dict[str, Any]) -> None:
    confirmations: List[LicenseConfirmationRequiredProp] = []

    # 既知の改変不可ライセンスを撥ねる
    # CC_NDなど
    license_name = str(
        deep.get(json_dict, ["extensions", "VRM", "meta", "licenseName"], "")
    )
    if re.match("CC(.*)ND(.*)", license_name):
        confirmations.append(
            LicenseConfirmationRequiredProp(
                None,
                None,
                pgettext(
                    'The VRM is licensed by "{license_name}". No derivative works are allowed.'
                ).format(license_name=license_name),
            )
        )

    validate_license_url(
        str(
            deep.get(json_dict, ["extensions", "VRM", "meta", "otherPermissionUrl"], "")
        ),
        "otherPermissionUrl",
        confirmations,
    )

    if license_name == "Other":
        other_license_url_str = str(
            deep.get(json_dict, ["extensions", "VRM", "meta", "otherLicenseUrl"], "")
        )
        if not other_license_url_str:
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
                other_license_url_str, "otherLicenseUrl", confirmations
            )

    if confirmations:
        raise LicenseConfirmationRequired(confirmations)
