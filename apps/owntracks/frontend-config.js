// api.baseUrl is deliberately not set: this container's nginx already
// reverse-proxies /api/ and /ws/ to owntracks-recorder, so the default (the
// current protocol and host) already resolves correctly. See every option at
// https://github.com/owntracks/frontend/blob/master/docs/config.md
window.owntracks = window.owntracks || {};
window.owntracks.config = {
  filters: {
    // Discards GPS points with accuracy worse than 100m — without this,
    // outliers skew the distance-travelled calculation (the docs recommend
    // turning this on).
    minAccuracy: 100,
  },
  map: {
    // Does not connect two points more than 1km apart with the same line —
    // it avoids visual "teleporting" on the map when there is a big jump
    // between points (poor GPS, or the phone off for a while).
    maxPointDistance: 1000,
  },
};
