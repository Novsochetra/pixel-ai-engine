import { spawn } from 'node:child_process';
import path from 'node:path';

const UI = path.join(import.meta.dirname, '..');
const SERVER = path.join(UI, '..', 'server');
const VITE = path.join(UI, 'node_modules', 'vite', 'bin', 'vite.js');

// Vite runs on this same Node, not whichever one the shell finds first: it needs Node 22.
const children = [
  spawn('uv', ['run', 'pixel-server', '--reload'], { cwd: SERVER, stdio: 'inherit' }),
  spawn(process.execPath, [VITE], { cwd: UI, stdio: 'inherit' }),
];

function stopAll() {
  for (const child of children) {
    child.kill('SIGINT');
  }
}

// One Ctrl+C stops both, and either one ending ends the other, so no server is left behind.
process.on('SIGINT', stopAll);
process.on('SIGTERM', stopAll);
for (const child of children) {
  child.on('exit', (code) => {
    process.exitCode ||= code ?? 0;
    stopAll();
  });
}
