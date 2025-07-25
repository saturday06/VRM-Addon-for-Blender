// SPDX-License-Identifier: MIT OR GPL-3.0-or-later
const defaultLocale = "en";
const supportedLocales = [defaultLocale, "ja"];
const autoRedirectionTargetLocaleKey =
  "vrm-format-auto-redirection-target-locale";
const hasPendingAutoRedirectionKey = "vrm-format-has-pending-auto-redirection";

/**
 * Register automatic redirection target locale.
 */
export function registerAutoRedirectionTargetLocale(
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
 * Detect automatic redirection target locale from storage and browser language settings.
 *
 * @returns {string} The guessed language code, either "en" (default) or "ja".
 */
function detectAutoRedirectionTargetLocale(
  storage: Storage,
): string | undefined {
  const targetLocale = storage.getItem(autoRedirectionTargetLocaleKey);
  if (targetLocale && supportedLocales.includes(targetLocale)) {
    return targetLocale;
  }

  // https://developer.mozilla.org/en-US/docs/Web/API/Navigator/languages
  if (navigator.languages) {
    for (const language of navigator.languages) {
      for (const supportedLocale of supportedLocales) {
        if (language.startsWith(supportedLocale)) {
          return supportedLocale;
        }
      }
    }
  }

  // https://developer.mozilla.org/en-US/docs/Web/API/Navigator/language
  if (navigator.language) {
    for (const supportedLocale of supportedLocales) {
      if (navigator.language.startsWith(supportedLocale)) {
        return supportedLocale;
      }
    }
  }

  return undefined;
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
  }

  if (requestLocale?.indexOf(".") !== -1) {
    // If an extension is included, treat it as an individual file and do not redirect.
    return;
  }

  if (requestLocale == "releases") {
    // The releases folder contains locale-independent files, so do not redirect.
    return;
  }

  let targetLocale = detectAutoRedirectionTargetLocale(storage);
  if (!targetLocale) {
    if (requestLocale) {
      // If automatic detection of the redirect target locale failed and
      // a locale can be obtained from the request, do nothing.
      return;
    }
    targetLocale = defaultLocale;
  }

  registerAutoRedirectionTargetLocale(storage, targetLocale);

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
