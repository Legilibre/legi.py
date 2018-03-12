const unified = require("unified");
const remarkStringify = require("remark-stringify");
const cleanup = require("@z0mt3c/clean-html");
const rehypeParse = require("rehype-parse");
const rehype2remark = require("rehype-remark");

const cleanBlocArticle = html => cleanup(html.replace(/&#13;/g, "").replace(/&amp;#13;/g, ""));

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
  depth: depth,
  children: [
    {
      type: "text",
      value: text
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
      getHeading({ text: node.data.titre_ta, depth }),
      /*getBreak(), getBreak(),*/ ...children
    ]
  }),
  article: async (node, children, depth) => ({
    type: "paragraph",
    children: [
      //...node,
      getHeading({ text: node.data.titre, depth }),
      // getBreak(),
      // getBreak(),
      await htmlToMdAst(await cleanBlocArticle(node.data.bloc_textuel)),
      ...children
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
    (node.children && (await Promise.all(node.children.map(n => nodeToMdast(n, depth + 1))))) || [];
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
  return nodeToMdast(node).then(x => {
    console.log("x", x);
    return stringifyMdast(x);
  });
};

module.exports = toMarkdown;
