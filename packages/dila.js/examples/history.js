const fs = require("fs");
const visit = require("unist-util-visit");

const Legi = require("../src/Legi");

const legi = new Legi();

const CODE = "LEGITEXT000006072050"; // code du travail

const test = async () => {
  const results = await legi.getCodeVersions({
    cid: CODE
  });
  console.log(`${CODE} has ${results.length} versions`);
};

test().catch(console.log);
