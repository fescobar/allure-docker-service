
require('module-alias/register')

module.exports = {
  timeout: 60000,
  spec: 'dist/**/*.js',
  reporter: 'allure-mocha'
};