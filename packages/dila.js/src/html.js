const remarkParse = require("remark-parse");
const unified = require("unified");
const rehypeStringify = require("rehype-stringify");
const remark2rehype = require("remark-rehype");
const doc = require("rehype-document");
const select = require("unist-util-select");
const map = require("unist-util-map");

const toMarkdown = require("./markdown");

const addClass = function(options) {
  return transformer;
  function transformer(tree) {
    tree.children = [
      {
        type: "element",
        tagName: "div",
        properties: { class: "markdown-body" },
        children: tree.children
      }
    ];
  }
};

const mdAstToHtml = async node => {
  const tree = map(node, function(node) {
    if (node.type === "code" || node.type === "section" || node.type === "article") {
      return {
        ...node,
        type: "element"
      };
    }
    return node;
  });

  const tree2 = await unified()
    .use(remarkParse)
    .use(remark2rehype)
    .use(addClass, {
      element: "markdown-body"
    })
    .use(doc, {
      css: "https://rawgit.com/sindresorhus/github-markdown-css/gh-pages/github-markdown.css",
      title: "legi.js",
      language: "fr"
    })
    .run(tree);

  return unified()
    .use(rehypeStringify)
    .stringify(tree2);
};

const html = node => toMarkdown(node, { tree: true }).then(mdAstToHtml);

module.exports = html;
