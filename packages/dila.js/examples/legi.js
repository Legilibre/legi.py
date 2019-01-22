const Legi = require("../src/Legi");

module.exports = new Legi({
  client: "pg",
  connection: {
    host: "vps.revolunet.com",
    port: 5444,
    user: "legi",
    password: "legi",
    database: "legi"
  }
});
