const Legi = require("../src/Legi");
const { range, JSONlog } = require("../src/utils");
const markdown = require("../src/markdown");
const serialExec = require("promise-serial-exec");
const words = require("lodash.words");

const legi = new Legi();

// evolution de la taille de certaines sections

// nb de mots dans une section au 1er janvier
const sectionByYear = (section, year) =>
  legi
    .getSection({ parent: section, date: `${year}-01-1` })
    .then(markdown)
    .then(md => words(md).length);

const getSectionSize = (section, years) => years.map(year => () => sectionByYear(section, year));

serialExec(getSectionSize("LEGISCTA000018537734", range(2008, 2018))).then(sizes => {
  console.log("LEGISCTA000018537734", sizes);
});

serialExec(getSectionSize("LEGISCTA000018537158", range(2008, 2018))).then(sizes => {
  console.log("LEGISCTA000018537158", sizes);
});

serialExec(getSectionSize("LEGISCTA000018532900", range(2008, 2018))).then(sizes => {
  console.log("LEGISCTA000018532900", sizes);
});


