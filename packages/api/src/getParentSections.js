const getParentSections = node => {
  const parents = [];
  while ((node = node.parent)) {
    if (node.data && node.data.id) {
      parents.push({
        id: node.data.id,
        titre_ta: node.data.titre_ta
      });
    }
  }
  parents.reverse();
  return parents;
};

module.exports = getParentSections;
