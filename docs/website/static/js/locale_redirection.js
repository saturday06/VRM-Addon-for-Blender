(function () {
  const localizedFolders = ["en", "ja"];

  function guessLocalizedFolder() {
    // https://developer.mozilla.org/en-US/docs/Web/API/Navigator/languages
    if (window.navigator.languages) {
      for (const language of window.navigator.languages) {
        for (const supportedLanguage of localizedFolders) {
          if (language.startsWith(supportedLanguage)) {
            return supportedLanguage;
          }
        }
      }
    }

    // https://developer.mozilla.org/en-US/docs/Web/API/Navigator/language
    for (const supportedLanguage of localizedFolders) {
      if (window.navigator.language.startsWith(supportedLanguage)) {
        return supportedLanguage;
      }
    }

    return null;
  }

  let redirection = false;
  const params = [];
  for (const param of window.location.search.substring(1).split("&")) {
    if (param === "locale_redirection") {
      redirection = true;
    } else {
      params.push(param);
    }
  }
  if (!redirection) {
    return;
  }

  const mainLocalizedFolder = guessLocalizedFolder();
  if (!mainLocalizedFolder) {
    return;
  }

  let currentLocalizedFolder = "";
  let contentPathname = "";
  for (const localizedFolder of localizedFolders) {
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
  if (
    !currentLocalizedFolder ||
    currentLocalizedFolder === mainLocalizedFolder
  ) {
    return;
  }

  let href = "/" + mainLocalizedFolder;
  if (contentPathname) {
    href += "/" + contentPathname;
  }
  const locationSearch = params.join("&");
  if (locationSearch) {
    href += "?" + locationSearch;
  }
  href += window.location.hash;
  window.location.replace(href);
})();
