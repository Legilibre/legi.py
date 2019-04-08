//const { toMatchDiffSnapshot } = require("snapshot-diff");

const Dila = require("../src");
const knexConfig = require("../src/knexfile");

const dila = new Dila(knexConfig.test);

afterAll(() => {
  dila.close();
});

// medailles LEGITEXT000006070666
// travail LEGITEXT000006072050
// PI LEGITEXT000006069414

const CODE_TEST = "LEGITEXT000006070666";

/*
 code/xxx                       OK
 code/xxx/article/xxx           OK
 code/xxx/article/xxx/liens     NOK
 code/xxx/article/xxx/versions  NOK
 code/xxx/section/xxx           OK
*/

it("getSection: article en vigueur doit apparaitre", async () => {
  expect.assertions(2);
  const res = await dila.getSection({
    id: "LEGISCTA000030730058",
    date: "2016-01-01"
  });
  const count = res.children.filter(node => node.data.num === "R2151-1").length;
  expect(count).toBe(1);
  expect(res).toMatchSnapshot();
});

it("getSection: article pas encore en vigueur ne doit pas apparaitre", async () => {
  expect.assertions(2);
  const res = await dila.getSection({ id: "LEGISCTA000030730058", date: "2015-01-01" });
  const count = res.children.filter(node => node.data.num === "R2151-1").length;
  expect(count).toBe(0);
  expect(res).toMatchSnapshot();
});

it("getSection: article pas encore abrogé doit apparaitre", async () => {
  expect.assertions(2);
  const res = await dila.getSection({ id: "LEGISCTA000029978970", date: "2015-02-01" });
  const count = res.children.filter(node => node.data.num === "R958-32").length;
  expect(count).toBe(1);
  expect(res).toMatchSnapshot();
});

it("getSection: article abrogé ne doit pas apparaitre", async () => {
  expect.assertions(2);
  const res = await dila.getSection({ id: "LEGISCTA000029978970", date: "2017-01-01" });
  const count = res.children.filter(node => node.data.num === "R958-32").length;
  expect(count).toBe(0);
  expect(res).toMatchSnapshot();
});

/*

it("getCodeVersions", async () => {
  expect.assertions(4);
  const res = await dila.getCodeVersions({ cid: CODE_TEST });
  expect(typeof res.length).not.toBe("undefined");
  expect(typeof res).toBe("object");
  expect(res.length).toBeGreaterThan(10);
  expect(res).toMatchSnapshot();
});


it("getJORF JORFTEXT000036386252", async () => {
  expect.assertions(1);
  const res = await dila.getJORF("JORFTEXT000036386252");
  expect(res).toMatchSnapshot();
});

*/
