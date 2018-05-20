const unified = require("unified");
const remarkStringify = require("remark-stringify");
const condense = require("condense-whitespace");
const rehypeParse = require("rehype-parse");
const rehype2remark = require("rehype-remark");

const cleanLegiText = html =>
  (html &&
    html
      // .replace(/\n/g, "<br/>")
      //.replace(/\n\n\n+/g, "<br/><br/>")
      //.replace(/\n\n+/g, "<br/>")
      //.replace(/\n/g, "<br/>")
      .replace(/&#x26;#13;/gm, "")
      .replace(/&amp;#x26;#13;/gm, "")
      .replace(/&amp;#13;/gm, "")
      .replace(/&#13;/gm, "")
      .replace(/&(amp;)?#13;/gm, "")
      .replace(/&amp;#13;/gm, "")) ||
  "";

const htmlToMdAst = async html => {
  const tree = unified()
    .use(rehypeParse, { fragment: true })
    .parse(html);
  return unified()
    .use(rehype2remark)
    .run(tree);
};

const getHeading = ({ text, depth = 1 }) => ({
  type: "heading",
  depth: Math.min(6, depth),
  children: [
    {
      type: "text",
      value: text || ""
    }
  ]
});

const getBreak = () => ({
  type: "break"
});

const nodeMap = {
  section: (node, children, depth) => ({
    type: "paragraph",
    children: [
      getHeading({ text: cleanLegiText(node.data.titre_ta), depth }),
      getBreak(),
      getBreak(),
      /* getBreak(),*/
      ...children
    ]
  }),
  article: async (node, children, depth) => ({
    type: "paragraph",
    children: [
      //...node,
      getHeading({ text: node.data.titre, depth }),
      getBreak(),
      getBreak(),
      // getBreak(),
      await htmlToMdAst(await cleanLegiText(node.data.bloc_textuel)),
      ...children,
      getBreak()
    ]
  }),
  text: async (node, children, depth) => ({
    type: "paragraph",
    children: [
      //...node,
      getHeading({ text: node.data.titre, depth: 1 }),
      getBreak(),
      getBreak(),
      // getBreak(),
      //await htmlToMdAst(await cleanLegiText(node.data.bloc_textuel)),
      ...children,
      getBreak()
    ]
  }),
  default: (node, children) => ({
    ...node,
    type: "paragraph",
    children
  })
};

// TODO
// convert section/article nodes to mdast
const nodeToMdast = async (node, depth = 0) => {
  const children =
    (node.children &&
      node.children.map &&
      (await Promise.all(node.children.map(n => nodeToMdast(n, depth + 1))))) ||
    [];
  const res = await (nodeMap[node.type] || nodeMap.default)(node, children, depth);
  return res;
};

const stringifyMdast = node =>
  unified()
    .use(remarkStringify)
    .stringify(node);

const DEFAULT_OPTIONS = {
  tree: false // return as syntax-tree
};

const toMarkdown = (node, options = DEFAULT_OPTIONS) => {
  if (options.tree) {
    return nodeToMdast(node);
  }
  return nodeToMdast(node).then(stringifyMdast);
};

module.exports = toMarkdown;
