// SPDX-License-Identifier: MIT OR GPL-3.0-or-later
const defaultLocale = "en";
const supportedLocales: readonly string[] = [defaultLocale, "ja"];
const autoRedirectionTargetLocaleKey =
  "vrm-format-auto-redirection-target-locale";
const hasPendingAutoRedirectionKey = "vrm-format-has-pending-auto-redirection";

/**
 * Save automatic redirection target locale to storage.
 */
export function setAutoRedirectionTargetLocaleToStorage(
  storage: Storage,
  locale: string,
): void {
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
  const targetLocale = storage.getItem(autoRedirectionTargetLocaleKey);
  if (targetLocale && supportedLocales.includes(targetLocale)) {
    return targetLocale;
  }
  return null;
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
    if (supportedLocaleComponents.length >= i) {
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
 * Redirect to the corresponding URL based on storage and browser language settings
 */
export function redirectToLocaleUrlIfNeeded(storage: Storage): void {
  storage.removeItem(hasPendingAutoRedirectionKey);

  const window = globalThis;
  if (!(window instanceof Window) || !(window.location instanceof Location)) {
    return;
  }

  // Separate the requested pathname into the first folder and the rest,
  // and use the first folder as the locale.
  let requestLocale;
  let requestPathname;
  const requestUrl = new URL(window.location.href);
  const requestPathComponents = requestUrl.pathname.split("/");
  if (requestPathComponents.length >= 2) {
    requestLocale = requestPathComponents[1];
    requestPathname = requestPathComponents.slice(2).join("/");

    if (requestLocale.indexOf(".") !== -1) {
      // If an extension is included, treat it as an individual file and do not redirect.
      return;
    }
  }

  if (requestLocale == "releases") {
    // The releases folder contains locale-independent files, so do not redirect.
    return;
  }

  let targetLocale = getAutoRedirectionTargetLocaleFromStorage(storage);
  if (!targetLocale) {
    targetLocale = getAutoRedirectionTargetLocaleFromNavigatorLanguage();
  }
  if (!targetLocale && requestLocale) {
    if (supportedLocales.includes(requestLocale)) {
      // If automatic detection of the redirect target locale failed and
      // a supported locale can be obtained from the request, do nothing.
      return;
    }
    const lowerCaseRequestLocale = requestLocale.toLowerCase();
    if (supportedLocales.includes(lowerCaseRequestLocale)) {
      targetLocale = lowerCaseRequestLocale;
    }
  }
  targetLocale ||= defaultLocale;

  setAutoRedirectionTargetLocaleToStorage(storage, targetLocale);

  // If the requested locale and the automatically detected locale are the same, do nothing
  if (requestLocale === targetLocale) {
    return;
  }

  // If we reach here, redirection is necessary.
  // Reconstruct the URL and redirect.
  const redirectUrl = new URL(window.location.href);
  redirectUrl.pathname = "/" + targetLocale + "/";
  if (requestPathname) {
    redirectUrl.pathname += requestPathname;
  }

  storage.setItem(hasPendingAutoRedirectionKey, "true");
  window.location.replace(redirectUrl.toString());
}
