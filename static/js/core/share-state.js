function encodeState(stateObj) {
  return btoa(JSON.stringify(stateObj || {}));
}

function decodeState(encoded) {
  return JSON.parse(atob(encoded));
}

window.ShareState = { encodeState, decodeState };
