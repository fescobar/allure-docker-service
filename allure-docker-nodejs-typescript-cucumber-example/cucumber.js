require('module-alias/register')

var common = [
    '--require ./dist/features/steps/*.js'
].join(' ');

module.exports = {
    default: common,
};