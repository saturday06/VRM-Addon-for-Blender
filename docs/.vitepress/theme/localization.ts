const defaultLanguage = "en";
const supportedLanguages = [defaultLanguage, "ja"];
const lastLocalizedFolderKey = "vrm-format-last-localized-folder";

export function registerLocale(storage: Storage, locale: string) {
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
  const window = globalThis;
  if (!(window instanceof Window) || !(window.location instanceof Location)) {
    return;
  }

  // History.stateに「既にリダイレクトした」という情報を保存しておく。
  // これが既にある場合は、リダイレクトを行わないようにする。
  const alreadyRedirectedOnceHistoryState = "Already Redirected Once";
  // TODO: DenoでHistory APIを使いたいが、なんか型が取れないのでanyを使う。要修正。
  // deno-lint-ignore no-explicit-any
  const history = (window as any).history;
  if (!history) {
    return;
  }
  if (history.state === alreadyRedirectedOnceHistoryState) {
    return;
  }

  const detectedLocalizedFolder = guessLocalizedFolder(window.localStorage);

  // リクエストされたpathnameを、最初のフォルダとそれ以外に分離し、
  // 最初のフォルダをLocalizedFolderとし、ここにロケール名が入っているものとする。
  let requestLocalizedFolder;
  let requestPathname;
  const pathComponents = window.location.pathname.split("/", 3);
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
  const params = [];
  for (const param of window.location.search.substring(1).split("&")) {
    if (param === "locale_redirection") {
      window.localStorage.removeItem(lastLocalizedFolderKey);
    } else {
      params.push(param);
    }
  }

  // locallizedFolder名がサポートされている言語であり、
  // かつ既に過去にアクセスしたローカライズ済みのフォルダと一致した場合はリダイレクトしない。
  if (
    requestLocalizedFolder &&
    supportedLanguages.includes(requestLocalizedFolder) &&
    requestLocalizedFolder ==
      window.localStorage.getItem(lastLocalizedFolderKey)
  ) {
    return;
  }
  registerLocale(window.localStorage, detectedLocalizedFolder);

  // リクエストされたフォルダと自動判定したフォルダのロケール名が同一なら何もしない
  if (requestLocalizedFolder === detectedLocalizedFolder) {
    return;
  }

  // ここに到達した場合はリダイレクトが必要になる。
  // URLを再構築してリダイレクトする。
  let href = "/" + detectedLocalizedFolder;
  if (requestPathname) {
    href += "/" + requestPathname;
  }
  const locationSearch = params.join("&");
  if (locationSearch) {
    href += "?" + locationSearch;
  }
  if (window.location.hash) {
    href += window.location.hash;
  }

  history.replaceState(alreadyRedirectedOnceHistoryState, "", href);
}
