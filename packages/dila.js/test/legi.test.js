const assert = require("assert");

const Legi = require("../src");

const legi = new Legi("./legi.sqlite");

describe("legi", () => {
  describe("getSection", () => {
    // b2b78e154444fdb49ef97822172479a25c95eab3
    it("should return a single L2232-13", async () => {
      const res = await legi.getSection({ parent: "LEGISCTA000006198560", date: "2018-01-01" });
      const count = res.filter(node => node.data.num === "L2232-13").length;
      assert.equal(count, 1, "there should be only one L2232-13 article");
    });
  });
});
