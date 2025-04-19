import DefaultTheme from "vitepress/theme";
import type { EnhanceAppContext } from "vitepress";

export default {
  ...DefaultTheme,
  enhanceApp(_enhanceAppContext: EnhanceAppContext) {
    redirectToLocaleUrlIfNeeded();
  },
};

const defaultLanguage = "en";
const supportedLanguages = [defaultLanguage, "ja"];
const lastLocalizedFolderKey = "vrm-format-last-localized-folder";

/**
 * localStorageとブラウザの言語設定から、URLのプレフィックスを推測する。
 *
 * @returns {string} The guessed language code, either "en" (default) or "ja".
 */
function guessLocalizedFolder(): string {
  const lastLocalizedFolder = localStorage.getItem(lastLocalizedFolderKey);
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
function redirectToLocaleUrlIfNeeded() {
  const window = globalThis;
  const mainLocalizedFolder = guessLocalizedFolder();

  let currentLocalizedFolder;
  let contentPathname;
  for (const localizedFolder of supportedLanguages) {
    if (window.location.pathname === "/" + localizedFolder) {
      currentLocalizedFolder = localizedFolder;
      break;
    } else if (
      window.location.pathname.startsWith("/" + localizedFolder + "/")
    ) {
      contentPathname = window.location.pathname.substring(
        localizedFolder.length + 2,
      );
      currentLocalizedFolder = localizedFolder;
      break;
    }
  }
  if (currentLocalizedFolder === mainLocalizedFolder) {
    return;
  }

  let href = "/" + mainLocalizedFolder;
  if (contentPathname) {
    if (localStorage.getItem(lastLocalizedFolderKey)) {
      return;
    }
    href += "/" + contentPathname;
  }
  if (window.location.search) {
    href += "?" + window.location.search;
  }
  if (window.location.hash) {
    href += window.location.hash;
  }

  localStorage.setItem(lastLocalizedFolderKey, mainLocalizedFolder);
  window.location.replace(href);
}
