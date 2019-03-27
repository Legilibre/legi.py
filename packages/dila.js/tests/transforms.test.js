const Dila = require("../src");
const markdown = require("../src/markdown");
const html = require("../src/html");
const knexConfig = require("../src/knexfile");

const dila = new Dila(knexConfig.test);

afterAll(() => {
  dila.close();
});

// medailles LEGITEXT000006070666
// travail LEGITEXT000006072050
// PI LEGITEXT000006069414

const CODE_TEST = "LEGITEXT000006070666";
//jest.setTimeout(20000);

it("getCode then markdown", async () => {
  expect.assertions(1);
  const res = await dila.getCode({ cid: CODE_TEST, date: "2018-12-01" }).then(markdown);
  expect(res).toMatchSnapshot();
});

it("getCode then html", async () => {
  expect.assertions(1);
  const res = await dila.getCode({ cid: CODE_TEST, date: "2018-12-01" }).then(html);
  expect(res).toMatchSnapshot();
});
