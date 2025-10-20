# React Native AI Translation Tool

React Native implementation of the AI-powered media translation tool, providing native mobile experience for iOS and Android users.

## Features

- 🎤 Real-time voice-to-text conversion
- 📹 Video file processing and transcription
- 📄 Text translation and editing
- 💾 Translation history and management
- 👤 User profile and subscription management
- 📱 Native mobile performance and device integration

## Getting Started

### Prerequisites

- Node.js 16+ 
- Expo CLI: `npm install -g @expo/cli`
- Physical device or emulator/simulator

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm start

# Run on device
npm run android  # Android
npm run ios      # iOS
```

### Development

```bash
# Run tests
npm test

# Lint code
npm run lint

# Format code
npm run format
```

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── ui/             # Basic UI components
│   ├── layout/         # Layout components
│   └── features/       # Feature-specific components
├── screens/            # Main app screens
├── navigation/         # Navigation configuration
├── services/           # API and business logic
├── store/              # Redux state management
├── types/              # TypeScript type definitions
├── utils/              # Utility functions
└── assets/             # Images, fonts, etc.
```

## API Integration

This app integrates with the FastAPI backend running at:
- Development: `http://localhost:8000/api/v1`
- Production: `https://your-api-domain.com/api/v1`

## Build & Deploy

```bash
# Build for production
expo build:android
expo build:ios
```

## License

MIT