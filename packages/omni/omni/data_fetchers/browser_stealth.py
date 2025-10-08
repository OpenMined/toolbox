from playwright.async_api import BrowserContext

BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
]

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"

STEALTH_JS = """
// Store original functions to maintain [native code] appearance
const originalDefineProperty = Object.defineProperty;
const originalGetOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;

// Try to make our overrides look as native as possible
const createNativeLookingFunction = (func, name) => {
  // Wrap function to return [native code] on toString()
  const wrapper = new Proxy(func, {
    apply(target, thisArg, args) {
      return target.apply(thisArg, args);
    },
  });

  // Override toString to return [native code]
  try {
    originalDefineProperty(wrapper, "toString", {
      value: function () {
        return `function ${name}() { [native code] }`;
      },
      configurable: false,
      writable: false,
    });
  } catch (e) {}

  return wrapper;
};

// 1. userAgentData - THE CRITICAL ONE
try {
  // Try to make it look native by defining on prototype
  const navProto = Object.getPrototypeOf(navigator);
  const originalGetter = originalGetOwnPropertyDescriptor(
    navProto,
    "userAgentData"
  )?.get;

  originalDefineProperty(navProto, "userAgentData", {
    get: createNativeLookingFunction(function () {
      return {
        brands: [
          { brand: "Chromium", version: "136" },
          { brand: "Google Chrome", version: "136" },
          { brand: "Not.A/Brand", version: "99" },
        ],
        mobile: false,
        platform: "macOS",
        getHighEntropyValues: createNativeLookingFunction(
          () =>
            Promise.resolve({
              brands: [
                { brand: "Chromium", version: "136" },
                { brand: "Google Chrome", version: "136" },
                { brand: "Not.A/Brand", version: "99" },
              ],
              mobile: false,
              platform: "macOS",
              platformVersion: "15.0.0",
              architecture: "arm64",
              bitness: "64",
              model: "",
              uaFullVersion: "136.0.6961.0",
            }),
          "getHighEntropyValues"
        ),
      };
    }, "get userAgentData"),
    configurable: true,
    enumerable: true,
  });
} catch (e) {
  console.error("Failed to override userAgentData:", e);
}

// 2. Remove webdriver - try to delete completely
try {
  delete Object.getPrototypeOf(navigator).webdriver;
  delete navigator.__proto__.webdriver;
  delete navigator.webdriver;
} catch (e) {}

// then redefine it
Object.defineProperty(navigator, 'webdriver', {
    get: () => false
});

// 3. Plugins - use native-looking array
try {
  const createPlugin = (name, desc, filename) => {
    return {
      0: { type: "application/pdf", suffixes: "pdf", description: desc },
      1: { type: "text/pdf", suffixes: "pdf", description: desc },
      description: desc,
      filename: filename,
      length: 2,
      name: name,
      item: createNativeLookingFunction(function (index) {
        return this[index] || null;
      }, "item"),
      namedItem: createNativeLookingFunction(function (name) {
        return null;
      }, "namedItem"),
    };
  };

  const plugins = [
    createPlugin(
      "PDF Viewer",
      "Portable Document Format",
      "internal-pdf-viewer"
    ),
    createPlugin(
      "Chrome PDF Viewer",
      "Portable Document Format",
      "internal-pdf-viewer"
    ),
    createPlugin(
      "Chromium PDF Viewer",
      "Portable Document Format",
      "internal-pdf-viewer"
    ),
    createPlugin(
      "Microsoft Edge PDF Viewer",
      "Portable Document Format",
      "internal-pdf-viewer"
    ),
    createPlugin(
      "WebKit built-in PDF",
      "Portable Document Format",
      "internal-pdf-viewer"
    ),
  ];

  plugins.item = createNativeLookingFunction(function (index) {
    return this[index] || null;
  }, "item");

  plugins.namedItem = createNativeLookingFunction(function (name) {
    return Array.from(this).find((p) => p.name === name) || null;
  }, "namedItem");

  plugins.refresh = createNativeLookingFunction(function () {}, "refresh");

  originalDefineProperty(Object.getPrototypeOf(navigator), "plugins", {
    get: createNativeLookingFunction(() => plugins, "get plugins"),
    configurable: true,
    enumerable: true,
  });
} catch (e) {
  console.error("Failed to override plugins:", e);
}

// 4. MimeTypes
try {
  const mimeTypes = [
    {
      type: "application/pdf",
      suffixes: "pdf",
      description: "Portable Document Format",
    },
    {
      type: "text/pdf",
      suffixes: "pdf",
      description: "Portable Document Format",
    },
  ];

  mimeTypes.item = createNativeLookingFunction(function (index) {
    return this[index] || null;
  }, "item");

  mimeTypes.namedItem = createNativeLookingFunction(function (name) {
    return Array.from(this).find((m) => m.type === name) || null;
  }, "namedItem");

  originalDefineProperty(Object.getPrototypeOf(navigator), "mimeTypes", {
    get: createNativeLookingFunction(() => mimeTypes, "get mimeTypes"),
    configurable: true,
    enumerable: true,
  });
} catch (e) {
  console.error("Failed to override mimeTypes:", e);
}

// 5. Chrome object
if (!window.chrome || !window.chrome.runtime) {
  window.chrome = {
    runtime: {},
    loadTimes: createNativeLookingFunction(function () {}, "loadTimes"),
    csi: createNativeLookingFunction(function () {}, "csi"),
    app: {},
  };
}

// 6. Permissions
const origQuery = navigator.permissions?.query;
if (origQuery) {
  navigator.permissions.query = createNativeLookingFunction(function (params) {
    if (params?.name === "notifications") {
      return Promise.resolve({ state: Notification.permission });
    }
    return origQuery.call(this, params);
  }, "query");
}
"""


async def apply_stealth_mode(context: BrowserContext) -> None:
    await context.add_init_script(STEALTH_JS)
