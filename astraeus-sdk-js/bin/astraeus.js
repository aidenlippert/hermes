#!/usr/bin/env node

/**
 * ASTRAEUS CLI - JavaScript/TypeScript
 *
 * Usage:
 *   npx @astraeus/sdk init
 *   npx @astraeus/sdk start
 *   npx @astraeus/sdk register
 */

const { Command } = require('commander');
const chalk = require('chalk');
const inquirer = require('inquirer');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const program = new Command();

program
  .name('astraeus')
  .description('ASTRAEUS AI Agent Network CLI')
  .version('1.0.0');

program
  .command('init [name]')
  .description('Initialize a new ASTRAEUS agent project')
  .action(async (name) => {
    console.log(chalk.blue('\n🚀 ASTRAEUS Agent Project Initializer\n'));

    const answers = await inquirer.prompt([
      {
        type: 'input',
        name: 'name',
        message: 'Agent name:',
        default: name || 'MyAgent'
      },
      {
        type: 'input',
        name: 'description',
        message: 'Agent description:',
        default: (answers) => `${answers.name} - An ASTRAEUS agent`
      },
      {
        type: 'input',
        name: 'email',
        message: 'Your email:',
        default: 'developer@example.com'
      },
      {
        type: 'list',
        name: 'language',
        message: 'Choose language:',
        choices: ['JavaScript', 'TypeScript'],
        default: 'TypeScript'
      }
    ]);

    const projectDir = answers.name.toLowerCase().replace(/\s+/g, '-');

    if (fs.existsSync(projectDir)) {
      console.log(chalk.red(`\n❌ Directory '${projectDir}' already exists!`));
      return;
    }

    fs.mkdirSync(projectDir);

    const isTypeScript = answers.language === 'TypeScript';
    const ext = isTypeScript ? 'ts' : 'js';

    // Create agent file
    const agentCode = isTypeScript ? `
import { Agent } from '@astraeus/sdk';

interface HelloInput {
  name?: string;
}

// Create your agent
const agent = new Agent({
  name: "${answers.name}",
  description: "${answers.description}",
  apiKey: process.env.ASTRAEUS_API_KEY || "your_api_key_here",
  owner: "${answers.email}"
});

// Add capabilities
agent.capability('hello', async (input: HelloInput) => {
  const name = input.name || 'World';
  return {
    message: \`Hello, \${name}!\`,
    agent: agent.name,
    status: '✅ Working!'
  };
}, {
  cost: 0.00,
  description: 'Say hello'
});

// Add more capabilities here
// agent.capability('your_capability', async (input) => {
//   return { result: '...' };
// }, { cost: 0.01, description: '...' });

// Start the agent
if (require.main === module) {
  console.log('\\n' + '='.repeat(70));
  console.log(\`🤖 Starting \${agent.name}\`);
  console.log('='.repeat(70));
  console.log(\`\\n📋 Description: \${agent.description}\`);
  console.log(\`📧 Owner: \${agent.owner}\`);
  console.log('\\n' + '='.repeat(70) + '\\n');

  agent.serve({ host: '0.0.0.0', port: 8000, register: true });
}

export default agent;
` : `
const { Agent } = require('@astraeus/sdk');

// Create your agent
const agent = new Agent({
  name: "${answers.name}",
  description: "${answers.description}",
  apiKey: process.env.ASTRAEUS_API_KEY || "your_api_key_here",
  owner: "${answers.email}"
});

// Add capabilities
agent.capability('hello', async (input) => {
  const name = input.name || 'World';
  return {
    message: \`Hello, \${name}!\`,
    agent: agent.name,
    status: '✅ Working!'
  };
}, {
  cost: 0.00,
  description: 'Say hello'
});

// Start the agent
if (require.main === module) {
  console.log('\\n' + '='.repeat(70));
  console.log(\`🤖 Starting \${agent.name}\`);
  console.log('='.repeat(70));
  console.log(\`\\n📋 Description: \${agent.description}\`);
  console.log(\`📧 Owner: \${agent.owner}\`);
  console.log('\\n' + '='.repeat(70) + '\\n');

  agent.serve({ host: '0.0.0.0', port: 8000, register: true });
}

module.exports = agent;
`;

    fs.writeFileSync(path.join(projectDir, `agent.${ext}`), agentCode);

    // Create package.json
    const packageJson = {
      name: projectDir,
      version: '1.0.0',
      description: answers.description,
      main: `agent.${ext}`,
      scripts: {
        start: isTypeScript ? 'ts-node agent.ts' : 'node agent.js',
        build: isTypeScript ? 'tsc' : 'echo "No build needed"',
        dev: isTypeScript ? 'ts-node-dev agent.ts' : 'nodemon agent.js'
      },
      dependencies: {
        '@astraeus/sdk': '^1.0.0',
        'dotenv': '^16.3.1'
      },
      devDependencies: isTypeScript ? {
        'typescript': '^5.3.0',
        'ts-node': '^10.9.2',
        'ts-node-dev': '^2.0.0',
        '@types/node': '^20.10.0'
      } : {
        'nodemon': '^3.0.2'
      }
    };

    fs.writeFileSync(
      path.join(projectDir, 'package.json'),
      JSON.stringify(packageJson, null, 2)
    );

    // Create .env
    const envContent = `# ASTRAEUS Configuration
ASTRAEUS_API_KEY=your_api_key_here
ASTRAEUS_NETWORK=https://web-production-3df46.up.railway.app
AGENT_PORT=8000
`;

    fs.writeFileSync(path.join(projectDir, '.env.example'), envContent);

    // Create tsconfig.json if TypeScript
    if (isTypeScript) {
      const tsconfig = {
        compilerOptions: {
          target: 'ES2020',
          module: 'commonjs',
          lib: ['ES2020'],
          outDir: './dist',
          rootDir: './src',
          strict: true,
          esModuleInterop: true,
          skipLibCheck: true,
          forceConsistentCasingInFileNames: true
        },
        include: ['*.ts'],
        exclude: ['node_modules', 'dist']
      };

      fs.writeFileSync(
        path.join(projectDir, 'tsconfig.json'),
        JSON.stringify(tsconfig, null, 2)
      );
    }

    // Create Dockerfile
    const dockerfile = `FROM node:18-slim

WORKDIR /app

COPY package*.json ./
RUN npm install --production

COPY . .

${isTypeScript ? 'RUN npm run build\n' : ''}
EXPOSE 8000

CMD ["npm", "start"]
`;

    fs.writeFileSync(path.join(projectDir, 'Dockerfile'), dockerfile);

    // Create README
    const readme = `# ${answers.name}

${answers.description}

## Quick Start

1. Get your API key from https://astraeus.ai
2. Copy \`.env.example\` to \`.env\` and add your API key
3. Install dependencies:

\`\`\`bash
npm install
\`\`\`

4. Run your agent:

\`\`\`bash
npm start
\`\`\`

## Deploy to Production

\`\`\`bash
npx @astraeus/sdk deploy
\`\`\`

## Documentation

- [ASTRAEUS Docs](https://docs.astraeus.ai)
- [SDK Reference](https://docs.astraeus.ai/sdk)
`;

    fs.writeFileSync(path.join(projectDir, 'README.md'), readme);

    console.log(chalk.green(`\n✅ Created agent project: ${projectDir}/`));
    console.log('\n📁 Project structure:');
    console.log(`   ${projectDir}/`);
    console.log(`   ├── agent.${ext}         # Your agent code`);
    console.log('   ├── package.json      # Dependencies');
    console.log('   ├── Dockerfile        # Docker deployment');
    console.log('   ├── .env.example      # Environment template');
    console.log('   └── README.md         # Documentation');

    console.log(chalk.blue('\n🔑 Next steps:'));
    console.log(`   1. cd ${projectDir}`);
    console.log('   2. npm install');
    console.log('   3. Get your API key from https://astraeus.ai');
    console.log('   4. Copy .env.example to .env and add your API key');
    console.log('   5. npm start\n');
  });

program
  .command('start')
  .description('Start your ASTRAEUS agent')
  .action(() => {
    console.log(chalk.blue('\n🚀 Starting ASTRAEUS Agent...\n'));

    if (!fs.existsSync('package.json')) {
      console.log(chalk.red('❌ No package.json found!'));
      console.log('   Run \'npx @astraeus/sdk init\' first');
      return;
    }

    const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    console.log(chalk.cyan(`📦 Agent: ${pkg.name}`));
    console.log(chalk.cyan(`📋 Description: ${pkg.description}\n`));

    try {
      execSync('npm start', { stdio: 'inherit' });
    } catch (error) {
      console.log(chalk.red('\n❌ Failed to start agent'));
    }
  });

program
  .command('register')
  .description('Register your agent on ASTRAEUS network')
  .action(() => {
    console.log(chalk.blue('\n🌐 ASTRAEUS Agent Registration\n'));
    console.log('To register your agent, visit:');
    console.log(chalk.cyan('\n   👉 https://astraeus.ai/register\n'));
    console.log('Or use the web portal at:');
    console.log(chalk.cyan('\n   👉 http://localhost:3000/register\n'));
    console.log('You\'ll get an API key to use in your .env file.\n');
  });

program
  .command('deploy')
  .description('Deploy your agent to production')
  .action(async () => {
    console.log(chalk.blue('\n🚀 ASTRAEUS Agent Deployment\n'));

    const { platform } = await inquirer.prompt([
      {
        type: 'list',
        name: 'platform',
        message: 'Choose deployment platform:',
        choices: ['Railway', 'Heroku', 'Docker', 'Kubernetes']
      }
    ]);

    if (platform === 'Railway') {
      console.log(chalk.cyan('\n📦 Railway Deployment:\n'));
      console.log('1. Install Railway CLI:');
      console.log('   npm install -g @railway/cli\n');
      console.log('2. Login:');
      console.log('   railway login\n');
      console.log('3. Deploy:');
      console.log('   railway up\n');
    } else if (platform === 'Heroku') {
      console.log(chalk.cyan('\n📦 Heroku Deployment:\n'));
      console.log('1. Install Heroku CLI');
      console.log('2. Login: heroku login');
      console.log('3. Create app: heroku create');
      console.log('4. Deploy: git push heroku main\n');
    } else if (platform === 'Docker') {
      console.log(chalk.cyan('\n🐳 Docker Deployment:\n'));
      console.log('1. Build: docker build -t my-agent .');
      console.log('2. Run: docker run -p 8000:8000 my-agent\n');
    } else if (platform === 'Kubernetes') {
      console.log(chalk.cyan('\n☸️  Kubernetes Deployment:\n'));
      console.log('1. Build and push image');
      console.log('2. Create deployment');
      console.log('3. Expose service\n');
    }
  });

program.parse();
