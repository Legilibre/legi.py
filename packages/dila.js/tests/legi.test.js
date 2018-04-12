//const { toMatchDiffSnapshot } = require("snapshot-diff");

const Legi = require("../src");
const markdown = require("../src/markdown");
const html = require("../src/html");

const legi = new Legi("./legi.sqlite");

afterAll(() => {
  legi.close();
});

// medailles LEGITEXT000006070666
// travail LEGITEXT000006072050
// PI LEGITEXT000006069414
const CODE_TEST = "LEGITEXT000006070666";

jest.setTimeout(20000);

it("getSection", async () => {
  expect.assertions(1);
  const res = await legi.getSection({ parent: "LEGISCTA000006177833", date: "2018-05-03" });
  expect(res).toMatchSnapshot();
});

it("getSection LEGISCTA000006198560-2017-01-01 should return a single L2232-13", async () => {
  expect.assertions(2);
  const res = await legi.getSection({ parent: "LEGISCTA000006198560", date: "2017-01-01" });
  const count = res.children.filter(node => node.data.num === "L2232-13").length;
  expect(count).toBe(1);
  expect(JSON.stringify(res)).toMatchSnapshot();
});

//cid="LEGITEXT000006072050" and date_fin like '2016-%'
//LEGIARTI000030730068  LEGISCTA000030730058  R2151-1 MODIFIE 2015-06-14  2016-10-23  AUTONOME
//R2151-1
//2999-01-01

it("getSection: article en vigueur doit apparaitre", async () => {
  expect.assertions(2);
  const res = await legi.getSection({ id: "LEGISCTA000030730058", date: "2016-01-01" });
  const count = res.children.filter(node => node.data.num === "R2151-1").length;
  expect(count).toBe(1);
  expect(res).toMatchSnapshot();
});

it("getSection: article pas encore en vigueur ne doit pas apparaitre", async () => {
  expect.assertions(2);
  const res = await legi.getSection({ id: "LEGISCTA000030730058", date: "2015-01-01" });
  const count = res.children.filter(node => node.data.num === "R2151-1").length;
  expect(count).toBe(0);
  expect(res).toMatchSnapshot();
});

it("getSection: article pas encore abrogé doit apparaitre", async () => {
  expect.assertions(2);
  const res = await legi.getSection({ id: "LEGISCTA000029978970", date: "2015-02-01" });
  const count = res.children.filter(node => node.data.num === "R958-32").length;
  expect(count).toBe(1);
  expect(res).toMatchSnapshot();
});

it("getSection: article abrogé ne doit pas apparaitre", async () => {
  expect.assertions(2);
  const res = await legi.getSection({ id: "LEGISCTA000029978970", date: "2017-01-01" });
  const count = res.children.filter(node => node.data.num === "R958-32").length;
  expect(count).toBe(0);
  expect(res).toMatchSnapshot();
});

it("getCodesList", async () => {
  expect.assertions(4);
  const res = await legi.getCodesList();
  expect(typeof res.length).not.toBe("undefined");
  expect(typeof res).toBe("object");
  expect(res.length).toBeGreaterThan(10);
  expect(res).toMatchSnapshot();
});

it("getCodeVersions", async () => {
  expect.assertions(4);
  const res = await legi.getCodeVersions({ cid: CODE_TEST });
  expect(typeof res.length).not.toBe("undefined");
  expect(typeof res).toBe("object");
  expect(res.length).toBeGreaterThan(10);
  expect(res).toMatchSnapshot();
});

it(`getCode ${CODE_TEST}-2018-04-01`, async () => {
  expect.assertions(1);
  const res = await legi.getCode({ id: CODE_TEST, date: "2018-04-01" });
  expect(res).toMatchSnapshot();
});

it(`getCode ${CODE_TEST}-1970-01-01`, async () => {
  expect.assertions(1);
  const res = await legi.getCode({ id: CODE_TEST, date: "1970-01-01" });
  expect(res).toMatchSnapshot();
});

it("getJORF JORFTEXT000036386252", async () => {
  expect.assertions(1);
  const res = await legi.getJORF("JORFTEXT000036386252");
  expect(res).toMatchSnapshot();
});

const codeTest = legi.getCode(CODE_TEST);

it("getCode then markdown", async () => {
  expect.assertions(1);
  const res = await codeTest.then(markdown).catch(console.log);
  expect(res).toMatchSnapshot();
});

it("getCode then html", async () => {
  expect.assertions(1);
  const res = await codeTest.then(html).catch(console.log);
  expect(res).toMatchSnapshot();
});
