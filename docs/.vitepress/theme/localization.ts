// SPDX-License-Identifier: MIT OR GPL-3.0-or-later
const defaultLocale = "en-us";
const supportedLocales: readonly string[] = [defaultLocale, "ja-jp"];
const autoRedirectionTargetLocaleKey =
  "vrm-format-auto-redirection-target-locale";
const hasPendingAutoRedirectionKey = "vrm-format-has-pending-auto-redirection";
const deletedLocaleToNewLocaleRedirectionMap: Readonly<Record<string, string>> =
  {
    // Mapping table for old, deleted locales.
    // If you add a new locale, you do not need to add it here.
    "en": "en-us",
    "ja": "ja-jp",
  };

/**
 * Save automatic redirection target locale to storage.
 */
export function setAutoRedirectionTargetLocaleToStorage(
  storage: Storage,
  locale: string,
): void {
  locale = locale.toLowerCase();
  locale = deletedLocaleToNewLocaleRedirectionMap[locale] ?? locale;

  if (storage.getItem(hasPendingAutoRedirectionKey)) {
    return;
  }

  if (!supportedLocales.includes(locale)) {
    return;
  }

  storage.setItem(autoRedirectionTargetLocaleKey, locale);
}

/**
 * Load automatic redirection target locale from storage.
 */
export function getAutoRedirectionTargetLocaleFromStorage(
  storage: Storage,
): string | null {
  let targetLocale = storage.getItem(autoRedirectionTargetLocaleKey);
  if (!targetLocale) {
    return null;
  }
  targetLocale = targetLocale.toLowerCase();
  targetLocale = deletedLocaleToNewLocaleRedirectionMap[targetLocale] ??
    targetLocale;
  if (!supportedLocales.includes(targetLocale)) {
    return null;
  }
  return targetLocale;
}

/**
 * Check if the navigator language contains the supported locale.
 *
 * @param navigatorLanguage
 * @param supportedLocale
 * @returns
 */
function isNavigatorLanguageContainsSupportedLocale(
  navigatorLanguage: string | null,
  supportedLocale: string,
): boolean {
  if (!navigatorLanguage) {
    return false;
  }
  navigatorLanguage = navigatorLanguage.toLowerCase();

  // There should be a more accurate algorithm.
  const navigatorLanguageComponents = navigatorLanguage.split("-");
  const supportedLocaleComponents = supportedLocale.split("-");
  for (let i = 0; i < navigatorLanguageComponents.length; i++) {
    const navigatorLanguageComponent = navigatorLanguageComponents[i];
    if (i >= supportedLocaleComponents.length) {
      return false;
    }
    const supportedLocaleComponent = supportedLocaleComponents[i];
    if (navigatorLanguageComponent !== supportedLocaleComponent) {
      return false;
    }
  }

  return true;
}

/**
 * Detect automatic redirection target locale from navigator language settings.
 *
 * @returns {string} The guessed language code.
 */
function getAutoRedirectionTargetLocaleFromNavigatorLanguage(): string | null {
  // https://developer.mozilla.org/en-US/docs/Web/API/Navigator/languages
  if (navigator.languages) {
    for (const navigatorLanguage of navigator.languages) {
      for (const supportedLocale of supportedLocales) {
        if (
          isNavigatorLanguageContainsSupportedLocale(
            navigatorLanguage,
            supportedLocale,
          )
        ) {
          return supportedLocale;
        }
      }
    }
  }

  // https://developer.mozilla.org/en-US/docs/Web/API/Navigator/language
  if (navigator.language) {
    for (const supportedLocale of supportedLocales) {
      if (
        isNavigatorLanguageContainsSupportedLocale(
          navigator.language,
          supportedLocale,
        )
      ) {
        return supportedLocale;
      }
    }
  }

  return null;
}

/**
 * Get the current location object.
 */
function getLocation(): Location | null {
  const window = globalThis;
  if (!(window instanceof Window)) {
    return null;
  }
  const location = window.location;
  if (!(location instanceof Location)) {
    return null;
  }
  return location;
}

/**
 * Get the redirect URL based on the storage and requested URL.
 */
function getRedirectUrl(storage: Storage, href: string): URL | null {
  // Separate the requested pathname into the first folder and the rest,
  // and use the first folder as the locale.
  let requestLocale: string | null = null;
  let requestPathname: string | null = null;
  const requestUrl = new URL(href);
  const requestRawPathnameComponents = requestUrl.pathname.split("/");
  if (requestRawPathnameComponents.length >= 2) {
    requestLocale = requestRawPathnameComponents[1];
    requestPathname = requestRawPathnameComponents.slice(2).join("/");

    // If requestLocale is not included in supportedLocales or as a key in
    // deletedLocaleToNewLocaleRedirectionMap, treat it as a locale-independent
    // request and return null.
    if (
      requestLocale.trim() !== "" &&
      !supportedLocales.includes(requestLocale) &&
      !deletedLocaleToNewLocaleRedirectionMap[requestLocale]
    ) {
      return null;
    }
  }

  let targetLocale = getAutoRedirectionTargetLocaleFromStorage(storage);
  if (!targetLocale) {
    targetLocale = getAutoRedirectionTargetLocaleFromNavigatorLanguage();
  }
  if (!targetLocale && requestLocale) {
    if (supportedLocales.includes(requestLocale)) {
      // If automatic detection of the redirect target locale failed and
      // a supported locale can be obtained from the request, do nothing.
      return null;
    }
    let canonicalizedRequestLocale = requestLocale.toLowerCase();
    canonicalizedRequestLocale =
      deletedLocaleToNewLocaleRedirectionMap[canonicalizedRequestLocale] ??
        canonicalizedRequestLocale;
    if (supportedLocales.includes(canonicalizedRequestLocale)) {
      targetLocale = canonicalizedRequestLocale;
    }
  }
  targetLocale ??= defaultLocale;

  // If the requested locale and the automatically detected locale are the same, do nothing
  if (requestLocale === targetLocale) {
    return null;
  }

  // If we reach here, redirection is necessary.
  // Reconstruct the URL and redirect.
  const redirectUrl = new URL(href);
  redirectUrl.pathname = "/" + targetLocale + "/";
  if (requestPathname) {
    redirectUrl.pathname += requestPathname;
  }
  return redirectUrl;
}

/**
 * Redirect to the corresponding URL based on storage and browser language settings
 */
export function redirectToLocaleUrlIfNeeded(storage: Storage): void {
  storage.removeItem(hasPendingAutoRedirectionKey);

  const location = getLocation();
  if (!location) {
    return;
  }

  const redirectUrl = getRedirectUrl(storage, location.href);
  if (!redirectUrl) {
    return;
  }

  storage.setItem(hasPendingAutoRedirectionKey, "true");

  location.replace(redirectUrl.toString());
}
