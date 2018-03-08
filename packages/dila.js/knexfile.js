module.exports = {
  // postgres: {
  //   client: "pg",
  //   connection: "postgresql://postgres:test@127.0.0.1:5434/legi",
  //   searchPath: ["knex", "public"],
  //   pool: { min: 2, max: 20 }
  // },
  // sqlite: {
  client: "sqlite3",
  useNullAsDefault: true,
  connection: {
    filename: "../legilibre/legi.py-docker/tarballs/legilibre.sqlite"
  },
  pool: {
    // https://blog.devart.com/increasing-sqlite-performance.html
    //     afterCreate: (conn, cb) => {
    //       conn.run(
    //         `
    // PRAGMA TEMP_STORE = MEMORY;
    // PRAGMA JOURNAL_MODE = OFF;
    // PRAGMA SYNCHRONOUS = OFF;
    // PRAGMA LOCKING_MODE = EXCLUSIVE;
    // PRAGMA CACHE_SIZE = 0
    // PRAGMA PAGE_SIZE = 0
    // `,
    //         cb
    //       );
    //     }
  }

  //}
};
