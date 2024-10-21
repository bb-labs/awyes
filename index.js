#!/usr/bin/env node
const fs = require("fs");
const child_process = require("child_process");

// Run the cloudview interface
fs.cpSync(
  "./awyes.ts",
  "./node_modules/@the-sage-group/awyes/cloudview/clients/awyes.ts"
);
fs.cpSync(
  "./package.json",
  "./node_modules/@the-sage-group/awyes/cloudview/clients/package.json"
);
child_process.execSync("npm install", {
  cwd: "./node_modules/@the-sage-group/awyes/cloudview/clients",
});
const cloudview = child_process.spawn("npm", [
  "run",
  "dev",
  "--prefix",
  "./node_modules/@the-sage-group/awyes/cloudview",
]);
cloudview.stdout.on("data", (data) => process.stdout.write(data.toString()));
cloudview.stderr.on("data", (data) => process.stderr.write(data.toString()));
