const Dila = require("dila");

const getDila = baseDILA => {
  if (process.env.DB_HOST && process.env.DB_USER && process.env.DB_PASSWORD) {
    return new Dila({
      host: process.env.DB_HOST,
      port: process.env.DB_PORT || 5432,
      user: process.env.DB_USER,
      password: process.env.DB_PASSWORD,
      database: baseDILA.toLowerCase()
    });
  } else {
    return new Dila();
  }
};

module.exports = getDila;
