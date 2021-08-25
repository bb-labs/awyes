const { spawn } = require('child_process');
const deploy = spawn('poetry', ['run', 'deploy']);

deploy.stdout.on('data', (data) => {
  console.log(`stdout: ${data}`);
});

deploy.stderr.on('data', (data) => {
  console.error(`stderr: ${data}`);
});

deploy.on('close', (code) => {
  console.log(`child process exited with code ${code}`);
});
