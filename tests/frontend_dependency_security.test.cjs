const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const lock = JSON.parse(fs.readFileSync(path.join(__dirname,
  "../strix/interface/viewer/frontend/package-lock.json"), "utf8"));
const minimums = {"browserslist": "4.29.0", "baseline-browser-mapping": "2.11.0", "nanoid": "3.3.18", "source-map-js": "1.2.2", "postcss": "8.5.23", "vite": "6.4.5"};
for (const [name, minimum] of Object.entries(minimums)) {
  test(`${name} excludes its audited vulnerable release range`, () => {
    const installed = lock.packages[`node_modules/${name}`].version.split(".").map(Number);
    const fixed = minimum.split(".").map(Number);
    const difference = installed.map((n, i) => n - fixed[i]).find(n => n !== 0) || 0;
    assert.ok(difference >= 0, `${name} must be >= ${minimum}`);
  });
}
