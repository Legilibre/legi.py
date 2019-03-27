const url = require("url");

const getDefaultConfig = () => {
  if (process && process.env && process.env.DB_URL) {
    const parsed = url.parse(process.env.DB_URL);
    const [user, password] = (parsed.auth || "").split(":");
    return {
      client: "pg",
      version: "9.6",
      connection: {
        host: parsed.host,
        port: parsed.port || 5432,
        user: user,
        password: password,
        database: parsed.path.substr(1) // starts with /
      },
      pool: {
        min: 0,
        max: 5
      }
    };
  }

  return {
    client: "pg",
    version: "9.6",
    connection: {
      host: "legi.vps.revolunet.com",
      port: 5444,
      user: "legi",
      password: "legi",
      database: "legi"
    },
    pool: {
      min: 0,
      max: 5
    }
  };
};

const defaultConfig = getDefaultConfig();

module.exports = {
  ...defaultConfig,
  test: defaultConfig
};
