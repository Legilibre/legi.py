// 1-1 promise
const serial = promises =>
  promises.reduce(
    (chain, c) => chain.then(res => c.then(cur => [...res, cur])),
    Promise.resolve([])
  );

// 1-1 promise callable
const serialExec = promises =>
  promises.reduce(
    (chain, c) => chain.then(res => c().then(cur => [...res, cur])),
    Promise.resolve([])
  );

const repeat = (s, times = 5) =>
  Array.from({ length: times })
    .fill(s)
    .join("");

const logSections = (node, d = 0) => {
  node.children &&
    node.children.forEach(n => {
      if (n.titre.match(/^Article.*/)) {
        console.log(repeat("  ", d), n.titre);
        n.bloc_textuel && console.log(repeat("  ", d + 1), n.bloc_textuel, "\n\n");
      } else {
        console.log(repeat("  ", d), n.titre);
        logSections(n, d + 1);
      }
    });
};

const range = (start, end) => Array.from({ length: end - start }, (k, v) => start + v);

const JSONlog = data => console.log(JSON.stringify(data, null, 2)) && data;

module.exports = {
  serial,
  serialExec,
  range,
  repeat,
  JSONlog
};
