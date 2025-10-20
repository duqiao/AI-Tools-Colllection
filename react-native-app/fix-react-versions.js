#!/usr/bin/env node

/**
 * Fix React Version Mismatch Script
 * 
 * This script fixes the common React version mismatch error by ensuring
 * react and react-dom have the exact same version.
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Read package.json
const packageJsonPath = path.join(__dirname, 'package.json');
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));

// Get current versions
const reactVersion = packageJson.dependencies.react;
const reactDomVersion = packageJson.dependencies['react-dom'];

console.log('🔍 Current React versions:');
console.log(`   react:     ${reactVersion}`);
console.log(`   react-dom: ${reactDomVersion}`);

// Extract version numbers without the caret (^)
const extractVersion = (versionString) => {
  return versionString.replace('^', '').replace('~', '');
};

const reactVersionNumber = extractVersion(reactVersion);
const reactDomVersionNumber = extractVersion(reactDomVersion);

console.log('\n📊 Version comparison:');
console.log(`   react version number:     ${reactVersionNumber}`);
console.log(`   react-dom version number: ${reactDomVersionNumber}`);

if (reactVersionNumber !== reactDomVersionNumber) {
  console.log('\n❌ Version mismatch detected!');
  console.log('🔧 Fixing version mismatch...');
  
  try {
    // Update react to match react-dom
    const targetVersion = reactDomVersion;
    console.log(`📦 Updating react to version: ${targetVersion}`);
    
    execSync(`npm install react@${targetVersion}`, { stdio: 'inherit' });
    
    console.log('✅ React version updated successfully!');
    
    // Clear Metro cache
    console.log('🗑️  Clearing Metro cache...');
    execSync('npx expo start --clear', { stdio: 'inherit' });
    
  } catch (error) {
    console.error('❌ Failed to fix version mismatch:', error.message);
    process.exit(1);
  }
} else {
  console.log('\n✅ React versions are already aligned!');
  
  // Still clear cache if requested
  if (process.argv.includes('--clear-cache')) {
    console.log('🗑️  Clearing Metro cache...');
    execSync('npx expo start --clear', { stdio: 'inherit' });
  }
}

console.log('\n🎉 React version check complete!');