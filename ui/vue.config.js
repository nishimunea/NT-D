const webpack = require('webpack')
const PrettierPlugin = require('prettier-webpack-plugin');

module.exports = {
  transpileDependencies: ["vuetify"],
  configureWebpack: {
    plugins: [
      new webpack.IgnorePlugin({
        resourceRegExp: /^\.\/locale$/,
        contextRegExp: /moment$/
      }),
      new PrettierPlugin({
        singleQuote: true,
        semi: true,
        tabWidth: 2,
        printWidth: 120
      })
    ]
  }
}
