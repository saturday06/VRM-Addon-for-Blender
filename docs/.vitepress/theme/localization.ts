const defaultLocale = "en";
const supportedLocales = [defaultLocale, "ja"];
const lastLocaleKey = "vrm-format-last-locale";
const localeRedirectionParam = "locale_redirection";
let hasPendingRedirection = false;

export function registerCurrentLocale(storage: Storage, locale: string) {
  if (hasPendingRedirection) {
    return;
  }

  if (!supportedLocales.includes(locale)) {
    return;
  }

  storage.setItem(lastLocaleKey, locale);
}

/**
 * Storageとブラウザの言語設定から、URLのプレフィックスを推測する。
 *
 * @returns {string} The guessed language code, either "en" (default) or "ja".
 */
function guessLocale(storage: Storage): string {
  const lastLocale = storage.getItem(lastLocaleKey);
  if (lastLocale && supportedLocales.includes(lastLocale)) {
    return lastLocale;
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
  for (const supportedLocale of supportedLocales) {
    if (navigator.language.startsWith(supportedLocale)) {
      return supportedLocale;
    }
  }

  return defaultLocale;
}

/**
 * ブラウザの言語設定から、対応するURLにリダイレクトする
 */
export function redirectToLocaleUrlIfNeeded() {
  hasPendingRedirection = false;

  const window = globalThis;
  if (!(window instanceof Window) || !(window.location instanceof Location)) {
    return;
  }

  const detectedLocale = guessLocale(window.localStorage);

  // リクエストされたpathnameを最初のフォルダとそれ以外に分離し、
  // 最初のフォルダをLocaleとする。
  let requestLocale;
  let requestPathname;
  const requestUrl = new URL(window.location.href);
  const pathComponents = requestUrl.pathname.split("/");
  if (pathComponents.length >= 2) {
    requestLocale = pathComponents[1];
    requestPathname = pathComponents.slice(2).join("/");
  }

  if (requestLocale?.indexOf(".") !== -1) {
    // 拡張子が含まれている場合は個別のファイルであるとし、リダイレクトしない。
    return;
  }

  // URLのクエリパラメータにlocale_redirectionが存在する場合、
  // localStorageから過去のリダイレクト情報を削除し、初回アクセスと同等の扱いにする。
  if (requestUrl.searchParams.has(localeRedirectionParam)) {
    window.localStorage.removeItem(lastLocaleKey);
  }

  // localizedFolder名がサポートされている言語であり、
  // かつ既に過去にアクセスしたローカライズ済みのフォルダと一致した場合はリダイレクトしない。
  if (
    requestLocale &&
    supportedLocales.includes(requestLocale) &&
    requestLocale ==
      window.localStorage.getItem(lastLocaleKey)
  ) {
    return;
  }
  registerCurrentLocale(window.localStorage, detectedLocale);

  // リクエストされたフォルダと自動判定したフォルダのロケール名が同一なら何もしない
  if (requestLocale === detectedLocale) {
    return;
  }

  // ここに到達した場合はリダイレクトが必要になる。
  // URLを再構築してリダイレクトする。
  const redirectUrl = new URL(window.location.href);
  redirectUrl.pathname = "/" + detectedLocale + "/";
  if (requestPathname) {
    redirectUrl.pathname += requestPathname;
  }
  redirectUrl.searchParams.delete(localeRedirectionParam);

  hasPendingRedirection = true;
  window.location.replace(redirectUrl.toString());
}
