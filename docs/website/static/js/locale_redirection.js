(function() {
  const localized_folders = ["en", "ja"];

  function guess_localized_folder() {
    // https://developer.mozilla.org/en-US/docs/Web/API/Navigator/languages
    if (window.navigator.languages) {
      for (const language of window.navigator.languages) {
        for (const supported_language of localized_folders) {
          if (language.startsWith(supported_language)) {
            return supported_language;
          }
        }
      }
    }

    // https://developer.mozilla.org/en-US/docs/Web/API/Navigator/language
    for (const supported_language of localized_folders) {
      if (window.navigator.language.startsWith(supported_language)) {
        return supported_language;
      }
    }

    return null;
  }

  var redirection = false;
  const params = []
  for (const param of window.location.search.substring(1).split("&")) {
    if (param == "locale_redirection") {
      redirection = true;
    } else {
      params.push(param)
    }
  }
  if (!redirection) {
    return;
  }
  window.location.search = params.join("&");

  const main_localized_folder = guess_localized_folder();
  if (!main_localized_folder) {
    return;
  }

  var current_localized_folder = "";
  var content_pathname = "";
  for (const localized_folder of localized_folders) {
    if (window.location.pathname == "/" + localized_folder) {
      current_localized_folder = localized_folder;
      break;
    } else if (window.location.pathname.startsWith("/" + localized_folder + "/")) {
      content_pathname = window.location.pathname.substring(localized_folder.length + 2)
      current_localized_folder = localized_folder;
      break;
    }
  }
  if (!current_localized_folder || current_localized_folder == main_localized_folder) {
    return;
  }

  var href = "/" + main_localized_folder;
  if (content_pathname) {
    href += "/" + content_pathname;
  }
  if (window.location.search != "?") {
    href += window.location.search;
  }
  href += window.location.hash;
  window.location.replace(href);
})();
