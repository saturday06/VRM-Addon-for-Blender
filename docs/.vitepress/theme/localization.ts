// SPDX-License-Identifier: MIT OR GPL-3.0-or-later
const defaultLocale = "en";
const supportedLocales = [defaultLocale, "ja"];
const autoRedirectionTargetLocaleKey =
  "vrm-format-auto-redirection-target-locale";
const hasPendingAutoRedirectionKey = "vrm-format-has-pending-auto-redirection";

/**
 * 自動リダイレクト先のLocaleを登録。
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
 * Storageとブラウザの言語設定から、自動リダイレクト先のLocaleを検知。
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
 * Storageとブラウザの言語設定から、対応するURLにリダイレクトする
 */
export function redirectToLocaleUrlIfNeeded(storage: Storage): void {
  storage.removeItem(hasPendingAutoRedirectionKey);

  const window = globalThis;
  if (!(window instanceof Window) || !(window.location instanceof Location)) {
    return;
  }

  // リクエストされたpathnameを最初のフォルダとそれ以外に分離し、
  // 最初のフォルダをlocaleとする。
  let requestLocale;
  let requestPathname;
  const requestUrl = new URL(window.location.href);
  const requestPathComponents = requestUrl.pathname.split("/");
  if (requestPathComponents.length >= 2) {
    requestLocale = requestPathComponents[1];
    requestPathname = requestPathComponents.slice(2).join("/");
  }

  if (requestLocale?.indexOf(".") !== -1) {
    // 拡張子が含まれている場合は個別のファイルであるとし、リダイレクトしない。
    return;
  }

  let targetLocale = detectAutoRedirectionTargetLocale(storage);
  if (!targetLocale) {
    if (requestLocale) {
      // リダイレクト先のロケールの自動取得に失敗した場合かつ、
      // リクエストからロケールが取得できた場合は何もしない。
      return;
    }
    targetLocale = defaultLocale;
  }

  registerAutoRedirectionTargetLocale(storage, targetLocale);

  // リクエストされたロケールと自動判定したロケールが同一なら何もしない
  if (requestLocale === targetLocale) {
    return;
  }

  // ここに到達した場合はリダイレクトが必要になる。
  // URLを再構築してリダイレクトする。
  const redirectUrl = new URL(window.location.href);
  redirectUrl.pathname = "/" + targetLocale + "/";
  if (requestPathname) {
    redirectUrl.pathname += requestPathname;
  }

  storage.setItem(hasPendingAutoRedirectionKey, "true");
  window.location.replace(redirectUrl.toString());
}
