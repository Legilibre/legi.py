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
jest.setTimeout(20000);

it("getSection", async () => {
  expect.assertions(1);
  const res = await dila
    .getSection({ id: "LEGISCTA000006088039", date: "2018-04-03" })
    .catch(console.log);
  expect(res).toMatchSnapshot();
});

it("getArticle", async () => {
  expect.assertions(1);
  const res = await dila.getArticle({ id: "LEGIARTI000006398351", date: "2018-04-03" });
  expect(res).toMatchSnapshot();
});

it("getCode", async () => {
  expect.assertions(1);
  const res = await dila.getCode({ cid: CODE_TEST, date: "2018-04-03" });
  expect(res).toMatchSnapshot();
});

it("getSommaire", async () => {
  expect.assertions(1);
  const res = await dila.getSommaire({ cid: CODE_TEST, date: "2018-04-03" });
  expect(res).toMatchSnapshot();
});

it("getCodesList", async () => {
  expect.assertions(4);
  const res = await dila.getCodesList();
  expect(typeof res.length).not.toBe("undefined");
  expect(typeof res).toBe("object");
  expect(res.length).toBeGreaterThan(10);
  expect(res).toMatchSnapshot();
});
