const defaultLanguage = "en";
const supportedLanguages = [defaultLanguage, "ja"];
const lastLocalizedFolderKey = "vrm-format-last-localized-folder";
const localeRedirectionParam = "locale_redirection";
let hasPendingRedirection = false;

export function registerCurrentLocale(storage: Storage, locale: string) {
  if (hasPendingRedirection) {
    return;
  }

  if (!supportedLanguages.includes(locale)) {
    return;
  }

  storage.setItem(lastLocalizedFolderKey, locale);
}

/**
 * Storageとブラウザの言語設定から、URLのプレフィックスを推測する。
 *
 * @returns {string} The guessed language code, either "en" (default) or "ja".
 */
function guessLocalizedFolder(storage: Storage): string {
  const lastLocalizedFolder = storage.getItem(lastLocalizedFolderKey);
  if (lastLocalizedFolder && supportedLanguages.includes(lastLocalizedFolder)) {
    return lastLocalizedFolder;
  }

  // https://developer.mozilla.org/en-US/docs/Web/API/Navigator/languages
  if (navigator.languages) {
    for (const language of navigator.languages) {
      for (const supportedLanguage of supportedLanguages) {
        if (language.startsWith(supportedLanguage)) {
          return supportedLanguage;
        }
      }
    }
  }

  // https://developer.mozilla.org/en-US/docs/Web/API/Navigator/language
  for (const supportedLanguage of supportedLanguages) {
    if (navigator.language.startsWith(supportedLanguage)) {
      return supportedLanguage;
    }
  }

  return defaultLanguage;
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

  const detectedLocalizedFolder = guessLocalizedFolder(window.localStorage);

  // リクエストされたpathnameを、最初のフォルダとそれ以外に分離し、
  // 最初のフォルダをLocalizedFolderとし、ここにロケール名が入っているものとする。
  let requestLocalizedFolder;
  let requestPathname;
  const requestUrl = new URL(window.location.href);
  const pathComponents = requestUrl.pathname.split("/", 3);
  if (pathComponents.length >= 2) {
    requestLocalizedFolder = pathComponents[1];
    requestPathname = pathComponents.slice(2).join("/");
  }

  if (requestLocalizedFolder?.indexOf(".") !== -1) {
    // 拡張子が含まれている場合は個別のファイルであるとし、リダイレクトしない。
    return;
  }

  // URLのクエリパラメータにlocale_redirectionが存在する場合、
  // localStorageから過去のリダイレクト情報を削除し、初回アクセスと同等の扱いにする。
  if (requestUrl.searchParams.has(localeRedirectionParam)) {
    window.localStorage.removeItem(lastLocalizedFolderKey);
  }

  // localizedFolder名がサポートされている言語であり、
  // かつ既に過去にアクセスしたローカライズ済みのフォルダと一致した場合はリダイレクトしない。
  if (
    requestLocalizedFolder &&
    supportedLanguages.includes(requestLocalizedFolder) &&
    requestLocalizedFolder ==
      window.localStorage.getItem(lastLocalizedFolderKey)
  ) {
    return;
  }
  registerCurrentLocale(window.localStorage, detectedLocalizedFolder);

  // リクエストされたフォルダと自動判定したフォルダのロケール名が同一なら何もしない
  if (requestLocalizedFolder === detectedLocalizedFolder) {
    return;
  }

  // ここに到達した場合はリダイレクトが必要になる。
  // URLを再構築してリダイレクトする。
  const redirectUrl = new URL(window.location.href);
  redirectUrl.pathname = "/" + detectedLocalizedFolder + "/";
  if (requestPathname) {
    redirectUrl.pathname += requestPathname;
  }
  redirectUrl.searchParams.delete(localeRedirectionParam);

  hasPendingRedirection = true;
  window.location.replace(redirectUrl.toString());
}
