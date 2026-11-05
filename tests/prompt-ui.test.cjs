const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.join(__dirname, '..');
test('shared ScoreCore loads in a browser without CommonJS', () => {
  const ctx = {window:{}}; vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(path.join(root,'scorecore.js'),'utf8'),ctx);
  assert.equal(ctx.window.ScoreCore.musicIntent('96 BPM E minor').bpm,96);
});
test('prompt UI uses qualified intent and saves only after successful compile', async () => {
  const ui = fs.readFileSync(path.join(root,'app-ui.js'),'utf8');
  const start = ui.indexOf('async function generateProject()');
  assert.notEqual(start,-1,'missing durable Generate action');
  const end = ui.indexOf('\nfunction ',start+1);
  const source = ui.slice(start,end);
  let saves=0, compiled=0;
  const ctx={compile(){compiled++;},async saveJSON(){saves++;},setStatus(){}};
  vm.createContext(ctx);vm.runInContext(source,ctx);
  await ctx.generateProject();assert.equal(compiled,1);assert.equal(saves,1);
  ctx.compile=()=>{throw Error('unsupported meter');};
  await ctx.generateProject();assert.equal(saves,1);
  const compile = ui.slice(ui.indexOf('function compile()'),ui.indexOf('function audioBufferToWav'));
  assert.match(compile,/ScoreCore\.compileIntent/);
  assert.match(compile,/ScoreCore\.musicIntent/);
  assert.match(fs.readFileSync(path.join(root,'index.html'),'utf8'),/src="scorecore.js"/);
});
test('release packaging retains shared browser adapter',()=>{
 assert.match(fs.readFileSync(path.join(root,'package_project.py'),'utf8'),/'scorecore.js'/);
});
