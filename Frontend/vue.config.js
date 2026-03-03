const { defineConfig } = require('@vue/cli-service');
const fs = require('fs');
const path = require('path');

const backendPort = process.env.VUE_APP_BACKEND_PORT || '5000';
const useHttpsBackend = process.env.VUE_APP_BACKEND_HTTPS === 'true';
const useHttpsFrontend = process.env.VUE_APP_FRONTEND_HTTPS === 'true';
const backendProtocol = useHttpsBackend ? 'https' : 'http';
const backendTarget = `${backendProtocol}://localhost:${backendPort}`;

const backendCertPath = path.resolve(__dirname, '../Backend/cert.pem');
const backendKeyPath = path.resolve(__dirname, '../Backend/key.pem');
const hasCertFiles = fs.existsSync(backendCertPath) && fs.existsSync(backendKeyPath);

const frontendServerConfig = useHttpsFrontend && hasCertFiles
  ? {
      type: 'https',
      options: {
        cert: fs.readFileSync(backendCertPath),
        key: fs.readFileSync(backendKeyPath),
      },
    }
  : 'http';

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    port: 3000,
    server: frontendServerConfig,
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
