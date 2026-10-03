const { spawn } = require('child_process');
const path = require('path');

const rootDir = path.resolve(__dirname, '..');
const backendDir = path.join(rootDir, 'backend');
const frontendDir = path.join(rootDir, 'frontend');

// Cross-platform PYTHONPATH configuration
const pythonPath = [rootDir, backendDir].join(path.delimiter);
const env = {
  ...process.env,
  PYTHONPATH: pythonPath,
  PASSWORD_HASH_ITERATIONS: process.env.PASSWORD_HASH_ITERATIONS || '20000',
};

console.log('\x1b[36m%s\x1b[0m', '=======================================================');
console.log('\x1b[36m%s\x1b[0m', '  AgentScore Platform — Starting Backend & Frontend  ');
console.log('\x1b[36m%s\x1b[0m', '=======================================================');
console.log('\x1b[34m[BACKEND]\x1b[0m  FastAPI API -> http://127.0.0.1:8000 (Docs: /docs)');
console.log('\x1b[35m[FRONTEND]\x1b[0m Next.js UI  -> http://localhost:3000');
console.log('\x1b[90m%s\x1b[0m', 'Press Ctrl+C to terminate both servers.\n');

// 1. Spawn FastAPI Backend
const backend = spawn(
  'python',
  ['-m', 'uvicorn', 'app.main:app', '--app-dir', backendDir, '--host', '127.0.0.1', '--port', '8000', '--reload'],
  { cwd: rootDir, env, shell: true }
);

backend.stdout.on('data', (data) => {
  process.stdout.write(`\x1b[34m[BACKEND]\x1b[0m ${data}`);
});

backend.stderr.on('data', (data) => {
  process.stderr.write(`\x1b[34m[BACKEND]\x1b[0m ${data}`);
});

backend.on('error', (err) => {
  console.error('\x1b[31m[BACKEND ERROR]\x1b[0m', err);
});

// 2. Spawn Next.js Frontend
const npmCmd = process.platform === 'win32' ? 'npm.cmd' : 'npm';
const frontend = spawn(npmCmd, ['run', 'dev'], { cwd: frontendDir, env: process.env, shell: true });

frontend.stdout.on('data', (data) => {
  process.stdout.write(`\x1b[35m[FRONTEND]\x1b[0m ${data}`);
});

frontend.stderr.on('data', (data) => {
  process.stderr.write(`\x1b[35m[FRONTEND]\x1b[0m ${data}`);
});

frontend.on('error', (err) => {
  console.error('\x1b[31m[FRONTEND ERROR]\x1b[0m', err);
});

// Handle graceful termination
function cleanup() {
  console.log('\n\x1b[33mShutting down AgentScore servers...\x1b[0m');
  if (process.platform === 'win32') {
    if (backend.pid) spawn('taskkill', ['/pid', backend.pid, '/f', '/t']);
    if (frontend.pid) spawn('taskkill', ['/pid', frontend.pid, '/f', '/t']);
  } else {
    backend.kill('SIGTERM');
    frontend.kill('SIGTERM');
  }
  process.exit(0);
}

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
