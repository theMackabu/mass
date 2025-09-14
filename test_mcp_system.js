#!/usr/bin/env node

/**
 * Test script for the MCP Repository Analysis System
 * This simulates what a Cursor IDE MCP client would send
 */

// Sample repository data - simulating a typical React + Express fullstack app
const sampleRepository = {
  repoId: "sample-fullstack-app",
  projectName: "Sample Fullstack Application", 
  description: "A React frontend with Express.js backend",
  files: {
    "package.json": JSON.stringify({
      "name": "sample-app",
      "version": "1.0.0",
      "scripts": {
        "start": "node server.js",
        "dev": "concurrently \"npm run server\" \"npm run client\"",
        "client": "cd client && npm start",
        "server": "nodemon server.js"
      },
      "dependencies": {
        "express": "^4.18.2",
        "cors": "^2.8.5",
        "dotenv": "^16.0.3",
        "mongoose": "^7.0.3"
      },
      "devDependencies": {
        "nodemon": "^2.0.22",
        "concurrently": "^7.6.0"
      }
    }, null, 2),
    
    "server.js": `const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// MongoDB connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/sampleapp');

// Routes
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

app.get('/api/users', async (req, res) => {
  try {
    // Mock user data
    const users = [
      { id: 1, name: 'John Doe', email: 'john@example.com' },
      { id: 2, name: 'Jane Smith', email: 'jane@example.com' }
    ];
    res.json(users);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/users', async (req, res) => {
  try {
    const { name, email } = req.body;
    const newUser = { id: Date.now(), name, email };
    res.status(201).json(newUser);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(\`Server running on port \${PORT}\`);
});`,

    "client/package.json": JSON.stringify({
      "name": "client",
      "version": "0.1.0",
      "dependencies": {
        "react": "^18.2.0",
        "react-dom": "^18.2.0",
        "axios": "^1.3.4"
      },
      "scripts": {
        "start": "react-scripts start",
        "build": "react-scripts build"
      }
    }, null, 2),

    "client/src/App.js": `import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newUser, setNewUser] = useState({ name: '', email: '' });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get('/api/users');
      setUsers(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching users:', error);
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/api/users', newUser);
      setNewUser({ name: '', email: '' });
      fetchUsers();
    } catch (error) {
      console.error('Error creating user:', error);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="App">
      <h1>User Management</h1>
      
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Name"
          value={newUser.name}
          onChange={(e) => setNewUser({...newUser, name: e.target.value})}
        />
        <input
          type="email"
          placeholder="Email"
          value={newUser.email}
          onChange={(e) => setNewUser({...newUser, email: e.target.value})}
        />
        <button type="submit">Add User</button>
      </form>

      <ul>
        {users.map(user => (
          <li key={user.id}>
            {user.name} - {user.email}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;`,

    "README.md": `# Sample Fullstack Application

A simple fullstack application built with React and Express.js.

## Features

- React frontend with user management interface
- Express.js backend with REST API
- MongoDB integration
- CORS enabled for cross-origin requests

## Setup

1. Install dependencies: \`npm install\`
2. Install client dependencies: \`cd client && npm install\`
3. Set up environment variables in \`.env\`
4. Start development server: \`npm run dev\`

## API Endpoints

- GET /api/health - Health check
- GET /api/users - Get all users
- POST /api/users - Create new user

## Tech Stack

- Frontend: React 18, Axios
- Backend: Express.js, Mongoose
- Database: MongoDB
- Dev Tools: Nodemon, Concurrently`,

    ".env.example": `PORT=5000
MONGODB_URI=mongodb://localhost:27017/sampleapp
NODE_ENV=development`,

    "Dockerfile": `FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy client package files and build
COPY client/package*.json ./client/
WORKDIR /app/client
RUN npm ci --only=production
RUN npm run build

# Copy server files
WORKDIR /app
COPY server.js .
COPY client/build ./client/build

EXPOSE 5000

CMD ["npm", "start"]`,

    "models/User.js": `const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
    trim: true
  },
  email: {
    type: String,
    required: true,
    unique: true,
    trim: true,
    lowercase: true
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model('User', userSchema);`,

    "routes/users.js": `const express = require('express');
const User = require('../models/User');
const router = express.Router();

// GET /api/users
router.get('/', async (req, res) => {
  try {
    const users = await User.find().sort({ createdAt: -1 });
    res.json(users);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// POST /api/users
router.post('/', async (req, res) => {
  try {
    const user = new User(req.body);
    const savedUser = await user.save();
    res.status(201).json(savedUser);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// GET /api/users/:id
router.get('/:id', async (req, res) => {
  try {
    const user = await User.findById(req.params.id);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }
    res.json(user);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;`,

    "tests/api.test.js": `const request = require('supertest');
const app = require('../server');

describe('API Endpoints', () => {
  test('GET /api/health should return OK', async () => {
    const response = await request(app)
      .get('/api/health')
      .expect(200);
    
    expect(response.body.status).toBe('OK');
    expect(response.body.timestamp).toBeDefined();
  });

  test('GET /api/users should return users array', async () => {
    const response = await request(app)
      .get('/api/users')
      .expect(200);
    
    expect(Array.isArray(response.body)).toBe(true);
  });
});`
  }
};

console.log('🚀 Sample MCP Repository Data');
console.log('==============================');
console.log('This simulates what Cursor IDE would send to the MCP server.');
console.log('');
console.log('Repository ID:', sampleRepository.repoId);
console.log('Project Name:', sampleRepository.projectName);
console.log('Total Files:', Object.keys(sampleRepository.files).length);
console.log('');
console.log('Files included:');
Object.keys(sampleRepository.files).forEach(filePath => {
  const size = sampleRepository.files[filePath].length;
  console.log(`  - ${filePath} (${size} chars)`);
});
console.log('');
console.log('📋 What the system will detect:');
console.log('  - Languages: JavaScript, TypeScript (JSX)');
console.log('  - Frameworks: React, Express.js, Mongoose');
console.log('  - Project Type: Fullstack Web Application');
console.log('  - API Endpoints: /api/health, /api/users (GET, POST)');
console.log('  - Database: MongoDB');
console.log('  - Build Tools: npm scripts, React build');
console.log('');
console.log('🔧 Expected Generated MCP Tools:');
console.log('  1. test-api-endpoint - Test the REST API endpoints');
console.log('  2. build-frontend - Build React frontend');
console.log('  3. database-query - Query MongoDB collections'); 
console.log('  4. run-tests - Execute test suite');
console.log('  5. deploy-fullstack - Deploy both frontend and backend');
console.log('');
console.log('🐳 Generated Dockerfile will:');
console.log('  - Use Node.js 18 Alpine base image');
console.log('  - Set up multi-stage build for React');
console.log('  - Install production dependencies');
console.log('  - Build and serve the application');
console.log('  - Expose port 5000');
console.log('');
console.log('📊 JSON payload to send to MCP server:');
console.log(JSON.stringify({
  repoId: sampleRepository.repoId,
  projectName: sampleRepository.projectName,
  description: sampleRepository.description,
  files: Object.fromEntries(
    Object.entries(sampleRepository.files).slice(0, 3).map(([k, v]) => 
      [k, v.length > 200 ? v.substring(0, 200) + '...' : v]
    )
  )
}, null, 2));
console.log('');
console.log('🎯 To test this system:');
console.log('  1. Start MASS server: cargo run');
console.log('  2. Set OPENAI_API_KEY environment variable');
console.log('  3. Connect MCP client to ws://localhost:PORT/socket');
console.log('  4. Call store-repository tool with the above data');
console.log('  5. Check generated tools with list-repositories');
console.log('  6. Deploy with deploy-repository');