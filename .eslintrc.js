module.exports = {
  parserOptions: {
    ecmaVersion: 2017,
    ecmaFeatures: { arrowFunctions: true, classes: true, experimentalObjectRestSpread: true }
  },
  env: {
    node: true,
    es6: true
  },
  extends: ["eslint:recommended", "plugin:prettier/recommended"],
  plugins: ["prettier"],
  rules: {
    "prettier/prettier": "error"
  }
};
