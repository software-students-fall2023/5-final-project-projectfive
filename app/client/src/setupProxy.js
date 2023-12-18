const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function (app) {
    app.use(
        '/api',
        createProxyMiddleware({
            target: 'http://127.0.0.1:9000',
            changeOrigin: true,
            pathRewrite: {
                '^/api': '', // 将/api前缀替换为空字符串
            },
        })
    );
};