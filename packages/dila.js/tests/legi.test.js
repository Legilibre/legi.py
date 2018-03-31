const Legi = require("../src");

const legi = new Legi("./legi.sqlite");

jest.setTimeout(10000);

// it("getSection", async () => {
//   expect.assertions(1);
//   const res = await legi.getSection({ parent: "LEGISCTA000006132321", date: "2018-05-03" });
//   expect(JSON.stringify(res)).toMatchSnapshot();
// });

// it("getSection LEGISCTA000006198560-2017-01-01 should return a single L2232-13", async () => {
//   expect.assertions(2);
//   const res = await legi.getSection({ parent: "LEGISCTA000006198560", date: "2017-01-01" });
//   const count = res.children.filter(node => node.data.num === "L2232-13").length;
//   expect(count).toBe(1);
//   expect(JSON.stringify(res)).toMatchSnapshot();
// });

it("getCodesList", async () => {
  expect.assertions(4);
  const res = await legi.getCodesList();
  expect(typeof res.length).not.toBe("undefined");
  expect(typeof res).toBe("object");
  expect(res.length).toBeGreaterThan(10);
  expect(JSON.stringify(res)).toMatchSnapshot();
});

it("getCodeDates", async () => {
  expect.assertions(1);
  const res = await legi.getCodeDates({ cid: "LEGITEXT000006072050" });
  expect(JSON.stringify(res)).toMatchSnapshot();
});

it("getCode LEGITEXT000006069414-2018-04-01", async () => {
  expect.assertions(1);
  const res = await legi.getCode({ id: "LEGITEXT000006069414", date: "2018-04-01" });
  expect(JSON.stringify(res)).toMatchSnapshot();
});

it("getCode LEGITEXT000006069414-2015-01-01", async () => {
  expect.assertions(1);
  const res = await legi.getCode({ id: "LEGITEXT000006069414", date: "2015-01-01" });
  expect(JSON.stringify(res)).toMatchSnapshot();
});

// it("getJORF JORFTEXT000000465978", async () => {
//   expect.assertions(1);
//   const res = await legi.getJORF("JORFTEXT000000465978");
//   expect(JSON.stringify(res)).toMatchSnapshot();
// });

// it("getJORF JORFTEXT000000465978", async () => {
//   expect.assertions(1);
//   const res = await legi.getJORF("JORFTEXT000000465978");
//   expect(JSON.stringify(res)).toMatchSnapshot();
// });

const markdown = require("../src/markdown");
const html = require("../src/html");

it("getCode then markdown", async () => {
  expect.assertions(1);
  const res = await legi
    .getCode("LEGITEXT000006069414")
    .then(markdown)
    .catch(console.log);
  expect(res).toMatchSnapshot("markdown-getCode");
});

it("getCode then html", async () => {
  expect.assertions(1);
  const res = await legi
    .getCode(CODE_TEST)
    .then(html)
    .catch(console.log);
  expect(res).toMatchSnapshot();
});
