const express = require('express');
const dotenv = require('dotenv');
const path = require('path');
const fs = require('fs');
const { IgApiClient, RealtimeClient, useMultiFileAuthState } = require('nodejs-insta-private-api-mqt');

// Load environment variables
dotenv.config();

// Environment variables with fallbacks
const USERNAME = process.env.IG_USERNAME;
const PASSWORD = process.env.IG_PASSWORD;
const SESSION_DIR = process.env.SESSION_DIR || path.join(__dirname, 'auth_info_ig');
const PORT = process.env.PORT || 3000;
const REPLY_MESSAGE = process.env.REPLY_MESSAGE || 'धन्यवाद! 💖 आपके प्यार के लिए शुक्रिया। यह ऑटोमेटेड रिप्लाई है।';

// Validate required variables
if (!USERNAME || !PASSWORD) {
  console.error('❌ IG_USERNAME and IG_PASSWORD must be set in .env file');
  process.exit(1);
}

// Create Express app
const app = express();

// Health check endpoint
app.get('/', (req, res) => {
  res.json({
    status: 'running',
    bot: 'Instagram Love Bot',
    uptime: process.uptime()
  });
});

// Session directory ensure
if (!fs.existsSync(SESSION_DIR)) {
  fs.mkdirSync(SESSION_DIR, { recursive: true });
  console.log(`📁 Session directory created: ${SESSION_DIR}`);
}

// Main bot function
async function startBot() {
  console.log('🤖 Starting Instagram Love Bot...');
  
  const ig = new IgApiClient();
  
  // Load auth state
  const auth = await useMultiFileAuthState(SESSION_DIR);
  
  // Set device
  ig.state.usePresetDevice('Samsung Galaxy S25 Ultra');
  
  // Login or load session
  if (!auth.hasSession()) {
    console.log('🔑 First time login...');
    await ig.login({ username: USERNAME, password: PASSWORD });
    await auth.saveCreds(ig);
    console.log('✅ Login successful!');
  } else {
    console.log('🔄 Loading saved session...');
  }
  
  // Create realtime client
  const realtime = new RealtimeClient(ig);
  
  // Handle connection
  realtime.on('connected', () => {
    console.log('🎉 Bot is online and listening for messages!');
  });
  
  // Handle incoming messages
  realtime.on('message_live', async (msg) => {
    try {
      const messageText = msg.text || '';
      const threadId = msg.thread_id;
      const senderUsername = msg.username;
      
      // Only trigger on .love and ignore self messages
      if (messageText.trim() === '.love' && senderUsername !== USERNAME) {
        console.log(`🔔 @${senderUsername} triggered .love - replying...`);
        
        // Send reply
        await realtime.directCommands.sendText({
          threadId: threadId,
          text: REPLY_MESSAGE
        });
        
        console.log(`✅ Reply sent: "${REPLY_MESSAGE.substring(0, 30)}..."`);
      }
    } catch (error) {
      console.error('❌ Error processing message:', error.message);
    }
  });
  
  // Handle errors
  realtime.on('error', (error) => {
    console.error('❌ Realtime client error:', error);
  });
  
  // Start listening
  await realtime.startRealTimeListener();
  console.log('👂 Bot is now listening for .love messages...');
}

// Start server and bot
app.listen(PORT, () => {
  console.log(`🌐 Server is running on port ${PORT}`);
  startBot().catch(err => {
    console.error('💥 Bot crashed:', err);
    process.exit(1);
  });
});

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n👋 Shutting down...');
  process.exit(0);
});